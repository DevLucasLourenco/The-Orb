"""A cidade retangular (R32, D-046, D-047, D-099): lista de realms -> traçado; estável ao incluir e esconder."""
from datetime import UTC, datetime

import pytest

from orb.core import World, city, rules

NOW = datetime(2026, 10, 14, 10, 0, 0, tzinfo=UTC)
IDS = ["alpha", "amora", "beta", "gamma", "the-orb", "trisafe", "trisafe-enhanced", "zeta", "7zip"]


def places(ids):
    return city.plan(ids)["places"]


def district(plan, letter):
    return next(d for d in plan["districts"] if d["letter"] == letter)


# --- bairros por letra, em ordem de leitura -----------------------------------------------------------------

def test_districts_exist_only_for_letters_with_realms_and_numbers_come_first_in_the_hash_district():
    plan = city.plan(IDS)
    assert [d["letter"] for d in plan["districts"]] == ["#", "A", "B", "G", "T", "Z"]     # sem bairro vazio; "#" no começo
    assert plan["places"]["7zip"]["district"] == "#"
    assert plan["places"]["the-orb"]["district"] == "T"


def test_the_letter_of_a_district_comes_from_the_first_character_and_symbols_go_to_hash():
    assert [city.district_letter(i) for i in ("alpha", "Beta", "9x", "-x", "_y", "ágil")] == ["A", "B", "#", "#", "#", "#"]


def test_lots_follow_the_alphabetical_order_inside_the_district():
    plan = city.plan(IDS)
    ordered = sorted((i for i in IDS if i.startswith("t")), key=lambda i: plan["places"][i]["lot"])
    assert ordered == ["the-orb", "trisafe", "trisafe-enhanced"]
    assert [plan["places"][i]["lot"] for i in ordered] == [1, 2, 3]


def test_districts_read_like_a_text_left_to_right_and_then_down():
    plan = city.plan([f"{chr(c)}realm" for c in range(ord("a"), ord("z") + 1)])
    rows: dict[float, list[str]] = {}
    for d in plan["districts"]:
        rows.setdefault(d["z"], []).append(d["letter"])
    flat = [letter for z in sorted(rows) for letter in sorted(rows[z], key=lambda lt: next(d["x"] for d in plan["districts"] if d["letter"] == lt))]
    assert flat == [chr(c).upper() for c in range(ord("a"), ord("z") + 1)]          # a ordem alfabética é a ordem de leitura
    assert len(rows) > 1                                                             # e quebra em fileiras


def test_the_city_is_wider_than_tall_close_to_16_by_9():
    plan = city.plan([f"{chr(c)}realm{n}" for c in range(ord("a"), ord("z") + 1) for n in range(3)])
    assert plan["width"] > plan["depth"]
    assert 1.2 < plan["width"] / plan["depth"] < 2.6


def test_the_rows_are_chosen_to_get_as_close_to_16_by_9_as_the_districts_allow():
    # Dez bairros de uma a quatro casas: com a divisão em três fileiras a cidade ficava quase quadrada (1,13).
    sizes = {"a": 2, "b": 4, "c": 4, "d": 1, "h": 1, "m": 1, "n": 2, "r": 1, "s": 4, "t": 4}
    plan = city.plan([f"{letter}{n}" for letter, count in sizes.items() for n in range(count)])
    assert 1.4 < plan["width"] / plan["depth"] < 2.4          # a opção de 3 fileiras dava 1,13; a de 2 dá 2,25, mais perto de 1,78


def test_an_empty_city_has_nothing():
    assert city.plan([]) == {"width": 0, "depth": 0, "pad": rules.CITY_PAD, "districts": [], "places": {}}


# --- o "aleatório" rastreável --------------------------------------------------------------------------------

def test_the_same_realm_always_gets_the_same_spot_and_turn():
    assert places(IDS) == places(list(reversed(IDS)))                 # a ordem em que chegam não importa
    assert city.plan(IDS) == city.plan(IDS)


def test_the_offset_and_the_turn_come_from_the_name_and_stay_inside_their_limits():
    spots = places(IDS)
    for realm_id, spot in spots.items():
        d = district(city.plan(IDS), spot["district"])
        col, row = (spot["lot"] - 1) % d["cols"], (spot["lot"] - 1) // d["cols"]
        cx = d["x"] + rules.CITY_PAD + (col + 0.5) * rules.CITY_LOT
        cz = d["z"] + rules.CITY_PAD + (row + 0.5) * rules.CITY_LOT
        assert abs(spot["x"] - cx) <= rules.CITY_JITTER + 0.01, realm_id
        assert abs(spot["z"] - cz) <= rules.CITY_JITTER + 0.01, realm_id
        assert abs(spot["turn"]) <= rules.CITY_TURN + 0.001, realm_id
    assert len({(s["x"], s["z"]) for s in spots.values()}) == len(IDS)
    assert len({s["turn"] for s in spots.values()}) > 1               # nem todos giram igual: o ar "orgânico"


def test_the_seed_does_not_depend_on_the_process(monkeypatch):
    # `hash()` do Python muda a cada execução; a semente aqui é um resumo fixo do nome.
    assert city.seed("the-orb") == city.seed("the-orb") != city.seed("the-orc")
    assert city.seed("the-orb") == 6258250645090972876               # valor fixo: o mesmo realm cai no mesmo lugar em toda máquina


def test_no_two_buildings_overlap_at_the_extreme_offsets():
    # O prédio mais largo (30 de lado, o pódio da Torre e do Arranha-céu) com o maior deslocamento e giro ainda cabe no lote de 46.
    half = rules.CITY_MAX_BASE / 2 + rules.CITY_JITTER + rules.CITY_MAX_BASE / 2 * rules.CITY_TURN
    assert 2 * half < rules.CITY_LOT


# --- estabilidade ao incluir e esconder ---------------------------------------------------------------------

def test_a_new_realm_only_reorganizes_its_own_district():
    before, after = city.plan(IDS), city.plan(IDS + ["tango"])
    for realm_id in IDS:
        if before["places"][realm_id]["district"] == "T":
            continue
        a, b = before["places"][realm_id], after["places"][realm_id]
        assert (a["district"], a["lot"], a["turn"]) == (b["district"], b["lot"], b["turn"]), realm_id     # o lote e o giro não mudam
    assert after["places"]["tango"]["district"] == "T"
    # os vizinhos de bairro: "tango" entra depois de "the-orb"? não: "ta" < "th", então ele é o 1º lote
    assert after["places"]["tango"]["lot"] == 1 and after["places"]["the-orb"]["lot"] == 2


def test_a_new_realm_in_another_district_never_moves_a_building_inside_its_district():
    before, after = city.plan(IDS), city.plan(IDS + ["tango"])
    for realm_id in IDS:
        a, b = before["places"][realm_id], after["places"][realm_id]
        da, db = district(before, a["district"]), district(after, b["district"])
        if a["district"] == "T":
            continue
        # a posição dentro do bairro é a mesma, mesmo que o bairro todo tenha se deslocado
        assert (round(a["x"] - da["x"], 2), round(a["z"] - da["z"], 2)) == (round(b["x"] - db["x"], 2), round(b["z"] - db["z"], 2)), realm_id


def test_a_new_letter_adds_a_district_and_leaves_the_size_of_the_others():
    before, after = city.plan(IDS), city.plan(IDS + ["delta"])
    assert [d["letter"] for d in after["districts"]] == ["#", "A", "B", "D", "G", "T", "Z"]
    for letter in ("#", "A", "B", "G", "T", "Z"):
        da, db = district(before, letter), district(after, letter)
        assert (da["w"], da["d"]) == (db["w"], db["d"])                    # o tamanho de cada bairro é o mesmo


def test_a_district_grows_to_hold_its_lots():
    one = district(city.plan(["alpha"]), "A")
    many = district(city.plan([f"a{n}" for n in range(10)]), "A")
    assert one["cols"] * one["rows"] >= 1 and many["cols"] * many["rows"] >= 10
    assert many["w"] > one["w"] or many["d"] > one["d"]


# --- no mundo: o realm escondido deixa o lote vago -----------------------------------------------------------

def world_of(ids):
    world = World()
    for realm_id in ids:
        world.add_realm(realm_id)
    return world


def test_the_snapshot_carries_the_city_and_the_place_of_each_realm():
    snap = world_of(IDS).snapshot(NOW)
    assert snap["city"]["width"] > 0 and {d["letter"] for d in snap["city"]["districts"]} == {"#", "A", "B", "G", "T", "Z"}
    assert all(realm["place"] == snap["city"]["places"][realm["id"]] for realm in snap["realms"])
    assert snap["city"]["places"]["the-orb"]["lot"] == 1


def test_a_hidden_realm_leaves_its_lot_vacant_and_the_neighbours_do_not_move():
    world = world_of(IDS)
    before = {r["id"]: r["place"] for r in world.snapshot(NOW)["realms"]}
    world.set_hidden({"trisafe"})
    snap = world.snapshot(NOW)
    after = {r["id"]: r["place"] for r in snap["realms"]}
    assert "trisafe" not in after                                              # o prédio some...
    assert {k: v for k, v in before.items() if k != "trisafe"} == after        # ...e ninguém mais anda
    assert snap["city"] == world_of(IDS).snapshot(NOW)["city"]                 # o bairro e o lote vago continuam no traçado
    world.set_hidden(set())
    assert {r["id"]: r["place"] for r in world.snapshot(NOW)["realms"]} == before


def test_a_realm_detected_later_gets_its_place_without_moving_other_districts():
    world = world_of(IDS)
    before = {r["id"]: r["place"] for r in world.snapshot(NOW)["realms"]}
    world.add_realm("alvorada")
    after = {r["id"]: r["place"] for r in world.snapshot(NOW)["realms"]}
    assert after["alvorada"]["district"] == "A"
    assert after["the-orb"]["district"] == before["the-orb"]["district"]


@pytest.mark.parametrize("ids", [IDS, ["solo"], [f"r{n}" for n in range(40)]])
def test_the_places_stay_inside_the_city_rectangle(ids):
    plan = city.plan(ids)
    for spot in plan["places"].values():
        assert abs(spot["x"]) <= plan["width"] / 2 and abs(spot["z"]) <= plan["depth"] / 2
