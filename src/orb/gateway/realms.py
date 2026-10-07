"""Observação contínua dos realms: para cada projeto, os 4 providers ao mesmo tempo.

Qualquer sessão que nasça na pasta de um realm (aberta pelo Orb ou fora dele, de qualquer CLI)
aparece sozinha como um Alter Ego que carrega o seu provider. Tudo é nível 0: somente leitura.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ..adapters._shared import realm_id_for
from ..adapters.claude import TranscriptReader
from ..adapters.codex import RolloutReader
from ..adapters.hermes import StateDbReader
from ..adapters.opencode import OpencodeDbReader
from ..protocol import Event

FEED_PER_ALTER_EGO = 300       # linhas de Inner World guardadas por sessão (para quem conecta depois)


class Reader(Protocol):
    def poll(self) -> list[Event]: ...


def readers_for(cwd: str, realm: str, since: float, home: Path | None = None) -> dict[str, Reader]:
    """Os leitores de nível 0 dos 4 providers para uma pasta. `home` só muda nos testes."""
    return {
        "claude": TranscriptReader(cwd, realm=realm, since=since, home=home),
        "codex": RolloutReader(cwd, realm=realm, since=since, home=home),
        "hermes": StateDbReader(cwd, realm=realm, since=since, home=home / "hermes" if home else None),
        "opencode": OpencodeDbReader(cwd, realm=realm, since=since, data_dir=home / "opencode" if home else None),
    }


@dataclass
class RealmObserver:
    id: str
    cwd: str
    readers: dict[str, Reader]
    errors: dict[str, str] = field(default_factory=dict)    # provider -> último erro (degradação visível)

    @property
    def name(self) -> str:
        return Path(self.cwd).name or self.id

    def poll(self) -> list[Event]:
        """Lê os 4 providers. A falha de um não afeta os outros."""
        events: list[Event] = []
        for provider, reader in self.readers.items():
            try:
                events.extend(reader.poll())
                self.errors.pop(provider, None)
            except Exception as exc:  # noqa: BLE001 - isolamento de falha por provider
                self.errors[provider] = f"{type(exc).__name__}: {exc}"
        return events

    def describe(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "cwd": self.cwd, "errors": dict(self.errors)}


def build_observers(cwds: list[str], *, lookback_minutes: float = 30.0, home: Path | None = None,
                    now: float | None = None) -> list[RealmObserver]:
    """Um observador por pasta. Sessões ativas nos últimos `lookback_minutes` já entram no mundo."""
    since = (time.time() if now is None else now) - lookback_minutes * 60
    observers: list[RealmObserver] = []
    used: set[str] = set()
    for cwd in cwds:
        realm = base = realm_id_for(cwd)
        n = 2
        while realm in used:
            realm, n = f"{base}-{n}", n + 1
        used.add(realm)
        observers.append(RealmObserver(realm, cwd, readers_for(cwd, realm, since, home)))
    return observers


class Feed:
    """As últimas linhas de Inner World de cada Alter Ego (memória limitada)."""

    def __init__(self, per_alter_ego: int = FEED_PER_ALTER_EGO) -> None:
        self.per_alter_ego = per_alter_ego
        self._lines: dict[str, deque[Event]] = {}

    def add(self, event: Event) -> bool:
        if not event.get("inner") or not event.get("alter_ego"):
            return False
        lines = self._lines.get(event["alter_ego"])
        if lines is None:
            lines = self._lines[event["alter_ego"]] = deque(maxlen=self.per_alter_ego)
        lines.append(event)
        return True

    def history(self, alter_ego: str, limit: int | None = None) -> list[Event]:
        lines = list(self._lines.get(alter_ego, ()))
        return lines[-limit:] if limit else lines
