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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ...protocol import Event
from .._shared import EventFactory
from .._shared.sqlite import connect_readonly, table_columns
from . import mapping

SOURCE = "hermes/state-db"
BATCH = 500

_WANTED_MESSAGE_COLUMNS = ("id", "session_id", "role", "content", "tool_call_id", "tool_calls",
                           "tool_name", "timestamp", "finish_reason", "reasoning", "active",
                           "input_tokens", "output_tokens")
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


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


class StateDbReader:
    def __init__(self, cwd: str | None, *, realm: str, home: Path | None = None,
                 since: float | None = None, replay: bool = False) -> None:
        self.cwd = _norm(cwd) if cwd else None
        self.realm = realm
        self.db_path = (home or hermes_home()) / "state.db"
        self.since = time.time() if since is None else since
        self.replay = replay
        self.last_id: int | None = None
        self._sessions: dict[str, dict[str, Any] | None] = {}
        self._factories: dict[str, EventFactory] = {}

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
        if self.cwd and (not isinstance(session.get("cwd"), str) or _norm(session["cwd"]) != self.cwd):
            session = None          # outra pasta: não é deste realm
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

    def _factory(self, root: str) -> EventFactory:
        factory = self._factories.get(root)
        if factory is None:
            factory = self._factories[root] = EventFactory(provider=mapping.PROVIDER, source=SOURCE,
                                                           realm=self.realm, session=root)
        return factory

    def _translate(self, conn: sqlite3.Connection, session: dict[str, Any], msg: dict[str, Any]) -> list[Event]:
        root, agent = self._root_and_agent(conn, session)
        factory = self._factory(root)
        ts = _iso(msg.get("timestamp"))
        key = f"m{msg['id']}"
        role = msg.get("role")
        content = msg.get("content") if isinstance(msg.get("content"), str) else ""
        out: list[Event] = []
        if role == "user":
            out.append(factory.make(key, ts, "messages/user", msg, agent=agent,
                                    inner={"role": "prompt", "text": content}))
            return out
        if role == "tool":
            out.append(factory.make(key, ts, "messages/tool", msg, agent=agent,
                                    inner={"role": "result", "text": content}))
            return out
        if role != "assistant":
            return out
        if isinstance(msg.get("reasoning"), str) and msg["reasoning"]:
            out.append(factory.make(f"{key}#reasoning", ts, "messages/assistant.reasoning", {"reasoning": msg["reasoning"]},
                                    agent=agent, inner={"role": "thought", "text": msg["reasoning"],
                                                        "fidelity": "raw"},
                                    signal={"type": "activity", "activity": "THINKING"}))
        if content:
            out.append(factory.make(key, ts, "messages/assistant", msg, agent=agent,
                                    inner={"role": "narration", "text": content}))
        for index, call in enumerate(_tool_calls(msg.get("tool_calls"))):
            function = call.get("function") if isinstance(call.get("function"), dict) else {}
            name = str(function.get("name") or call.get("name") or "?")
            arguments = function.get("arguments")
            try:
                parsed = json.loads(arguments) if isinstance(arguments, str) else arguments
            except json.JSONDecodeError:
                parsed = arguments
            out.append(factory.make(f"{key}#tool{index}", ts, "messages/assistant.tool_call", call, agent=agent,
                                    inner={"role": "tool", "text": f"{name} {arguments or ''}".strip()},
                                    signal={"type": "activity", "activity": mapping.activity_for_tool(name, parsed)}))
        # Valor "stop" segue a convenção chat-completions que o Hermes usa; a confirmar ao vivo.
        if msg.get("finish_reason") == "stop" and agent is None:
            out.append(factory.make(f"{key}#stop", ts, "messages/assistant.stop", {"finish_reason": "stop"},
                                    signal={"type": "idle"}))
        return out


def _tool_calls(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    return [call for call in raw if isinstance(call, dict)] if isinstance(raw, list) else []
