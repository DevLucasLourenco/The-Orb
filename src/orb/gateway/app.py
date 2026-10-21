"""Gateway: o servidor local do The Orb.

- Detecta os realms sozinho, pelas sessões que os 4 CLIs já gravaram, e os observa ao mesmo tempo (Core).
- `/world`: o mundo para o cliente 3D — snapshot, depois deltas e as linhas de Inner World.
- `/ws`: o terminal real de um Inner World (abre uma sessão nova do CLI num realm).
- `/`: o cliente 3D (clients/web).

Uso:  the-orb [--port 8765]        (ou: python -m orb.gateway.app). Abra a URL com token que o servidor imprime.
      Opções de depuração: --root, --realm e --lookback (R3: o Lucas nunca informa caminhos de projetos).

Segurança (o servidor abre shells): só 127.0.0.1, token por execução, `Origin` local obrigatória,
lista fixa de executáveis, linha de comando validada (orb.terminal_host.launch).
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import secrets
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..adapters._shared import alter_ego_id, norm_path
from ..core import NameBook, NameSource, World, XpSource, rules
from ..core.rules import GENERATED_FILE_PATTERNS, LineFilter
from ..probes import git_tracked_files
from ..protocol import validate
from ..registry import SETTINGS, LocalRegistry, Preferences, PreferencesFile, orb_home
from ..terminal_host import (
    HostedTerminal,
    InvalidLaunchValue,
    Launch,
    ProviderNotInstalled,
    UnknownProvider,
    available_providers,
    resolve_provider,
    winpty_factory,
)
from .messages import handle_client_message
from .probes import ChangeScheduler, CommitScheduler, LineScheduler
from .realms import Feed, Observatory, Realm

REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_CLIENT = REPO_ROOT / "clients" / "web"
ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost"})
POLL_SECONDS = 0.25            # leitura dos realms com sessão ativa (D-087)
HISTORY_LIMIT = 1000           # sessões do Histórico enviadas por pedido; o total sempre vai junto, nada é escondido
IDLE_POLL_SECONDS = 2.0        # sem sessão ativa: só a varredura de sessões novas, a cada 2 s (D-087)
CLIENT_QUEUE = 2000            # mensagens pendentes por cliente do mundo; além disso, só o snapshot
FEED_ON_CONNECT = 80           # linhas de Inner World por sessão enviadas a quem acabou de conectar
XP_EXTRACT_LIMIT = 200          # entradas do extrato de XP enviadas por pedido (as mais novas; o painel Progressão)
TIME_TICK_SECONDS = 15.0       # de quanto em quanto tempo se reavalia o que só o tempo muda (dormindo, sem sinal)


@dataclass
class GatewayConfig:
    realms: list[str] = field(default_factory=list)   # pastas de projeto (cada uma é um realm)
    roots: list[str] = field(default_factory=list)    # pastas cujas subpastas são realms
    token: str = field(default_factory=lambda: secrets.token_urlsafe(24))
    home: Path | None = None               # raiz das pastas dos providers (testes)
    poll_seconds: float = POLL_SECONDS
    idle_poll_seconds: float = IDLE_POLL_SECONDS
    recent_seconds: float = rules.RECENT_SESSION_SECONDS   # o prazo da sala (R28a): o ticket 07 o torna configurável
    lookback_minutes: float | None = None                  # [depuração] estreita a leitura do conteúdo
    state_dir: Path | None = None          # pasta do Orb (registro local, R36); sem ela os nomes vivem só em memória


def authorized(token: str, query_token: str | None, origin: str | None) -> bool:
    """Protege contra páginas de terceiros abrindo um shell na máquina (CSWSH)."""
    if not query_token or not secrets.compare_digest(query_token, token):
        return False
    return origin is not None and urlparse(origin).hostname in ALLOWED_HOSTS


class Hub:
    """O mundo vivo: observa os realms, aplica no Core e distribui aos clientes do mundo.

    O Hub é a borda que conhece a hora: o Core é puro e só recebe a hora que o Hub informa (R47)."""

    def __init__(self, observatory: Observatory, *, clock: Callable[[], datetime] | None = None,
                 names: NameSource | None = None, preferences: PreferencesFile | None = None,
                 tracked: Callable[[Any], list[str] | None] | None = None, xp: XpSource | None = None) -> None:
        self.observatory = observatory
        self.clock = clock or (lambda: datetime.now(UTC))
        self.preferences_file = preferences
        self.preferences = preferences.load() if preferences is not None else Preferences()
        if preferences is not None:
            observatory.set_recent_seconds(self.preferences.recent_seconds)     # o que o Lucas escolheu vale desde a subida
        self.world = World(names=names, recent_seconds=observatory.recent_seconds, window_percent=self.preferences.window_percent, xp=xp)
        self._sync_hidden()
        # O Probe de linhas (R19) roda numa thread própria, um realm por vez; aqui só se liga e se recebem os eventos.
        self.lines = LineScheduler(lambda: self.observatory.realms, self._line_filter, lambda: self.world.hidden,
                                   wall=self.clock, tracked=tracked or git_tracked_files)
        # O Probe das alterações locais (R20b): lê o git de cada realm a cada poucos segundos, só leitura, numa thread própria.
        self.changes = ChangeScheduler(lambda: self.observatory.realms, lambda: self.world.hidden, wall=self.clock)
        # O Probe dos commits (R53): pergunta ao git pelos commits que as sessões disseram ter feito; o mundo diz quais conferir.
        self.commits = CommitScheduler(lambda: self.observatory.realms, lambda: self.world.hidden, self.world.pending_commits, wall=self.clock)
        self.feed = Feed()
        self.clients: set[asyncio.Queue[dict[str, Any]]] = set()
        self._published_time_key: tuple | None = None      # o que os clientes viram da última vez

    def realms(self) -> list[dict[str, Any]]:
        return [self.observatory.describe(rid) for rid in sorted(self.observatory.realms)]

    def registry_error(self) -> str | None:
        """Por que o registro local não está gravando (nomes só em memória), ou None."""
        names = self.world.names
        return names.error if names is not None else None

    def snapshot(self, now: datetime | None = None) -> dict[str, Any]:
        """O mundo na hora do servidor (`generated_at`): é com ela que o Core deriva dormindo e sem sinal."""
        now = now or self.clock()
        for realm_id in self.observatory.realms:
            self.world.add_realm(realm_id)           # todo realm observado existe e tem lote, mesmo sem nenhuma sessão ainda
        world = self.world.snapshot(now)
        world["generated_at"] = now.isoformat()
        for realm in world["realms"]:
            if realm["id"] in self.observatory.realms:
                realm.update({k: v for k, v in self.observatory.describe(realm["id"]).items() if k != "id"})
        world["realms"].sort(key=lambda r: r["id"])
        return world

    def poll_once(self) -> tuple[list[dict[str, Any]], bool]:
        """Lê todos os realms (chamado fora do loop). Devolve (eventos aplicados, mudou?)."""
        applied: list[dict[str, Any]] = []
        known = len(self.observatory.realms)
        events = self.observatory.poll() + self.lines.drain() + self.changes.drain() + self.commits.drain()
        for realm_id in self.observatory.realms:
            self.world.add_realm(realm_id)           # todo realm detectado existe, mesmo "de noite" (D-059)
        self._sync_hidden()                          # antes de aplicar: um realm escondido recém-detectado nunca aparece, nem por um instante
        for event in events:
            if validate(event) is None and self.world.apply(event):
                applied.append(event)
                self.feed.add(event)
        shown = [e for e in applied if e["realm"] not in self.world.hidden]       # o que o Lucas escondeu não é distribuído
        return shown, bool(shown) or len(self.observatory.realms) != known

    def _line_filter(self, realm: Realm) -> LineFilter:
        return self.preferences.line_filter(norm_path(realm.cwd))

    def _sync_hidden(self) -> None:
        """Os realms escondidos (R3c) são guardados pelo caminho do projeto; o id pode mudar, o caminho não."""
        hidden = set(self.preferences.hidden_realms)
        self.world.set_hidden(rid for rid, realm in self.observatory.realms.items() if norm_path(realm.cwd) in hidden)

    def update_preferences(self, changes: dict[str, Any]) -> None:
        """Muda as preferências do Lucas: valida (`ValueError` se não der), grava na pasta do Orb e aplica na hora.
        `hidden_realms` chega como ids de realms; só os conhecidos contam, e os caminhos escondidos de projetos que o
        Orb não detecta agora são mantidos (o projeto pode voltar). Roda fora do loop: cada atribuição ao mundo e ao
        Observatório é atômica, então quem lê vê o valor antigo ou o novo, nunca um meio-termo."""
        changes = dict(changes)
        if "hidden_realms" in changes:
            ids = changes["hidden_realms"]
            if isinstance(ids, (str, bytes)) or not isinstance(ids, (list, tuple, set)):
                raise ValueError("realms escondidos: precisa ser uma lista")
            known = {norm_path(realm.cwd) for realm in self.observatory.realms.values()}
            chosen = [norm_path(self.observatory.realms[i].cwd) for i in ids if isinstance(i, str) and i in self.observatory.realms]
            changes["hidden_realms"] = chosen + [p for p in self.preferences.hidden_realms if p not in known]
        if "realm_lines" in changes:                      # o cliente fala em ids de realm; o arquivo guarda o caminho do projeto
            own = changes["realm_lines"]
            if not isinstance(own, dict):
                raise ValueError("filtro de linhas por realm: precisa ser um objeto")
            changes["realm_lines"] = {norm_path(self.observatory.realms[i].cwd): value for i, value in own.items()
                                      if isinstance(i, str) and i in self.observatory.realms}
        new = self.preferences.updated(**changes)
        if self.preferences_file is not None:
            self.preferences_file.save(new)
        self.preferences = new
        self.observatory.set_recent_seconds(new.recent_seconds)
        self.world.set_recent_seconds(new.recent_seconds)
        self.world.set_window_percent(new.window_percent)         # o x das janelas vale na hora (R20d)
        self._sync_hidden()
        if "lines" in changes:
            self.lines.refresh()                         # o Lucas mexeu no filtro de todos: conta tudo de novo já
        elif "realm_lines" in changes:
            paths = {norm_path(r.cwd): rid for rid, r in self.observatory.realms.items()}
            self.lines.refresh([paths[p] for p in changes["realm_lines"] if p in paths])      # só os realms que ele mexeu, na frente

    def _own_line_options(self, realm: Realm) -> dict[str, Any] | None:
        """O que este realm muda no filtro de linhas (só isso; o resto vem do geral), ou None."""
        own = self.preferences.realm_lines.get(norm_path(realm.cwd))
        return None if not own else {k: list(v) if k == "exclude" else v for k, v in own.items()}

    def settings(self) -> dict[str, Any]:
        """O que a tela de configurações mostra: todos os realms detectados (inclusive os escondidos), os valores
        de hoje e a tabela de opções numéricas (os tickets 09 e 11 só acrescentam linhas a ela)."""
        realms = [{"id": rid, "name": realm.name, "cwd": realm.cwd, "hidden": rid in self.world.hidden,
                   "lines": self._own_line_options(realm),
                   "lines_note": self.lines.notes.get(rid) or self.lines.errors.get(rid)}
                  for rid, realm in sorted(self.observatory.realms.items())]
        options = [{"key": s.key, "kind": s.kind, "label": s.label, "unit": s.unit, "minimum": s.minimum, "maximum": s.maximum,
                    "value": self.preferences.options.get(s.key, s.default)} for s in SETTINGS]
        error = self.preferences_file.error if self.preferences_file is not None else None
        general = self.preferences.lines
        return {"realms": realms, "options": options, "error": error, "persistent": self.preferences_file is not None,
                "lines": {"include_markdown": general.include_markdown, "exclude": list(general.exclude),
                          "default_exclude": list(GENERATED_FILE_PATTERNS)},
                "preferences": {**self.preferences.options, "hidden_realms": sorted(self.world.hidden)}}

    def xp_extract(self) -> list[dict[str, Any]]:
        """O extrato de XP para o painel Progressão (as `XP_EXTRACT_LIMIT` entradas mais novas)."""
        return self.world.xp_extract(XP_EXTRACT_LIMIT)

    def history(self, realm_id: str) -> list[dict[str, Any]]:
        """O Histórico do realm: as sessões mais antigas que a sala, com o nome histórico quando já foi sorteado."""
        metas = self._history_metas(realm_id)[:HISTORY_LIMIT]
        egos = [alter_ego_id(meta.provider, meta.session_id) for meta in metas]
        names = self.world.names.names_of(egos) if self.world.names is not None else {}
        return [{"alter_ego": ego, "provider": meta.provider, "session": meta.session_id, "name": names.get(ego),
                 "title": meta.title, "model": meta.model, "started_at": meta.started_at, "updated_at": meta.updated_at}
                for ego, meta in zip(egos, metas, strict=True)]

    def _history_metas(self, realm_id: str) -> list:
        if realm_id not in self.observatory.realms:
            return []
        return self.observatory.history(realm_id, now=self.clock().timestamp())      # a hora do mundo, a mesma do Core (R47)

    def history_total(self, realm_id: str) -> int:
        """Quantas sessões o Histórico do realm tem (a lista enviada pode vir cortada em `HISTORY_LIMIT`)."""
        return len(self._history_metas(realm_id))

    def poll_interval(self, fast: float, idle: float) -> float:
        """Quanto esperar até a próxima leitura: `fast` com alguma sessão ativa, `idle` sem nenhuma (D-087). A
        varredura de sessões novas continua a cada 2 s de qualquer jeito (cada leitor espaça a dele)."""
        return fast if self.world.any_active(self.clock()) else max(fast, idle)

    def publish(self, message: dict[str, Any]) -> None:
        for queue in list(self.clients):
            if queue.full():
                continue           # cliente lento: recebe o próximo snapshot, não trava os outros
            queue.put_nowait(message)

    def publish_world(self) -> None:
        """Envia o mundo (na hora do servidor) a todos os clientes e guarda o que eles viram do tempo."""
        now = self.clock()
        self._published_time_key = self.world.time_key(now)
        self.publish({"channel": "world", "world": self.snapshot(now)})

    def time_changed(self) -> bool:
        """Só o passar do tempo mudou algo (alguém dormiu, um subagente ficou sem sinal) desde o
        último mundo enviado? Assim os clientes são avisados sem esperar um evento novo."""
        return self.world.time_key(self.clock()) != self._published_time_key

    async def run(self, poll_seconds: float, idle_poll_seconds: float | None = None) -> None:
        self.lines.start()
        self.changes.start()
        self.commits.start()
        last_tick = time.monotonic()
        while True:
            try:
                applied, changed = await asyncio.to_thread(self.poll_once)
            except Exception:  # noqa: BLE001 - observação nunca derruba o servidor
                applied, changed = [], False
            for event in applied:
                if event.get("inner"):
                    self.publish({"channel": "event", "event": event})
            now = time.monotonic()
            if changed:
                self.publish_world()
                last_tick = now
            elif now - last_tick >= TIME_TICK_SECONDS:
                last_tick = now
                if self.time_changed():
                    self.publish_world()
            await asyncio.sleep(self.poll_interval(poll_seconds, idle_poll_seconds if idle_poll_seconds is not None else poll_seconds))


def create_app(config: GatewayConfig, *, pty_factory: Callable = winpty_factory,
               check_installed: bool = True, observatory: Observatory | None = None) -> FastAPI:
    names = LocalRegistry(config.state_dir) if config.state_dir is not None else NameBook()
    preferences = PreferencesFile(config.state_dir) if config.state_dir is not None else None
    hub = Hub(observatory if observatory is not None else
              Observatory(config.realms, roots=config.roots, lookback_minutes=config.lookback_minutes,
                          recent_seconds=config.recent_seconds, home=config.home),
              names=names, preferences=preferences, xp=names if isinstance(names, LocalRegistry) else None)       # o extrato de XP mora no mesmo registro

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI):
        task = asyncio.create_task(hub.run(config.poll_seconds, config.idle_poll_seconds))
        try:
            yield
        finally:
            task.cancel()
            hub.lines.stop()
            hub.changes.stop()
            hub.commits.stop()

    app = FastAPI(title="The Orb", lifespan=lifespan)
    app.state.hub = hub
    app.state.config = config
    if WEB_CLIENT.is_dir():
        app.mount("/static", StaticFiles(directory=WEB_CLIENT), name="static")

    @app.get("/")
    async def index():
        return FileResponse(WEB_CLIENT / "index.html")

    @app.get("/config")
    async def get_config():
        return JSONResponse({"realms": hub.realms(), "providers": available_providers(),
                             "registry_error": hub.registry_error()})

    @app.websocket("/world")
    async def world_stream(ws: WebSocket):
        if not authorized(config.token, ws.query_params.get("token"), ws.headers.get("origin")):
            await ws.close(code=4401)
            return
        await ws.accept()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=CLIENT_QUEUE)
        await ws.send_json({"channel": "world", "world": hub.snapshot()})
        for realm_id, realm in hub.world.realms.items():
            if realm_id in hub.world.hidden:
                continue
            for ego_id in realm:
                lines = hub.feed.history(ego_id, FEED_ON_CONNECT)
                if lines:
                    await ws.send_json({"channel": "feed", "alter_ego": ego_id, "events": lines})
        hub.clients.add(queue)

        async def pump():
            while True:
                await ws.send_json(await queue.get())

        sender = asyncio.create_task(pump())
        try:
            while True:
                raw = await ws.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(msg, dict) and msg.get("type") == "settings":
                    await queue.put({"channel": "settings", **hub.settings()})
                elif isinstance(msg, dict) and msg.get("type") == "preferences":
                    error = None
                    try:
                        changes = {k: v for k, v in msg.items() if k != "type"}
                        await asyncio.to_thread(hub.update_preferences, changes)     # grava na pasta do Orb: fora do loop
                    except ValueError as exc:
                        error = str(exc)
                    except OSError:
                        error = "não foi possível gravar as preferências na pasta do Orb"     # sem o caminho do sistema
                    reply = {"channel": "settings", **hub.settings()}
                    if error is not None:
                        await queue.put({**reply, "error": error})                   # só quem pediu vê a recusa
                    else:
                        hub.publish(reply)                                           # todos os clientes veem as caixas e a cidade novas
                        hub.publish_world()
                elif isinstance(msg, dict) and msg.get("type") == "history" and isinstance(msg.get("realm"), str):
                    sessions = await asyncio.to_thread(hub.history, msg["realm"])    # nomes vêm do disco: fora do loop
                    await queue.put({"channel": "history", "realm": msg["realm"], "sessions": sessions,
                                     "total": max(len(sessions), hub.history_total(msg["realm"]))})
                elif isinstance(msg, dict) and msg.get("type") == "xp":
                    await queue.put({"channel": "xp", "entries": hub.xp_extract(), "limit": XP_EXTRACT_LIMIT})
                elif isinstance(msg, dict) and msg.get("type") == "feed" and isinstance(msg.get("alter_ego"), str):
                    await queue.put({"channel": "feed", "alter_ego": msg["alter_ego"],
                                     "events": hub.feed.history(msg["alter_ego"])})
        except WebSocketDisconnect:
            pass
        finally:
            hub.clients.discard(queue)
            sender.cancel()

    @app.websocket("/ws")
    async def terminal_session(ws: WebSocket):
        if not authorized(config.token, ws.query_params.get("token"), ws.headers.get("origin")):
            await ws.close(code=4401)
            return
        await ws.accept()
        realms = hub.observatory.realms
        realm = realms.get(ws.query_params.get("realm") or "") or next(iter(realms.values()), None)
        if realm is None:
            await ws.send_json({"channel": "system", "error": "nenhum realm detectado ainda"})
            await ws.close()
            return
        loop = asyncio.get_running_loop()
        out: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()
        mode = ws.query_params.get("provider", "auto")       # "shell" | provider | "auto"
        model = ws.query_params.get("model") or None
        try:
            provider = None if mode == "shell" else resolve_provider(None if mode == "auto" else mode, model)
            session_id = str(uuid.uuid4()) if provider == "claude" else None
            launch = None if provider is None else Launch(
                provider=provider, model=model, session_id=session_id,
                session_name=f"orb-{session_id[:8]}" if session_id else None)
            if launch is not None:
                launch.line()                                   # valida antes de abrir o terminal
        except (UnknownProvider, InvalidLaunchValue) as exc:
            await ws.send_json({"channel": "system", "error": f"não foi possível abrir: {exc}"})
            await ws.close()
            return

        def from_pty_thread(channel: str, payload: Any) -> None:
            """Chamado pela thread da PTY; depois que a conexão fecha não há para quem entregar."""
            try:
                loop.call_soon_threadsafe(out.put_nowait, (channel, payload))
            except RuntimeError:
                pass

        term = HostedTerminal(cwd=realm.cwd, launch=launch, pty_factory=pty_factory, check_installed=check_installed,
                              on_output=lambda data: from_pty_thread("term", data),
                              on_exit=lambda code: from_pty_thread("exit", code))
        try:
            term.start()
        except ProviderNotInstalled as exc:
            await ws.send_json({"channel": "system", "error": f"CLI não instalado: {exc}"})
            await ws.close()
            return
        except Exception as exc:  # noqa: BLE001
            await ws.send_json({"channel": "system", "error": f"falha ao abrir terminal: {exc}"})
            await ws.close()
            return
        # Com Claude o Orb escolhe o id da sessão: o cliente já sabe qual personagem é este terminal.
        await ws.send_json({"channel": "system", "info": f"provider={provider or 'shell'}", "realm": realm.id,
                            "alter_ego": alter_ego_id(provider, session_id) if session_id and provider else None})

        async def pump_out():
            while True:
                channel, payload = await out.get()
                if channel == "term":
                    await ws.send_json({"channel": "term", "data": payload})
                elif channel == "exit":
                    await ws.send_json({"channel": "exit", "code": payload})
                else:
                    await ws.send_json({"channel": "system", "error": payload})

        sender = asyncio.create_task(pump_out())
        try:
            while True:
                problem = handle_client_message(term, await ws.receive_text())
                if problem:
                    await out.put(("system", problem))     # avisa o cliente; a sessão continua
        except WebSocketDisconnect:
            pass
        finally:
            sender.cancel()
            term.close()

    return app


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="The Orb — o mundo das suas sessões de IA")
    parser.add_argument("--port", type=int, default=8765)
    debug = parser.add_argument_group("depuração", "Os projetos são detectados sozinhos; estas opções existem só para depurar.")
    debug.add_argument("--root", action="append", default=[], help="pasta cujas subpastas viram realms, mesmo sem sessão")
    debug.add_argument("--realm", action="append", default=[], help="pasta que vira um realm, mesmo sem sessão (repita para vários)")
    debug.add_argument("--cwd", action="append", default=[], help="o mesmo que --realm")
    debug.add_argument("--lookback", type=float, default=None, help="minutos: estreita a leitura do conteúdo (padrão: a sala de 10 dias)")
    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace) -> GatewayConfig:
    """Sem argumentos nenhum realm é informado: a cidade se monta sozinha (R3)."""
    return GatewayConfig(realms=[str(Path(p).resolve()) for p in (args.realm + args.cwd)],
                         roots=[str(Path(p).resolve()) for p in args.root], lookback_minutes=args.lookback,
                         state_dir=orb_home())


def main() -> None:
    args = parse_args()
    import uvicorn

    config = config_from_args(args)
    print("\nThe Orb")
    print("  · os projetos são detectados pelas sessões dos CLIs")
    print(f"  · registro local do Orb: {config.state_dir}")
    for root in config.roots:
        print(f"  · [depuração] cada projeto em {root}")
    for folder in config.realms:
        print(f"  · [depuração] {folder}")
    print(f"\nAbra: http://127.0.0.1:{args.port}/?token={config.token}\n", flush=True)
    uvicorn.run(create_app(config), host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
