"""A fachada do prédio (R20, R20a, R20b, R20d, VISUAL.md §6): das alterações locais às janelas acesas.

Puro e determinístico. Cada **janela acesa** vale x% das alterações locais do realm; uma alteração nunca se divide entre duas
janelas; a cor é a do tipo de alteração e o andar é o da pasta de primeiro nível. As janelas apagadas não aparecem aqui: são as
posições da fachada que ficam sem janela acesa. O cliente só desenha o que sai daqui.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, NamedTuple

from ..protocol import CHANGE_TYPES
from . import rules


class Change(NamedTuple):
    path: str          # relativo à raiz do projeto, com `/`
    type: str          # um de `CHANGE_TYPES`
    lines: int         # o peso: linhas alteradas


class _Floors(NamedTuple):
    """Os andares indexados uma vez: onde está cada pasta, o térreo e "demais pastas"."""
    folders: dict[str, int]
    ground: int | None
    rest: int | None

    @classmethod
    def of(cls, floors: Sequence[dict[str, Any]]) -> _Floors:
        found: dict[str, int] = {}
        for index, floor in enumerate(floors):
            found.setdefault(floor["kind"] if floor["kind"] != "folder" else f"folder:{floor['name']}", index)
        return cls({k[7:]: v for k, v in found.items() if k.startswith("folder:")}, found.get("ground"), found.get("rest"))

    def of_path(self, path: str) -> int:
        """Em que andar cai uma alteração: arquivo da raiz no térreo; pasta de primeiro nível no andar dela. Pasta que não é andar
        (ela só tem arquivos que a contagem de linhas não conta, como `.md`) cai em "demais pastas" e, se o prédio não tem esse
        andar, no térreo; arquivo da raiz num prédio sem térreo cai em "demais pastas"."""
        top, slash, _ = path.partition("/")
        if slash and top in self.folders:
            return self.folders[top]
        order = (self.rest, self.ground) if slash else (self.ground, self.rest)
        return next((index for index in order if index is not None), 0)


def _pack(group: list[Change], capacity: float) -> list[list[Change]]:
    """Agrupa, na ordem do caminho, até somar `capacity` linhas; uma alteração que sozinha passa disso fica numa janela só dela."""
    packets: list[list[Change]] = []
    weight = 0.0
    for change in sorted(group):
        if packets and weight + change.lines <= capacity:
            packets[-1].append(change)
            weight += change.lines
        else:
            packets.append([change])
            weight = change.lines
    return packets


def _packets_for_floor(by_type: dict[str, list[Change]], capacity: float, slots: int) -> list[tuple[str, list[Change]]]:
    """Os pacotes de um andar. Se precisam de mais janelas do que o andar tem, juntam-se mais (o x daquele andar sobe) até
    caber; no limite há um pacote por tipo, e eles sempre cabem."""
    while True:
        packets = [(kind, packet) for kind in CHANGE_TYPES if kind in by_type for packet in _pack(by_type[kind], capacity)]
        if len(packets) <= slots or len(packets) == len(by_type):
            return packets
        capacity *= 2


def windows(floors: Sequence[dict[str, Any]], changes: Iterable[Change], percent: float) -> list[dict[str, Any]]:
    """As janelas acesas: `level` (o nível do prédio, de baixo para cima), `face` (0 a 3), `col` (0 a 7), o `type`, quantas
    alterações a janela junta (`changes`) e as linhas delas (`lines`). Cada janela acesa vale `percent`% das linhas alteradas
    do realm. Sem andares ou sem alterações, nenhuma."""
    changes = [Change(c.path, c.type, max(1, c.lines)) for c in changes]
    if not floors or not changes:
        return []
    capacity = sum(c.lines for c in changes) * percent / 100
    where = _Floors.of(floors)
    grouped: dict[int, dict[str, list[Change]]] = {}
    for change in changes:
        grouped.setdefault(where.of_path(change.path), {}).setdefault(change.type, []).append(change)
    per_row = rules.FACADE_FACES * rules.FACADE_COLS
    starts, level = [], 0
    for floor in floors:
        starts.append(level)
        level += floor["levels"]
    lit: list[dict[str, Any]] = []
    for index in sorted(grouped):
        slots = floors[index]["levels"] * per_row
        packets = _packets_for_floor(grouped[index], capacity, slots)
        for order, (kind, packet) in enumerate(packets):
            slot = int((order + 0.5) * slots / len(packets))              # espalhadas por igual pela fachada do andar
            row, rest = divmod(slot, per_row)
            lit.append({"level": starts[index] + row, "face": rest // rules.FACADE_COLS, "col": rest % rules.FACADE_COLS,
                        "type": kind, "changes": len(packet), "lines": sum(c.lines for c in packet)})
    return lit
