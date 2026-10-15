"""Nível 0 do Hermes: acompanha o SQLite `<HERMES_HOME>/state.db` somente leitura.

- Conexão `file:...state.db?mode=ro` (nunca `SessionDB()` do Hermes: o construtor dele migra o banco).
- `messages.id` é AUTOINCREMENT: lê só `id > último visto`, em lotes.
- Colunas são descobertas por `PRAGMA table_info` (o esquema muda entre versões; hoje 26).
- `/retry`, `/undo` e compactação reescrevem linhas (`active = 0`): linhas inativas são ignoradas.
Detalhes e o que não foi verificado: docs/adapters/HERMES.md.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ...protocol import Event
from .._shared import EventFactory, RealmOf, result_signal, single_realm
from .._shared.sqlite import connect_readonly, table_columns
from . import mapping

SOURCE = "hermes/state-db"
BATCH = 500
_SHELL_CALLS = 512        # comandos de shell sem resultado ainda, lembrados para dar o resultado a eles (Weather)

_WANTED_MESSAGE_COLUMNS = ("id", "session_id", "role", "content", "tool_call_id", "tool_calls",
                           "tool_name", "timestamp", "finish_reason", "reasoning", "codex_reasoning_items",
                           "active", "input_tokens", "output_tokens")
_WANTED_SESSION_COLUMNS = ("id", "source", "model", "parent_session_id", "cwd", "title",
                           "end_reason", "ended_at", "model_config")


def hermes_home(env: dict[str, str] | None = None) -> Path:
    """HERMES_HOME, senão o padrão do Windows (%LOCALAPPDATA%/hermes) ou ~/.hermes."""
    env = dict(os.environ if env is None else env)
    if env.get("HERMES_HOME"):
        return Path(env["HERMES_HOME"])
    if env.get("LOCALAPPDATA"):
        return Path(env["LOCALAPPDATA"]) / "hermes"
    return Path.home() / ".hermes"


def _iso(value: Any) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat(timespec="milliseconds")
    return value if isinstance(value, str) and value else None



class StateDbReader:
    def __init__(self, cwd: str | None = None, *, realm: str = "", home: Path | None = None,
                 since: float | None = None, replay: bool = False, realm_of: RealmOf | None = None) -> None:
        self.realm_of = realm_of or single_realm(cwd, realm)
        self.db_path = (home or hermes_home()) / "state.db"
        self.since = time.time() if since is None else since
        self.replay = replay
        self.last_id: int | None = None
        self._sessions: dict[str, dict[str, Any] | None] = {}
        self._factories: dict[str, EventFactory] = {}
        self._announced: set[str] = set()
        self._shell_calls: OrderedDict[str, str] = OrderedDict()      # tool_call_id -> comando, até o resultado

    def poll(self) -> list[Event]:
        if not self.db_path.is_file():
            return []
        conn = connect_readonly(self.db_path)
        try:
            columns = table_columns(conn, "messages", _WANTED_MESSAGE_COLUMNS)
            if "id" not in columns or "session_id" not in columns:
                return []
            if self.last_id is None:
                self.last_id = 0 if self.replay else int(conn.execute("SELECT COALESCE(MAX(id), 0) FROM messages").fetchone()[0])
                return []
            rows = conn.execute(f"SELECT {', '.join(columns)} FROM messages WHERE id > ? ORDER BY id LIMIT ?",
                                (self.last_id, BATCH)).fetchall()
            events: list[Event] = []
            for row in rows:
                self.last_id = int(row["id"])
                message = dict(row)
                if message.get("active") == 0:
                    continue
                session = self._session(conn, str(message["session_id"]))
                if session is None:
                    continue
                events.extend(self._translate(conn, session, message))
            return events
        finally:
            conn.close()

    def _session(self, conn: sqlite3.Connection, session_id: str) -> dict[str, Any] | None:
        if session_id in self._sessions:
            return self._sessions[session_id]
        columns = table_columns(conn, "sessions", _WANTED_SESSION_COLUMNS)
        row = conn.execute(f"SELECT {', '.join(columns)} FROM sessions WHERE id = ?", (session_id,)).fetchone() if columns else None
        if row is None:
            return None             # sessão ainda não gravada: tenta de novo na próxima mensagem
        session: dict[str, Any] | None = dict(row)
        session["_realm"] = self.realm_of(session.get("cwd"))
        if session["_realm"] is None:
            session = None          # outra pasta: não é de nenhum realm observado
        self._sessions[session_id] = session
        return session

    def _root_and_agent(self, conn: sqlite3.Connection, session: dict[str, Any]) -> tuple[str, str | None]:
        """Subagente = sessão filha com source "subagent" (compactação e /branch também usam
        parent_session_id, mas não são subagentes)."""
        current, agent, seen = session, None, set()
        while current and current.get("source") == "subagent" and current.get("parent_session_id") and current["id"] not in seen:
            seen.add(current["id"])
            agent = agent or str(session["id"])
            parent_id = str(current["parent_session_id"])
            parent = self._sessions.get(parent_id)
            if parent is None:
                row = conn.execute("SELECT id, source, parent_session_id FROM sessions WHERE id = ?", (parent_id,)).fetchone()
                parent = dict(row) if row else {"id": parent_id}
            current = parent
        return str(current["id"]) if current else str(session["id"]), agent

    def _factory(self, realm: str, root: str) -> EventFactory:
        factory = self._factories.get(root)
        if factory is None:
            factory = self._factories[root] = EventFactory(provider=mapping.PROVIDER, source=SOURCE,
                                                           realm=realm, session=root)
        return factory

    def _announce(self, session: dict[str, Any], root: str, agent: str | None, factory: EventFactory,
                  ts: str | None) -> Event | None:
        """A sessão entra no mundo com o título e o modelo que o Hermes gravou, na hora da mensagem que a
        revelou (nunca na hora da leitura: D-128)."""
        sid = str(session["id"])
        if sid in self._announced:
            return None
        self._announced.add(sid)
        body = {k: session.get(k) for k in ("id", "source", "model", "title", "cwd", "parent_session_id")}
        body = {k: v for k, v in body.items() if not k.startswith("_")}
        signal = ({"type": "subagent.started", "kind": session.get("source")} if agent else
                  {"type": "session.started", "cwd": session.get("cwd"), "title": session.get("title"),
                   "model": session.get("model")})
        return factory.make(f"{sid}:start", ts, "sessions", body, agent=agent, signal=signal)

    def _command_result(self, msg: dict[str, Any], content: str) -> dict[str, Any] | None:
        """O resultado de um comando de shell: o código de saída vem no JSON do resultado e o comando, da chamada vista antes."""
        call_id = msg.get("tool_call_id")
        command = self._shell_calls.pop(call_id, None) if isinstance(call_id, str) else None
        code = _exit_code(content) if command is not None else None
        return None if code is None else result_signal(command, ok=code == 0, exit_code=code)

    def _translate(self, conn: sqlite3.Connection, session: dict[str, Any], msg: dict[str, Any]) -> list[Event]:
        root, agent = self._root_and_agent(conn, session)
        factory = self._factory(session["_realm"], root)
        ts = _iso(msg.get("timestamp"))
        announce = self._announce(session, root, agent, factory, ts)
        key = f"m{msg['id']}"
        role = msg.get("role")
        content = msg.get("content") if isinstance(msg.get("content"), str) else ""
        out: list[Event] = [announce] if announce else []
        # Os itens de raciocínio só dizem a fidelidade; o blob cifrado deles não vai no evento nativo.
        reasoning_items = _json_items(msg.get("codex_reasoning_items"))
        native = {k: v for k, v in msg.items() if k != "codex_reasoning_items"}
        if role == "user":
            out.append(factory.make(key, ts, "messages/user", native, agent=agent,
                                    inner={"role": "prompt", "text": content}))
            return out
        if role == "tool":
            out.append(factory.make(key, ts, "messages/tool", native, agent=agent,
                                    inner={"role": "result", "text": content}, signal=self._command_result(msg, content)))
            return out
        if role != "assistant":
            return out
        if isinstance(msg.get("reasoning"), str) and msg["reasoning"]:
            out.append(factory.make(f"{key}#reasoning", ts, "messages/assistant.reasoning", {"reasoning": msg["reasoning"]},
                                    agent=agent, inner={"role": "thought", "text": msg["reasoning"],
                                                        "fidelity": mapping.thought_fidelity(reasoning_items)},
                                    signal={"type": "activity", "activity": "THINKING"}))
        if content:
            out.append(factory.make(key, ts, "messages/assistant", native, agent=agent,
                                    inner={"role": "narration", "text": content}))
        for index, call in enumerate(_json_items(msg.get("tool_calls"))):
            function = call.get("function") if isinstance(call.get("function"), dict) else {}
            name = str(function.get("name") or call.get("name") or "?")
            arguments = function.get("arguments")
            try:
                parsed = json.loads(arguments) if isinstance(arguments, str) else arguments
            except json.JSONDecodeError:
                parsed = arguments
            if name.lower() in mapping.SHELL_TOOLS and isinstance(parsed, dict) and isinstance(call.get("id"), str):
                self._shell_calls[call["id"]] = str(parsed.get("command") or "")
                if len(self._shell_calls) > _SHELL_CALLS:
                    self._shell_calls.popitem(last=False)
            out.append(factory.make(f"{key}#tool{index}", ts, "messages/assistant.tool_call", call, agent=agent,
                                    inner={"role": "tool", "text": f"{name} {arguments or ''}".strip()},
                                    signal={"type": "activity", "activity": mapping.activity_for_tool(name, parsed)}))
        # Valor "stop" segue a convenção chat-completions que o Hermes usa; a confirmar ao vivo.
        if msg.get("finish_reason") == "stop" and agent is None:
            out.append(factory.make(f"{key}#stop", ts, "messages/assistant.stop", {"finish_reason": "stop"},
                                    signal={"type": "idle"}))
        return out


def _exit_code(content: str) -> int | None:
    """O `exit_code` do JSON que o `terminal` do Hermes grava como resultado; texto que não é isso não afirma nada."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return None
    code = data.get("exit_code") if isinstance(data, dict) else None
    return code if isinstance(code, int) and not isinstance(code, bool) else None


def _json_items(raw: Any) -> list[dict[str, Any]]:
    """Coluna JSON em texto (`tool_calls`, `codex_reasoning_items`) -> lista de objetos; o que não for isso, vazio."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    return [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []
