"""A leitura única do passado do Codex (R48, camada 3): o rollout da sessão e o das threads-filhas dela, pelo mesmo leitor da sala."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from ...protocol import Event
from .._shared import SessionMeta, family
from . import mapping
from .index import RolloutIndex
from .rollout import RolloutReader


class RolloutPast:
    provider = mapping.PROVIDER

    def __init__(self, home: Path | None = None) -> None:
        self.home = home
        self._index = RolloutIndex(home)
        self._metas: list[SessionMeta] | None = None          # o índice é varrido uma vez: as filhas de cada sessão saem dele

    def read(self, meta: SessionMeta, realm: str) -> Iterator[list[Event]]:
        if self._metas is None:
            self._metas = self._index.scan()
        paths = [Path(m.path) for m in family(meta, self._metas) if m.path]
        reader = RolloutReader(realm=realm, paths=paths, since=0.0, replay=True, home=self.home, realm_of=lambda _cwd: realm)
        first = True
        while True:
            events = reader.poll()
            if first and not events:
                raise FileNotFoundError("o rollout da sessão não foi encontrado ou ainda está sendo criado")      # achado, ele sempre anuncia a thread
            first = False
            if events:
                yield events
            if not reader.behind():
                return
