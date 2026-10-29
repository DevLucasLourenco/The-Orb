"""A leitura única do passado, em segundo plano (R48 camada 3; D-088, D-108; PROGRESSION.md §7).

Na primeira vez (e a cada versão nova da tabela de XP, D-203) o Orb lê as sessões antigas **uma única vez** e calcula a XP delas pelas mesmas regras
da sala (`core.progression.Ledger`). O ponto de parada é do registro local: cada sessão lida é marcada na mesma transação que grava as entradas
dela, então uma sessão nunca é lida duas vezes, e a leitura interrompida recomeça pela sessão que não terminou.

Não pesa no Orb: roda numa thread própria, **uma sessão por vez e um lote por passo** (cada lote é uma leitura limitada do adapter) e descansa depois
de cada passo um múltiplo do tempo que gastou. A thread nunca toca no mundo: entrega o resultado por `drain()`, que o Hub aplica na thread dele.
"""
from __future__ import annotations

import queue
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from ..adapters._shared import PastSource, SessionMeta, alter_ego_id
from ..core import Entry, Ledger, rules
from ..core.progression import PastStore, XpSource
from ..protocol import Event, validate

REST_RATIO = 3.0           # depois de cada passo a thread descansa 3 vezes o que gastou: no máximo ~25% de uma CPU
IDLE_SECONDS = 1.0         # sem trabalho agora (índice ainda não varrido, registro com falha): olha de novo depois disto
MAX_ERRORS = 20            # erros guardados (uma linha por sessão que falhou), para nunca crescer sem limite


@dataclass(frozen=True)
class PastResult:
    """Uma sessão antiga lida: o extrato inteiro dela, nesta versão da tabela, para o mundo somar."""
    ego: str
    realm: str
    provider: str
    entries: tuple[Entry, ...]


class RegistryStore(PastStore, XpSource, Protocol):
    """O que o registro local dá a esta leitura (o mesmo objeto que o mundo usa para o extrato)."""


class PastXp:
    thread_name = "orb-past"

    def __init__(self, leaders: Callable[[], list[tuple[SessionMeta, str]]], sources: dict[str, PastSource], store: RegistryStore, *,
                 table: rules.XpTable = rules.XP_TABLE, wall: Callable[[], datetime] | None = None,
                 clock: Callable[[], float] = time.monotonic, rest_ratio: float = REST_RATIO) -> None:
        self._leaders = leaders
        self._sources = sources
        self._store = store
        self._table = table
        self._wall = wall or (lambda: datetime.now(UTC))
        self._clock = clock
        self._rest = rest_ratio
        self._todo: deque[tuple[SessionMeta, str]] | None = None             # as sessões que ainda faltam (None: o índice ainda não disse quais)
        self._current: tuple[SessionMeta, str, str, Iterator[list[Event]], Ledger, set[tuple[str, str]]] | None = None
        self._results: queue.SimpleQueue[PastResult] = queue.SimpleQueue()
        self._total: dict[str, int] = {}
        self._done: dict[str, int] = {}
        self._finished = False
        self.errors: dict[str, str] = {}                                     # sessão -> o que falhou (degradação visível; a leitura segue com as outras)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    # --- o que o resto do Orb vê --------------------------------------------------------------------------------------------
    def progress(self) -> dict[str, Any]:
        """O indicador de progresso (V-HUD-18): `waiting` (o índice de sessões ainda não disse o que há), `running`, `paused` (o registro local não está gravando:
        sem ponto de parada não se lê) ou `done`; quantas sessões há, quantas já foram lidas, por provider."""
        if self._todo is None:
            state = "waiting"
        elif self._finished:
            state = "done"
        elif self._store.error:
            state = "paused"
        else:
            state = "running"
        total, done = dict(self._total), dict(self._done)
        return {"state": state, "version": self._table.version, "total": sum(total.values()), "done": sum(done.values()),
                "providers": {name: {"total": total[name], "done": done.get(name, 0)} for name in sorted(total)},
                "errors": len(self.errors)}

    def drain(self) -> list[PastResult]:
        """As sessões lidas desde a última chamada."""
        out = []
        while True:
            try:
                out.append(self._results.get_nowait())
            except queue.Empty:
                return out

    # --- o trabalho -----------------------------------------------------------------------------------------------------------
    def run_once(self) -> bool:
        """Um passo: no máximo um lote de uma sessão. Devolve se havia trabalho (a thread descansa mais quando não há)."""
        if self._todo is None and not self._plan():
            return False
        if self._store.error and not self._store.recover():
            return False                                      # sem registro gravando não há ponto de parada: espera voltar (e tenta de novo a cada volta)
        if self._current is None and not self._open_next():
            return False
        assert self._current is not None
        meta, realm, ego, batches, ledger, stored = self._current
        try:
            batch = next(batches)
        except StopIteration:
            self._close(meta, realm, ego, ledger, stored)
            return True
        except Exception as exc:  # noqa: BLE001 - uma sessão que falha não derruba as outras: fica sem marca e volta na próxima abertura
            self._fail(meta, exc)
            return True
        for event in batch:
            if event.get("alter_ego") == ego and validate(event) is None:
                ledger.observe(event)
        return True

    def _plan(self) -> bool:
        """Decide o que falta ler: as sessões que o índice listou, menos as que o registro já marcou para esta versão da tabela, as mais recentes
        primeiro (o que o Lucas mais olha ganha XP antes). Falso enquanto o índice ainda não varreu nada."""
        leaders = [(meta, realm) for meta, realm in self._leaders() if meta.provider in self._sources]
        if not leaders:
            return False
        done = self._store.past_done(self._table.version)
        self._total, self._done = {}, {}
        for meta, _realm in leaders:
            self._total[meta.provider] = self._total.get(meta.provider, 0) + 1
            if (meta.provider, meta.session_id) in done:
                self._done[meta.provider] = self._done.get(meta.provider, 0) + 1
        todo = [pair for pair in leaders if (pair[0].provider, pair[0].session_id) not in done]
        todo.sort(key=lambda pair: (pair[0].updated_at or "", pair[0].session_id), reverse=True)
        self._todo = deque(todo)
        self._finished = not todo
        return True

    def _open_next(self) -> bool:
        assert self._todo is not None
        if not self._todo:
            self._finished = True
            return False
        meta, realm = self._todo.popleft()
        ego = alter_ego_id(meta.provider, meta.session_id)
        before = self._store.entries_of(ego, self._table.version)         # o que o registro já tem: a conta recomeça dele, e só o novo é gravado
        self._current = (meta, realm, ego, self._sources[meta.provider].read(meta, realm), Ledger(self._table, before),
                         {(e.rule, e.ref) for e in before})
        return True

    def _close(self, meta: SessionMeta, realm: str, ego: str, ledger: Ledger, stored: set[tuple[str, str]]) -> None:
        """Terminou a sessão: o que já passou do prazo de 30 dias sem chegar à principal expira (regra pura, sem o git); o resto o Probe
        dos commits decide, como para qualquer sessão. Grava as entradas novas com a marca de lida (uma transação) e entrega o extrato ao mundo."""
        now = self._wall().isoformat()
        ledger.settle([], now)
        fresh = [e for e in ledger.entries if (e.rule, e.ref) not in stored]
        self._store.record_past(ego, fresh, meta.provider, meta.session_id, self._table.version, now)
        self._results.put(PastResult(ego, realm, meta.provider, tuple(ledger.entries)))
        self._done[meta.provider] = self._done.get(meta.provider, 0) + 1
        self._current = None

    def _fail(self, meta: SessionMeta, exc: Exception) -> None:
        if len(self.errors) < MAX_ERRORS:
            self.errors[f"{meta.provider}:{meta.session_id}"] = f"{type(exc).__name__}: {exc}"
        self._current = None

    # --- thread -----------------------------------------------------------------------------------------------------------------
    def rest_after(self, spent: float) -> float:
        """Quanto descansar depois de um passo que levou `spent` segundos: um múltiplo do que se gastou, para o Orb não perder o fôlego."""
        return max(0.0, spent * self._rest)

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()

        def loop() -> None:
            while not self._stop.is_set():
                began = self._clock()
                try:
                    worked = self.run_once()
                except Exception as exc:  # noqa: BLE001 - nada derruba a thread
                    self.errors["*"] = f"{type(exc).__name__}: {exc}"
                    worked = False
                if self._finished and not worked:
                    return                                    # acabou: a thread não fica à toa
                if worked:
                    self._stop.wait(self.rest_after(self._clock() - began))
                else:
                    self._stop.wait(IDLE_SECONDS)

        self._thread = threading.Thread(target=loop, name=self.thread_name, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
