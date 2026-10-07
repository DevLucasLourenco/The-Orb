"""Nível 1 do Codex: o Orb observa um app-server PRÓPRIO (loopback), ao qual a TUI nativa se
conecta com `codex --remote`. Nada na configuração do Lucas muda (ADR 0005).

O observador NUNCA responde a pedidos do servidor, nem para recusar (ADR 0006): um pedido de
aprovação é do Lucas, na TUI. Só registra e mostra como `waiting`.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable, Protocol

from ...protocol import Event
from .._shared import EventFactory, iso_from_ms, now_iso
from . import mapping

SOURCE = "codex/app-server"


class AppServerTranslator:
    """Mensagem JSON-RPC do app-server -> evento. Uma instância por app-server observado."""

    def __init__(self, realm: str) -> None:
        self.realm = realm
        self._root: dict[str, str] = {}               # thread -> thread raiz (o Alter Ego)
        self._factories: dict[str, EventFactory] = {}
        self._waiting_flag: set[str] = set()          # threads com activeFlags de espera
        self._arrivals = 0                            # ordem de chegada (eventos sem id nativo)

    def _resolve(self, thread_id: str) -> str:
        seen = set()
        while thread_id in self._root and self._root[thread_id] != thread_id and thread_id not in seen:
            seen.add(thread_id)
            thread_id = self._root[thread_id]
        return thread_id

    def _factory(self, root: str) -> EventFactory:
        factory = self._factories.get(root)
        if factory is None:
            factory = self._factories[root] = EventFactory(
                provider=mapping.PROVIDER, source=SOURCE, realm=self.realm, session=root)
        return factory

    def translate(self, msg: Any, received_at: str | None = None) -> Event | None:
        """None para respostas, streaming e mensagens sem thread (não pertencem a um Alter Ego)."""
        if not isinstance(msg, dict) or not isinstance(msg.get("method"), str):
            return None
        method = msg["method"]
        if mapping.is_streaming(method):
            return None
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        thread = params.get("thread") if isinstance(params.get("thread"), dict) else None
        thread_id = params.get("threadId") or (thread or {}).get("id")
        if not isinstance(thread_id, str):
            return None
        if method == "thread/started" and thread is not None:
            parent = thread.get("parentThreadId")
            self._root[thread_id] = self._resolve(parent) if isinstance(parent, str) else thread_id
        root = self._resolve(thread_id)
        agent = thread_id if root != thread_id else None
        ts = received_at or now_iso()
        is_request = "id" in msg
        key = self._key(method, params, msg.get("id") if is_request else None)
        kind = method
        inner = signal = None

        if is_request:
            if method in mapping.WAITING_REQUESTS:
                signal = {"type": "waiting", "request": str(msg["id"]),
                          "action": params.get("command") or params.get("reason") or method}
        elif method in ("item/started", "item/completed") and isinstance(params.get("item"), dict):
            item = params["item"]
            itype = str(item.get("type"))
            kind = f"{method}:{itype}"
            key = f"{kind}:{item.get('id')}"
            ms = params.get("startedAtMs") if method == "item/started" else params.get("completedAtMs")
            if isinstance(ms, (int, float)):
                ts = iso_from_ms(ms)
            inner, signal = self._item(method == "item/started", itype, item)
        elif method == "thread/started":
            if agent:
                signal = {"type": "subagent.started", "kind": (thread or {}).get("agentRole") or (thread or {}).get("agentNickname"),
                          "parent": None if self._root.get(thread_id) == (thread or {}).get("parentThreadId") else (thread or {}).get("parentThreadId")}
            else:
                signal = {"type": "session.started", "cwd": (thread or {}).get("cwd"),
                          "model": (thread or {}).get("model"), "title": (thread or {}).get("name")}
        elif method == "turn/started":
            signal = {"type": "activity", "activity": "THINKING"}
        elif method == "turn/completed":
            signal = {"type": "idle"}
        elif method == "thread/closed":
            signal = {"type": "subagent.ended"} if agent else {"type": "session.ended"}
        elif method == "thread/status/changed":
            signal = self._status(thread_id, params.get("status"))
        elif method == "serverRequest/resolved":
            signal = {"type": "waiting.resolved", "request": str(params.get("requestId"))}
        elif method == "thread/tokenUsage/updated":
            signal = mapping.usage_signal(params.get("tokenUsage"))
        elif method == "error":
            error = params.get("error") if isinstance(params.get("error"), dict) else {}
            message = str(error.get("message") or mapping.short_json(params.get("error")))
            inner = {"origin": "agent", "role": "system", "text": message}
            signal = {"type": "error", "message": message, "recoverable": bool(params.get("willRetry"))}
        return self._factory(root).make(key, ts, kind, params, agent=agent, inner=inner, signal=signal)

    def _key(self, method: str, params: dict[str, Any], request_id: Any) -> str:
        """Id nativo quando existe (pedido, item, turno, thread). Senão, a ordem de chegada: duas
        notificações iguais em momentos diferentes (ex.: duas esperas) são dois fatos distintos."""
        if request_id is not None:
            return f"req:{request_id}"
        turn = params.get("turn") if isinstance(params.get("turn"), dict) else None
        if method.startswith("turn/") and turn and turn.get("id"):
            return f"{method}:{turn['id']}"
        if method in ("thread/started", "thread/closed"):
            return f"{method}:{params.get('threadId') or (params.get('thread') or {}).get('id')}"
        self._arrivals += 1
        return f"{method}#{self._arrivals}"

    def _status(self, thread_id: str, status: Any) -> dict[str, Any] | None:
        if not isinstance(status, dict):
            return None
        flags = set(status.get("activeFlags") or []) & mapping.WAITING_FLAGS
        request = f"{thread_id}:status"
        if status.get("type") == "active" and flags:
            self._waiting_flag.add(thread_id)
            return {"type": "waiting", "request": request, "action": ",".join(sorted(flags))}
        if thread_id in self._waiting_flag:
            self._waiting_flag.discard(thread_id)
            return {"type": "waiting.resolved", "request": request}
        if status.get("type") == "systemError":
            return {"type": "error", "message": "systemError", "recoverable": False}
        return None

    @staticmethod
    def _item(started: bool, itype: str, item: dict[str, Any]):
        if itype == "userMessage":
            if not started:
                return None, None
            text = mapping.user_text(item.get("content"))
            return ({"origin": "human", "role": "prompt", "text": text},
                    {"type": "human.input", "kind": "prompt", "channel": "terminal"})
        if itype == "agentMessage" and not started:
            return {"origin": "agent", "role": "narration", "text": str(item.get("text") or "")}, None
        if itype == "plan" and not started:
            return {"origin": "agent", "role": "narration", "text": str(item.get("text") or "")}, None
        if itype == "reasoning" and not started:
            summary = "\n".join(str(part) for part in item.get("summary") or [] if part)
            signal = {"type": "activity", "activity": "THINKING"}
            if not summary:
                return None, signal     # sem texto: nada de entrada `thought`
            return {"origin": "agent", "role": "thought", "text": summary, "fidelity": "summary"}, signal
        if itype == "commandExecution":
            if started:
                return ({"origin": "agent", "role": "tool", "text": mapping.item_text(item)},
                        {"type": "activity", "activity": mapping.command_activity(item), "target": item.get("command")})
            return {"origin": "agent", "role": "result", "text": mapping.result_text(item)}, None
        if started and itype in mapping.ITEM_ACTIVITY:
            return ({"origin": "agent", "role": "tool", "text": mapping.item_text(item)},
                    {"type": "activity", "activity": mapping.ITEM_ACTIVITY[itype]})
        return None, None


class Connection(Protocol):
    async def send(self, data: str) -> None: ...
    async def recv(self) -> str: ...


class AppServerObserver:
    """Cliente JSON-RPC observador. Só envia: initialize, initialized, thread/loaded/list e
    thread/resume (inscrição). Nunca responde a um pedido do servidor."""

    LIST_EVERY = 2.0

    def __init__(self, conn: Connection, translator: AppServerTranslator,
                 on_event: Callable[[Event], Awaitable[None] | None]) -> None:
        self.conn = conn
        self.translator = translator
        self.on_event = on_event
        self.subscribed: set[str] = set()
        self.ignored_requests = 0          # pedidos do servidor vistos e deixados ao Lucas
        self._next_id = 0
        self._list_ids: set[int] = set()

    async def _request(self, method: str, params: dict[str, Any] | None = None) -> int:
        self._next_id += 1
        msg: dict[str, Any] = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            msg["params"] = params
        await self.conn.send(json.dumps(msg))
        return self._next_id

    async def start(self) -> None:
        await self._request("initialize", {"clientInfo": {"name": "the-orb-observer", "title": "The Orb", "version": "0.1.0"}})
        await self.conn.send(json.dumps({"jsonrpc": "2.0", "method": "initialized"}))

    async def subscribe(self, thread_id: str) -> None:
        if thread_id not in self.subscribed:
            self.subscribed.add(thread_id)
            await self._request("thread/resume", {"threadId": thread_id})

    async def handle(self, raw: str) -> None:
        """Processa UMA mensagem do servidor. Nunca levanta por causa do conteúdo."""
        try:
            msg = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return
        if not isinstance(msg, dict):
            return
        if "id" in msg and "method" in msg:
            self.ignored_requests += 1          # pedido do servidor: é do Lucas. Sem resposta.
        if msg.get("id") in self._list_ids and isinstance(msg.get("result"), dict):
            self._list_ids.discard(msg["id"])
            for entry in msg["result"].get("data") or []:
                thread_id = entry if isinstance(entry, str) else (entry or {}).get("id")
                if isinstance(thread_id, str):
                    await self.subscribe(thread_id)
        if msg.get("method") == "thread/started":
            thread_id = ((msg.get("params") or {}).get("thread") or {}).get("id")
            if isinstance(thread_id, str):
                await self.subscribe(thread_id)
        event = self.translator.translate(msg)
        if event is not None:
            result = self.on_event(event)
            if asyncio.iscoroutine(result):
                await result

    async def run(self, stop: asyncio.Event) -> None:
        await self.start()
        loop = asyncio.get_running_loop()
        last_list = 0.0
        while not stop.is_set():
            if loop.time() - last_list > self.LIST_EVERY:
                last_list = loop.time()
                self._list_ids.add(await self._request("thread/loaded/list", {}))
            try:
                raw = await asyncio.wait_for(self.conn.recv(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            await self.handle(raw)


def app_server_command(port: int) -> list[str]:
    """Comando do app-server PRÓPRIO do Orb (loopback; sem autenticação em loopback)."""
    return ["codex", "app-server", "--listen", f"ws://127.0.0.1:{int(port)}"]
