from orb.core import World
from orb.protocol import make_event

_seq = iter(range(1, 10_000))


def ev(signal=None, *, agent=None, key=None, ego="claude:s1", source="claude/transcript", seq=None):
    n = next(_seq)
    return make_event(id=f"{ego}:{key or n}", ts=f"2026-10-07T10:00:{n % 60:02d}Z", provider="claude",
                      source=source, realm="the-orb", alter_ego=ego, agent=agent, seq=seq if seq is not None else n,
                      kind="x", body={}, signal=signal)


def ego_snapshot(world, ego="claude:s1"):
    return next(e for r in world.snapshot()["realms"] for e in r["alter_egos"] if e["id"] == ego)


def test_each_session_is_one_alter_ego_in_its_realm():
    world = World()
    world.apply(ev({"type": "session.started", "model": "opus"}))
    world.apply(ev({"type": "session.started"}, ego="claude:s2"))
    snap = world.snapshot()
    assert [r["id"] for r in snap["realms"]] == ["the-orb"]
    assert {e["id"] for e in snap["realms"][0]["alter_egos"]} == {"claude:s1", "claude:s2"}
    assert snap["mankind"]["alter_egos"] == 2


def test_activity_moves_character_to_its_area():
    world = World()
    world.apply(ev({"type": "activity", "activity": "CODING", "target": "a.py"}))
    snap = ego_snapshot(world)
    assert (snap["state"], snap["area"], snap["target"]) == ("CODING", "Development Center", "a.py")
    world.apply(ev({"type": "activity", "activity": "TESTING"}))
    assert ego_snapshot(world)["area"] == "Testing Lab"


def test_waiting_overlays_activity_until_resolved():
    world = World()
    world.apply(ev({"type": "activity", "activity": "EXECUTING"}))
    world.apply(ev({"type": "waiting", "request": "r1", "action": "Bash git push"}))
    assert ego_snapshot(world)["state"] == "WAITING"
    assert world.snapshot()["mankind"]["waiting"] == 1
    world.apply(ev({"type": "waiting.resolved", "request": "r1"}))
    assert ego_snapshot(world)["state"] == "EXECUTING"


def test_team_is_not_idle_while_a_subagent_works():
    world = World()
    world.apply(ev({"type": "subagent.started", "kind": "Explore"}, agent="a1"))
    world.apply(ev({"type": "activity", "activity": "READING"}, agent="a1"))
    world.apply(ev({"type": "idle"}))                        # o líder terminou o turno
    snap = ego_snapshot(world)
    assert snap["state"] == "DELEGATING"
    assert snap["team"][0]["state"] == "READING" and snap["team"][0]["kind"] == "Explore"
    world.apply(ev({"type": "subagent.ended"}, agent="a1"))
    snap = ego_snapshot(world)
    assert snap["state"] == "IDLE" and snap["team"][0]["active"] is False


def test_duplicates_are_ignored_and_rereading_is_idempotent():
    world = World()
    first = ev({"type": "usage", "input_tokens": 10, "output_tokens": 5}, key="u1")
    assert world.apply(first) is True
    assert world.apply(dict(first)) is False
    assert ego_snapshot(world)["usage"] == {"input_tokens": 10, "output_tokens": 5}


def test_error_no_signal_and_invalid_events():
    world = World()
    world.apply(ev({"type": "error", "message": "boom", "recoverable": False}))
    assert ego_snapshot(world)["state"] == "ERROR"
    world.apply(ev({"type": "activity", "activity": "READING"}))
    assert ego_snapshot(world)["state"] == "READING"
    world.apply(ev({"type": "signal.lost"}))
    assert ego_snapshot(world)["state"] == "NO_SIGNAL"
    assert world.apply({"v": "0.2"}) is False and world.rejected == 1


def test_seq_gaps_are_counted_per_source():
    world = World()
    world.apply(ev(None, seq=1, key="a"))
    world.apply(ev(None, seq=5, key="b"))
    world.apply(ev(None, seq=1, key="c", source="claude/hooks"))
    assert ego_snapshot(world)["seq_gaps"] == 1


def test_same_events_same_world():
    events = [ev({"type": "activity", "activity": "CODING"}), ev({"type": "waiting", "request": "x"}),
              ev({"type": "subagent.started"}, agent="a")]
    w1, w2 = World(), World()
    for e in events:
        w1.apply(e)
        w2.apply(e)
    assert w1.snapshot() == w2.snapshot()
