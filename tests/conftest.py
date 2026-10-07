"""Utilidades de teste. As amostras são mínimas e sintéticas, com a FORMA verificada nos spikes e
no esquema oficial do Codex; nenhuma contém dados reais (fixtures reais não são versionadas)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def write_jsonl(path: Path, entries: list[dict], *, append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a" if append else "w", encoding="utf-8", newline="\n") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")


@pytest.fixture
def jsonl():
    return write_jsonl
