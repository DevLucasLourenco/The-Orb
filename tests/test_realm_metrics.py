"""Protocolo 0.3 e estado por realm (R19, R49, D-051, D-052, D-085, D-091): eventos de realm e a classe do prédio."""
from datetime import UTC, datetime

import pytest

from orb.core import World, rules
from orb.protocol import PROTOCOL_VERSION, make_event, validate

T0 = datetime(2026, 10, 7, 10, 0, 0, tzinfo=UTC)


def realm_metrics_event(loc, *, realm="the-orb", key=None, ts="2026-10-07T10:00:00Z", **extra):
    signal = {"type": "realm.metrics"} if loc is None else {"type": "realm.metrics", "loc": loc}
    return make_event(id=f"{realm}:lines:{key or loc}", ts=ts, provider=None, source="probe/lines", realm=realm,
                      alter_ego=None, agent=None, seq=1, kind="realm/lines", body={}, signal={**signal, **extra})


def realm_of(world, realm="the-orb"):
    return next(r for r in world.snapshot(T0)["realms"] if r["id"] == realm)


# --- protocolo 0.3 -----------------------------------------------------------------------------------------

def test_the_protocol_is_0_3_and_an_older_minor_version_still_validates():
    event = realm_metrics_event(10)
    assert PROTOCOL_VERSION == "0.3" and event["v"] == "0.3"
    assert validate({**event, "v": "0.2"}) is None                              # só a versão maior decide


def test_a_realm_event_has_no_alter_ego_and_carries_the_lines_of_the_project():
    event = realm_metrics_event(48_000, files=312)
    assert event["alter_ego"] is None and event["provider"] is None and validate(event) is None


def test_a_realm_signal_needs_a_null_alter_ego_and_a_valid_files_count():
    event = realm_metrics_event(10)
    assert validate({**event, "alter_ego": "claude:s1"}) is not None             # só os Probes falam por um realm
    assert validate({**event, "agent": "a1"}) is not None
    for bad in (-1, 1.5, "3", True):
        assert validate(realm_metrics_event(10, files=bad)) is not None, bad
    assert validate(realm_metrics_event(10, files=0)) is None


def test_realm_metrics_needs_a_whole_non_negative_number_of_lines():
    assert validate(realm_metrics_event(None)) is not None                      # falta `loc`
    for bad in (-1, 1.5, "10", True):
        assert validate(realm_metrics_event(bad)) is not None, bad
    assert validate(realm_metrics_event(0)) is None


# --- a classe do prédio ------------------------------------------------------------------------------------

BAND_CASES = [(0, "Casa"), (999, "Casa"), (1_000, "Sobrado"), (4_999, "Sobrado"), (5_000, "Prédio"), (19_999, "Prédio"),
              (20_000, "Edifício"), (99_999, "Edifício"), (100_000, "Torre"), (499_999, "Torre"), (500_000, "Arranha-céu"),
              (5_000_000, "Arranha-céu")]


@pytest.mark.parametrize(("lines", "name"), BAND_CASES)
def test_the_building_class_comes_from_fixed_bands_of_lines(lines, name):
    assert rules.building_class(lines) == name                                  # faixa fechada embaixo: 500 mil já é Arranha-céu


def test_the_six_classes_and_their_bands_live_in_one_table():
    assert [c for c, _ in rules.BUILDING_CLASSES] == ["Casa", "Sobrado", "Prédio", "Edifício", "Torre", "Arranha-céu"]
    assert [lower for _, lower in rules.BUILDING_CLASSES] == [0, 1_000, 5_000, 20_000, 100_000, 500_000]


# --- o mundo guarda estado por realm ----------------------------------------------------------------------

def test_the_world_keeps_state_per_realm_and_derives_the_class_from_the_lines():
    world = World()
    assert world.apply(realm_metrics_event(48_000, files=312))
    metrics = realm_of(world)["metrics"]
    assert (metrics["loc"], metrics["class"], metrics["files"]) == (48_000, "Edifício", 312)
    assert metrics["counted_at"] == "2026-10-07T10:00:00Z"


def test_a_realm_without_a_count_has_no_metrics_instead_of_an_invented_zero():
    world = World()
    world.add_realm("novo")
    assert realm_of(world, "novo")["metrics"] is None                           # sem dado: nada (R12)


def test_the_newer_count_replaces_the_older_one_and_a_repeated_event_is_ignored():
    world = World()
    world.apply(realm_metrics_event(900, ts="2026-10-07T10:00:00Z"))
    assert world.apply(realm_metrics_event(900, ts="2026-10-07T10:00:00Z")) is False         # mesmo id: dedupe
    world.apply(realm_metrics_event(1_200, ts="2026-10-07T10:05:00Z"))
    assert realm_of(world)["metrics"]["class"] == "Sobrado" and realm_of(world)["metrics"]["loc"] == 1_200
    world.apply(realm_metrics_event(50, key="velho", ts="2026-10-07T09:00:00Z"))             # chegou atrasado: não volta no tempo
    assert realm_of(world)["metrics"]["loc"] == 1_200


def test_a_realm_event_creates_no_alter_ego_and_does_not_disturb_the_sessions():
    world = World()
    world.apply(make_event(id="claude:s1:1", ts="2026-10-07T10:00:00Z", provider="claude", source="x", realm="the-orb",
                           alter_ego="claude:s1", agent=None, seq=1, kind="x", body={}, signal={"type": "idle"}))
    world.apply(realm_metrics_event(10))
    assert [e["id"] for e in realm_of(world)["alter_egos"]] == ["claude:s1"]
    assert world.snapshot(T0)["mankind"]["alter_egos"] == 1


def test_a_hidden_realm_keeps_its_metrics_for_when_it_is_shown_again():
    world = World()
    world.apply(realm_metrics_event(2_000))
    world.set_hidden({"the-orb"})
    assert world.snapshot(T0)["realms"] == []
    world.set_hidden(set())
    assert realm_of(world)["metrics"]["class"] == "Sobrado"


# --- as pastas de primeiro nível e a altura (ticket 10) -------------------------------------------------------

def test_the_event_can_carry_the_lines_of_the_root_and_of_each_first_level_folder():
    event = realm_metrics_event(100, root=10, folders={"src": 60, "docs": 20})
    assert validate(event) is None
    assert validate(realm_metrics_event(100, root=0, folders={})) is None


def test_the_split_by_folder_must_be_well_formed_and_cannot_exceed_the_total():
    bad = [dict(root=-1), dict(root=1.5), dict(root=True), dict(folders=[1]), dict(folders={"": 3}), dict(folders={"a": -1}),
           dict(folders={"a": 1.5}), dict(folders={"a": True}), dict(folders={7: 3}), dict(folders={"x" * 300: 1}),
           dict(folders={f"p{n}": 1 for n in range(65)}), dict(root=60, folders={"a": 50})]        # passa do total (100)
    for extra in bad:
        assert validate(realm_metrics_event(100, **extra)) is not None, extra
    assert validate(realm_metrics_event(100, folders={f"p{n}": 1 for n in range(64)})) is None


def test_the_world_derives_the_height_trim_and_floors_from_the_lines_and_the_folders():
    world = World()
    world.apply(realm_metrics_event(48_000, files=312, root=2_000, folders={"src": 40_000, "tests": 6_000}))
    metrics = realm_of(world)["metrics"]
    assert (metrics["class"], metrics["levels"], metrics["bands"], metrics["antenna"]) == ("Edifício", 14, 3, False)
    assert [(f["kind"], f["name"]) for f in metrics["floors"]] == [("ground", None), ("folder", "src"), ("folder", "tests")]
    assert sum(f["levels"] for f in metrics["floors"]) == metrics["levels"] and sum(f["loc"] for f in metrics["floors"]) == 48_000


def test_a_count_without_the_folder_split_has_a_height_but_no_floors_instead_of_invented_ones():
    world = World()
    world.apply(realm_metrics_event(800))
    metrics = realm_of(world)["metrics"]
    assert (metrics["class"], metrics["levels"], metrics["bands"], metrics["floors"]) == ("Casa", 1, 0, None)


def test_the_skyscraper_has_five_bands_and_an_antenna():
    world = World()
    world.apply(realm_metrics_event(900_000))
    metrics = realm_of(world)["metrics"]
    assert (metrics["class"], metrics["bands"], metrics["antenna"]) == ("Arranha-céu", 5, True)
