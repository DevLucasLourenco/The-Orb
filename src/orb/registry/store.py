"""O arquivo SQLite do registro local: só o que o Orb derivou, nunca o conteúdo das sessões (R36).

Hoje guarda a associação sessão -> nome histórico e a sacola de nomes (R37) e o extrato de XP de cada sessão (R53, ticket 22). O Chronicle
e os pontos de parada das leituras entram aqui nos tickets deles. É o único arquivo que o Orb grava por
conta própria (os dos providers e dos projetos são só lidos, R16); nunca é apagado nem recriado por cima.

Falha de disco (pasta sem permissão, arquivo corrompido, registro de um Orb mais novo, banco travado) não derruba
nada: enquanto durar, os nomes e o extrato vêm de uma cópia em memória (que segue a mesma sacola) e `error` diz o motivo. A
cada pedido o disco é tentado de novo, então uma falha passageira (duas instâncias, antivírus) não desliga o registro.
"""
from __future__ import annotations

import json
import random
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

from ..core import NAMES, Entry, NameBag, NameBook

REGISTRY_FILE = "registry.db"
SCHEMA_VERSION = 3
_QUERY_CHUNK = 500        # chaves por consulta (o SQLite limita as variáveis de uma consulta)
_BUSY_SECONDS = 5.0       # o sorteio roda na thread de leitura (to_thread): esperar mais que isso travaria a observação
_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS names (key TEXT PRIMARY KEY, name TEXT NOT NULL)",       # id do Alter Ego -> nome
    "CREATE TABLE IF NOT EXISTS bag (position INTEGER PRIMARY KEY, name TEXT NOT NULL)",  # nomes que ainda restam, na ordem
    # O extrato de XP (R53): uma linha por recibo, com a versão da tabela que a gerou e o estado (confirmada, provisória, anulada ou
    # expirada). A chave impede pagar duas vezes o mesmo recibo; o estado e a XP de um commit mudam quando o git responde.
    ("CREATE TABLE IF NOT EXISTS xp_ledger (ego TEXT NOT NULL, ts TEXT NOT NULL, rule TEXT NOT NULL, xp INTEGER NOT NULL, "
     "ref TEXT NOT NULL, evidence TEXT NOT NULL, version INTEGER NOT NULL, state TEXT NOT NULL DEFAULT 'confirmed', "
     "PRIMARY KEY (ego, rule, ref, version))"),
)
# O que cada versão anterior do esquema precisa para chegar à atual (o que `CREATE IF NOT EXISTS` não faz): de uma tabela que já existe.
_MIGRATIONS: dict[int, tuple[str, ...]] = {
    2: ("ALTER TABLE xp_ledger ADD COLUMN state TEXT NOT NULL DEFAULT 'confirmed'",),      # ticket 23: o estado do extrato
}


class NewerRegistry(Exception):
    """O arquivo é de um Orb mais novo que este: não se mexe nele."""


_DISK_ERRORS = (OSError, sqlite3.Error, NewerRegistry)


class LocalRegistry:
    """Implementa `NameSource` e `XpSource` (orb.core) em cima do SQLite."""

    def __init__(self, folder: Path, *, rng: random.Random | None = None) -> None:
        self.path = Path(folder) / REGISTRY_FILE
        self.error: str | None = None
        self._rng = rng
        self._busy_seconds = _BUSY_SECONDS
        self._memory = NameBook(rng=rng)        # a cópia que atende enquanto o disco falha
        self._xp_memory: dict[str, dict[tuple[str, str, int], Entry]] = {}       # o extrato de cada sessão, a cópia que segue o disco
        self._ready = False
        try:
            self._prepare()
        except _DISK_ERRORS as exc:
            self._fail(exc)

    def name_for(self, key: str, avoid: frozenset[str] = frozenset()) -> str:
        """O nome da sessão `key`: o que já tem, para sempre, ou o próximo da sacola que não esteja em `avoid`."""
        try:
            name = self._name_on_disk(key, avoid)
        except _DISK_ERRORS as exc:
            self._fail(exc)
            return self._memory.name_for(key, avoid)
        self.error = None
        return name

    def name_of(self, key: str) -> str | None:
        """O nome já sorteado da sessão `key`, sem sortear nem gravar nada."""
        try:
            with closing(sqlite3.connect(self.path, timeout=self._busy_seconds)) as conn:
                row = conn.execute("SELECT name FROM names WHERE key = ?", (key,)).fetchone()
        except _DISK_ERRORS:
            return self._memory.name_of(key)
        return row[0] if row is not None else self._memory.name_of(key)

    def names_of(self, keys: list[str]) -> dict[str, str]:
        """O nome já sorteado de várias sessões, numa conexão só (o Histórico do realm pede centenas de uma vez)."""
        found: dict[str, str] = {}
        try:
            with closing(sqlite3.connect(self.path, timeout=self._busy_seconds)) as conn:
                for start in range(0, len(keys), _QUERY_CHUNK):
                    chunk = keys[start:start + _QUERY_CHUNK]
                    marks = ", ".join("?" for _ in chunk)
                    found.update(conn.execute(f"SELECT key, name FROM names WHERE key IN ({marks})", chunk).fetchall())
        except _DISK_ERRORS:
            pass
        return {**self._memory.names_of(keys), **found}

    def entries_of(self, ego_id: str, version: int) -> list[Entry]:
        """O extrato de XP guardado da sessão `ego_id`, só o da versão `version` da tabela (a outra fica de lado, intacta)."""
        try:
            with closing(sqlite3.connect(self.path, timeout=self._busy_seconds)) as conn:
                rows = conn.execute("SELECT ts, rule, xp, ref, evidence, version, state FROM xp_ledger WHERE ego = ? AND version = ? ORDER BY rowid",
                                    (ego_id, version)).fetchall()
        except _DISK_ERRORS:
            return [e for e in self._xp_memory.get(ego_id, {}).values() if e.version == version]
        found: list[Entry] = []
        for ts, rule, xp, ref, evidence, v, state in rows:
            try:
                found.append(Entry(ts=ts, rule=rule, xp=xp, ref=ref, evidence=json.loads(evidence), version=v, state=state))
            except ValueError:                  # uma linha estragada não derruba as outras: fica de fora e o resto do extrato vale
                continue
        return found

    def record(self, ego_id: str, entry: Entry) -> None:
        """Guarda uma entrada do extrato de XP; o mesmo recibo na mesma versão nunca entra duas vezes (se já existe, o estado, a XP e a
        evidência dele são os da entrada nova: o git respondeu sobre o commit)."""
        self._xp_memory.setdefault(ego_id, {})[(entry.rule, entry.ref, entry.version)] = entry
        try:
            if not self._ready:
                self._prepare()
            with self._transaction() as conn:
                conn.execute("INSERT INTO xp_ledger (ego, ts, rule, xp, ref, evidence, version, state) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                             "ON CONFLICT (ego, rule, ref, version) DO UPDATE SET xp = excluded.xp, evidence = excluded.evidence, state = excluded.state",
                             (ego_id, entry.ts, entry.rule, entry.xp, entry.ref, json.dumps(entry.evidence, ensure_ascii=False), entry.version,
                              entry.state))
        except _DISK_ERRORS as exc:
            self._fail(exc)
        else:
            self.error = None

    def _fail(self, exc: Exception) -> None:
        self.error = f"registro local indisponível, nomes e extrato de XP só em memória por enquanto: {type(exc).__name__}: {exc}"

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        """Uma transação que pega a escrita logo no início: dois Orbs abertos não sorteiam o mesmo nome."""
        with closing(sqlite3.connect(self.path, timeout=self._busy_seconds, isolation_level=None)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            conn.execute("COMMIT")

    def _prepare(self) -> None:
        """Cria a pasta e o esquema (uma vez); recusa um registro de Orb mais novo sem tocar nele."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._transaction() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise NewerRegistry(f"o registro é de um Orb mais novo (versão {version}); ele não será alterado")
            if version < SCHEMA_VERSION:
                for statement in _SCHEMA:
                    conn.execute(statement)
                for statement in _MIGRATIONS.get(version, ()):
                    conn.execute(statement)
                conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        self._ready = True

    def _name_on_disk(self, key: str, avoid: frozenset[str]) -> str:
        if not self._ready:
            self._prepare()
        with self._transaction() as conn:
            row = conn.execute("SELECT name FROM names WHERE key = ?", (key,)).fetchone()
            bag = NameBag(self._bag_rows(conn), rng=self._rng)
            if row is not None:
                name = row[0]
            else:
                name = bag.draw(avoid)
                conn.execute("INSERT INTO names (key, name) VALUES (?, ?)", (key, name))
                conn.execute("DELETE FROM bag")
                conn.executemany("INSERT INTO bag (position, name) VALUES (?, ?)", enumerate(bag.remaining))
        self._memory.assigned[key] = name          # a cópia segue o disco: se ele falhar, a sacola continua de onde parou
        self._memory.bag = bag
        return name

    @staticmethod
    def _bag_rows(conn: sqlite3.Connection) -> list[str]:
        """Os nomes que restam, na ordem em que saem; um nome que não é da lista aprovada é ignorado."""
        return [name for (name,) in conn.execute("SELECT name FROM bag ORDER BY position") if name in NAMES]
