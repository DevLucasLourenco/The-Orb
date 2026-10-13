"""O arquivo SQLite do registro local: só o que o Orb derivou, nunca o conteúdo das sessões (R36).

Hoje guarda a associação sessão -> nome histórico e a sacola de nomes (R37). O Chronicle, o extrato de XP
e os pontos de parada das leituras entram aqui nos tickets deles. É o único arquivo que o Orb grava por
conta própria (os dos providers e dos projetos são só lidos, R16); nunca é apagado nem recriado por cima.

Falha de disco (pasta sem permissão, arquivo corrompido, registro de um Orb mais novo) não derruba nada: os
nomes passam a viver em memória até o fim da execução e `error` diz o motivo.
"""
from __future__ import annotations

import random
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

from ..core import NameBag, NameBook

REGISTRY_FILE = "registry.db"
SCHEMA_VERSION = 1
_BUSY_SECONDS = 5.0
_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS names (key TEXT PRIMARY KEY, name TEXT NOT NULL)",       # id do Alter Ego -> nome
    "CREATE TABLE IF NOT EXISTS bag (position INTEGER PRIMARY KEY, name TEXT NOT NULL)",  # nomes que ainda restam, na ordem
)


class LocalRegistry:
    """Implementa `NameSource` (orb.core) em cima do SQLite."""

    def __init__(self, folder: Path, *, rng: random.Random | None = None) -> None:
        self.path = Path(folder) / REGISTRY_FILE
        self.error: str | None = None
        self._rng = rng
        self._memory = NameBook(rng=rng)        # só entra em uso se o disco falhar
        self._on_disk = True
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._prepare()
        except (OSError, sqlite3.Error, RuntimeError) as exc:
            self._degrade(exc)

    def name_for(self, key: str, avoid: frozenset[str] = frozenset()) -> str:
        """O nome da sessão `key`: o que já tem, para sempre, ou o próximo da sacola que não esteja em `avoid`."""
        if self._on_disk:
            try:
                return self._name_on_disk(key, avoid)
            except (OSError, sqlite3.Error) as exc:
                self._degrade(exc)
        return self._memory.name_for(key, avoid)

    def _degrade(self, exc: Exception) -> None:
        self._on_disk = False
        self.error = f"registro local indisponível, nomes só em memória nesta execução: {type(exc).__name__}: {exc}"

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        """Uma transação que pega a escrita logo no início: dois Orbs abertos não sorteiam o mesmo nome."""
        with closing(sqlite3.connect(self.path, timeout=_BUSY_SECONDS, isolation_level=None)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            conn.execute("COMMIT")

    def _prepare(self) -> None:
        with self._transaction() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise RuntimeError(f"o registro é de um Orb mais novo (versão {version}); ele não será alterado")
            if version < SCHEMA_VERSION:
                for statement in _SCHEMA:
                    conn.execute(statement)
                conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def _name_on_disk(self, key: str, avoid: frozenset[str]) -> str:
        with self._transaction() as conn:
            row = conn.execute("SELECT name FROM names WHERE key = ?", (key,)).fetchone()
            if row is not None:
                return row[0]
            bag = NameBag([name for (name,) in conn.execute("SELECT name FROM bag ORDER BY position")], rng=self._rng)
            name = bag.draw(avoid)
            conn.execute("INSERT INTO names (key, name) VALUES (?, ?)", (key, name))
            conn.execute("DELETE FROM bag")
            conn.executemany("INSERT INTO bag (position, name) VALUES (?, ?)", enumerate(bag.remaining))
            return name
