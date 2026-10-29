"""A leitura única do passado do Hermes (R48, camada 3): as mensagens da sessão e das sessões-filhas dela, pelo mesmo leitor da sala."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from ...protocol import Event
from .._shared import SessionMeta, family
from . import mapping
from .index import StateDbIndex
from .state_db import StateDbReader


class StateDbPast:
    provider = mapping.PROVIDER

    def __init__(self, home: Path | None = None) -> None:
        self.home = home
        self._index = StateDbIndex(home)
        self._metas: list[SessionMeta] | None = None          # o índice é consultado uma vez: as filhas de cada sessão saem dele

    def read(self, meta: SessionMeta, realm: str) -> Iterator[list[Event]]:
        if self._metas is None:
            self._metas = self._index.scan()
        ids = frozenset(m.session_id for m in family(meta, self._metas))
        reader = StateDbReader(realm=realm, home=self.home, since=0.0, replay=True, sessions=ids, realm_of=lambda _cwd: realm)
        while True:
            events = reader.poll()
            if events:
                yield events
            if reader.drained:
                return
