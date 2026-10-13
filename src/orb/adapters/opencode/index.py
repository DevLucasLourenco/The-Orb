"""Índice do opencode: uma consulta à tabela `session_v2` do `opencode.db`. Somente leitura.

Só `session_v2` (ALLOWED_TABLES): o banco também guarda credenciais e o Orb nunca as lê. Por isso a raiz
do projeto não vem da tabela `project` do opencode: a pasta (`directory`) sobe até o repositório git no
Observatório (pergunta Q-T03-1).
"""
from __future__ import annotations

from pathlib import Path

from .._shared.index import SessionMeta, iso_from_seconds
from .._shared.sqlite import connect_readonly, table_columns
from . import state_db

_COLUMNS = ("id", "parent_id", "directory", "title", "model", "time_created", "time_updated")


def _iso(ms: object) -> str | None:
    return iso_from_seconds(ms / 1000) if isinstance(ms, (int, float)) and not isinstance(ms, bool) else None


class SessionsIndex:
    def __init__(self, data_dir: Path | None = None) -> None:
        self.db_path = (data_dir or state_db.opencode_data_dir()) / "opencode.db"

    def scan(self) -> list[SessionMeta]:
        if not self.db_path.is_file():
            return []
        conn = connect_readonly(self.db_path)
        try:
            columns = table_columns(conn, "session_v2", _COLUMNS)
            if "id" not in columns or "directory" not in columns:
                return []                         # esquema diferente do levantado: degrada sem inventar
            rows = [dict(row) for row in state_db._select(conn, "session_v2", columns, "", ())]
        finally:
            conn.close()
        found: list[SessionMeta] = []
        for row in rows:
            if not isinstance(row.get("directory"), str) or not row["directory"]:
                continue
            found.append(SessionMeta(
                provider="opencode", session_id=str(row["id"]), cwd=row["directory"],
                parent_id=row["parent_id"] if isinstance(row.get("parent_id"), str) and row["parent_id"] else None,
                started_at=_iso(row.get("time_created")), updated_at=_iso(row.get("time_updated")) or _iso(row.get("time_created")),
                title=row.get("title") if isinstance(row.get("title"), str) and row["title"] else None,
                model=row.get("model") if isinstance(row.get("model"), str) and row["model"] else None))
        return found
