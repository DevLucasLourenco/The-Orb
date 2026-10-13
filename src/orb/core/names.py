"""Nomes históricos dos Alter Egos (R37, D-063 a D-067, VISUAL.md §9).

Puro: sem disco nem relógio. A sacola sorteia sem reposição; quem guarda a associação sessão -> nome
para sempre é o livro de nomes (aqui, em memória; no disco, o registro local do Orb, R36).
O nome é identidade, não dado de telemetria (R12): subagentes não ganham nome (D-065).
"""
from __future__ import annotations

import random
from collections.abc import Collection, Iterable, Mapping
from typing import Protocol

# Os 60 nomes aprovados (D-067), na ordem da tabela de VISUAL.md §9. Um teste confere as duas listas.
NAMES: tuple[str, ...] = (
    "Einstein", "Newton", "Galileu", "Marie Curie", "Tesla", "Oppenheimer",
    "Feynman", "Bohr", "Planck", "Faraday", "Maxwell", "Schrödinger",
    "Heisenberg", "Dirac", "Fermi", "Lise Meitner", "Hawking", "César Lattes",
    "Kepler", "Copérnico", "Euler", "Gauss", "Emmy Noether", "Ramanujan",
    "Gödel", "Hilbert", "Riemann", "Poincaré", "Galois", "Euclides",
    "Pitágoras", "Arquimedes", "Al-Khwarizmi", "Hipátia", "Ada Lovelace", "Turing",
    "Babbage", "Boole", "Shannon", "Von Neumann", "Grace Hopper", "Dijkstra",
    "Ritchie", "McCarthy", "Katherine Johnson", "Hedy Lamarr", "Santos Dumont", "Da Vinci",
    "Sócrates", "Platão", "Aristóteles", "Tales", "Descartes", "Pascal",
    "Leibniz", "Kant", "Spinoza", "Wittgenstein", "Confúcio", "Simone de Beauvoir",
)


class NameBag:
    """Sacola de nomes: cada nome sai uma vez antes de qualquer um voltar; esvaziou, embaralha de novo.

    `remaining` é o estado que o registro local guarda, na ordem em que os nomes vão sair: reabrir o
    Orb continua a mesma sacola. Dado `remaining`, a ordem é a dada (sem embaralhar); sem ele, uma sacola
    cheia e embaralhada."""

    def __init__(self, remaining: Iterable[str] | None = None, *, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._remaining: list[str] = self._shuffled() if remaining is None else list(remaining)

    @property
    def remaining(self) -> tuple[str, ...]:
        return tuple(self._remaining)

    def _shuffled(self) -> list[str]:
        names = list(NAMES)
        self._rng.shuffle(names)
        return names

    def draw(self, avoid: Collection[str] = ()) -> str:
        """O próximo nome que não está em `avoid` (os já em uso na sala, D-064). O nome pulado continua
        na sacola. Sacola vazia: embaralha uma nova. Se o que resta só tem nomes em uso, sai um nome de fora da
        sacola, que fica como está (não ter gêmeos na sala vale mais que esgotar a sacola, Q-T04-2). Com os 60
        em uso, repetir é inevitável."""
        if not self._remaining:
            self._remaining = self._shuffled()
        for index, name in enumerate(self._remaining):
            if name not in avoid:
                return self._remaining.pop(index)
        free = [name for name in NAMES if name not in avoid]
        return self._rng.choice(free) if free else self._remaining.pop(0)


class NameSource(Protocol):
    """O que o mundo pede: o nome da sessão `key` (o id do Alter Ego), sorteando um se ela ainda não tem.
    `avoid` são os nomes dos outros personagens da mesma sala. `error` diz por que o nome não está sendo
    guardado (disco com falha), ou é None."""

    error: str | None

    def name_for(self, key: str, avoid: frozenset[str] = frozenset()) -> str: ...


class NameBook:
    """O livro de nomes em memória: sessão -> nome, sempre o mesmo, mais a sacola global (D-064).
    `rng` só vale quando a sacola é criada aqui (sem `bag`)."""

    error: str | None = None

    def __init__(self, assigned: Mapping[str, str] | None = None, bag: NameBag | None = None, *,
                 rng: random.Random | None = None) -> None:
        self.assigned: dict[str, str] = dict(assigned or {})
        self.bag = bag if bag is not None else NameBag(rng=rng)

    def name_for(self, key: str, avoid: frozenset[str] = frozenset()) -> str:
        name = self.assigned.get(key)
        if name is None:
            name = self.assigned[key] = self.bag.draw(avoid)
        return name
