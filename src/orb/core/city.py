"""O traçado da cidade retangular (R32, D-046, D-047, D-099, VISUAL.md §7): dos realms ao lugar de cada prédio.

Puro e determinístico: a mesma lista de realms dá sempre o mesmo traçado, e a semente de cada prédio vem do nome
dele (um resumo fixo, nunca o `hash()` do Python, que muda a cada execução). O cliente só desenha o que sai daqui.
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from hashlib import blake2b
from typing import Any

from . import rules

HASH_DISTRICT = "#"      # números e símbolos: o bairro que vem antes de todas as letras


def district_letter(realm_id: str) -> str:
    """A letra do bairro: a inicial do nome em maiúscula; qualquer outra coisa (número, símbolo, acento) vai para "#"."""
    first = realm_id[:1].upper()
    return first if "A" <= first <= "Z" else HASH_DISTRICT


def seed(realm_id: str) -> int:
    """A semente do prédio, tirada do nome. Igual em qualquer máquina e em qualquer execução."""
    return int.from_bytes(blake2b(realm_id.encode("utf-8"), digest_size=8).digest(), "big")


def _unit(seed_value: int, shift: int) -> float:
    """Um número de -1 a 1 tirado de 16 bits da semente (`shift` escolhe quais): o "aleatório" rastreável."""
    return ((seed_value >> shift) & 0xFFFF) / 0xFFFF * 2 - 1


def _grid(count: int) -> tuple[int, int]:
    """Colunas e fileiras de lotes de um bairro com `count` prédios: o mais quadrado que couber."""
    cols = max(1, math.ceil(math.sqrt(count)))
    return cols, max(1, math.ceil(count / cols))


def _rows_for(letters: list[str], steps: dict[str, int], limit: float) -> list[list[str]]:
    """Os bairros em fileiras: cada uma recebe bairros enquanto a largura couber em `limit` (a 1ª sempre recebe um)."""
    rows: list[list[str]] = [[]]
    used = 0.0
    for letter in letters:
        if rows[-1] and used + steps[letter] > limit:
            rows.append([])
            used = 0.0
        rows[-1].append(letter)
        used += steps[letter]
    return rows


def _limits(letters: list[str], steps: dict[str, int]) -> list[float]:
    """As larguras a tentar: de um bairro sozinho até todos numa fileira só, de bairro em bairro."""
    widest = max(steps.values())
    total = sum(steps.values())
    limits = {float(widest), float(total)}
    for start in range(len(letters)):
        seen = 0
        for letter in letters[start:]:
            seen += steps[letter]
            limits.add(float(max(seen, widest)))
    return sorted(limit for limit in limits if limit <= total)


def _ratio_gap(rows: list[list[str]], sizes: dict[str, tuple[int, int, int, int]], steps: dict[str, int], street: int) -> tuple[float, int]:
    """Quão longe a cidade desta divisão fica de 16:9 (em escala logarítmica, para largo e alto pesarem igual); no
    empate, a de menor área. Desempate fixo: o resultado é sempre o mesmo para os mesmos bairros."""
    width = max(sum(steps[lt] for lt in row) - street for row in rows)
    depth = sum(max(sizes[lt][3] for lt in row) + street for row in rows) - street
    return abs(math.log(width / depth) - math.log(rules.CITY_ASPECT)), width * depth


def plan(realm_ids: Iterable[str]) -> dict[str, Any]:
    """Os bairros e o lugar de cada realm. Coordenadas em unidades do mundo, com o centro da cidade em (0, 0);
    +x para a direita e +z para a frente (a câmera inicial). Cada bairro tem `x`/`z` (o canto de trás e da esquerda),
    `w`/`d` (largura e profundidade), `cols`/`rows` (a grade de lotes) e a letra, e `pad` é a calçada de cada bairro
    (onde fica a placa); cada prédio tem o bairro, o número do lote (1, 2, 3… em ordem alfabética), a posição do
    centro (já com o deslocamento) e o giro em radianos."""
    by_letter: dict[str, list[str]] = {}
    for realm_id in sorted(set(realm_ids)):
        by_letter.setdefault(district_letter(realm_id), []).append(realm_id)
    letters = sorted(by_letter, key=lambda lt: (lt != HASH_DISTRICT, lt))         # "#" primeiro, depois A..Z
    if not letters:
        return {"width": 0, "depth": 0, "pad": rules.CITY_PAD, "districts": [], "places": {}}

    sizes = {}
    for letter in letters:
        cols, rows = _grid(len(by_letter[letter]))
        sizes[letter] = (cols, rows, cols * rules.CITY_LOT + 2 * rules.CITY_PAD, rows * rules.CITY_LOT + 2 * rules.CITY_PAD)

    # Os bairros se leem como um texto: da esquerda para a direita, quebrando em fileiras. Cada bairro ocupa o seu
    # retângulo mais a rua. Entre as larguras em que se pode quebrar, vale a que deixa a cidade mais perto de 16:9.
    street = rules.CITY_STREET
    steps = {lt: sizes[lt][2] + street for lt in letters}
    best = min((_rows_for(letters, steps, limit) for limit in _limits(letters, steps)),
               key=lambda rows: _ratio_gap(rows, sizes, steps, street))
    rows_of_districts = best

    districts: list[dict[str, Any]] = []
    top = 0.0
    width = 0.0
    for row in rows_of_districts:
        left = 0.0
        for letter in row:
            cols, rows, w, d = sizes[letter]
            districts.append({"letter": letter, "x": left, "z": top, "w": w, "d": d, "cols": cols, "rows": rows})
            left += w + street
        width = max(width, left - street)
        top += max(sizes[lt][3] for lt in row) + street
    depth = top - street

    # O centro da cidade fica em (0, 0): a câmera, os atalhos e o voo continuam olhando para a origem.
    for d in districts:
        d["x"] = round(d["x"] - width / 2, 2)
        d["z"] = round(d["z"] - depth / 2, 2)

    places: dict[str, dict[str, Any]] = {}
    for d in districts:
        for index, realm_id in enumerate(by_letter[d["letter"]]):
            s = seed(realm_id)
            col, row = index % d["cols"], index // d["cols"]
            places[realm_id] = {
                "district": d["letter"], "lot": index + 1,
                "x": round(d["x"] + rules.CITY_PAD + (col + 0.5) * rules.CITY_LOT + _unit(s, 0) * rules.CITY_JITTER, 2),
                "z": round(d["z"] + rules.CITY_PAD + (row + 0.5) * rules.CITY_LOT + _unit(s, 16) * rules.CITY_JITTER, 2),
                "turn": round(_unit(s, 32) * rules.CITY_TURN, 4),
            }
    return {"width": round(width, 2), "depth": round(depth, 2), "pad": rules.CITY_PAD, "districts": districts, "places": places}
