"""Leitura SOMENTE LEITURA de bancos SQLite que os providers mantêm (Hermes, opencode).

- Conexão por URI `file:...?mode=ro`: o Orb nunca grava, migra nem trava o banco do provider.
- Colunas descobertas com `PRAGMA table_info`: o esquema muda entre versões do provider.
- Verificado no Windows com bancos em WAL (Hermes 0.20.5, opencode 2.0.23).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_readonly(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=1.0)
    conn.row_factory = sqlite3.Row
    return conn


def table_columns(conn: sqlite3.Connection, table: str, wanted: tuple[str, ...]) -> list[str]:
    """As colunas de `wanted` que existem em `table` (vazio se a tabela não existe)."""
    have = {row["name"] for row in conn.execute(f'PRAGMA table_info("{table}")')}
    return [column for column in wanted if column in have]
