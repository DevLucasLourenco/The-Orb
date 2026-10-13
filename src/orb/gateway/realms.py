"""Observação contínua dos realms (a cidade): cada projeto, os 4 providers ao mesmo tempo.

Os realms nascem das sessões que os CLIs já gravaram (R3, R3a): um **índice de metadados** de todas as
sessões (pasta, datas, título; R48, camada 1) diz quais projetos existem, e `ProjectResolver` decide a que
projeto cada pasta pertence (worktrees contam para o principal; pasta do usuário, sistema, temporárias e
inexistentes ficam de fora). O conteúdo continua lido de forma incremental, só das sessões ativas.
Tudo é nível 0: somente leitura.

Desempenho: cada provider tem UM leitor para a cidade inteira, que distribui as sessões pelos realms.
O índice é varrido de tempos em tempos (barato: primeira linha, linhas de uma tabela, datas de arquivos).
"""
from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ..adapters._shared import SessionIndex, norm_path, realm_id_for, realm_resolver
from ..adapters.claude import TranscriptIndex, TranscriptReader
from ..adapters.codex import RolloutIndex, RolloutReader
from ..adapters.hermes import StateDbIndex, StateDbReader
from ..adapters.opencode import OpencodeDbIndex, OpencodeDbReader
from ..protocol import Event
from .projects import Exclusions, ProjectResolver

FEED_PER_ALTER_EGO = 300       # linhas de Inner World guardadas por sessão (para quem conecta depois)
ROOT_RESCAN_SECONDS = 30.0     # [depuração] pastas novas dentro de um --root viram realms sozinhas
INDEX_RESCAN_SECONDS = 30.0    # de quanto em quanto tempo o índice de sessões é varrido de novo
NOT_A_PROJECT_RETRY = 60.0     # segundos até reavaliar uma pasta que ainda não era projeto (ex.: ainda não existia)


class Reader(Protocol):
    def poll(self) -> list[Event]: ...


@dataclass(frozen=True)
class Realm:
    id: str
    cwd: str

    @property
    def name(self) -> str:
        return Path(self.cwd).name or self.id


class Observatory:
    """Todos os realms observados e os leitores que os alimentam. É a borda que conhece o disco e o relógio
    (`clock`, em segundos monotônicos, entra por parâmetro para os testes)."""

    def __init__(self, folders: list[str] = (), *, roots: list[str] = (), lookback_minutes: float = 30.0,
                 home: Path | None = None, now: float | None = None, exclusions: Exclusions | None = None,
                 index_every: float = INDEX_RESCAN_SECONDS, clock: Callable[[], float] = time.monotonic) -> None:
        self.since = (time.time() if now is None else now) - lookback_minutes * 60
        self.home = home
        self.roots = [Path(r) for r in roots]
        self.resolver = ProjectResolver(exclusions)
        self.index_every = index_every
        self._clock = clock
        self.realms: dict[str, Realm] = {}             # trocado por um dicionário novo a cada realm (leitura sem trava)
        self.errors: dict[str, str] = {}               # leitor -> último erro (degradação visível)
        self._ids: dict[str, str] = {}                 # caminho normalizado do projeto -> id do realm
        self._containing = realm_resolver({})          # pasta -> realm conhecido que a contém
        self._provider_roots: dict[str, str] = {}      # pasta de sessão -> raiz que o provider informou (vem do índice)
        self._projects: dict[tuple, tuple[float, str | None]] = {}   # decisões já tomadas, com validade se negativas
        self._last_index = float("-inf")
        self._last_root_scan = float("-inf")
        hermes_home = home / "hermes" if home else None
        opencode_dir = home / "opencode" if home else None
        self.indexes: dict[str, SessionIndex] = {
            "claude": TranscriptIndex(home=home),
            "codex": RolloutIndex(home=home),
            "hermes": StateDbIndex(home=hermes_home),
            "opencode": OpencodeDbIndex(data_dir=opencode_dir),
        }
        self.readers: dict[str, Reader] = {
            "claude": TranscriptReader(since=self.since, home=home, realm_of=self.realm_of),
            "codex": RolloutReader(since=self.since, home=home, realm_of=self.realm_of),
            "hermes": StateDbReader(since=self.since, home=hermes_home, realm_of=self.realm_of),
            "opencode": OpencodeDbReader(since=self.since, data_dir=opencode_dir, realm_of=self.realm_of),
        }
        for folder in folders:
            self.add(folder)
        self.sync_roots(force=True)

    # --- de pasta para realm --------------------------------------------------------------------
    def realm_of(self, cwd: Any) -> str | None:
        """O realm da pasta de uma sessão (criado na hora, se for de um projeto novo), ou `None`. Os leitores
        passam o valor cru do arquivo ou do banco: o que não for texto vira `None`, nunca um erro."""
        root = self._provider_roots.get(cwd) if isinstance(cwd, str) else None
        return self._realm_for(cwd, root)

    def _realm_for(self, cwd: Any, provider_root: Any) -> str | None:
        if not isinstance(cwd, str) or not cwd:
            return None
        if not isinstance(provider_root, str):
            provider_root = None
        project = self._project(cwd, provider_root, fallback=False)
        if project is None:
            known = self._containing(cwd)      # pasta dentro de um realm já conhecido (ex.: worktree apagado)
            if known:
                return known
            project = self._project(cwd, provider_root, fallback=True)
        return self._realm_id(project) if project else None

    def _project(self, cwd: str, provider_root: str | None, *, fallback: bool) -> str | None:
        key = (norm_path(cwd), norm_path(provider_root) if provider_root else None, fallback)
        now = self._clock()
        hit = self._projects.get(key)
        if hit is not None and (hit[1] is not None or hit[0] > now):
            return hit[1]
        project = self.resolver.project_of(cwd, provider_root, fallback=fallback)
        self._projects[key] = (now + NOT_A_PROJECT_RETRY, project)
        return project

    def _realm_id(self, project: str) -> str:
        """O id do realm de um projeto; o realm nasce na primeira vez. O id é o nome da pasta, com sufixo
        quando outro projeto já ficou com ele (quem já está na cidade nunca muda de id)."""
        key = norm_path(project)
        if key in self._ids:
            return self._ids[key]
        rid = base = realm_id_for(project)
        n = 2
        while rid in self.realms:
            rid, n = f"{base}-{n}", n + 1
        self._ids[key] = rid
        self.realms = {**self.realms, rid: Realm(rid, project)}
        self._containing = realm_resolver({r.id: r.cwd for r in self.realms.values()})
        return rid

    def add(self, folder: str) -> str:
        """[depuração] Torna uma pasta um realm, mesmo sem sessão (idempotente). Devolve o id do realm."""
        return self._realm_id(str(Path(folder).resolve()))

    # --- descoberta -----------------------------------------------------------------------------
    def refresh_index(self, force: bool = False) -> None:
        """Varre o índice de sessões dos 4 providers e cria os realms que ainda não existem."""
        now = self._clock()
        if not force and now - self._last_index < self.index_every:
            return
        self._last_index = now
        found: set[tuple[str, str | None]] = set()
        for name, index in self.indexes.items():
            try:
                for meta in index.scan():
                    if meta.parent_id:
                        continue                   # subagente é da Team, não define projeto
                    found.add((meta.cwd, meta.project_root))
                    if meta.project_root:
                        self._provider_roots[meta.cwd] = meta.project_root
                self.errors.pop(f"index:{name}", None)
            except Exception as exc:  # noqa: BLE001 - isolamento de falha por provider
                self.errors[f"index:{name}"] = f"{type(exc).__name__}: {exc}"
        unresolved: list[tuple[str, str | None]] = []
        projects: set[str] = set()
        for cwd, root in sorted(found, key=lambda pair: (norm_path(pair[0]), pair[0], pair[1] or "")):
            project = self._project(cwd, root, fallback=False)
            if project:
                projects.add(project)
            else:
                unresolved.append((cwd, root))
        for project in sorted(projects, key=lambda p: (norm_path(p), p)):   # ordem estável: nomes iguais ganham sufixo sempre igual
            self._realm_id(project)
        for cwd, root in sorted(unresolved, key=lambda pair: (len(norm_path(pair[0])), norm_path(pair[0]))):
            self._realm_for(cwd, root)                           # a pasta mais curta primeiro: as de dentro entram nela

    def sync_roots(self, force: bool = False) -> None:
        now = self._clock()
        if not self.roots or (not force and now - self._last_root_scan < ROOT_RESCAN_SECONDS):
            return
        self._last_root_scan = now
        for root in self.roots:
            try:
                children = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))
            except OSError:
                continue
            for child in children:
                self.add(str(child))

    def poll(self) -> list[Event]:
        """Lê todos os leitores. A falha de um não afeta os outros."""
        self.sync_roots()
        self.refresh_index()
        events: list[Event] = []
        for name, reader in list(self.readers.items()):
            try:
                events.extend(reader.poll())
                self.errors.pop(name, None)
            except Exception as exc:  # noqa: BLE001 - isolamento de falha por provider
                self.errors[name] = f"{type(exc).__name__}: {exc}"
        return events

    def describe(self, realm_id: str) -> dict[str, Any]:
        realm = self.realms[realm_id]
        errors: dict[str, str] = {}
        for name, message in dict(self.errors).items():        # cópia: a thread de leitura altera `errors` ao mesmo tempo
            provider = name.removeprefix("index:")              # falha do índice e do leitor aparecem no mesmo provider
            errors[provider] = f"{errors[provider]}; {message}" if provider in errors else message
        return {"id": realm.id, "name": realm.name, "cwd": realm.cwd, "errors": errors}


class Feed:
    """As últimas linhas de Inner World de cada Alter Ego (memória limitada)."""

    def __init__(self, per_alter_ego: int = FEED_PER_ALTER_EGO) -> None:
        self.per_alter_ego = per_alter_ego
        self._lines: dict[str, deque[Event]] = {}

    def add(self, event: Event) -> bool:
        if not event.get("inner") or not event.get("alter_ego"):
            return False
        lines = self._lines.get(event["alter_ego"])
        if lines is None:
            lines = self._lines[event["alter_ego"]] = deque(maxlen=self.per_alter_ego)
        lines.append(event)
        return True

    def history(self, alter_ego: str, limit: int | None = None) -> list[Event]:
        lines = list(self._lines.get(alter_ego, ()))
        return lines[-limit:] if limit else lines
