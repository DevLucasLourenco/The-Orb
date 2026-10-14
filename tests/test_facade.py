"""A fachada do prédio (R20, R20a, R20b, R20d; VISUAL.md §6): alterações locais -> janelas acesas por andar, tipo e x%."""
import random
from datetime import UTC, datetime

import pytest

from orb.core import World, facade, rules
from orb.protocol import make_event, validate

T0 = datetime(2026, 10, 14, 10, 0, 0, tzinfo=UTC)

# Um prédio de 10 níveis: térreo (1), src (5), tests (3) e "demais pastas" (1).
FLOORS = [
    {"kind": "ground", "name": None, "levels": 1, "loc": 100},
    {"kind": "folder", "name": "src", "levels": 5, "loc": 5_000},
    {"kind": "folder", "name": "tests", "levels": 3, "loc": 2_000},
    {"kind": "rest", "name": None, "levels": 1, "loc": 100},
]


def changes(spec):
    """[(caminho, tipo, linhas)] -> lista de alterações."""
    return [facade.Change(path, kind, lines) for path, kind, lines in spec]


def lit(floors, spec, percent=5):
    return facade.windows(floors, changes(spec), percent)


def floor_of(window, floors=FLOORS):
    """Em que andar uma janela caiu (pelo nível absoluto dela)."""
    start = 0
    for index, floor in enumerate(floors):
        if start <= window["level"] < start + floor["levels"]:
            return index
        start += floor["levels"]
    raise AssertionError(window)


# --- o pacote: andar, tipo, x% e nada dividido -----------------------------------------------------------------

def test_the_changes_of_one_floor_and_type_are_packed_until_they_sum_x_percent():
    spec = [(f"src/f{n:03d}.py", "modified", 1) for n in range(100)]                   # 100 alterações de 1 linha: x = 5% = 5 linhas
    wins = lit(FLOORS, spec, 5)
    assert len(wins) == 20 and {w["changes"] for w in wins} == {5}                      # ~20 janelas no prédio inteiro
    assert sum(w["changes"] for w in wins) == 100 and {w["type"] for w in wins} == {"modified"}


def test_a_change_is_never_split_and_one_bigger_than_x_takes_a_whole_window_alone():
    spec = [("src/grande.py", "modified", 500)] + [(f"src/p{n}.py", "modified", 1) for n in range(10)]
    wins = lit(FLOORS, spec, 5)
    assert sum(w["changes"] for w in wins) == 11                                       # nenhuma se perdeu nem se dividiu
    big = [w for w in wins if w["lines"] >= 500]
    assert len(big) == 1 and big[0]["changes"] == 1                                      # passa de x%: uma janela inteira só dela


def test_with_few_changes_each_one_has_its_own_window_when_they_do_not_fit_in_x_percent():
    spec = [("src/a.py", "modified", 40), ("src/b.py", "modified", 40), ("src/c.py", "modified", 40)]
    wins = lit(FLOORS, spec, 5)
    assert len(wins) == 3 and all(w["changes"] == 1 for w in wins)


def test_changes_of_different_types_or_floors_never_share_a_window_and_each_combination_gets_one():
    spec = [("src/a.py", "modified", 1), ("src/b.py", "added", 1), ("tests/t.py", "modified", 1), ("README", "deleted", 1),
            ("src/c.py", "untracked", 1), ("src/d.py", "conflict", 1), ("src/e.py", "renamed", 1)]
    wins = lit(FLOORS, spec, 50)
    pairs = {(floor_of(w), w["type"]) for w in wins}
    assert pairs == {(1, "modified"), (1, "added"), (2, "modified"), (0, "deleted"), (1, "untracked"), (1, "conflict"), (1, "renamed")}
    assert len(wins) == 7                                                                 # mesmo com x = 50%: cor única e andar certo


def test_the_order_of_packing_is_stable_by_path_whatever_order_the_changes_arrive():
    spec = [(f"src/f{n:03d}.py", "modified", 1 + n % 7) for n in range(60)]
    shuffled = spec[:]
    random.Random(7).shuffle(shuffled)
    assert lit(FLOORS, spec) == lit(FLOORS, shuffled)                                    # a fachada não "pisca" a cada leitura


def test_a_bigger_x_makes_fewer_windows():
    spec = [(f"src/f{n:03d}.py", "modified", 1) for n in range(100)]
    assert len(lit(FLOORS, spec, 10)) < len(lit(FLOORS, spec, 5)) < len(lit(FLOORS, spec, 2))


# --- em que andar cai cada alteração ---------------------------------------------------------------------------

def test_root_files_light_the_ground_floor_and_each_folder_its_own_floor():
    wins = lit(FLOORS, [("pyproject.toml", "modified", 3), ("src/a.py", "modified", 3), ("tests/t.py", "modified", 3)], 50)
    assert sorted(floor_of(w) for w in wins) == [0, 1, 2]


def test_a_folder_that_is_not_a_floor_lights_the_rest_floor_and_without_one_the_ground_floor():
    assert [floor_of(w) for w in lit(FLOORS, [("docs/guia.md", "modified", 2)])] == [3]            # "demais pastas"
    no_rest = FLOORS[:3]
    assert [floor_of(w, no_rest) for w in lit(no_rest, [("docs/guia.md", "modified", 2)])] == [0]   # sem ela, o térreo
    no_ground = FLOORS[1:]
    assert [floor_of(w, no_ground) for w in lit(no_ground, [("raiz.toml", "modified", 2)])] == [2]  # raiz sem térreo: "demais pastas"


def test_without_floors_or_without_changes_there_is_nothing_to_light():
    assert lit([], [("a.py", "modified", 1)]) == [] and lit(FLOORS, []) == []


# --- onde no andar -----------------------------------------------------------------------------------------------

def test_the_windows_of_a_floor_spread_over_the_faces_and_rows_instead_of_piling_in_a_corner():
    spec = [(f"src/f{n}.py", "modified", 10) for n in range(8)]
    wins = [w for w in lit(FLOORS, spec, 1) if floor_of(w) == 1]
    assert len(wins) == 8
    assert len({w["face"] for w in wins}) == 4 and len({w["level"] for w in wins}) >= 4
    assert len({(w["level"], w["face"], w["col"]) for w in wins}) == 8                  # nenhuma janela em cima de outra
    assert all(1 <= w["level"] < 6 and 0 <= w["face"] < rules.FACADE_FACES and 0 <= w["col"] < rules.FACADE_COLS for w in wins)


def test_a_small_floor_with_too_many_packets_merges_them_more_until_they_fit_without_splitting_any_change():
    spec = [(f"src/f{n:03d}.py", "modified", 1) for n in range(400)]
    tiny = [{"kind": "folder", "name": "src", "levels": 1, "loc": 400}]                 # 1 nível: 32 janelas no andar
    wins = lit(tiny, spec, 1)                                                           # x = 1% pediria 100 janelas
    assert len(wins) <= rules.FACADE_FACES * rules.FACADE_COLS
    assert sum(w["changes"] for w in wins) == 400                                       # e nenhuma alteração se perdeu
    assert len({(w["level"], w["face"], w["col"]) for w in wins}) == len(wins)


# --- o protocolo e o mundo ---------------------------------------------------------------------------------------

def changes_event(items, *, realm="the-orb", key="1", ts="2026-10-14T10:00:00Z", **extra):
    return make_event(id=f"{realm}:changes:{key}", ts=ts, provider=None, source="probe/changes", realm=realm, alter_ego=None,
                      agent=None, seq=1, kind="realm/changes", body={}, signal={"type": "realm.changes", "changes": items, **extra})


def metrics_event(loc=7_200, *, root=100, folders=None, ts="2026-10-14T09:00:00Z"):
    folders = folders if folders is not None else {"src": 5_000, "tests": 2_000}
    return make_event(id=f"the-orb:lines:{ts}", ts=ts, provider=None, source="probe/lines", realm="the-orb", alter_ego=None, agent=None,
                      seq=1, kind="realm/lines", body={}, signal={"type": "realm.metrics", "loc": loc, "root": root, "folders": folders})


def item(path="src/a.py", kind="modified", lines=3):
    return {"path": path, "type": kind, "lines": lines}


def test_the_changes_event_is_a_valid_realm_event_with_a_closed_list_of_types():
    event = changes_event([item(), item("novo.txt", "untracked", 1)], more=0)
    assert event["alter_ego"] is None and validate(event) is None
    assert validate(changes_event([])) is None                                          # limpo é um dado válido
    assert validate({**event, "alter_ego": "claude:s1"}) is not None


def test_a_malformed_changes_event_is_rejected_at_the_border():
    bad = [[item(kind="mexido")], [item(path="")], [item(path="/etc/passwd")], [item(path="../fora.py")], [item(path="a/../b.py")],
           [item(lines=-1)], [item(lines=1.5)], [item(lines=True)], [item(lines="3")], ["texto"], [{"path": "a.py"}],
           [item(path="x" * 1100)], [item(path="a\\b.py")]]
    for items in bad:
        assert validate(changes_event(items)) is not None, items
    assert validate(changes_event([item()], more=-1)) is not None
    assert validate(changes_event("nao e lista")) is not None
    assert validate(changes_event([item(path=f"p{n}.py") for n in range(5001)])) is not None


def world_with(metrics=True, percent=5.0):
    world = World(window_percent=percent)
    if metrics:
        world.apply(metrics_event())
    return world


def realm_of(world, realm="the-orb"):
    return next(r for r in world.snapshot(T0)["realms"] if r["id"] == realm)


def test_the_world_lights_windows_from_the_changes_and_the_floors_it_calculated():
    world = world_with()
    world.apply(changes_event([item("src/a.py", "modified", 10), item("src/b.py", "added", 10), item("tests/t.py", "deleted", 4)]))
    built = realm_of(world)["facade"]
    assert {w["type"] for w in built["windows"]} == {"modified", "added", "deleted"} and built["changes"] == 3
    floors = realm_of(world)["metrics"]["floors"]
    assert [f["name"] for f in floors] == [None, "src", "tests", None]


def test_without_a_changes_reading_or_without_floors_the_facade_has_no_data_instead_of_dark_windows():
    assert realm_of(world_with())["facade"] is None                                      # o Probe ainda não leu o git
    no_floors = World()
    no_floors.apply(make_event(id="x", ts="2026-10-14T09:00:00Z", provider=None, source="p", realm="the-orb", alter_ego=None, agent=None,
                               seq=1, kind="k", body={}, signal={"type": "realm.metrics", "loc": 500}))
    no_floors.apply(changes_event([item()]))
    assert realm_of(no_floors)["facade"] is None                                         # sem andares não dá para dizer onde acende


def test_a_clean_repository_is_a_facade_with_every_window_dark_and_that_is_data():
    world = world_with()
    world.apply(changes_event([]))
    assert realm_of(world)["facade"] == {"windows": [], "changes": 0, "more": 0}


def test_the_newer_reading_replaces_the_older_one_and_a_late_one_does_not_go_back_in_time():
    world = world_with()
    world.apply(changes_event([item("src/a.py")], key="1", ts="2026-10-14T10:00:00Z"))
    world.apply(changes_event([item("src/a.py"), item("src/b.py")], key="2", ts="2026-10-14T10:01:00Z"))
    assert realm_of(world)["facade"]["changes"] == 2
    world.apply(changes_event([], key="old", ts="2026-10-14T09:30:00Z"))                 # chegou atrasada
    assert realm_of(world)["facade"]["changes"] == 2


def test_changing_x_changes_the_windows_at_once_and_the_facade_is_the_same_for_the_same_input():
    world = world_with()
    world.apply(changes_event([item(f"src/f{n:03d}.py", "modified", 1) for n in range(100)]))
    first = realm_of(world)["facade"]
    assert realm_of(world)["facade"] == first and len(first["windows"]) == 20
    world.set_window_percent(10)
    assert len(realm_of(world)["facade"]["windows"]) == 10


def test_the_count_of_changes_cut_by_the_probe_is_kept():
    world = world_with()
    world.apply(changes_event([item()], more=120))
    assert realm_of(world)["facade"]["more"] == 120


def test_x_has_one_default_and_its_limits_in_the_table_of_settings():
    from orb.registry import preferences
    setting = next(s for s in preferences.SETTINGS if s.key == "window_percent")
    assert (setting.default, setting.minimum, setting.maximum) == (5, 1, 50)
    assert World().window_percent == setting.default == rules.WINDOW_PERCENT
    with pytest.raises(ValueError):
        preferences.Preferences().updated(window_percent=0)
