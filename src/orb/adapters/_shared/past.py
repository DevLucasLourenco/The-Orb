"""A leitura única do passado (R48, camada 3; D-088, D-108): o contrato comum aos 4 providers.

Cada adapter sabe abrir **uma sessão antiga inteira** (com as sub-sessões dela) e entregar os eventos em lotes pequenos, pelos mesmos leitores
da sala, só que do começo ao fim. Quem decide a ordem, o ritmo, o que já foi lido e o que fazer com os eventos (a XP) é o Gateway: aqui não há
nada de domínio. Somente leitura, como todo adapter.
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Protocol

from ...protocol import Event
from .index import SessionMeta


class PastSource(Protocol):
    provider: str

    def read(self, meta: SessionMeta, realm: str) -> Iterator[list[Event]]:
        """Os eventos da sessão `meta` (líder) e da Team dela, do começo ao fim, em lotes. Cada lote é uma leitura limitada: quem consome pode
        descansar entre um e outro. Nos adapters de arquivo, uma sessão que não foi achada levanta `FileNotFoundError`: quem lê não a marca como lida
        (volta na próxima abertura). Nos de banco, uma sessão sem mensagens é só uma sessão vazia."""


def family(root: SessionMeta, metas: Iterable[SessionMeta]) -> list[SessionMeta]:
    """A sessão e todas as sub-sessões dela (filhas, netas...), pelo `parent_id` que o índice informa. A própria sessão vem primeiro."""
    metas = list(metas)
    found = [root]
    seen = {root.session_id}
    pending = [root.session_id]
    while pending:
        parent = pending.pop()
        for meta in metas:
            if meta.parent_id == parent and meta.session_id not in seen:
                seen.add(meta.session_id)
                found.append(meta)
                pending.append(meta.session_id)
    return found
