"""Peças comuns a todo adapter, sem conhecimento de provider (docs/ARCHITECTURE.md §3)."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ...protocol import Event, make_event


def alter_ego_id(provider: str, session: str) -> str:
    """Um Alter Ego é uma sessão (ADR 0001): o id é `<provider>:<id da sessão>`."""
    return f"{provider}:{session}"


def realm_id_for(cwd: str) -> str:
    """Id estável de um realm a partir da pasta do projeto (ex.: 'The Orb' -> 'the-orb')."""
    name = re.split(r"[\\/]", cwd.rstrip("\\/"))[-1] or cwd
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "realm"


def stable_key(value: Any) -> str:
    """Chave determinística para eventos sem id nativo (mesmo conteúdo -> mesma chave)."""
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def iso_from_ms(ms: int | float) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="milliseconds")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass(frozen=True)
class Capabilities:
    """O que um provider consegue informar. O resto do sistema se adapta a isto."""
    thought_fidelity: tuple[str, ...]     # () = nenhum; ("raw",), ("summary",)
    approvals: str                        # "none" | "requested" | "requested+resolved"
    subagents: bool
    human_origin: str                     # "confirmed" | "heuristic" | "none"
    realtime: bool                        # nível 1 disponível
    usage: bool


class EventFactory:
    """Monta os eventos de UM Alter Ego numa fonte: `seq` crescente e ids determinísticos."""

    def __init__(self, *, provider: str, source: str, realm: str, session: str) -> None:
        self.provider = provider
        self.source = source
        self.realm = realm
        self.alter_ego = alter_ego_id(provider, session)
        self.seq = 0

    def make(self, key: str, ts: str | None, kind: str, body: Any, *, agent: str | None = None,
             inner: dict[str, Any] | None = None, signal: dict[str, Any] | None = None) -> Event:
        self.seq += 1
        return make_event(id=f"{self.alter_ego}:{key}", ts=ts or now_iso(), provider=self.provider,
                          source=self.source, realm=self.realm, alter_ego=self.alter_ego, agent=agent,
                          seq=self.seq, kind=kind, body=body, inner=inner, signal=signal)
