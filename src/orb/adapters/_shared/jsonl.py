"""Leitura incremental e somente leitura de arquivos JSONL que o provider só acrescenta (append-only).

Nunca escreve nem trava o arquivo. Lê só os bytes novos desde a última vez; uma linha parcial fica
em buffer até completar; linha inválida é descartada (validação na borda).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

READ_CHUNK = 4 * 1024 * 1024     # lê no máximo 4 MiB por poll e continua no próximo


@dataclass
class JsonlFollower:
    path: Path
    start_at_end: bool = False      # arquivo que já existia: começa do fim (rollouts de 145 MB)
    offset: int = -1
    _buffer: bytes = field(default=b"", repr=False)
    discarded: int = 0              # linhas inválidas descartadas (observabilidade)

    def poll(self) -> list[tuple[int, dict[str, Any]]]:
        """Novas entradas completas como (offset da linha, objeto)."""
        try:
            size = os.stat(self.path).st_size
        except OSError:
            return []
        if self.offset < 0:
            self.offset = size if self.start_at_end else 0
        if size < self.offset:            # arquivo truncado/recriado: recomeça
            self.offset, self._buffer = 0, b""
        if size == self.offset:
            return []
        try:
            with open(self.path, "rb") as fh:  # somente leitura
                fh.seek(self.offset)
                chunk = fh.read(min(READ_CHUNK, size - self.offset))
        except OSError:
            return []
        line_start = self.offset - len(self._buffer)
        self.offset += len(chunk)
        data = self._buffer + chunk
        *lines, rest = data.split(b"\n")
        self._buffer = rest
        out: list[tuple[int, dict[str, Any]]] = []
        for raw in lines:
            here = line_start
            line_start += len(raw) + 1
            if not raw.strip():
                continue
            try:
                entry = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.discarded += 1
                continue
            if isinstance(entry, dict):
                out.append((here, entry))
        return out
