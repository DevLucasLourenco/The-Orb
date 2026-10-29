"""A leitura única do passado do Claude (R48, camada 3): um transcript inteiro, com os subagentes dele, pelo mesmo leitor da sala."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from ...protocol import Event
from .._shared import SessionMeta
from . import mapping
from .transcript import TranscriptReader


class TranscriptPast:
    provider = mapping.PROVIDER

    def __init__(self, home: Path | None = None) -> None:
        self.home = home

    def read(self, meta: SessionMeta, realm: str) -> Iterator[list[Event]]:
        reader = TranscriptReader(meta.cwd, realm=realm, session_id=meta.session_id, since=0.0, replay=True, home=self.home)
        first = True
        while True:
            events = reader.poll()
            if first and not events:
                raise FileNotFoundError("o transcript da sessão não foi encontrado")      # achado, ele sempre anuncia a sessão: sem evento, sumiu
            first = False
            if events:
                yield events
            if not reader.behind():
                return
