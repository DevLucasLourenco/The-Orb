"""Spike 1: Terminal Host + telemetria nível 0.

Uso:  python server.py [--cwd PASTA] [--port 8765]
Abra a URL com token que o servidor imprime. Escuta somente em 127.0.0.1.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import secrets
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse

from terminal_host import (HostedTerminal, ProviderNotInstalled, UnknownProvider,
                           available_providers, resolve_provider)
from transcript_tail import TranscriptTail

HERE = Path(__file__).parent
TOKEN = secrets.token_urlsafe(24)
ALLOWED_HOSTS = {"127.0.0.1", "localhost"}

app = FastAPI()
STATE = {"cwd": os.getcwd(), "port": 8765}


def _authorized(ws: WebSocket) -> bool:
    """Protege contra páginas de terceiros abrindo um shell na máquina (CSWSH)."""
    if ws.query_params.get("token") != TOKEN:
        return False
    origin = ws.headers.get("origin")
    if origin is None:
        return False
    return urlparse(origin).hostname in ALLOWED_HOSTS


MAX_CLIENT_MESSAGE = 1_000_000


def handle_client_message(term, raw: str) -> str | None:
    """Valida UMA mensagem do cliente e a aplica ao terminal. Nunca levanta: mensagem inválida
    é descartada e devolve o motivo (validação na borda, falha isolada; ver ARCHITECTURE.md §4).

    Mensagens: {"type":"input","data":"texto"} | {"type":"input","data_b64":"..."} (seguro para
    bytes arbitrários) | {"type":"resize","cols":N,"rows":N}
    """
    if len(raw) > MAX_CLIENT_MESSAGE:
        return "mensagem grande demais"
    try:
        msg = json.loads(raw)
    except (json.JSONDecodeError, RecursionError):
        return "mensagem não é JSON válido"
    if not isinstance(msg, dict):
        return "mensagem deve ser um objeto"
    kind = msg.get("type")
    if kind == "input":
        if isinstance(msg.get("data_b64"), str):
            try:
                text = base64.b64decode(msg["data_b64"], validate=True).decode("utf-8", "replace")
            except (ValueError, TypeError):
                return "data_b64 inválido"
        elif isinstance(msg.get("data"), str):
            text = msg["data"]
        else:
            return "input sem data"
        term.write(text)
    elif kind == "resize":
        cols, rows = msg.get("cols"), msg.get("rows")
        if not (isinstance(cols, int) and isinstance(rows, int) and 1 <= cols <= 1000 and 1 <= rows <= 500):
            return "resize inválido"
        term.resize(cols, rows)
    else:
        return f"tipo de mensagem desconhecido: {kind!r}"
    return None


@app.get("/")
async def index():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/config")
async def config():
    return JSONResponse({"cwd": STATE["cwd"], "providers": available_providers()})


@app.websocket("/ws")
async def session(ws: WebSocket):
    if not _authorized(ws):
        await ws.close(code=4401)
        return
    await ws.accept()
    loop = asyncio.get_running_loop()
    out: asyncio.Queue[tuple[str, object]] = asyncio.Queue()
    mode = ws.query_params.get("provider", "auto")      # "shell" | nome do provider | "auto"
    model = ws.query_params.get("model")                # usado quando provider=auto
    try:
        provider = None if mode == "shell" else resolve_provider(None if mode == "auto" else mode, model)
    except UnknownProvider as exc:
        await ws.send_json({"channel": "system", "error": f"provider/modelo desconhecido: {exc}"})
        await ws.close()
        return
    session_id = str(uuid.uuid4()) if provider == "claude" else None
    term = HostedTerminal(
        cwd=STATE["cwd"],
        provider=provider,
        session_id=session_id,
        session_name=f"orb-{session_id[:8]}" if session_id else None,
        on_output=lambda data: loop.call_soon_threadsafe(out.put_nowait, ("term", data)),
        on_exit=lambda code: loop.call_soon_threadsafe(out.put_nowait, ("exit", code)),
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
    await ws.send_json({"channel": "system", "info": f"provider={provider or 'shell'}"})

    tail = TranscriptTail(cwd=STATE["cwd"], since=started, session_id=session_id)

    async def pump_transcript():
        while True:
            try:
                events = await asyncio.to_thread(tail.poll)
            except Exception as exc:  # noqa: BLE001 - telemetria nunca derruba o terminal
                await out.put(("sys", f"transcript: {exc}"))
                events = []
            for event in events:
                await out.put(("event", event))
            await asyncio.sleep(0.25)

    async def pump_out():
        while True:
            channel, payload = await out.get()
            if channel == "term":
                await ws.send_json({"channel": "term", "data": payload})
            elif channel == "event":
                await ws.send_json({"channel": "event", "event": payload, "t": time.time()})
            elif channel == "exit":
                await ws.send_json({"channel": "exit", "code": payload})
            else:
                await ws.send_json({"channel": "system", "error": payload})

    tasks = [asyncio.create_task(pump_transcript()), asyncio.create_task(pump_out())]
    try:
        while True:
            problem = handle_client_message(term, await ws.receive_text())
            if problem:
                await out.put(("sys", problem))   # avisa o cliente; a sessão continua
    except WebSocketDisconnect:
        pass
    finally:
        for task in tasks:
            task.cancel()
        term.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    STATE["cwd"] = str(Path(args.cwd).resolve())
    STATE["port"] = args.port
    print(f"\nOrb spike 01 — cwd: {STATE['cwd']}")
    print(f"Abra: http://127.0.0.1:{args.port}/?token={TOKEN}\n", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
