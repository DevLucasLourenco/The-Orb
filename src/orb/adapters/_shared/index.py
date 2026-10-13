"""Índice de metadados das sessões (R48, camada 1), comum aos 4 providers.

Cada adapter lista **todas** as sessões que o provider guarda (sem filtro por pasta) lendo só metadados
(pasta, datas, título, modelo), nunca o conteúdo. Quem decide o que é projeto e o que é realm é o
Observatório (gateway), não o adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class SessionMeta:
    """O que se sabe de uma sessão sem abrir o conteúdo dela."""
    provider: str
    session_id: str
    cwd: str                              # pasta onde a sessão rodou
    project_root: str | None = None       # raiz do projeto, quando o próprio provider a informa
    parent_id: str | None = None          # sessão de quem esta é subagente (membro da Team, não Alter Ego)
    started_at: str | None = None         # ISO 8601 UTC
    updated_at: str | None = None
    title: str | None = None
    model: str | None = None


class SessionIndex(Protocol):
    def scan(self) -> list[SessionMeta]: ...


def iso_from_seconds(value: Any) -> str | None:
    """Data em segundos desde 1970 (como `st_mtime` e as colunas do Hermes) -> ISO 8601 UTC."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(float(value), tz=UTC).isoformat(timespec="milliseconds")
    return None
