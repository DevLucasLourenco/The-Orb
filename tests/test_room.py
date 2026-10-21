"""A sala cheia e os estados do personagem (ticket 13, R33, R51, R52, D-057, D-094, D-095): ponto de teste = o mundo.
Eventos sintéticos entram; o snapshot diz quem está em cada lugar (até 8 por lugar e o "+N"), o estado de cada líder e quando o subagente terminou."""
from datetime import UTC, datetime, timedelta
from itertools import chain, count

import pytest

from orb.core import World, rules
from orb.protocol import make_event

_n = count(1)
T0 = datetime(2026, 10, 7, 10, 0, 0, tzinfo=UTC)
DEV, TEST, RESEARCH, REVIEW, BOARD = "Development Center", "Testing Lab", "Research Center", "Code Review", "Task Board"


def ev(minutes, signal, *, ego="claude:s1", agent=None):
    n = next(_n)
    ts = (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")
    return make_event(id=f"{ego}:{n}", ts=ts, provider="claude", source="claude/transcript", realm="the-orb", alter_ego=ego, agent=agent,
                      seq=n, kind="x", body={}, signal=signal)


def act(minutes, activity, **kw):
    return ev(minutes, {"type": "activity", "activity": activity}, **kw)


def world_with(*events):
    world = World()
    for event in events:
        assert world.apply(event) is True
    return world


def room(world, minutes=1):
    return world.snapshot(T0 + timedelta(minutes=minutes))["realms"][0]["room"]


def ego_of(world, ego="claude:s1", minutes=1):
    return next(e for e in world.snapshot(T0 + timedelta(minutes=minutes))["realms"][0]["alter_egos"] if e["id"] == ego)


# --- os lugares da sala ------------------------------------------------------------------------------------------------

def test_the_room_always_lists_the_five_areas_the_lobby_and_the_dormitory_even_when_empty():
    snap = World()
    snap.add_realm("the-orb")
    realm = snap.snapshot(T0)["realms"][0]
    assert list(realm["room"]) == [DEV, TEST, RESEARCH, REVIEW, BOARD, "__lobby", "__dorm"]
    assert all(place == {"shown": [], "more": 0} for place in realm["room"].values())


@pytest.mark.parametrize("activity, place", [
    ("CODING", DEV), ("EXECUTING", DEV), ("TESTING", TEST), ("READING", RESEARCH), ("RESEARCHING", RESEARCH), ("REVIEWING", REVIEW),
    ("COMPLETED", BOARD), ("THINKING", "__lobby"), ("DELEGATING", "__lobby"), ("BLOCKED", "__lobby"),
])
def test_each_leader_stands_in_the_place_of_what_it_is_doing(activity, place):
    world = world_with(act(0, activity))
    assert room(world)[place]["shown"] == ["claude:s1"]
    assert sum(len(p["shown"]) for p in room(world).values()) == 1


def test_who_waits_for_the_lucas_and_who_is_idle_stand_in_the_lobby():
    world = world_with(ev(0, {"type": "waiting", "request": "r", "action": "x"}), act(0, "CODING", ego="claude:s2"),
                       ev(1, {"type": "idle"}, ego="claude:s2"))
    assert sorted(room(world)["__lobby"]["shown"]) == ["claude:s1", "claude:s2"]


def test_a_sleeping_or_ended_session_goes_to_the_dormitory_and_the_team_of_an_ended_session_does_not_stand_anywhere():
    world = world_with(act(0, "CODING"), ev(0, {"type": "subagent.started", "kind": "x"}, agent="a1"), act(0, "READING", agent="a1"),
                       act(0, "CODING", ego="claude:s2"), ev(1, {"type": "subagent.started", "kind": "x"}, ego="claude:s2", agent="b1"),
                       act(1, "READING", ego="claude:s2", agent="b1"), ev(2, {"type": "session.ended"}, ego="claude:s2"))
    placed = room(world, 2)
    assert placed["__dorm"]["shown"] == ["claude:s2"]                        # encerrada: dormitório
    assert "claude:s2/b1" not in list(chain.from_iterable(p["shown"] for p in placed.values()))      # a Team de uma sessão encerrada fica de fora
    assert "claude:s1" in placed[DEV]["shown"] or "claude:s1" in placed[RESEARCH]["shown"] or "claude:s1" in placed["__lobby"]["shown"]


def test_a_session_that_stopped_for_more_than_15_minutes_sleeps_in_the_dormitory():
    world = world_with(act(0, "CODING"), ev(0, {"type": "idle"}))
    assert room(world, 5)["__lobby"]["shown"] == ["claude:s1"]               # parou agora: ainda no lobby
    assert room(world, 20)["__dorm"]["shown"] == ["claude:s1"]               # 20 min parada: dorme (R31)


def test_an_active_subagent_is_one_more_character_in_its_area_and_a_finished_one_is_not():
    world = world_with(act(0, "CODING"), ev(0, {"type": "subagent.started", "kind": "Explore"}, agent="a1"), act(0, "READING", agent="a1"),
                       ev(0, {"type": "subagent.started", "kind": "Plan"}, agent="a2"), ev(1, {"type": "subagent.ended", "outcome": "completed"}, agent="a2"))
    placed = room(world)
    assert placed[RESEARCH]["shown"] == ["claude:s1/a1"] and placed[DEV]["shown"] == ["claude:s1"]
    assert "claude:s1/a2" not in list(chain.from_iterable(p["shown"] for p in placed.values()))


def test_a_session_out_of_the_room_stands_nowhere():
    world = world_with(act(0, "CODING"))
    far = world.snapshot(T0 + timedelta(days=30))["realms"][0]
    assert sum(len(p["shown"]) for p in far["room"].values()) == 0 and far["alter_egos"][0]["in_room"] is False


# --- a sala cheia: até 8 por lugar e o "+N" -----------------------------------------------------------------------------------

@pytest.mark.parametrize("total, shown, more", [(1, 1, 0), (8, 8, 0), (9, 8, 1), (11, 8, 3), (30, 8, 22)])
def test_a_place_shows_at_most_8_characters_and_counts_the_rest(total, shown, more):
    assert rules.PLACE_CAP == 8
    world = world_with(*[act(0, "CODING", ego=f"claude:s{i:02d}") for i in range(total)])
    place = room(world)[DEV]
    assert (len(place["shown"]), place["more"]) == (shown, more)
    assert len(set(place["shown"])) == len(place["shown"])


def test_the_cap_applies_to_the_lobby_and_to_the_dormitory_too():
    world = world_with(*[e for i in range(10) for e in (act(0, "THINKING", ego=f"claude:s{i:02d}"), ev(0, {"type": "idle"}, ego=f"claude:s{i:02d}"))])
    assert room(world)["__lobby"]["more"] == 2
    asleep = room(world, 60)
    assert asleep["__dorm"]["more"] == 2 and len(asleep["__dorm"]["shown"]) == 8


def test_when_there_is_no_room_the_ones_waiting_for_the_lucas_are_kept_then_leaders_then_the_most_recent():
    events = [act(i, "THINKING", ego=f"claude:s{i:02d}") for i in range(12)]            # 12 no lobby, o s00 é o mais antigo
    events.append(ev(11.5, {"type": "waiting", "request": "r", "action": "x"}, ego="claude:s00"))        # o mais antigo espera o Lucas
    world = world_with(*events)
    shown = room(world, 12)["__lobby"]["shown"]
    assert "claude:s00" in shown and "claude:s01" not in shown                           # quem espera fica; dos outros, os mais antigos saem
    assert shown[0] == "claude:s00"


def test_a_leader_is_kept_before_a_subagent_when_the_area_is_full():
    events = [act(0, "READING", ego="claude:lider")]
    for i in range(9):
        events += [ev(1, {"type": "subagent.started", "kind": "x"}, ego="claude:lider", agent=f"a{i}"), act(1, "READING", ego="claude:lider", agent=f"a{i}")]
    world = world_with(*events)
    place = room(world)[RESEARCH]
    assert place["shown"][0] == "claude:lider" and len(place["shown"]) == 8 and place["more"] == 2


def test_the_count_is_stable_and_the_same_snapshot_gives_the_same_room():
    world = world_with(*[act(0, "CODING", ego=f"claude:s{i:02d}") for i in range(12)])
    assert room(world) == room(world)


# --- os estados do líder -----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("events, state", [
    ([("activity", "BLOCKED")], "BLOCKED"),
    ([("error", "boom")], "ERROR"),
    ([("lost", None)], "NO_SIGNAL"),
])
def test_the_leader_states_that_get_a_neutral_icon_come_from_the_world(events, state):
    signals = {"activity": lambda v: {"type": "activity", "activity": v}, "error": lambda v: {"type": "error", "message": v, "recoverable": True},
               "lost": lambda v: {"type": "signal.lost"}}
    world = world_with(*[ev(0, signals[kind](value)) for kind, value in events])
    assert ego_of(world)["state"] == state


def test_a_leader_in_error_or_blocked_stands_in_the_lobby_and_comes_back_when_it_works_again():
    world = world_with(act(0, "CODING"), ev(1, {"type": "error", "message": "x", "recoverable": True}))
    assert ego_of(world)["state"] == "ERROR" and room(world)["__lobby"]["shown"] == ["claude:s1"]
    world.apply(act(2, "CODING"))
    assert ego_of(world)["state"] == "CODING" and room(world)[DEV]["shown"] == ["claude:s1"]


# --- o subagente que termina (R51) ---------------------------------------------------------------------------------------------------

def test_a_subagent_that_ended_tells_when_so_the_client_can_walk_it_to_the_leader():
    world = world_with(ev(0, {"type": "subagent.started", "kind": "Explore"}, agent="a1"), act(0, "READING", agent="a1"),
                       ev(5, {"type": "subagent.ended", "outcome": "completed"}, agent="a1"))
    (sub,) = ego_of(world)["team"]
    assert sub["active"] is False and sub["outcome"] == "completed" and sub["ended_at"] == "2026-10-07T10:05:00Z"


def test_a_subagent_still_working_or_without_the_end_signal_has_no_end_time():
    world = world_with(ev(0, {"type": "subagent.started", "kind": "Explore"}, agent="a1"), act(0, "READING", agent="a1"))
    (sub,) = ego_of(world)["team"]
    assert sub["ended_at"] is None and sub["active"] is True
    (silent,) = ego_of(world, minutes=20)["team"]                             # 20 min sem sinal: cinza no lugar (R7), nada de fim inventado
    assert silent["no_signal"] is True and silent["ended_at"] is None


def test_a_subagent_is_leaving_only_while_the_end_is_recent():
    world = world_with(ev(0, {"type": "subagent.started", "kind": "Explore"}, agent="a1"), act(0, "READING", agent="a1"),
                       ev(5, {"type": "subagent.ended", "outcome": "completed"}, agent="a1"))
    assert ego_of(world, minutes=5.25)["team"][0]["leaving"] is True             # 15 s depois do fim: caminha até o líder (R51)
    assert ego_of(world, minutes=6)["team"][0]["leaving"] is False                # 60 s depois: já saiu (quem abre a página agora não vê nada)


def test_a_subagent_still_working_or_without_the_end_signal_is_never_leaving():
    world = world_with(ev(0, {"type": "subagent.started", "kind": "Explore"}, agent="a1"), act(0, "READING", agent="a1"))
    assert ego_of(world, minutes=1)["team"][0]["leaving"] is False
    assert ego_of(world, minutes=20)["team"][0]["leaving"] is False               # sem o sinal do fim vale o cinza (R7)
    assert world.snapshot()["realms"][0]["alter_egos"][0]["team"][0]["leaving"] is False   # sem `now`, nada que dependa do tempo é afirmado
