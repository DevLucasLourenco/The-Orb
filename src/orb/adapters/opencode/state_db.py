"""Nível 0 do opencode: acompanha o SQLite `opencode.db` SOMENTE LEITURA.

- Só as tabelas `session_v2` e `session_message`. O banco também guarda credenciais (`credential`,
  `account`, `control_account`): **o Orb nunca as lê** (ALLOWED_TABLES abaixo, coberto por teste).
- `session_message` é reescrita durante o streaming (a linha do assistente cresce): o cursor é
  `(time_updated, id)`, e cada bloco é emitido uma vez, quando está pronto:
  ferramenta ao começar (e o resultado ao terminar); texto e pensamento quando a mensagem termina.
Detalhes: docs/adapters/OPENCODE.md.
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
from .._shared import EventFactory, connect_readonly, table_columns
from . import mapping

SOURCE = "opencode/db"
BATCH = 500
_TRACKED_MESSAGES = 4096
ALLOWED_TABLES = frozenset({"session_v2", "session_message"})

_SESSION_COLUMNS = ("id", "parent_id", "directory", "title", "model", "agent", "fork_session_id")
_MESSAGE_COLUMNS = ("id", "session_id", "type", "seq", "time_created", "time_updated", "data")


def opencode_data_dir(env: dict[str, str] | None = None) -> Path:
    """Pasta de dados do opencode (`opencode debug paths`): XDG_DATA_HOME ou ~/.local/share."""
    env = dict(os.environ if env is None else env)
    base = Path(env["XDG_DATA_HOME"]) if env.get("XDG_DATA_HOME") else Path.home() / ".local" / "share"
    return base / "opencode"


def _iso(ms: Any) -> str | None:
    if isinstance(ms, (int, float)) and not isinstance(ms, bool):
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="milliseconds")
    return None


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


def _select(conn: sqlite3.Connection, table: str, columns: list[str], where: str, params: tuple) -> list[sqlite3.Row]:
    if table not in ALLOWED_TABLES:
        raise PermissionError(f"tabela fora do permitido: {table}")
    return conn.execute(f'SELECT {", ".join(columns)} FROM "{table}" {where}', params).fetchall()


class OpencodeDbReader:
    def __init__(self, cwd: str | None, *, realm: str, data_dir: Path | None = None,
                 since: float | None = None, replay: bool = False) -> None:
        self.cwd = _norm(cwd) if cwd else None
        self.realm = realm
        self.db_path = (data_dir or opencode_data_dir()) / "opencode.db"
        self.since = time.time() if since is None else since
        self.replay = replay
        self.cursor: tuple[int, str] | None = None
        self._sessions: dict[str, dict[str, Any] | None] = {}
        self._announced: set[str] = set()
        self._factories: dict[str, EventFactory] = {}
        self._emitted: "OrderedDict[str, set[str]]" = OrderedDict()

    def poll(self) -> list[Event]:
        if not self.db_path.is_file():
            return []
        conn = connect_readonly(self.db_path)
        try:
            columns = table_columns(conn, "session_message", _MESSAGE_COLUMNS)
            if len(columns) < len(_MESSAGE_COLUMNS):
                return []        # esquema diferente do levantado: degrada sem inventar
            if self.cursor is None:
                if self.replay:
                    self.cursor = (-1, "")
                else:
                    row = conn.execute('SELECT time_updated, id FROM "session_message" '
                                       "ORDER BY time_updated DESC, id DESC LIMIT 1").fetchone()
                    self.cursor = (int(row[0]), str(row[1])) if row else (-1, "")
                    return []
            last_time, last_id = self.cursor
            rows = _select(conn, "session_message", columns,
                           "WHERE time_updated > ? OR (time_updated = ? AND id > ?) "
                           "ORDER BY time_updated, id LIMIT ?", (last_time, last_time, last_id, BATCH))
            events: list[Event] = []
            for row in rows:
                self.cursor = (int(row["time_updated"]), str(row["id"]))
                session = self._session(conn, str(row["session_id"]))
                if session is not None:
                    events.extend(self._translate(conn, session, dict(row)))
            return events
        finally:
            conn.close()

    # --- sessões ------------------------------------------------------------------------------
    def _session(self, conn: sqlite3.Connection, session_id: str) -> dict[str, Any] | None:
        if session_id in self._sessions:
            return self._sessions[session_id]
        columns = table_columns(conn, "session_v2", _SESSION_COLUMNS)
        if "id" not in columns:
            return None
        rows = _select(conn, "session_v2", columns, "WHERE id = ?", (session_id,))
        if not rows:
            return None              # ainda não gravada: tenta na próxima linha
        session: dict[str, Any] | None = dict(rows[0])
        if self.cwd and (not isinstance(session.get("directory"), str) or _norm(session["directory"]) != self.cwd):
            session = None
        self._sessions[session_id] = session
        return session

    def _root(self, conn: sqlite3.Connection, session: dict[str, Any]) -> tuple[str, str | None]:
        current, seen = session, set()
        while current.get("parent_id") and current["id"] not in seen:
            seen.add(current["id"])
            parent = self._sessions.get(current["parent_id"])
            if parent is None:
                rows = _select(conn, "session_v2", ["id", "parent_id"], "WHERE id = ?", (current["parent_id"],))
                parent = dict(rows[0]) if rows else {"id": current["parent_id"], "parent_id": None}
            current = parent
        root = str(current["id"])
        return root, (str(session["id"]) if root != session["id"] else None)

    def _factory(self, root: str) -> EventFactory:
        factory = self._factories.get(root)
        if factory is None:
            factory = self._factories[root] = EventFactory(provider=mapping.PROVIDER, source=SOURCE,
                                                           realm=self.realm, session=root)
        return factory

    def _once(self, message_id: str, key: str) -> bool:
        keys = self._emitted.get(message_id)
        if keys is None:
            keys = self._emitted[message_id] = set()
            if len(self._emitted) > _TRACKED_MESSAGES:
                self._emitted.popitem(last=False)
        if key in keys:
            return False
        keys.add(key)
        return True

    # --- tradução -----------------------------------------------------------------------------
    def _translate(self, conn: sqlite3.Connection, session: dict[str, Any], row: dict[str, Any]) -> list[Event]:
        root, agent = self._root(conn, session)
        factory = self._factory(root)
        out: list[Event] = []
        sid = str(session["id"])
        if sid not in self._announced:
            self._announced.add(sid)
            body = {k: v for k, v in session.items() if k in _SESSION_COLUMNS}
            signal = ({"type": "subagent.started", "kind": session.get("agent")} if agent else
                      {"type": "session.started", "cwd": session.get("directory"),
                       "model": session.get("model") if isinstance(session.get("model"), str) else None,
                       "title": session.get("title")})
            out.append(factory.make(f"{sid}:start", _iso(row.get("time_created")), "session_v2", body,
                                    agent=agent, signal=signal))
        try:
            data = json.loads(row["data"]) if isinstance(row.get("data"), str) else {}
        except json.JSONDecodeError:
            return out
        if not isinstance(data, dict):
            return out
        mid, mtype = str(row["id"]), str(row.get("type"))
        kind = f"session_message/{mtype}"
        ts = _iso((data.get("time") or {}).get("created")) or _iso(row.get("time_created"))
        make = factory.make

        if mtype in mapping.MESSAGE_TYPES:
            if self._once(mid, "msg"):
                out.append(make(mid, ts, kind, data, agent=agent,
                                inner={"role": mapping.MESSAGE_TYPES[mtype], "text": str(data.get("text") or "")}))
            return out
        if mtype == "idle":
            if self._once(mid, "idle"):
                out.append(make(mid, ts, kind, data, agent=agent, signal={"type": "idle"}))
            return out
        if mtype != "assistant":
            return out

        completed = bool((data.get("time") or {}).get("completed"))
        for index, block in enumerate(data.get("content") or []):
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            key = f"{mid}#{index}"
            if btype == "tool":
                name = str(block.get("name") or "?")
                state = block.get("state") if isinstance(block.get("state"), dict) else {}
                tool_input = state.get("input")
                if self._once(mid, f"{index}:start"):
                    out.append(make(key, ts, f"{kind}:tool", {k: v for k, v in block.items() if k != "state"} | {"input": tool_input},
                                    agent=agent,
                                    inner={"role": "tool", "text": mapping.tool_text(name, tool_input)},
                                    signal={"type": "activity", "activity": mapping.activity_for_tool(name, tool_input),
                                            "target": mapping.tool_target(tool_input)}))
                if state.get("status") in mapping.FINISHED_TOOL_STATUS and self._once(mid, f"{index}:end"):
                    text = mapping.content_text(state.get("content"))
                    out.append(make(f"{key}:end", ts, f"{kind}:tool_result", {"name": name, "status": state.get("status"),
                                                                               "content": state.get("content")},
                                    agent=agent, inner={"role": "result",
                                                        "text": ("[erro] " if state.get("status") == "error" else "") + text}))
            elif completed and btype in ("text", "reasoning") and block.get("text") and self._once(mid, str(index)):
                if btype == "text":
                    out.append(make(key, ts, f"{kind}:text", block, agent=agent,
                                    inner={"role": "narration", "text": block["text"]}))
                else:
                    out.append(make(key, ts, f"{kind}:reasoning", block, agent=agent,
                                    inner={"role": "thought", "text": block["text"], "fidelity": "raw"},
                                    signal={"type": "activity", "activity": "THINKING"}))
        if completed and self._once(mid, "usage"):
            usage = mapping.usage_signal(data)
            if usage:
                out.append(make(f"{mid}#usage", ts, f"{kind}:usage",
                                {k: data.get(k) for k in ("tokens", "cost", "model", "finish")}, agent=agent, signal=usage))
        return out
