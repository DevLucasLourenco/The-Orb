"""O perfil de trabalho do Alter Ego (R40, R57, D-069, D-096, D-116, VISUAL.md V-HUD-8, 16 e 17): papel, atributos por área e
árvore da Team, tudo por contagem e ordem do que foi observado.

Puro, como o resto do Core: nenhuma chamada a modelo (R38), nenhum I/O. As tabelas (áreas que contam, papel de cada área) estão
em `rules.py`; aqui só se conta, se compara e se ordena.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import rules


def tally(counts: dict[str, int], activity: str) -> None:
    """Conta uma atividade do líder, se ela cai numa das áreas de trabalho (pensar e delegar, por exemplo, não caem)."""
    area = rules.area_for(activity)
    if area in rules.ROLE_BY_AREA:
        counts[area] = counts.get(area, 0) + 1


def attributes(counts: Mapping[str, int]) -> dict[str, Any] | None:
    """A parcela do trabalho em cada área (D-096): dado real, não pontuação. Sem nenhuma atividade contada não há o que mostrar."""
    total = sum(counts.get(area, 0) for area in rules.ATTRIBUTE_AREAS)
    if not total:
        return None
    return {"total": total, "areas": [{"area": area, "count": counts.get(area, 0), "share": counts.get(area, 0) / total}
                                      for area in rules.ATTRIBUTE_AREAS]}


def role(counts: Mapping[str, int]) -> str | None:
    """O papel é o da área onde a sessão mais fez (R40). Com empate no topo, ou sem nada contado, não se afirma papel nenhum (R12)."""
    ranked = sorted(rules.ATTRIBUTE_AREAS, key=lambda area: counts.get(area, 0), reverse=True)
    first, second = counts.get(ranked[0], 0), counts.get(ranked[1], 0)
    return rules.ROLE_BY_AREA[ranked[0]] if first > second else None


def team_order(parents: Mapping[str, str | None]) -> list[tuple[str, int]]:
    """A Team em árvore (R57, D-116): `(id, profundidade)` com o pai antes dos filhos e os irmãos na ordem em que nasceram (a ordem do
    mapa). Sem pai, com pai desconhecido ou que é ele mesmo, o subagente é filho direto do líder (profundidade 0). Um laço de pais
    (A é pai de B e B é pai de A) não trava: quem sobra do laço vira raiz, na ordem do mapa, e todos continuam listados."""
    children: dict[str, list[str]] = {}
    roots: list[str] = []
    for agent, parent in parents.items():
        if parent is None or parent == agent or parent not in parents:
            roots.append(agent)
        else:
            children.setdefault(parent, []).append(agent)
    ordered: list[tuple[str, int]] = []
    seen: set[str] = set()

    def walk(start: str) -> None:
        stack = [(start, 0)]                # sem recursão: uma cadeia longa de pais não estoura a pilha
        while stack:
            agent, depth = stack.pop()
            if agent in seen:
                continue
            seen.add(agent)
            ordered.append((agent, depth))
            stack.extend((child, depth + 1) for child in reversed(children.get(agent, ())))

    for agent in roots:
        walk(agent)
    for agent in parents:           # o que ficou de fora é um laço: o primeiro dele vira raiz
        walk(agent)
    return ordered
