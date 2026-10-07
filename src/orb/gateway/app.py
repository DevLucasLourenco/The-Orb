"""Gateway: liga terminal (Inner World) + adapter do provider + Core e distribui por WebSocket.

Uso:  the-orb --cwd PASTA [--port 8765]   (ou: python -m orb.gateway.app ...)
Abra a URL com token que o servidor imprime. Escuta SOMENTE em 127.0.0.1.

Segurança (o servidor abre um shell): loopback, token por execução, `Origin` local obrigatória,
lista fixa de executáveis, linha de comando validada (orb.terminal_host.launch).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import secrets
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse

from ..adapters._shared import realm_id_for
from ..adapters.claude import TranscriptReader
from ..adapters.codex import RolloutReader
from ..adapters.hermes import StateDbReader
from ..adapters.opencode import OpencodeDbReader
from ..core import World
from ..protocol import validate
from ..terminal_host import (HostedTerminal, InvalidLaunchValue, Launch, ProviderNotInstalled,
                             UnknownProvider, available_providers, resolve_provider, winpty_factory)
from .messages import handle_client_message

REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_PANEL = REPO_ROOT / "clients" / "web_panel" / "index.html"
ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost"})
POLL_SECONDS = 0.25


@dataclass
class GatewayConfig:
    cwd: str
    token: str = field(default_factory=lambda: secrets.token_urlsafe(24))
    realm: str | None = None
    home: Path | None = None            # raiz das pastas dos providers (testes)
    poll_seconds: float = POLL_SECONDS

    @property
    def realm_id(self) -> str:
        return self.realm or realm_id_for(self.cwd)


def authorized(token: str, query_token: str | None, origin: str | None) -> bool:
    """Protege contra páginas de terceiros abrindo um shell na máquina (CSWSH)."""
    if not query_token or not secrets.compare_digest(query_token, token):
        return False
    return origin is not None and urlparse(origin).hostname in ALLOWED_HOSTS


def telemetry_reader(provider: str | None, config: GatewayConfig, session_id: str | None, since: float):
    """Leitor de nível 0 do provider da sessão hospedada (ou None para um shell puro)."""
    if provider == "claude":
        return TranscriptReader(config.cwd, realm=config.realm_id, session_id=session_id, since=since, home=config.home)
    if provider == "codex":
        return RolloutReader(config.cwd, realm=config.realm_id, since=since, home=config.home)
    if provider == "hermes":
        hermes_home = config.home / "hermes" if config.home else None
        return StateDbReader(config.cwd, realm=config.realm_id, since=since, home=hermes_home)
    if provider == "opencode":
        data_dir = config.home / "opencode" if config.home else None
        return OpencodeDbReader(config.cwd, realm=config.realm_id, since=since, data_dir=data_dir)
    return None


def create_app(config: GatewayConfig, *, pty_factory: Callable = winpty_factory,
               check_installed: bool = True) -> FastAPI:
    app = FastAPI(title="The Orb")
    world = World()
    app.state.world = world
    app.state.config = config

    @app.get("/")
    async def index():
        return FileResponse(WEB_PANEL)

    @app.get("/config")
    async def get_config():
        return JSONResponse({"cwd": config.cwd, "realm": config.realm_id, "providers": available_providers()})

    @app.websocket("/ws")
    async def session(ws: WebSocket):
        if not authorized(config.token, ws.query_params.get("token"), ws.headers.get("origin")):
            await ws.close(code=4401)
            return
        await ws.accept()
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
            """Chamado pela thread da PTY. Depois que a conexão fecha o loop pode não existir mais:
            descartar é o certo (não há para quem entregar)."""
            try:
                loop.call_soon_threadsafe(out.put_nowait, (channel, payload))
            except RuntimeError:
                pass

        term = HostedTerminal(
            cwd=config.cwd, launch=launch, pty_factory=pty_factory, check_installed=check_installed,
            on_output=lambda data: from_pty_thread("term", data),
            on_exit=lambda code: from_pty_thread("exit", code),
        )
        started = time.time()
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
        await ws.send_json({"channel": "system", "info": f"provider={provider or 'shell'}",
                            "realm": config.realm_id, "session": session_id})
        await ws.send_json({"channel": "world", "world": world.snapshot()})
        reader = telemetry_reader(provider, config, session_id, started)

        async def pump_telemetry():
            while reader is not None:
                try:
                    events = await asyncio.to_thread(reader.poll)
                except Exception as exc:  # noqa: BLE001 - telemetria nunca derruba o terminal
                    await out.put(("system", f"telemetria: {exc}"))
                    events = []
                changed = False
                for event in events:
                    problem = validate(event)
                    if problem:
                        await out.put(("system", f"evento descartado: {problem}"))
                        continue
                    if world.apply(event):           # repetido não é reenviado
                        changed = True
                        await out.put(("event", event))
                if changed:
                    await out.put(("world", world.snapshot()))
                await asyncio.sleep(config.poll_seconds)

        async def pump_out():
            while True:
                channel, payload = await out.get()
                if channel == "term":
                    await ws.send_json({"channel": "term", "data": payload})
                elif channel == "event":
                    await ws.send_json({"channel": "event", "event": payload, "t": time.time()})
                elif channel == "world":
                    await ws.send_json({"channel": "world", "world": payload})
                elif channel == "exit":
                    await ws.send_json({"channel": "exit", "code": payload})
                else:
                    await ws.send_json({"channel": "system", "error": payload})

        tasks = [asyncio.create_task(pump_telemetry()), asyncio.create_task(pump_out())]
        try:
            while True:
                problem = handle_client_message(term, await ws.receive_text())
                if problem:
                    await out.put(("system", problem))     # avisa o cliente; a sessão continua
        except WebSocketDisconnect:
            pass
        finally:
            for task in tasks:
                task.cancel()
            term.close()

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="The Orb — Gateway (terminal + telemetria)")
    parser.add_argument("--cwd", default=os.getcwd(), help="pasta do projeto (o realm)")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--realm", default=None, help="id do realm (padrão: nome da pasta)")
    args = parser.parse_args()
    import uvicorn

    config = GatewayConfig(cwd=str(Path(args.cwd).resolve()), realm=args.realm)
    print(f"\nThe Orb — realm {config.realm_id} ({config.cwd})")
    print(f"Abra: http://127.0.0.1:{args.port}/?token={config.token}\n", flush=True)
    uvicorn.run(create_app(config), host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
