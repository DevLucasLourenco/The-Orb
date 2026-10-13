"""Índice do Codex: um rollout por thread; só a primeira linha (`session_meta`) é lida, uma única vez.

O nome da conversa vem do `session_index.jsonl` (arquivo pequeno, relido só quando muda). Somente leitura.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .._shared.index import SessionMeta, iso_from_seconds
from .rollout import first_entry, load_session_titles, session_index, sessions_root


class RolloutIndex:
    def __init__(self, home: Path | None = None) -> None:
        self.home = home
        self._known: dict[Path, SessionMeta | None] = {}     # None: o arquivo existe mas não serve (sem id ou pasta)
        self._titles: dict[str, str] = {}
        self._titles_mtime: float | None = None

    def scan(self) -> list[SessionMeta]:
        root = sessions_root(self.home)
        if not root.is_dir():
            return []
        self._load_titles()
        found: list[SessionMeta] = []
        for path in root.glob("*/*/*/rollout-*.jsonl"):
            if path in self._known and self._known[path] is None:
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            meta = self._known.get(path)
            if meta is None:
                entry = first_entry(path)
                if entry is None:
                    continue                      # primeira linha ainda incompleta: tenta na próxima varredura
                meta = self._known[path] = self._meta(entry)
                if meta is None:
                    continue
            found.append(replace(meta, updated_at=iso_from_seconds(stat.st_mtime), title=self._titles.get(meta.session_id)))
        return found

    @staticmethod
    def _meta(entry: dict) -> SessionMeta | None:
        payload = entry.get("payload") if entry.get("type") == "session_meta" else None
        if not isinstance(payload, dict) or not isinstance(payload.get("id"), str) or not isinstance(payload.get("cwd"), str):
            return None
        parent = payload.get("parent_thread_id")
        return SessionMeta(provider="codex", session_id=payload["id"], cwd=payload["cwd"],
                           parent_id=parent if isinstance(parent, str) and parent else None,
                           started_at=payload.get("timestamp") if isinstance(payload.get("timestamp"), str) else None)

    def _load_titles(self) -> None:
        path = session_index(self.home)
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return
        if mtime != self._titles_mtime:
            self._titles_mtime = mtime
            self._titles = load_session_titles(path) or self._titles
