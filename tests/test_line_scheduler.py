"""Quando contar as linhas de cada realm (R19, D-055): ao abrir e quando algo muda, no máximo 1 vez por minuto por realm."""
import time

from orb.core.rules import LineFilter
from orb.gateway import Hub
from orb.gateway.probes import LineScheduler, Realm
from orb.protocol import validate
from orb.registry import PreferencesFile

from .test_realms import (  # noqa: F401 - a máquina falsa de test_realms
    hermes_session,
    machine,
)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def make(tmp_path, names=("a.py",), **kw):
    root = tmp_path / "proj"
    root.mkdir(exist_ok=True)
    (root / "a.py").write_text("x\ny\n", encoding="utf-8")
    realms = {"proj": Realm("proj", str(root))}
    clock = Clock()
    hidden = kw.pop("hidden", frozenset())
    flt = kw.pop("flt", LineFilter())
    scheduler = LineScheduler(lambda: realms, lambda realm: flt, lambda: hidden,
                              tracked=lambda r: list(names), clock=clock)
    return scheduler, clock, root, realms


def test_a_realm_is_counted_when_the_orb_opens_and_the_event_is_a_valid_realm_event(tmp_path):
    scheduler, _, _, _ = make(tmp_path)
    assert scheduler.run_once() == 1
    [event] = scheduler.drain()
    assert validate(event) is None and event["alter_ego"] is None and event["realm"] == "proj"
    assert event["signal"] == {"type": "realm.metrics", "loc": 2, "files": 1}
    assert scheduler.drain() == []                                              # entregue uma vez só


def test_it_counts_a_realm_at_most_once_a_minute_and_only_again_when_something_changed(tmp_path):
    scheduler, clock, root, _ = make(tmp_path)
    scheduler.run_once()
    scheduler.drain()
    clock.now += 30
    assert scheduler.run_once() == 0                                            # menos de um minuto: nem olha
    clock.now += 31
    assert scheduler.run_once() == 0 and scheduler.drain() == []                # passou o minuto, nada mudou: não conta de novo
    (root / "a.py").write_text("x\ny\nz\n", encoding="utf-8")
    assert scheduler.run_once() == 0                                            # mudou, mas o minuto recomeçou a contar
    clock.now += 61
    assert scheduler.run_once() == 1
    assert scheduler.drain()[0]["signal"]["loc"] == 3


def test_only_one_realm_is_handled_per_turn_so_the_reading_never_stalls(tmp_path):
    scheduler, _, _, realms = make(tmp_path)
    other = tmp_path / "outra"
    other.mkdir()
    (other / "a.py").write_text("q\n", encoding="utf-8")
    realms["outra"] = Realm("outra", str(other))
    assert [scheduler.run_once(), scheduler.run_once(), scheduler.run_once()] == [1, 1, 0]
    assert sorted(e["realm"] for e in scheduler.drain()) == ["outra", "proj"]


def test_a_hidden_realm_is_not_counted_until_it_is_shown_again(tmp_path):
    hidden = {"proj"}
    scheduler, _, _, _ = make(tmp_path, hidden=hidden)
    assert scheduler.run_once() == 0
    hidden.clear()
    assert scheduler.run_once() == 1


def test_a_folder_the_git_cannot_list_gives_no_event_instead_of_a_zero(tmp_path):
    root = tmp_path / "sem-git"
    root.mkdir()
    scheduler = LineScheduler(lambda: {"x": Realm("x", str(root))}, lambda realm: LineFilter(), lambda: frozenset(),
                              tracked=lambda r: None, clock=Clock())
    assert scheduler.run_once() == 0 and scheduler.drain() == []


def test_changing_the_filter_counts_again_right_away_without_waiting_the_minute(tmp_path):
    flt = {"value": LineFilter()}
    root = tmp_path / "proj"
    root.mkdir()
    (root / "a.py").write_text("x\n", encoding="utf-8")
    (root / "README.md").write_text("um\ndois\n", encoding="utf-8")
    scheduler = LineScheduler(lambda: {"proj": Realm("proj", str(root))}, lambda realm: flt["value"], lambda: frozenset(),
                              tracked=lambda r: ["a.py", "README.md"], clock=Clock())
    scheduler.run_once()
    assert scheduler.drain()[0]["signal"]["loc"] == 1
    flt["value"] = LineFilter(include_markdown=True)                            # o Lucas passou a contar o .md
    scheduler.refresh()
    assert scheduler.run_once() == 1
    assert scheduler.drain()[0]["signal"]["loc"] == 3


def test_a_failure_while_counting_one_realm_does_not_stop_the_others(tmp_path):
    scheduler, _, _, realms = make(tmp_path)
    realms["quebra"] = Realm("quebra", str(tmp_path / "nao-existe"))
    scheduler._tracked = lambda r: (_ for _ in ()).throw(RuntimeError("quebrou")) if r.name == "nao-existe" else ["a.py"]
    scheduler.run_once()
    scheduler.run_once()
    assert [e["realm"] for e in scheduler.drain()] == ["proj"] and "quebra" in scheduler.errors


def test_the_background_thread_delivers_the_counts_and_stops(tmp_path):
    scheduler, _, _, _ = make(tmp_path)
    scheduler.start(idle_seconds=0.01)
    try:
        deadline = time.time() + 5
        found = []
        while time.time() < deadline and not found:
            found = scheduler.drain()
            time.sleep(0.02)
        assert found and found[0]["signal"]["loc"] == 2
    finally:
        scheduler.stop()
    assert not scheduler.running


# --- no Hub: a contagem vira estado do realm no mundo ------------------------------------------------------------

def test_the_settings_tell_why_a_realm_has_no_number(machine, tmp_path):  # noqa: F811
    alpha = machine.project("alpha", git=False)
    hermes_session(machine, "H1", alpha, days_ago=1)
    hub = Hub(machine.observatory(), tracked=lambda root: None)
    hub.poll_once()
    hub.lines.run_once()
    realm = next(r for r in hub.settings()["realms"] if r["id"] == "alpha")
    assert "git" in realm["lines_note"]                                                  # nada de realm sem número e sem motivo


def test_a_bad_line_filter_from_the_client_is_refused_and_an_unknown_realm_is_ignored(machine, tmp_path):  # noqa: F811
    import pytest
    alpha = machine.project("alpha", git=False)
    hermes_session(machine, "H1", alpha, days_ago=1)
    hub = Hub(machine.observatory(), preferences=PreferencesFile(tmp_path / "orb"))
    hub.poll_once()
    for bad in ({"lines": "todos"}, {"lines": {"exclude": "x"}}, {"realm_lines": ["alpha"]}, {"realm_lines": {"alpha": {"nao": 1}}}):
        with pytest.raises(ValueError):
            hub.update_preferences(bad)
    hub.update_preferences({"realm_lines": {"fantasma": {"include_markdown": True}}})   # id que não existe: ignorado
    assert hub.preferences.realm_lines == {}


def test_the_hub_turns_the_count_into_the_realm_state_with_the_class(machine, tmp_path):  # noqa: F811
    alpha = machine.project("alpha", git=False)
    (alpha / "main.py").write_text("\n".join(["x = 1"] * 1500) + "\n", encoding="utf-8")
    hermes_session(machine, "H1", alpha, days_ago=1)
    hub = Hub(machine.observatory(), tracked=lambda root: ["main.py"])
    hub.poll_once()
    hub.lines.run_once()
    hub.poll_once()
    metrics = next(r for r in hub.snapshot()["realms"] if r["id"] == "alpha")["metrics"]
    assert (metrics["loc"], metrics["class"]) == (1500, "Sobrado")


def test_changing_the_line_filter_in_the_settings_recounts_that_realm(machine, tmp_path):  # noqa: F811
    alpha = machine.project("alpha", git=False)
    (alpha / "main.py").write_text("x\n", encoding="utf-8")
    (alpha / "NOTAS.md").write_text("a\nb\nc\n", encoding="utf-8")
    hermes_session(machine, "H1", alpha, days_ago=1)
    hub = Hub(machine.observatory(), preferences=PreferencesFile(tmp_path / "orb"), tracked=lambda root: ["main.py", "NOTAS.md"])
    hub.poll_once()
    hub.lines.run_once()
    hub.poll_once()
    assert next(r for r in hub.snapshot()["realms"] if r["id"] == "alpha")["metrics"]["loc"] == 1
    hub.update_preferences({"realm_lines": {"alpha": {"include_markdown": True}}})           # só este realm passa a contar o .md
    hub.lines.run_once()
    hub.poll_once()
    assert next(r for r in hub.snapshot()["realms"] if r["id"] == "alpha")["metrics"]["loc"] == 4
    hub.update_preferences({"lines": {"include_markdown": True}, "realm_lines": {"alpha": None}})
    assert hub.preferences.line_filter(None).include_markdown is True               # para todos os realms


def test_a_realm_the_user_just_changed_is_counted_before_the_others(tmp_path):
    scheduler, _, _, realms = make(tmp_path)
    other = tmp_path / "outra"
    other.mkdir()
    (other / "a.py").write_text("q\n", encoding="utf-8")
    realms["outra"] = Realm("outra", str(other))
    scheduler.run_once()
    scheduler.run_once()
    scheduler.drain()
    scheduler.refresh()                                                          # os dois voltam a ser devidos
    scheduler.refresh(["proj"])                                                  # mas o Lucas mexeu no "proj"
    scheduler.run_once()
    assert "proj" in scheduler._last_check and "outra" not in scheduler._last_check        # o "proj" foi visto primeiro


def test_a_count_that_goes_back_to_an_older_state_is_not_dropped_as_a_repeat(tmp_path):
    from orb.core import World
    flt = {"value": LineFilter()}
    root = tmp_path / "proj"
    root.mkdir()
    (root / "a.py").write_text("x\n", encoding="utf-8")
    (root / "N.md").write_text("a\nb\n", encoding="utf-8")
    scheduler = LineScheduler(lambda: {"proj": Realm("proj", str(root))}, lambda realm: flt["value"], lambda: frozenset(),
                              tracked=lambda r: ["a.py", "N.md"], clock=Clock())
    world = World()
    for value in (LineFilter(), LineFilter(include_markdown=True), LineFilter()):        # liga e desliga o .md
        flt["value"] = value
        scheduler.refresh()
        time.sleep(0.002)                                                                # a hora do evento muda
        scheduler.run_once()
        for event in scheduler.drain():
            assert world.apply(event)
    assert world.snapshot()["realms"][0]["metrics"]["loc"] == 1                          # a última contagem vale, não a velha


def test_the_background_thread_survives_an_unexpected_failure(tmp_path):
    scheduler, _, _, _ = make(tmp_path)
    calls = {"n": 0}
    real = scheduler.run_once

    def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("falha fora da contagem")
        return real()

    scheduler.run_once = flaky
    scheduler.start(idle_seconds=0.01)
    try:
        deadline = time.time() + 5
        found = []
        while time.time() < deadline and not found:
            found = scheduler.drain()
            time.sleep(0.02)
        assert found and "*" in scheduler.errors                                         # contou depois da falha e deixou o motivo
    finally:
        scheduler.stop()


def test_refreshing_two_realms_in_a_row_keeps_both_in_front(tmp_path):
    scheduler, _, _, realms = make(tmp_path)
    for name in ("b", "c"):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "a.py").write_text("q\n", encoding="utf-8")
        realms[name] = Realm(name, str(folder))
    for _ in range(3):
        scheduler.run_once()
    scheduler.drain()
    scheduler.refresh(["c"])
    scheduler.refresh(["b"])
    assert scheduler._priority == ["c", "b"]
