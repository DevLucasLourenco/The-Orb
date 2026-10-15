"""Papel, atributos por área e árvore da Team (ticket 12, R40, R57, D-069, D-096, D-116): ponto de teste = o mundo.
Eventos de atividade sintéticos entram; o snapshot do Alter Ego diz o papel, a parcela do trabalho em cada área e a Team em árvore."""
from itertools import count

import pytest

from orb.core import World, profile, rules
from orb.protocol import make_event

_n = count(1)


def act(activity, *, ego="claude:s1", agent=None, key=None):
    n = next(_n)
    return make_event(id=f"{ego}:{key or n}", ts=f"2026-10-07T10:{n // 60 % 60:02d}:{n % 60:02d}Z", provider="claude", source="claude/transcript",
                      realm="the-orb", alter_ego=ego, agent=agent, seq=n, kind="x", body={},
                      signal={"type": "activity", "activity": activity})


def started(agent, *, parent=None, kind="Explore", ego="claude:s1"):
    n = next(_n)
    signal = {"type": "subagent.started", "kind": kind}
    if parent is not None:
        signal["parent"] = parent
    return make_event(id=f"{ego}:{agent}:{n}", ts=f"2026-10-07T10:00:{n % 60:02d}Z", provider="claude", source="claude/transcript",
                      realm="the-orb", alter_ego=ego, agent=agent, seq=n, kind="x", body={}, signal=signal)


def ego_of(world, ego="claude:s1"):
    return next(e for r in world.snapshot()["realms"] for e in r["alter_egos"] if e["id"] == ego)


def run(*activities, ego="claude:s1"):
    world = World()
    for activity in activities:
        world.apply(act(activity, ego=ego))
    return world


def shares(snapshot):
    return {a["area"]: (a["count"], a["share"]) for a in snapshot["attributes"]["areas"]}


# --- o papel e os atributos -------------------------------------------------------------------------

@pytest.mark.parametrize("activity, role", [
    ("CODING", "desenvolvedor"), ("EXECUTING", "desenvolvedor"), ("TESTING", "testador"),
    ("READING", "pesquisador"), ("RESEARCHING", "pesquisador"), ("REVIEWING", "revisor"),
])
def test_role_comes_from_the_area_of_what_the_session_did_most(activity, role):
    assert ego_of(run(activity, activity))["role"] == role


def test_the_role_follows_the_biggest_count_and_changes_with_it():
    world = run("REVIEWING", "REVIEWING", "CODING")
    assert ego_of(world)["role"] == "revisor"
    for _ in range(3):
        world.apply(act("CODING"))
    assert ego_of(world)["role"] == "desenvolvedor"                      # 4 de código contra 2 de revisão


def test_attributes_are_the_share_of_the_work_in_each_area_in_a_fixed_order():
    snap = ego_of(run("REVIEWING", "READING", "READING", "CODING", "EXECUTING", "TESTING", "TESTING", "READING"))
    attributes = snap["attributes"]
    assert attributes["total"] == 8
    assert [a["area"] for a in attributes["areas"]] == list(rules.ATTRIBUTE_AREAS)
    assert shares(snap) == {"Development Center": (2, 0.25), "Testing Lab": (2, 0.25), "Research Center": (3, 0.375), "Code Review": (1, 0.125)}
    assert sum(share for _, share in shares(snap).values()) == pytest.approx(1)
    assert snap["role"] == "pesquisador"


def test_a_tie_has_no_role_but_the_attributes_still_show():
    snap = ego_of(run("REVIEWING", "CODING"))
    assert snap["role"] is None                                           # ninguém lidera: não se afirma um papel (R12)
    assert shares(snap)["Code Review"] == (1, 0.5)


def test_a_session_that_did_nothing_countable_has_neither_role_nor_attributes():
    world = World()
    world.apply(make_event(id="claude:s1:start", ts="2026-10-07T10:00:00Z", provider="claude", source="claude/transcript", realm="the-orb",
                           alter_ego="claude:s1", agent=None, seq=1, kind="x", body={}, signal={"type": "session.started"}))
    snap = ego_of(world)
    assert snap["role"] is None and snap["attributes"] is None


def test_only_the_leaders_own_activities_in_an_area_count():
    world = World()
    world.apply(started("a1"))
    for activity in ("THINKING", "DELEGATING", "BLOCKED", "COMPLETED"):      # sem área: não entram na contagem
        world.apply(act(activity))
    for _ in range(5):
        world.apply(act("REVIEWING", agent="a1"))                          # a Team não conta para o líder
    snap = ego_of(world)
    assert snap["role"] is None and snap["attributes"] is None
    world.apply(act("CODING"))
    assert ego_of(world)["attributes"]["total"] == 1


def test_each_session_has_its_own_count():
    world = World()
    world.apply(act("CODING", ego="claude:s1"))
    world.apply(act("REVIEWING", ego="claude:s2"))
    assert ego_of(world, "claude:s1")["role"] == "desenvolvedor"
    assert ego_of(world, "claude:s2")["role"] == "revisor"


def test_reading_the_same_event_again_does_not_count_twice():
    world = World()
    event = act("CODING", key="same")
    assert world.apply(event) is True
    assert world.apply(event) is False
    assert ego_of(world)["attributes"]["total"] == 1


def test_the_tables_cover_the_areas_of_the_environment_that_do_work():
    assert set(rules.ROLE_BY_AREA) == set(rules.ATTRIBUTE_AREAS)
    assert set(rules.ATTRIBUTE_AREAS) <= {a for a in rules.AREA_BY_STATE.values() if a}
    assert profile.attributes({}) is None and profile.role({}) is None
    assert profile.role({"Code Review": 2, "Testing Lab": 1}) == "revisor"


# --- a árvore da Team -----------------------------------------------------------------------------

def team_of(world):
    return [(s["id"], s["depth"]) for s in ego_of(world)["team"]]


def test_the_team_is_a_tree_of_who_created_whom():
    world = World()
    for event in (started("a"), started("b", parent="a"), started("c"), started("d", parent="b"), started("e", parent="a")):
        world.apply(event)
    assert team_of(world) == [("a", 0), ("b", 1), ("d", 2), ("e", 1), ("c", 0)]       # o pai vem antes dos filhos; irmãos na ordem em que nasceram


def test_a_child_that_starts_before_its_parent_is_still_listed_under_it():
    world = World()
    world.apply(started("b", parent="a"))
    world.apply(started("a"))
    assert team_of(world) == [("a", 0), ("b", 1)]


def test_an_unknown_or_self_parent_hangs_from_the_leader():
    world = World()
    world.apply(started("a", parent="nobody"))
    world.apply(started("b", parent="b"))
    assert team_of(world) == [("a", 0), ("b", 0)]


def test_a_loop_of_parents_does_not_hang_and_keeps_everyone_listed():
    world = World()
    world.apply(started("a", parent="b"))
    world.apply(started("b", parent="a"))
    world.apply(started("c", parent="b"))
    assert sorted(i for i, _ in team_of(world)) == ["a", "b", "c"]


def test_the_team_keeps_its_type_state_and_parent_for_the_overview():
    world = World()
    world.apply(started("a", kind="Explore"))
    world.apply(started("b", parent="a", kind="Plan"))
    world.apply(act("READING", agent="b"))
    team = {s["id"]: s for s in ego_of(world)["team"]}
    assert (team["b"]["kind"], team["b"]["state"], team["b"]["parent"], team["b"]["depth"]) == ("Plan", "READING", "a", 1)
    assert team["a"]["parent"] is None

