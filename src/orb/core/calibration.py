"""A calibração da curva de níveis com o histórico real (R54, D-107, PROGRESSION.md §4).

Puro: recebe a XP confirmada de cada sessão (e a dos realms e de Mankind) e devolve como ela se distribui pelos níveis, na curva em uso
e em curvas candidatas. O Orb **não escolhe** o k: mostra os números ao Lucas, que aprova uma nova versão da tabela (`rules.XP_TABLE`).

A meta é a de D-107: a sessão típica fica entre os níveis 2 e 4 e só sessões excepcionais passam do 8. "Típica" é a **mediana** das sessões
que têm alguma XP (uma sessão sem recibo nenhum não diz nada sobre a curva) e "só excepcionais" é no máximo `EXCEPTIONAL_SHARE` delas.
"""
from __future__ import annotations

from bisect import bisect_left
from collections.abc import Sequence
from typing import Any

from . import rules
from .progression import level_of

CANDIDATE_K: tuple[int, ...] = (25, 50, 75, 100, 150, 200)      # as curvas que o relatório compara, além da que está em uso
TYPICAL_LEVELS = (2, 4)                                         # D-107: a sessão típica fica entre estes níveis
EXCEPTIONAL_LEVEL = 8                                           # D-107: só sessões excepcionais passam deste nível
EXCEPTIONAL_SHARE = 0.05                                        # "só excepcionais": no máximo esta parcela das sessões (provisório, qt25-3)
_SEARCH_K = range(5, 1001, 5)                                   # onde se procura a faixa de k que cumpre a meta


def _percentile(sorted_values: Sequence[int], percent: int) -> int:
    """O valor na posição de `percent` por ranking mais próximo (sem interpolar: o relatório só mostra XP que existe)."""
    if not sorted_values:
        return 0
    rank = max(1, -(-len(sorted_values) * percent // 100))
    return sorted_values[min(rank, len(sorted_values)) - 1]


def _levels(ordered: Sequence[int], k: int) -> dict[int, int]:
    """Quantos há em cada nível da curva `k`, de `ordered` (em ordem crescente): o nível n começa em k·n·(n−1), então basta contar por faixa."""
    counts: dict[int, int] = {}
    n = 1
    while ordered and k * n * (n - 1) <= ordered[-1]:
        found = bisect_left(ordered, k * (n + 1) * n) - bisect_left(ordered, k * n * (n - 1))
        if found:
            counts[n] = found
        n += 1
    return counts


def judge(ordered: Sequence[int], k: int) -> dict[str, Any]:
    """Como `ordered` (a XP de cada sessão que tem alguma, em ordem crescente) se distribui pelos níveis da curva `k`, e se cumpre a meta de D-107."""
    levels = _levels(ordered, k)
    count = len(ordered)
    median = level_of(_percentile(ordered, 50), k)["level"] if count else None
    typical = sum(n for lvl, n in levels.items() if TYPICAL_LEVELS[0] <= lvl <= TYPICAL_LEVELS[1])
    above = sum(n for lvl, n in levels.items() if lvl > EXCEPTIONAL_LEVEL)
    meets = bool(count) and TYPICAL_LEVELS[0] <= median <= TYPICAL_LEVELS[1] and above <= count * EXCEPTIONAL_SHARE
    return {"k": k, "levels": levels, "median_level": median, "typical_share": typical / count if count else None,
            "above_share": above / count if count else None, "meets": meets}


def fit_range(ordered: Sequence[int]) -> dict[str, int] | None:
    """O menor e o maior k (de 5 em 5) que cumprem a meta de D-107 com estas sessões, ou None se nenhum cumpre (ou sem sessões)."""
    ok = [k for k in _SEARCH_K if judge(ordered, k)["meets"]]
    return {"min": ok[0], "max": ok[-1]} if ok else None


def report(table: rules.XpTable, sessions: Sequence[int], realms: Sequence[int], mankind: int) -> dict[str, Any]:
    """O relatório da distribuição de níveis: `sessions` é a XP confirmada de cada Alter Ego (com ou sem XP), `realms` a de cada realm
    que a cidade mostra e `mankind` a soma. Cada curva (a em uso e as candidatas) traz os níveis das sessões, se cumpre a meta e como
    ficariam os realms e Mankind mantendo a proporção atual entre as três escalas (Realm e Mankind valem tantas vezes o k do Alter Ego
    quanto hoje). `fit` é a faixa de k que cumpre a meta com este histórico."""
    with_xp = sorted(xp for xp in sessions if xp > 0)
    by_realm = sorted(realms)
    ratio_realm, ratio_mankind = table.k_realm / table.k, table.k_mankind / table.k

    def curve(k: int) -> dict[str, Any]:
        k_realm, k_mankind = round(k * ratio_realm), round(k * ratio_mankind)
        return {**judge(with_xp, k), "realm_k": k_realm, "realm_levels": _levels(by_realm, k_realm),
                "mankind_k": k_mankind, "mankind_level": level_of(mankind, k_mankind)["level"]}

    return {
        "version": table.version,
        "target": {"typical": list(TYPICAL_LEVELS), "exceptional_level": EXCEPTIONAL_LEVEL, "exceptional_share": EXCEPTIONAL_SHARE},
        "sessions": {"total": len(sessions), "with_xp": len(with_xp), "zero": len(sessions) - len(with_xp)},
        "realms": len(realms),
        "mankind_xp": mankind,
        "xp": {"median": _percentile(with_xp, 50), "p90": _percentile(with_xp, 90), "p99": _percentile(with_xp, 99),
               "max": with_xp[-1] if with_xp else 0},
        "current": curve(table.k),
        "candidates": [curve(k) for k in CANDIDATE_K if k != table.k],
        "fit": fit_range(with_xp),
    }
