"""Quem está onde no Rooftop Room (R33, D-057): a sala cheia.

A sala não cresce: cada lugar mostra até `rules.PLACE_CAP` personagens e conta o resto ("+N"); o overview continua listando todos. Os lugares
são as cinco áreas do Environment, o lobby (quem pensa, espera ou está parado) e o dormitório (quem dorme ou terminou). Puro, como o resto
do Core: parte dos snapshots dos Alter Egos que estão na sala e devolve, por lugar, quem aparece e quantos ficaram de fora.

Quando falta lugar, ficam primeiro quem espera o Lucas, depois os líderes (antes dos subagentes) e, dentro de cada grupo, quem mexeu por último.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from . import rules


def _place_of(state_area: str | None) -> str:
    return state_area or rules.LOBBY


def occupancy(egos: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """O que a sala mostra em cada lugar: `shown` (as chaves de quem aparece, na ordem de prioridade) e `more` (quantos passaram do limite).
    A chave de um líder é o id do Alter Ego; a de um subagente é `<id do Alter Ego>/<id do subagente>`. Só entram os Alter Egos que estão
    na sala; os subagentes ativos de uma sessão encerrada ficam de fora."""
    members: dict[str, list[tuple[str, bool, bool, str]]] = {place: [] for place in rules.PLACES}
    for ego in egos:
        waiting = bool(ego["waiting"]) or ego["state"] == "WAITING"
        place = rules.DORM if ego["asleep"] else _place_of(ego["area"])
        members[place].append((ego["id"], False, waiting, ego["last_ts"] or ""))
        if ego["ended"]:
            continue
        for sub in ego["team"]:
            if sub["active"]:
                members[_place_of(sub["area"])].append((f"{ego['id']}/{sub['id']}", True, False, sub["last_ts"] or ego["last_ts"] or ""))
    room: dict[str, dict[str, Any]] = {}
    for place, found in members.items():
        found.sort(key=lambda m: m[0])                       # a ordem final é estável: por id, depois por quem mexeu por último...
        found.sort(key=lambda m: m[3], reverse=True)
        found.sort(key=lambda m: m[1])                       # ...depois líderes antes dos subagentes...
        found.sort(key=lambda m: not m[2])                   # ...e, antes de tudo, quem espera o Lucas
        room[place] = {"shown": [m[0] for m in found[:rules.PLACE_CAP]], "more": max(0, len(found) - rules.PLACE_CAP)}
    return room
