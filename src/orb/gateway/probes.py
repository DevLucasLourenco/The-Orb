"""Quando rodar o Probe de linhas em cada realm (R19, D-055): ao abrir e quando algo muda, no máximo 1 vez por minuto por realm.

Contar lê arquivos do projeto e pode levar segundos num projeto grande; por isso roda numa thread própria, **um realm por
vez**, e nunca na thread que lê os providers. O resultado volta como um evento de realm (`realm.metrics`, protocolo 0.3)
que o Hub aplica no mundo. A decisão de "mudou?" é a impressão digital do Probe (arquivos que contam e filtro); o `stat`
de cada arquivo é barato perto de ler todos.
"""
from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..core.rules import LineFilter
from ..probes import count_lines, fingerprint, git_tracked_files, list_countable
from ..protocol import MAX_FOLDERS, Event, make_event
from .realms import Realm

__all__ = ["LineScheduler", "Realm"]

MIN_INTERVAL_SECONDS = 60.0      # D-055: no máximo uma contagem por minuto por realm
IDLE_SECONDS = 1.0               # a thread olha de novo depois disto quando nada estava na hora


def _biggest(folders: dict[str, int]) -> dict[str, int]:
    """As pastas de primeiro nível que vão no evento: as `MAX_FOLDERS` maiores (no empate, pelo nome). O que sobra fica no total,
    e o mundo o põe em "demais pastas"."""
    ranked = sorted(((name, count) for name, count in folders.items() if count > 0), key=lambda item: (-item[1], item[0]))
    return dict(ranked[:MAX_FOLDERS])


class LineScheduler:
    """Decide qual realm contar e quando. `run_once` trata no máximo um realm por chamada e devolve quantos eventos produziu."""

    def __init__(self, realms: Callable[[], dict[str, Realm]], filter_for: Callable[[Realm], LineFilter],
                 hidden: Callable[[], frozenset[str] | set[str]], *,
                 tracked: Callable[[Any], list[str] | None] = git_tracked_files,
                 clock: Callable[[], float] = time.monotonic, wall: Callable[[], datetime] | None = None,
                 interval: float = MIN_INTERVAL_SECONDS) -> None:
        self._realms = realms
        self._filter_for = filter_for
        self._hidden = hidden
        self._tracked = tracked
        self._clock = clock
        self._wall = wall or (lambda: datetime.now(UTC))        # a hora do mundo (o Hub informa a dele, R47)
        self._interval = interval
        self._last_check: dict[str, float] = {}
        self._last_print: dict[str, str] = {}
        self._events: queue.SimpleQueue[Event] = queue.SimpleQueue()
        self._seq = 0
        self._priority: list[str] = []                # realms que o Lucas acabou de mexer: contados antes dos outros
        self._lock = threading.Lock()                 # `refresh` roda em outra thread (to_thread); protege `_last_check` e `_priority`
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.notes: dict[str, str] = {}               # realm -> por que não tem número (a tela de configurações mostra)
        self.errors: dict[str, str] = {}              # realm -> último erro (degradação visível, nunca derruba os outros)

    # --- decisão ----------------------------------------------------------------------------------------
    def refresh(self, realm_ids: list[str] | None = None) -> None:
        """O filtro mudou nas configurações (ação do Lucas): os realms afetados são vistos de novo já, sem esperar o minuto, e
        os que ele escolheu passam à frente. Sem lista, são todos."""
        with self._lock:
            if realm_ids is None:
                self._last_check.clear()
                self._priority = []
                return
            for realm_id in realm_ids:
                self._last_check.pop(realm_id, None)
                if realm_id not in self._priority:
                    self._priority.append(realm_id)      # acrescenta: dois pedidos seguidos não se atropelam

    def run_once(self) -> int:
        with self._lock:
            return self._run_locked()

    def _run_locked(self) -> int:
        now = self._clock()
        hidden = self._hidden()
        due = sorted((realm.id not in self._priority, self._last_check.get(realm.id, float("-inf")), realm.id)
                     for realm in self._realms().values()
                     if realm.id not in hidden and now - self._last_check.get(realm.id, float("-inf")) >= self._interval)
        if not due:
            return 0
        realm = self._realms().get(due[0][2])
        if realm is None:
            return 0
        self._last_check[realm.id] = now
        if realm.id in self._priority:
            self._priority.remove(realm.id)
        self._lock.release()                              # contar lê arquivos e pode levar segundos: sem segurar a trava
        try:
            event = self._measure(realm)
        except Exception as exc:  # noqa: BLE001 - a falha de um realm nunca derruba os outros
            self.errors[realm.id] = f"{type(exc).__name__}: {exc}"
            return 0
        finally:
            self._lock.acquire()
        self.errors.pop(realm.id, None)
        if event is None:
            return 0
        self._events.put(event)
        return 1

    def _measure(self, realm: Realm) -> Event | None:
        root, flt = Path(realm.cwd), self._filter_for(realm)
        entries = list_countable(root, flt, self._tracked)
        if entries is None:
            self.notes[realm.id] = "o git não listou os arquivos (sem repositório, git ausente, tempo esgotado ou pasta que o git não aceita)"
            return None                                   # sem repositório: sem número, nunca um zero inventado
        self.notes.pop(realm.id, None)
        print_now = fingerprint(entries, flt)
        if self._last_print.get(realm.id) == print_now:
            return None                                   # nada que conta mudou desde a última contagem
        result = count_lines(root, entries)
        self._last_print[realm.id] = print_now
        self._seq += 1
        ts = self._wall().isoformat(timespec="milliseconds")
        # O id leva a hora: a impressão digital pode voltar a um valor antigo (ligar e desligar o .md) e a contagem nova
        # não pode ser descartada como repetida pela janela de dedupe do Core.
        return make_event(id=f"{realm.id}:lines:{ts}", ts=ts,
                          provider=None, source="probe/lines", realm=realm.id, alter_ego=None, agent=None, seq=self._seq,
                          kind="realm/lines", body={"loc": result.loc, "files": result.files},
                          signal={"type": "realm.metrics", "loc": result.loc, "files": result.files,
                                  "root": result.root, "folders": _biggest(result.folders)})

    def drain(self) -> list[Event]:
        """Os eventos prontos desde a última chamada."""
        out = []
        while True:
            try:
                out.append(self._events.get_nowait())
            except queue.Empty:
                return out

    # --- thread -----------------------------------------------------------------------------------------
    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, idle_seconds: float = IDLE_SECONDS) -> None:
        if self.running:
            return
        self._stop.clear()

        def loop() -> None:
            while not self._stop.is_set():
                try:
                    produced = self.run_once()
                except Exception as exc:  # noqa: BLE001 - nada derruba a thread: a contagem segue na próxima volta
                    self.errors["*"] = f"{type(exc).__name__}: {exc}"
                    produced = 0
                if not produced:
                    self._stop.wait(idle_seconds)

        self._thread = threading.Thread(target=loop, name="orb-lines", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
