"""Spike 4: o Orb observa o Codex pelo protocolo OFICIAL do app-server, sem tocar na configuração.

O Orb sobe o seu PRÓPRIO app-server (loopback), a TUI nativa do Codex se conecta a ele
(`codex --remote`) e um segundo cliente (o observador, futuro adapter) recebe os eventos.

Uso:  python observe.py [--attach]    (--attach: o observador também faz thread/resume)
Saída: captures/observer-*.jsonl, resumo no terminal.
"""
from __future__ import annotations

import asyncio
import collections
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import websockets
from winpty import PtyProcess

HERE = Path(__file__).parent
PORT = 8780
PROJECT = str(HERE.parent.parent)
ATTACH = "--attach" in sys.argv
PROMPT = "Leia o arquivo docs/MVP.md e responda só com o título da seção 1."

log: list[dict] = []
t0 = time.time()


def stamp() -> float:
    return round(time.time() - t0, 2)


def wait_port(port: int, timeout: float = 30) -> bool:
    import socket
    end = time.time() + timeout
    while time.time() < end:
        with socket.socket() as s:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.3)
    return False


async def observer(stop: asyncio.Event) -> None:
    url = f"ws://127.0.0.1:{PORT}"
    async with websockets.connect(url, max_size=None) as ws:
        async def send(method, params=None, id_=None):
            msg = {"jsonrpc": "2.0", "method": method}
            if id_ is not None:
                msg["id"] = id_
            if params is not None:
                msg["params"] = params
            await ws.send(json.dumps(msg))

        await send("initialize", {"clientInfo": {"name": "orb-observer", "title": "The Orb", "version": "0.0.1"}}, id_=1)
        await send("initialized")
        attached: set[str] = set()
        next_id = 100
        last_poll = 0.0
        while not stop.is_set():
            if ATTACH and time.time() - last_poll > 2:
                last_poll = time.time()
                next_id += 1
                await send("thread/loaded/list", {}, id_=next_id)
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            msg = json.loads(raw)
            log.append({"t": stamp(), "msg": msg})
            if ATTACH and "result" in msg and isinstance(msg["result"], dict):
                for tid in msg["result"].get("data", []) or []:
                    tid = tid if isinstance(tid, str) else tid.get("id")
                    if tid and tid not in attached:
                        attached.add(tid)
                        next_id += 1
                        await send("thread/resume", {"threadId": tid}, id_=next_id)


def screen_text(chunks: list[str]) -> str:
    """Texto aproximado da tela atual da TUI (últimos bytes, sem escapes)."""
    import re
    raw = "".join(chunks)[-6000:]
    raw = re.sub(r"\x1b\[[0-9;]*[Hf]", "\n", raw)
    return re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[()][A-Z0-9]", "", raw).replace("\r", "")


# A TUI abre na raiz do The Orb. Se o Codex ainda não confia nesta pasta, o diálogo de confiança
# aparece e o script ABORTA (o Orb nunca aceita diálogos de confiança/atualização pelo Lucas, e este
# script NUNCA digita sem checar a tela).
TRUSTED_CWD = PROJECT
UPDATE_OFF = ["--strict-config", "-c", "check_for_update_on_startup=false"]   # só desta sessão
# Sem a letra "t": evita qualquer chance de acionar o atalho "t = trust all" de uma tela de revisão.
PROMPT_TUI = "Leia o arquivo docs/MVP.md e diga so o nome da secao 1."


def run_tui() -> str:
    proc = PtyProcess.spawn(["powershell.exe", "-NoLogo"], cwd=TRUSTED_CWD, dimensions=(32, 120))
    chunks: list[str] = []
    threading.Thread(target=lambda: [chunks.append(proc.read(65536)) for _ in iter(lambda: proc.isalive(), False)],
                     daemon=True).start()
    flags = " ".join(UPDATE_OFF)
    proc.write(f'codex --remote ws://127.0.0.1:{PORT} {flags} -C "{TRUSTED_CWD}"\r')
    ready = False
    declined_hooks_review = False
    # Marcadores de QUALQUER diálogo modal da TUI (o compositor "Ask Codex" aparece desenhado por
    # baixo deles, então ele sozinho não prova que a TUI está livre).
    modal_markers = ("Press enter", "enter to review", "esc to close", "Yes, continue", "Update available",
                     "Do you trust", "trust all", "Skip until")
    for _ in range(50):                      # até ~25 s
        time.sleep(0.5)
        scr = screen_text(chunks)
        modal = [m for m in modal_markers if m in scr]
        if modal and not declined_hooks_review and "esc to close" in scr and "trust all" in scr:
            # Única tecla permitida: Esc, que apenas FECHA a revisão de hooks (não confia em nada).
            declined_hooks_review = True
            log.append({"t": stamp(), "marker": "revisão de hooks: enviado apenas Esc (não confiar)"})
            proc.write("\x1b")
            chunks.clear()               # descarta a tela antiga: só vale o que for redesenhado depois
            time.sleep(3)
            fresh = screen_text(chunks)
            if any(m in fresh for m in modal_markers):
                modal = [m for m in modal_markers if m in fresh]
            else:
                ready = True             # a TUI redesenhou sem nenhum diálogo
                break
        if modal:
            log.append({"t": stamp(), "marker": f"ABORTADO: diálogo {modal}; nada foi digitado"})
            print(f"ABORTADO: diálogo na TUI {modal}, nenhuma tecla enviada.\n" + screen_text(chunks)[-400:])
            try:
                proc.terminate(force=True)
            except Exception:
                pass
            return "".join(chunks)
        if "Ask Codex to do anything" in scr and "loading" not in scr.split("Ask Codex")[0][-300:]:
            ready = True
            break
    log.append({"t": stamp(), "marker": f"TUI pronta={ready}; enviando prompt" })
    if ready:
        proc.write(PROMPT_TUI)
        time.sleep(0.5)
        proc.write("\r")
    time.sleep(45)
    log.append({"t": stamp(), "marker": "fim da espera; encerrando TUI"})
    proc.write("\x03"); time.sleep(0.8); proc.write("\x03"); time.sleep(2)
    proc.write("exit\r"); time.sleep(1)
    try:
        proc.terminate(force=True)
    except Exception:
        pass
    return "".join(chunks)


async def main() -> None:
    logfile = open(HERE / "app-server.log", "wb")
    server = subprocess.Popen(["codex", "app-server", "--listen", f"ws://127.0.0.1:{PORT}"],
                              stdout=logfile, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    try:
        if not wait_port(PORT):
            print("app-server não subiu; veja app-server.log")
            return
        print(f"app-server no ar (pid {server.pid}), porta {PORT}; attach={ATTACH}")
        stop = asyncio.Event()
        obs = asyncio.create_task(observer(stop))
        await asyncio.sleep(1.0)
        tui_text = await asyncio.to_thread(run_tui)
        stop.set()
        out = HERE / "captures"
        out.mkdir(exist_ok=True)
        name = out / f"observer-{'attach' if ATTACH else 'passive'}-{int(time.time())}.jsonl"
        with open(name, "w", encoding="utf-8") as fh:
            for row in log:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        methods = collections.Counter(r["msg"].get("method") for r in log if "msg" in r and "method" in r["msg"])
        responses = sum(1 for r in log if "msg" in r and "result" in r["msg"])
        print(f"\nmensagens do observador: {len(log)} | respostas a requests: {responses}")
        for m, n in methods.most_common():
            print(f"  {n:4d}  {m}")
        print("\ntexto final da TUI (últimos 600 chars, sem escapes):")
        import re
        clean = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07", "", tui_text)
        print(clean[-600:].replace("\r", ""))
        print(f"\ncaptura: {name}")
        try:                                   # fecha o observador por último, sem travar o resultado
            await asyncio.wait_for(obs, timeout=3)
        except (asyncio.TimeoutError, asyncio.CancelledError, Exception):
            obs.cancel()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        logfile.close()


if __name__ == "__main__":
    asyncio.run(main())
