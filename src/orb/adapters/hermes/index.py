"""Índice do Hermes: uma consulta à tabela `sessions` do `state.db` (nunca a `messages`). Somente leitura.

`git_repo_root` é a raiz do projeto que o próprio Hermes informa. Só `source = "subagent"` marca subagente:
`parent_session_id` também liga compactação e `/branch`, que são sessões comuns.
"""
from __future__ import annotations

from pathlib import Path

from .._shared.index import SessionMeta, iso_from_seconds
from .._shared.sqlite import connect_readonly, table_columns
from .state_db import hermes_home

_COLUMNS = ("id", "source", "model", "parent_session_id", "cwd", "title", "started_at", "last_activity_at", "git_repo_root")


class StateDbIndex:
    def __init__(self, home: Path | None = None) -> None:
        self.db_path = (home or hermes_home()) / "state.db"

    def scan(self) -> list[SessionMeta]:
        if not self.db_path.is_file():
            return []
        conn = connect_readonly(self.db_path)
        try:
            columns = table_columns(conn, "sessions", _COLUMNS)
            if "id" not in columns or "cwd" not in columns:
                return []                         # esquema diferente do levantado: degrada sem inventar
            rows = [dict(row) for row in conn.execute(f"SELECT {', '.join(columns)} FROM sessions")]
        finally:
            conn.close()
        found: list[SessionMeta] = []
        for row in rows:
            if not isinstance(row.get("cwd"), str) or not row["cwd"]:
                continue                          # sem pasta: não dá para atribuir a um projeto
            subagent = row.get("source") == "subagent" and isinstance(row.get("parent_session_id"), str)
            found.append(SessionMeta(
                provider="hermes", session_id=str(row["id"]), cwd=row["cwd"],
                project_root=row.get("git_repo_root") if isinstance(row.get("git_repo_root"), str) and row["git_repo_root"] else None,
                parent_id=row["parent_session_id"] if subagent else None,
                started_at=iso_from_seconds(row.get("started_at")),
                updated_at=iso_from_seconds(row.get("last_activity_at")) or iso_from_seconds(row.get("started_at")),
                title=row.get("title") if isinstance(row.get("title"), str) and row["title"] else None,
                model=row.get("model") if isinstance(row.get("model"), str) and row["model"] else None))
        return found
