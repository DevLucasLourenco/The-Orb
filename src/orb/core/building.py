"""A altura e os andares do prédio (R19, R20, R41, D-052, D-099, VISUAL.md §8): das linhas e das pastas, no mundo.

Puro e determinístico, como o resto do Core: as linhas dizem a altura em **níveis** (uma fileira de janelas) e a distribuição
das linhas pelas pastas de primeiro nível diz os **andares**. O cliente só desenha o que sai daqui.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from . import rules

GROUND, FOLDER, REST = "ground", "folder", "rest"     # o térreo (arquivos da raiz), uma pasta, "demais pastas"


def levels(loc: int) -> int:
    """A altura em níveis: depende só das linhas do próprio projeto (D-051). Cada classe tem a sua faixa, com crescimento
    logarítmico dentro dela; o Arranha-céu segue devagar até um teto."""
    name = rules.building_class(loc)
    low, high = rules.BUILDING_LEVELS[name]
    bounds = [lower for _, lower in rules.BUILDING_CLASSES]
    index = [n for n, _ in rules.BUILDING_CLASSES].index(name)
    lower = bounds[index]
    if low == high:                                                   # faixa de um nível só (a Casa, cujo `lower` é 0: sem logaritmo)
        return low
    if index + 1 == len(bounds):                                      # a última classe não tem fim de faixa
        return min(high, low + round(rules.SKYSCRAPER_LEVELS_PER_DOUBLING * math.log2(loc / lower)))
    upper = bounds[index + 1]
    return low + round((high - low) * math.log(loc / lower) / math.log(upper / lower))


def floors(*, height: int, loc: int, root: int, folders: Mapping[str, int]) -> list[dict[str, Any]]:
    """Os andares de baixo para cima: o térreo (arquivos da raiz), cada pasta de primeiro nível em ordem alfabética e, no topo,
    "demais pastas". Cada andar tem pelo menos um nível e a altura dele segue a parcela das linhas; a soma é `height` (os níveis
    do prédio, que `levels` calcula).

    Se há mais pastas do que níveis, as menores se juntam em "demais pastas" (o térreo nunca se junta). As linhas que o Probe não
    listou por pasta (`loc` menos a raiz e as pastas) entram em "demais pastas" também. Pasta sem linhas não é andar."""
    ground = max(0, root)
    listed = {name: count for name, count in folders.items() if count > 0}
    unlisted = max(0, loc - ground - sum(listed.values()))
    if not ground and not listed and not unlisted:
        return []
    if height <= 1:                                                   # um nível só: um andar só, que é o térreo
        return [{"kind": GROUND, "name": None, "levels": 1, "loc": ground + sum(listed.values()) + unlisted}]
    slots = height - (1 if ground else 0)                             # vagas para pastas e "demais pastas"
    by_size = sorted(listed.items(), key=lambda item: (-item[1], item[0]))
    if len(by_size) + (1 if unlisted else 0) > slots:
        kept, merged = by_size[:slots - 1], by_size[slots - 1:]       # uma vaga fica para "demais pastas"
        rest = unlisted + sum(count for _, count in merged)
    else:
        kept, rest = by_size, unlisted
    parts: list[dict[str, Any]] = []
    if ground:
        parts.append({"kind": GROUND, "name": None, "loc": ground})
    parts += [{"kind": FOLDER, "name": name, "loc": count} for name, count in sorted(kept, key=lambda item: item[0].casefold())]
    if rest:
        parts.append({"kind": REST, "name": None, "loc": rest})
    return _distribute(parts, height)


def _distribute(parts: list[dict[str, Any]], height: int) -> list[dict[str, Any]]:
    """Reparte os níveis: um para cada andar e o resto na proporção das linhas (maior resto primeiro; no empate, o de baixo).
    As contas são em inteiros: o desempate é exato, sem ruído de ponto flutuante."""
    extra = height - len(parts)
    total = sum(part["loc"] for part in parts)
    given, remainders = [], []
    for part in parts:
        whole, rest = divmod(extra * part["loc"], total)
        given.append(whole)
        remainders.append(rest)
    order = sorted(range(len(parts)), key=lambda i: (-remainders[i], i))
    for i in order[:extra - sum(given)]:
        given[i] += 1
    return [{**part, "levels": 1 + given[i]} for i, part in enumerate(parts)]
