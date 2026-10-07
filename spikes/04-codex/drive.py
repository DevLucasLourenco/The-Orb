"""Spike 4: fluxo REAL de eventos do Codex pelo protocolo oficial do app-server.

- App-server EFÊMERO e próprio do Orb (loopback, porta 8781). Não toca no config.toml do usuário.
- Cliente A conduz uma conversa (thread/start + turn/start), sandbox read-only, aprovação "never",
  thread `ephemeral` (não grava histórico).
- Cliente B só OBSERVA (é o papel do adapter, src/orb/adapters/codex): vê as notificações da thread
  do A? O observador NUNCA responde a um ServerRequest, nem para recusar (ADR 0006).
- Só o cliente A (que conduz o teste, com aprovação "never") recusa pedidos do servidor, por segurança.

Saída: fixtures/codex-<versão>/<método>.json (1 amostra por método) e resumo no terminal.
"""
from __future__ import annotations

import asyncio
import collections
import json
import subprocess
import sys
import time
from pathlib import Path

import websockets

HERE = Path(__file__).parent
PORT = 8781
CWD = str(HERE.parent.parent)                 # raiz do The Orb
PROMPT = "Leia o arquivo docs/MVP.md e diga so o nome da secao 1."
TIMEOUT = 120

t0 = time.time()
logs: dict[str, list[dict]] = {"A": [], "B": []}


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


class Client:
    def __init__(self, name: str, observer: bool = False):
        self.name = name
        self.observer = observer          # observador: nunca responde ao servidor
        self.ws = None
        self.next_id = 0
        self.pending: dict[int, asyncio.Future] = {}
        self.done = asyncio.Event()

    async def connect(self):
        self.ws = await websockets.connect(f"ws://127.0.0.1:{PORT}", max_size=None)
        asyncio.create_task(self._reader())
        res = await self.request("initialize", {"clientInfo": {"name": f"orb-{self.name}", "title": "The Orb", "version": "0.0.1"}})
        await self.notify("initialized")
        return res

    async def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))

    async def request(self, method, params=None, timeout=30):
        self.next_id += 1
        fut = asyncio.get_running_loop().create_future()
        self.pending[self.next_id] = fut
        msg = {"jsonrpc": "2.0", "method": method, "id": self.next_id}
        if params is not None:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))
        return await asyncio.wait_for(fut, timeout)

    async def _reader(self):
        try:
            async for raw in self.ws:
                msg = json.loads(raw)
                logs[self.name].append({"t": stamp(), "msg": msg})
                if "id" in msg and "method" in msg:              # ServerRequest
                    if self.observer:
                        continue                                 # é do Lucas: o observador não responde
                    await self.ws.send(json.dumps({"jsonrpc": "2.0", "id": msg["id"],
                                                   "error": {"code": -32601, "message": "orb spike: recusado"}}))
                elif "id" in msg and msg["id"] in self.pending:
                    self.pending.pop(msg["id"]).set_result(msg.get("result", msg.get("error")))
                if msg.get("method") == "turn/completed" and self.name == "A":
                    self.done.set()
        except websockets.ConnectionClosed:
            pass


async def main() -> None:
    version = subprocess.run(["codex", "--version"], capture_output=True, text=True).stdout.split()[-1]
    log = open(HERE / "app-server-drive.log", "wb")
    server = subprocess.Popen(["codex", "app-server", "--listen", f"ws://127.0.0.1:{PORT}"],
                              stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    try:
        assert wait_port(PORT), "app-server não subiu"
        print(f"codex {version}; app-server efêmero na porta {PORT}")
        b = Client("B", observer=True)
        await b.connect()                                  # observador conecta ANTES
        a = Client("A")
        await a.connect()
        models = await a.request("model/list", {})
        items = models.get("data") or models.get("models") or []
        ids = [(m.get("model") or m.get("id")) for m in items if isinstance(m, dict)]
        print("modelos disponíveis:", ids)
        if "--models" in sys.argv:
            return
        model = next((i for i in ids if i and "luna" in i), None) or (ids[0] if ids else None)
        print("modelo escolhido:", model)
        started = await a.request("thread/start", {"cwd": CWD, "sandbox": "read-only", "approvalPolicy": "never",
                                                   "ephemeral": "--persist" not in sys.argv, "model": model})
        thread_id = (started.get("thread") or {}).get("id") or started.get("threadId")
        print("thread:", thread_id)
        t_send = stamp()
        await a.request("turn/start", {"threadId": thread_id, "input": [{"type": "text", "text": PROMPT}]})
        # O observador B tenta se inscrever na thread do A COM O TURNO EM ANDAMENTO (o rollout só
        # existe depois do primeiro turno; thread efêmera não tem rollout e não pode ser retomada).
        await asyncio.sleep(0.4)
        mark = len(logs["B"])
        try:
            sub = await b.request("thread/resume", {"threadId": thread_id}, timeout=15)
            print("B thread/resume ->", json.dumps(sub, ensure_ascii=False)[:260])
        except Exception as exc:  # noqa: BLE001
            print("B thread/resume FALHOU:", repr(exc))
        try:
            await asyncio.wait_for(a.done.wait(), TIMEOUT)
            print("turn/completed recebido")
        except asyncio.TimeoutError:
            print("TIMEOUT sem turn/completed")
        await asyncio.sleep(1.5)

        # --- resumo
        for name in ("A", "B"):
            rows = logs[name] if name == "A" else logs[name][mark:]   # B: só depois de se inscrever
            counts = collections.Counter(r["msg"].get("method") for r in rows if "method" in r["msg"])
            print(f"\n=== cliente {name}{' (após se inscrever)' if name == 'B' else ''}: {sum(counts.values())} notificações/pedidos")
            for m, n in counts.most_common():
                print(f"  {n:4d}  {m}")
        # --- fixtures (1 amostra por método, do cliente A)
        fx = HERE / "fixtures" / f"codex-{version}"
        fx.mkdir(parents=True, exist_ok=True)
        seen = set()
        for r in logs["A"]:
            m = r["msg"].get("method")
            if m and m not in seen:
                seen.add(m)
                (fx / (m.replace("/", "__") + ".json")).write_text(
                    json.dumps(r["msg"], indent=2, ensure_ascii=False), encoding="utf-8")
        cap = HERE / "captures"
        cap.mkdir(exist_ok=True)
        with open(cap / f"drive-{int(time.time())}.json", "w", encoding="utf-8") as fh:
            json.dump(logs, fh, ensure_ascii=False)
        print(f"\nfixtures: {fx} ({len(seen)} métodos)")
        print(f"cliente A enviou o prompt em t={t_send}s; último evento em t={logs['A'][-1]['t']}s")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()


if __name__ == "__main__":
    asyncio.run(main())
