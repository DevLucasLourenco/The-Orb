"""Observação contínua dos realms (a cidade): cada projeto, os 4 providers ao mesmo tempo.

Qualquer sessão que nasça na pasta de um realm, ou numa subpasta dele (ex.: worktrees), aberta pelo
Orb ou fora dele, de qualquer CLI, aparece sozinha como um Alter Ego que carrega o seu provider.
Tudo é nível 0: somente leitura.

Desempenho: Codex, Hermes e opencode guardam tudo numa loja única (rollouts, state.db, opencode.db),
então cada um tem UM leitor para a cidade inteira, que distribui as sessões pelos realms. O Claude
guarda uma pasta por projeto, então tem um leitor (barato) por realm.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ..adapters._shared import norm_path, realm_id_for, realm_resolver
from ..adapters.claude import TranscriptReader
from ..adapters.codex import RolloutReader
from ..adapters.hermes import StateDbReader
from ..adapters.opencode import OpencodeDbReader
from ..protocol import Event

FEED_PER_ALTER_EGO = 300       # linhas de Inner World guardadas por sessão (para quem conecta depois)
ROOT_RESCAN_SECONDS = 30.0     # pastas novas dentro de um --root viram realms sozinhas


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
    """Todos os realms observados e os leitores que os alimentam."""

    def __init__(self, folders: list[str] = (), *, roots: list[str] = (), lookback_minutes: float = 30.0,
                 home: Path | None = None, now: float | None = None) -> None:
        self.since = (time.time() if now is None else now) - lookback_minutes * 60
        self.home = home
        self.roots = [Path(r) for r in roots]
        self.realms: dict[str, Realm] = {}
        self.errors: dict[str, str] = {}               # leitor -> último erro (degradação visível)
        self._resolve = realm_resolver({})
        self._last_root_scan = float("-inf")
        self.readers: dict[str, Reader] = {
            "codex": RolloutReader(since=self.since, home=home, realm_of=self.realm_of),
            "hermes": StateDbReader(since=self.since, home=home / "hermes" if home else None, realm_of=self.realm_of),
            "opencode": OpencodeDbReader(since=self.since, data_dir=home / "opencode" if home else None,
                                         realm_of=self.realm_of),
        }
        for folder in folders:
            self.add(folder)
        self.sync_roots(force=True)

    def realm_of(self, cwd: Any) -> str | None:
        return self._resolve(cwd)

    def add(self, folder: str) -> str:
        """Torna uma pasta um realm (idempotente). Devolve o id do realm."""
        cwd = str(Path(folder).resolve())
        for realm in self.realms.values():
            if norm_path(realm.cwd) == norm_path(cwd):
                return realm.id
        rid = base = realm_id_for(cwd)
        n = 2
        while rid in self.realms:
            rid, n = f"{base}-{n}", n + 1
        self.realms[rid] = Realm(rid, cwd)
        self.readers[f"claude:{rid}"] = TranscriptReader(cwd, realm=rid, since=self.since, home=self.home)
        self._resolve = realm_resolver({r.id: r.cwd for r in self.realms.values()})
        return rid

    def sync_roots(self, force: bool = False) -> None:
        now = time.monotonic()
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
        errors = {name.split(":")[0]: msg for name, msg in self.errors.items()
                  if ":" not in name or name == f"claude:{realm_id}"}
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
