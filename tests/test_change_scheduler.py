"""Quando ler as alterações locais de cada realm (R20b): ao abrir e a cada poucos segundos, só publicando o que mudou."""
from datetime import UTC, datetime

from orb.gateway import Hub
from orb.gateway.probes import ChangeScheduler, Realm
from orb.probes import Change, ChangeSet
from orb.protocol import validate

from .test_realms import (  # noqa: F401 - a máquina falsa de test_realms
    hermes_session,
    machine,
)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class Reader:
    """Um leitor de git falso: devolve o que o teste puser em `result` e conta quantas vezes foi chamado."""

    def __init__(self, result):
        self.result = result
        self.calls = 0

    def __call__(self, root):
        self.calls += 1
        return self.result


def make(result=None, **kw):
    reader = Reader(result if result is not None else ChangeSet([Change("src/a.py", "modified", 3)]))
    realms = {"proj": Realm("proj", "C:/x/proj")}
    clock = Clock()
    hidden = kw.pop("hidden", frozenset())
    scheduler = ChangeScheduler(lambda: realms, lambda: hidden, reader=reader, clock=clock, **kw)
    return scheduler, clock, reader, realms


def test_a_realm_is_read_when_the_orb_opens_and_the_event_is_a_valid_realm_event():
    scheduler, _, _, _ = make()
    assert scheduler.run_once() == 1
    [event] = scheduler.drain()
    assert validate(event) is None and event["alter_ego"] is None and event["realm"] == "proj"
    assert event["signal"] == {"type": "realm.changes", "changes": [{"path": "src/a.py", "type": "modified", "lines": 3}], "more": 0}
    assert scheduler.drain() == []                                              # entregue uma vez só


def test_it_looks_at_a_realm_at_most_every_15_seconds_and_only_publishes_what_changed():
    scheduler, clock, reader, _ = make()
    scheduler.run_once()
    scheduler.drain()
    clock.now += 10
    assert scheduler.run_once() == 0 and reader.calls == 1                      # cedo demais: nem olha
    clock.now += 6
    assert scheduler.run_once() == 0 and reader.calls == 2 and scheduler.drain() == []     # olhou, nada mudou: não publica
    reader.result = ChangeSet([Change("src/a.py", "modified", 3), Change("novo.txt", "untracked", 1)])
    clock.now += 16
    assert scheduler.run_once() == 1
    assert len(scheduler.drain()[0]["signal"]["changes"]) == 2


def test_a_clean_repository_is_published_once_as_an_empty_list_and_that_is_data():
    scheduler, clock, _, _ = make(ChangeSet([]))
    assert scheduler.run_once() == 1
    assert scheduler.drain()[0]["signal"]["changes"] == []
    clock.now += 16
    assert scheduler.run_once() == 0                                            # continua limpo: nada novo


def test_a_folder_without_git_publishes_nothing_and_says_why_instead_of_looking_clean():
    scheduler, clock, reader, _ = make(None)
    reader.result = None
    assert scheduler.run_once() == 0 and scheduler.drain() == []
    assert "proj" in scheduler.notes
    reader.result = ChangeSet([])
    clock.now += 16
    assert scheduler.run_once() == 1 and "proj" not in scheduler.notes          # o git voltou a responder


def test_a_hidden_realm_is_not_read():
    scheduler, _, reader, _ = make(hidden=frozenset({"proj"}))
    assert scheduler.run_once() == 0 and reader.calls == 0


def test_a_failing_reader_is_recorded_and_never_stops_the_others():
    scheduler, _, reader, realms = make()
    realms["aaa"] = Realm("aaa", "C:/x/aaa")                                     # é o primeiro da fila (ordem do id)

    def reader_that_fails_for_aaa(root):
        if str(root).endswith("aaa"):
            raise OSError("disco")
        return reader(root)

    scheduler._reader = reader_that_fails_for_aaa
    assert scheduler.run_once() == 0 and "disco" in scheduler.errors["aaa"]
    assert scheduler.run_once() == 1 and scheduler.drain()[0]["realm"] == "proj"   # o realm seguinte é lido mesmo assim


def test_the_event_id_carries_the_time_so_a_return_to_an_old_state_is_not_dropped_as_repeated():
    ticks = iter(range(100))
    wall = lambda: datetime(2026, 10, 14, 10, 0, next(ticks), tzinfo=UTC)  # um relógio falso que anda 1 s por chamada
    scheduler, clock, reader, _ = make(wall=wall)
    scheduler.run_once()
    reader.result = ChangeSet([])
    clock.now += 16
    scheduler.run_once()
    reader.result = ChangeSet([Change("src/a.py", "modified", 3)])                # volta ao estado do começo
    clock.now += 16
    scheduler.run_once()
    ids = [e["id"] for e in scheduler.drain()]
    assert len(ids) == 3 and len(set(ids)) == 3


def test_the_hub_applies_the_reading_in_the_world_and_the_window_percent_reaches_it(machine):  # noqa: F811
    alpha = machine.project("alpha")
    hermes_session(machine, "H-a", alpha, days_ago=1)
    hub = Hub(machine.observatory())
    hub.poll_once()
    assert hub.world.window_percent == 5.0
    hub.update_preferences({"window_percent": 10})
    assert hub.world.window_percent == 10 and hub.settings()["preferences"]["window_percent"] == 10
    assert any(o["key"] == "window_percent" and o["value"] == 10 for o in hub.settings()["options"])
