"""A XP e os níveis do Alter Ego (R53, R54, D-101 a D-105, D-110, PROGRESSION.md §3 e §4).

XP é **recibo de trabalho confirmado**: cada ponto aponta para o evento que o gerou, e o extrato do Alter Ego guarda data, regra,
evidência e a versão da tabela. Puro, como o resto do Core: a XP é uma função dos eventos e da tabela (`rules.XP_TABLE`), sem disco,
rede nem relógio, e o mesmo histórico dá sempre a mesma XP. Nunca é negativa; tokens, mensagens, custo e espera não rendem nada.

Nesta versão só entra o que o próprio mundo confirma na hora (teste, conserto, subagente, ofício). O commit (X-COMMIT, provisório até
chegar à branch principal) e as escalas de Realm e Mankind vêm no ticket 23.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from ..protocol import Event
from . import rules

X_TEST, X_FIX, X_DELEG, X_CRAFT, X_COMMIT = "X-TEST", "X-FIX", "X-DELEG", "X-CRAFT", "X-COMMIT"
# Os estados de uma entrada (PROGRESSION.md §1 e §3): só a confirmada conta para o nível. Anulada (commit revertido) e expirada
# (30 dias sem chegar à principal) são finais.
CONFIRMED, PROVISIONAL, ANNULLED, EXPIRED = "confirmed", "provisional", "annulled", "expired"


@dataclass(frozen=True)
class Entry:
    """Uma linha do extrato. `ref` é a chave do recibo dentro da regra (o evento, o subagente, a janela de tempo): reler a mesma
    fonte nunca paga duas vezes. A `evidence` só tem ids e números, nunca o texto de um comando ou de uma sessão."""
    ts: str
    rule: str
    xp: int
    ref: str
    evidence: dict[str, Any]
    version: int
    state: str = CONFIRMED


class XpSource(Protocol):
    """O que o mundo pede do registro local (R36): o extrato guardado de um Alter Ego (só o da versão da tabela em uso) e onde
    gravar uma entrada (nova, ou a mesma com o estado e a XP que o git mudou). `error` diz por que não está guardando (disco com
    falha), ou é None."""

    error: str | None

    def entries_of(self, ego_id: str, version: int) -> list[Entry]: ...

    def record(self, ego_id: str, entry: Entry) -> None: ...


def level_of(xp: int, k: int) -> dict[str, int]:
    """O nível pela curva k·n·(n−1): o nível n começa em k·n·(n−1) de XP e o seguinte em k·(n+1)·n. Devolve também onde a barra começa
    e termina."""
    n = max(1, int((1 + math.sqrt(1 + 4 * xp / k)) / 2))
    while k * (n + 1) * n <= xp:             # o ponto flutuante pode errar por um nível nas bordas
        n += 1
    while n > 1 and k * n * (n - 1) > xp:
        n -= 1
    return {"level": n, "xp": xp, "floor": k * n * (n - 1), "next": k * (n + 1) * n}


def scale(xp: int, k: int) -> dict[str, int]:
    """O nível de uma escala (Alter Ego, Realm ou Mankind) para a XP confirmada `xp`: o total e a barra do nível."""
    info = level_of(xp, k)
    return {"total": info["xp"], "level": info["level"], "floor": info["floor"], "next": info["next"]}


def _when(ts: str) -> datetime | None:
    """A hora do evento em UTC; sem hora legível ou sem fuso não se afirma nada (R12): sem XP."""
    try:
        moment = datetime.fromisoformat(ts)
        return moment.astimezone(UTC) if moment.utcoffset() is not None else None
    except (TypeError, ValueError, OverflowError):          # o Protocol só exige uma string: um ano 0001 com fuso estoura a conversão
        return None


class Ledger:
    """O extrato e a conta de XP de um Alter Ego. Recebe o extrato já guardado (só o da versão da tabela) e os eventos; devolve as
    entradas novas. Os limites (um teste por 10 min, os tetos por dia) saem do próprio extrato, então valem também depois de reabrir."""

    def __init__(self, table: rules.XpTable = rules.XP_TABLE, entries: Iterable[Entry] = ()) -> None:
        self.table = table
        self.entries: list[Entry] = [e for e in entries if e.version == table.version]
        self._seen = {(e.rule, e.ref) for e in self.entries}
        self.total = 0                                          # a XP confirmada (a que conta para o nível) e a provisória:
        self.provisional = 0                                    # somas correntes, o snapshot as pede a cada leitura
        self._recount()
        self._open_failure: str | None = None                   # o primeiro teste vermelho que ainda não foi consertado
        self._last_test: datetime | None = None
        self._day_xp: dict[tuple[str, Any], int] = {}
        for entry in self.entries:
            when = _when(entry.ts)
            if when is None:
                continue
            day = (entry.rule, when.date())
            self._day_xp[day] = self._day_xp.get(day, 0) + entry.xp
            if entry.rule == X_TEST and (self._last_test is None or when > self._last_test):
                self._last_test = when

    def _recount(self) -> None:
        self.total = sum(e.xp for e in self.entries if e.state == CONFIRMED)
        self.provisional = sum(e.xp for e in self.entries if e.state == PROVISIONAL)

    def snapshot(self) -> dict[str, int]:
        """O que os clientes veem: a XP confirmada, a provisória (a barra tracejada), o nível e onde a barra começa e termina."""
        return {**scale(self.total, self.table.k), "provisional": self.provisional}

    def observe(self, event: Event) -> list[Entry]:
        """Olha um evento e devolve as entradas novas do extrato (já acrescentadas a ele)."""
        signal = event.get("signal")
        when = _when(event["ts"]) if signal else None
        if not signal or when is None:
            return []
        kind = signal["type"]
        if kind == "command.result":
            earned = self._commit(event, signal, when) if signal.get("ok") and isinstance(signal.get("commit"), dict) else []
            return earned + (self._tests(event, signal, when) if signal.get("activity") == "TESTING" else [])
        if kind == "subagent.ended" and event.get("agent") and signal.get("outcome") in (None, "completed"):
            return self._award(event, when, X_DELEG, str(event["agent"]), self.table.deleg_xp, {"agent": event["agent"]},
                               cap=self.table.deleg_cap)
        if kind == "activity" and signal.get("activity") in self.table.craft_activities:
            window = int(when.timestamp()) // self.table.craft_window_seconds
            start = datetime.fromtimestamp(window * self.table.craft_window_seconds, UTC).isoformat().replace("+00:00", "Z")
            return self._award(event, when, X_CRAFT, str(window), self.table.craft_xp, {"window": start, "event": event["id"]},
                               cap=self.table.craft_cap)
        return []

    def _commit(self, event: Event, signal: dict[str, Any], when: datetime) -> list[Entry]:
        """Um commit feito pela sessão (X-COMMIT): a evidência é do provider (Claude: o `gitOperation`, com o hash; os outros: o `git commit`
        que deu certo). Começa **provisório**: o que o git disser depois (`settle`) o confirma, anula ou expira. O recibo é o hash,
        ou o evento quando não veio hash."""
        sha = signal["commit"].get("sha")
        evidence: dict[str, Any] = {"event": event["id"], "at": event["ts"], **({"sha": sha} if sha else {})}
        # O recibo sem hash é o id do evento; o protocolo não limita o tamanho do id, e o recibo vai num evento de realm (200 caracteres):
        # um id comprido vira um resumo dele.
        ref = sha or (event["id"] if len(event["id"]) <= 120 else "ev-" + hashlib.sha256(event["id"].encode()).hexdigest()[:40])
        return self._award(event, when, X_COMMIT, ref, self.table.commit_xp, evidence, state=PROVISIONAL)

    def commit_queries(self, now: datetime) -> list[dict[str, Any]]:
        """O que perguntar ao git: os commits provisórios e os confirmados que ainda estão na janela em que uma reversão os anula."""
        window = self.table.commit_expire_days * 86400
        asked = []
        for entry in self.entries:
            if entry.rule != X_COMMIT or entry.state not in (PROVISIONAL, CONFIRMED):
                continue
            at = entry.evidence.get("at", entry.ts)
            moment = _when(at)
            if entry.state == CONFIRMED and (moment is None or (now - moment).total_seconds() > window):
                continue
            asked.append({"key": entry.ref, "sha": entry.evidence.get("sha"), "at": at})
        return asked

    def settle(self, commits: Iterable[dict[str, Any]], ts: str) -> list[Entry]:
        """Aplica o que o git disse dos commits (`realm.commits`) e o tempo (`ts` é a hora da leitura): o commit que existe e chegou à
        principal é confirmado, o revertido é anulado, o que não chegou em `commit_expire_days` expira. As linhas dão a XP (10 + 1 a cada 20,
        com teto). Anulada e expirada são finais; um commit confirmado só cai por reversão. Devolve as entradas que mudaram."""
        now = _when(ts)
        if now is None:
            return []
        facts = {fact["key"]: fact for fact in commits}
        table, changed = self.table, []
        for index, entry in enumerate(self.entries):
            if entry.rule != X_COMMIT or entry.state in (ANNULLED, EXPIRED):
                continue
            fact = facts.get(entry.ref)
            xp, state, evidence = entry.xp, entry.state, entry.evidence
            if fact is not None and fact["exists"]:
                if fact["lines"] is not None:
                    xp = min(table.commit_cap, table.commit_xp + fact["lines"] // table.commit_lines_per_xp)
                if fact["sha"] and evidence.get("sha") != fact["sha"]:
                    evidence = {**evidence, "sha": fact["sha"]}
                if fact["reverted"]:
                    state = ANNULLED
                elif fact["on_main"]:
                    state = CONFIRMED
            at = _when(evidence.get("at", entry.ts))
            if state == PROVISIONAL and at is not None and (now - at).total_seconds() > table.commit_expire_days * 86400:
                state = EXPIRED
            if (xp, state, evidence) != (entry.xp, entry.state, entry.evidence):
                self.entries[index] = Entry(entry.ts, entry.rule, xp, entry.ref, evidence, entry.version, state)
                changed.append(self.entries[index])
        if changed:
            self._recount()
        return changed

    def _tests(self, event: Event, signal: dict[str, Any], when: datetime) -> list[Entry]:
        """Um teste que falha abre uma falha; um que passa rende X-TEST (no máximo um a cada `test_gap_seconds`) e, se havia uma falha
        aberta, também X-FIX, uma vez por falha consertada."""
        if not signal.get("ok"):
            if self._open_failure is None:
                self._open_failure = event["id"]
            return []
        evidence: dict[str, Any] = {"event": event["id"]}
        if isinstance(signal.get("exit_code"), int):
            evidence["exit_code"] = signal["exit_code"]
        earned: list[Entry] = []
        spaced = self._last_test is None or abs((when - self._last_test).total_seconds()) >= self.table.test_gap_seconds
        if spaced:
            earned += self._award(event, when, X_TEST, event["id"], self.table.test_xp, evidence)
            if earned:
                self._last_test = when if self._last_test is None else max(self._last_test, when)      # um evento atrasado não recua o limite
        if self._open_failure is not None:
            earned += self._award(event, when, X_FIX, event["id"], self.table.fix_xp, {"failed": self._open_failure, "passed": event["id"]})
            self._open_failure = None
        return earned

    def _award(self, event: Event, when: datetime, rule: str, ref: str, xp: int, evidence: dict[str, Any], *,
               cap: int | None = None, state: str = CONFIRMED) -> list[Entry]:
        """Acrescenta uma entrada, a menos que o recibo já esteja no extrato ou que o teto do dia já tenha sido atingido."""
        if (rule, ref) in self._seen:
            return []
        day = (rule, when.date())
        if cap is not None and self._day_xp.get(day, 0) + xp > cap:
            return []
        entry = Entry(ts=event["ts"], rule=rule, xp=xp, ref=ref, evidence=evidence, version=self.table.version, state=state)
        self.entries.append(entry)
        if state == CONFIRMED:
            self.total += xp
        elif state == PROVISIONAL:
            self.provisional += xp
        self._seen.add((rule, ref))
        self._day_xp[day] = self._day_xp.get(day, 0) + xp
        return [entry]


def replay(table: rules.XpTable, events: Iterable[Event]) -> Ledger:
    """Recalcula o extrato de um Alter Ego a partir dos eventos, na ordem, com a tabela dada (trocar a versão da tabela é isto)."""
    ledger = Ledger(table)
    for event in events:
        ledger.observe(event)
    return ledger
