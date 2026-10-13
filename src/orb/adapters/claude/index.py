"""Índice do Claude: uma pasta por projeto em `~/.claude/projects`, um `.jsonl` por sessão.

A pasta onde a sessão rodou é o `cwd` que o Claude gravou nas primeiras linhas de um transcript da pasta
(o nome da pasta é ambíguo: "a-b" pode ser "a b" ou "a/b"). Datas vêm do arquivo; título e modelo exigem
abrir o conteúdo e ficam para a leitura incremental das sessões da sala. Somente leitura.
"""
from __future__ import annotations

from pathlib import Path

from .._shared.index import SessionMeta, iso_from_seconds
from .transcript import projects_root, recorded_cwd


class TranscriptIndex:
    def __init__(self, home: Path | None = None) -> None:
        self.home = home
        self._cwd: dict[Path, str] = {}
        self._unknown: dict[Path, tuple] = {}     # pasta sem `cwd` gravado -> como estavam os arquivos quando foi lida

    def scan(self) -> list[SessionMeta]:
        root = projects_root(self.home)
        if not root.is_dir():
            return []
        found: list[SessionMeta] = []
        try:
            folders = [folder for folder in root.iterdir() if folder.is_dir()]
        except OSError:
            return []
        for folder in folders:
            files = []
            for path in folder.glob("*.jsonl"):
                try:
                    files.append((path, path.stat()))
                except OSError:
                    continue
            if not files:
                continue
            cwd = self._cwd.get(folder)
            if cwd is None:
                state = tuple(sorted((path.name, stat.st_size, stat.st_mtime_ns) for path, stat in files))
                if self._unknown.get(folder) == state:
                    continue                      # nada mudou desde a última tentativa: não reabre os arquivos
                cwd = recorded_cwd(folder)
                if cwd is None:
                    self._unknown[folder] = state  # ainda sem `cwd` gravado: não dá para atribuir a um projeto
                    continue
                self._cwd[folder] = cwd
                self._unknown.pop(folder, None)
            for path, stat in files:
                born = getattr(stat, "st_birthtime", stat.st_ctime)
                found.append(SessionMeta(provider="claude", session_id=path.stem, cwd=cwd,
                                         started_at=iso_from_seconds(born), updated_at=iso_from_seconds(stat.st_mtime)))
        return found
