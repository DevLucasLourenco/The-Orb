"""A XP de uma sessão antiga, lida uma vez em segundo plano (R48, camada 3; D-088, D-108; PROGRESSION.md §7).

A sessão antiga não é um personagem (não está na sala, não tem estado nem nome): o mundo só guarda o que ela rendeu, para somar nos níveis
do Realm e de Mankind e no relatório de calibração. Os commits ficam inteiros num `Ledger` porque o git ainda pode confirmá-los, anulá-los ou
expirá-los (R53); o resto da XP já é definitivo e fica só como soma.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from . import rules
from .progression import CONFIRMED, X_COMMIT, Entry, Ledger


@dataclass
class PastEgo:
    ego: str
    realm: str
    provider: str
    commits: Ledger          # só os X-COMMIT desta sessão: quem o git ainda decide
    others: int              # a XP confirmada das outras regras

    @classmethod
    def from_entries(cls, table: rules.XpTable, ego: str, realm: str, provider: str, entries: Iterable[Entry]) -> PastEgo:
        mine = [e for e in entries if e.version == table.version]
        return cls(ego, realm, provider, Ledger(table, (e for e in mine if e.rule == X_COMMIT)),
                   sum(e.xp for e in mine if e.rule != X_COMMIT and e.state == CONFIRMED))

    @property
    def total(self) -> int:
        """A XP confirmada (a que conta para o nível)."""
        return self.others + self.commits.total

    @property
    def provisional(self) -> int:
        return self.commits.provisional
