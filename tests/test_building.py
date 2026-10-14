"""A altura e os andares do prédio (R19, R20, R41, D-052; VISUAL.md §8): métricas -> níveis e andares, no mundo."""
import pytest

from orb.core import building, rules

LEVEL_CASES = [
    (0, 1), (999, 1),                      # Casa: 1 nível
    (1_000, 2), (2_236, 2), (4_999, 3),    # Sobrado: 2 a 3
    (5_000, 5), (19_999, 8),               # Prédio: 5 a 8
    (20_000, 11), (99_999, 16),            # Edifício: 11 a 16
    (100_000, 20), (499_999, 28),          # Torre: 20 a 28
    (500_000, 34), (1_000_000, 38),        # Arranha-céu: 34 e cresce devagar (4 níveis a cada vez que dobra)
    (10_000_000, 48), (10**12, 48),        # ...e para num teto, para um monorepo gigante não sair da tela
]


@pytest.mark.parametrize(("loc", "levels"), LEVEL_CASES)
def test_the_height_in_levels_comes_from_the_lines(loc, levels):
    assert building.levels(loc) == levels


def test_each_class_keeps_its_band_of_levels_and_the_bands_never_touch():
    bounds = []
    for name, lower in rules.BUILDING_CLASSES:
        low, high = rules.BUILDING_LEVELS[name]
        assert building.levels(lower) == low
        bounds.append((low, high))
    for (_, high), (low, _) in zip(bounds[1:], bounds[2:], strict=False):
        assert low - high >= 2                       # o salto entre classes: 3→5, 8→11, 16→20, 28→34 (a Casa, de 1 nível, passa a 2 no Sobrado)


def test_the_height_only_grows_with_the_lines_and_never_depends_on_other_realms():
    previous = 0
    for loc in range(0, 2_000_000, 997):
        now = building.levels(loc)
        assert now >= previous
        previous = now


def test_inside_a_class_the_growth_is_logarithmic():
    assert building.levels(21_000) < building.levels(90_000)                       # 90 mil é mais alto que 21 mil...
    assert rules.building_class(21_000) == rules.building_class(90_000) == "Edifício"   # ...e os dois seguem Edifício
    assert building.levels(60_000) - building.levels(20_000) >= 3                   # o meio da faixa já passou da metade da altura


def test_trim_bands_grow_by_one_per_class_and_only_the_skyscraper_has_an_antenna():
    assert [rules.BUILDING_TRIM[name] for name, _ in rules.BUILDING_CLASSES] == [0, 1, 2, 3, 4, 5]
    assert [name for name in rules.BUILDING_TRIM if name in rules.ANTENNA_CLASSES] == ["Arranha-céu"]


# --- andares ------------------------------------------------------------------------------------------------

def total(floors, key):
    return sum(f[key] for f in floors)


def test_the_ground_floor_holds_the_root_files_and_each_folder_is_a_floor_in_alphabetical_order():
    floors = building.floors(levels=12, loc=10_000, root=1_000, folders={"src": 6_000, "docs": 1_000, "tests": 2_000})
    assert [(f["kind"], f["name"]) for f in floors] == [("ground", None), ("folder", "docs"), ("folder", "src"), ("folder", "tests")]
    assert total(floors, "loc") == 10_000 and total(floors, "levels") == 12


def test_every_floor_has_at_least_one_level_and_the_height_follows_the_share_of_lines():
    floors = building.floors(levels=12, loc=10_000, root=1_000, folders={"src": 6_000, "docs": 1_000, "tests": 2_000})
    by_name = {f["name"]: f["levels"] for f in floors}
    assert min(f["levels"] for f in floors) >= 1
    assert by_name["src"] > by_name["tests"] >= by_name["docs"] >= 1                # proporcional às linhas
    assert total(floors, "levels") == 12                                            # a soma dos andares é a altura do prédio


def test_a_building_with_more_folders_than_levels_joins_the_smallest_ones_in_the_rest_floor():
    folders = {f"p{n}": 100 + n for n in range(10)}                                 # 10 pastas
    loc = sum(folders.values())
    floors = building.floors(levels=5, loc=loc, root=0, folders=folders)
    assert len(floors) == 5 and floors[-1]["kind"] == "rest"                        # "demais pastas" no topo
    kept = [f["name"] for f in floors[:-1]]
    assert kept == sorted(kept) and set(kept) == {"p9", "p8", "p7", "p6"}           # ficam as maiores
    assert floors[-1]["loc"] == sum(100 + n for n in range(6)) and total(floors, "levels") == 5


def test_the_ground_floor_is_never_the_one_that_gets_joined():
    floors = building.floors(levels=3, loc=1_020, root=10, folders={"a": 500, "b": 400, "c": 110})
    assert floors[0]["kind"] == "ground" and floors[0]["loc"] == 10
    assert [f["kind"] for f in floors] == ["ground", "folder", "rest"] and total(floors, "loc") == 1_020


def test_lines_the_probe_did_not_list_go_to_the_rest_floor():
    floors = building.floors(levels=10, loc=1_000, root=100, folders={"src": 700})             # 200 linhas em pastas que não vieram
    assert [f["kind"] for f in floors] == ["ground", "folder", "rest"] and floors[-1]["loc"] == 200


def test_a_one_level_house_is_one_floor():
    assert building.floors(levels=1, loc=500, root=500, folders={}) == [{"kind": "ground", "name": None, "levels": 1, "loc": 500}]
    one = building.floors(levels=1, loc=500, root=100, folders={"src": 400})
    assert one == [{"kind": "rest", "name": None, "levels": 1, "loc": 500}]


def test_folders_without_lines_are_not_floors_and_a_project_without_lines_has_none():
    floors = building.floors(levels=5, loc=300, root=0, folders={"src": 300, "vazia": 0})
    assert [f["name"] for f in floors] == ["src"]
    assert building.floors(levels=1, loc=0, root=0, folders={}) == []


def test_the_same_numbers_always_give_the_same_floors_in_any_order():
    a = building.floors(levels=9, loc=900, root=0, folders={"x": 300, "y": 300, "z": 300})
    b = building.floors(levels=9, loc=900, root=0, folders=dict(reversed(list({"x": 300, "y": 300, "z": 300}.items()))))
    assert a == b and [f["levels"] for f in a] == [3, 3, 3]
    tie = building.floors(levels=2, loc=300, root=0, folders={"b": 100, "a": 100, "c": 100})     # empate: o nome decide quem se junta
    assert [(f["kind"], f["name"]) for f in tie] == [("folder", "a"), ("rest", None)]
