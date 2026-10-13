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
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..adapters._shared import alter_ego_id
from ..core import NameBook, NameSource, World, rules
from ..protocol import validate
from ..registry import LocalRegistry, orb_home
from ..terminal_host import (HostedTerminal, InvalidLaunchValue, Launch, ProviderNotInstalled,
                             UnknownProvider, available_providers, resolve_provider, winpty_factory)
from .messages import handle_client_message
from .realms import Feed, Observatory

REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_CLIENT = REPO_ROOT / "clients" / "web"
ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost"})
POLL_SECONDS = 0.25            # leitura dos realms com sessão ativa (D-087)
IDLE_POLL_SECONDS = 2.0        # sem sessão ativa: só a varredura de sessões novas, a cada 2 s (D-087)
CLIENT_QUEUE = 2000            # mensagens pendentes por cliente do mundo; além disso, só o snapshot
FEED_ON_CONNECT = 80           # linhas de Inner World por sessão enviadas a quem acabou de conectar
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
                 names: NameSource | None = None) -> None:
        self.observatory = observatory
        self.clock = clock or (lambda: datetime.now(UTC))
        self.world = World(names=names, recent_seconds=observatory.recent_seconds)
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
        world = self.world.snapshot(now)
        world["generated_at"] = now.isoformat()
        known = {realm["id"] for realm in world["realms"]}
        # Todo realm observado existe na cidade, mesmo sem nenhuma sessão ainda.
        world["realms"] += [{"id": rid, "alter_egos": [], "night": True} for rid in self.observatory.realms if rid not in known]
        for realm in world["realms"]:
            if realm["id"] in self.observatory.realms:
                realm.update({k: v for k, v in self.observatory.describe(realm["id"]).items() if k != "id"})
        world["realms"].sort(key=lambda r: r["id"])
        return world

    def poll_once(self) -> tuple[list[dict[str, Any]], bool]:
        """Lê todos os realms (chamado fora do loop). Devolve (eventos aplicados, mudou?)."""
        applied: list[dict[str, Any]] = []
        known = len(self.observatory.realms)
        for event in self.observatory.poll():
            if validate(event) is None and self.world.apply(event):
                applied.append(event)
                self.feed.add(event)
        for realm_id in self.observatory.realms:
            self.world.add_realm(realm_id)           # todo realm detectado existe, mesmo "de noite" (D-059)
        return applied, bool(applied) or len(self.observatory.realms) != known

    def history(self, realm_id: str) -> list[dict[str, Any]]:
        """O Histórico do realm: as sessões mais antigas que a sala, com o nome histórico quando já foi sorteado."""
        names = self.world.names
        out = []
        for meta in self.observatory.history(realm_id) if realm_id in self.observatory.realms else []:
            ego = alter_ego_id(meta.provider, meta.session_id)
            out.append({"alter_ego": ego, "provider": meta.provider, "session": meta.session_id,
                        "name": names.name_of(ego) if names is not None else None, "title": meta.title,
                        "model": meta.model, "started_at": meta.started_at, "updated_at": meta.updated_at})
        return out

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
    hub = Hub(observatory if observatory is not None else
              Observatory(config.realms, roots=config.roots, lookback_minutes=config.lookback_minutes,
                          recent_seconds=config.recent_seconds, home=config.home),
              names=names)

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI):
        task = asyncio.create_task(hub.run(config.poll_seconds, config.idle_poll_seconds))
        try:
            yield
        finally:
            task.cancel()

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
        for realm in hub.world.realms.values():
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
                if isinstance(msg, dict) and msg.get("type") == "history" and isinstance(msg.get("realm"), str):
                    await queue.put({"channel": "history", "realm": msg["realm"], "sessions": hub.history(msg["realm"])})
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
