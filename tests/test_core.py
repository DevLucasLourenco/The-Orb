import random
from datetime import UTC, datetime, timedelta

import pytest

from orb.core import NameBag, NameBook, World, rules
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


# --- o tempo (R47, D-086): o mundo recebe a hora de quem pede; nunca lê relógio -------------------
T0 = datetime(2026, 10, 7, 10, 0, 0, tzinfo=UTC)


def at(minutes, signal=None, *, agent=None, ego="claude:s1", inner=None):
    """Evento no instante T0 + minutos: a hora vem do evento."""
    n = next(_seq)
    ts = (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")
    return make_event(id=f"{ego}:t{n}", ts=ts, provider="claude", source="claude/transcript", realm="the-orb",
                      alter_ego=ego, agent=agent, seq=n, kind="x", body={}, inner=inner, signal=signal)


def ego_at(world, minutes, ego="claude:s1"):
    snap = world.snapshot(T0 + timedelta(minutes=minutes))
    return next(e for r in snap["realms"] for e in r["alter_egos"] if e["id"] == ego)


def sub_at(world, minutes, ego="claude:s1"):
    return ego_at(world, minutes, ego)["team"][0]


def test_time_limits_live_in_the_rules_table():
    assert rules.ASLEEP_AFTER_SECONDS == 15 * 60                # R31, D-044
    assert rules.SUBAGENT_NO_SIGNAL_AFTER_SECONDS == 5 * 60     # R7, D-045, D-050


def test_idle_session_sleeps_after_more_than_15_minutes():
    world = World()
    world.apply(at(0, {"type": "session.started"}))
    world.apply(at(1, {"type": "idle"}))
    assert ego_at(world, 1 + 14.99)["asleep"] is False
    assert ego_at(world, 1 + 15)["asleep"] is False             # "mais de 15 min": exatamente 15 ainda não
    assert ego_at(world, 1 + 15.02)["asleep"] is True


def test_a_session_working_or_waiting_does_not_sleep_by_age():
    world = World()
    world.apply(at(0, {"type": "activity", "activity": "CODING"}))
    assert ego_at(world, 120)["asleep"] is False
    world.apply(at(1, {"type": "waiting", "request": "r1", "action": "Bash"}))
    assert ego_at(world, 120)["asleep"] is False                # esperar o Lucas é visível de longe


def test_an_ended_session_is_asleep_at_any_time():
    world = World()
    world.apply(at(0, {"type": "session.ended"}))
    assert ego_at(world, 0)["asleep"] is True


def test_new_activity_wakes_the_session_up():
    world = World()
    world.apply(at(0, {"type": "idle"}))
    assert ego_at(world, 30)["asleep"] is True
    world.apply(at(31, {"type": "activity", "activity": "READING"}))
    assert ego_at(world, 32)["asleep"] is False


def test_subagent_without_activity_for_5_minutes_has_no_signal_but_stays_in_place():
    world = World()
    world.apply(at(0, {"type": "subagent.started", "kind": "Explore"}, agent="a1"))
    world.apply(at(1, {"type": "activity", "activity": "READING"}, agent="a1"))
    working = sub_at(world, 1 + 4.9)
    assert (working["state"], working["no_signal"]) == ("READING", False)
    lost = sub_at(world, 1 + 5.1)
    assert lost["no_signal"] is True and lost["state"] == "NO_SIGNAL"
    assert lost["active"] is True                               # não sumiu: segue na Team
    assert lost["area"] == "Research Center"                    # fica no lugar onde estava
    assert len(ego_at(world, 1 + 5.1)["team"]) == 1


def test_a_subagent_that_ended_is_never_no_signal():
    world = World()
    world.apply(at(0, {"type": "subagent.started"}, agent="a1"))
    world.apply(at(2, {"type": "subagent.ended"}, agent="a1"))
    ended = sub_at(world, 60)
    assert (ended["no_signal"], ended["active"], ended["state"]) == (False, False, "COMPLETED")


def test_any_event_of_the_subagent_counts_as_activity():
    world = World()
    world.apply(at(0, {"type": "subagent.started"}, agent="a1"))
    world.apply(at(8, None, agent="a1", inner={"role": "result", "text": "ok"}))   # sem sinal, só resultado
    assert sub_at(world, 10)["no_signal"] is False
    assert sub_at(world, 13.1)["no_signal"] is True


def test_subagent_activity_brings_it_back_from_no_signal():
    world = World()
    world.apply(at(0, {"type": "subagent.started"}, agent="a1"))
    assert sub_at(world, 6)["no_signal"] is True
    world.apply(at(7, {"type": "activity", "activity": "CODING"}, agent="a1"))
    assert sub_at(world, 8)["state"] == "CODING"


def test_a_no_signal_subagent_does_not_keep_the_leader_delegating_forever():
    world = World()
    world.apply(at(0, {"type": "subagent.started"}, agent="a1"))
    world.apply(at(1, {"type": "idle"}))                         # o líder terminou o turno
    assert ego_at(world, 3)["state"] == "DELEGATING"             # o subagente ainda tem sinal
    assert ego_at(world, 3)["asleep"] is False
    parked = ego_at(world, 1 + 16)                               # subagente em segundo plano nunca avisou o fim
    assert parked["state"] == "IDLE" and parked["asleep"] is True
    assert parked["team"][0]["no_signal"] is True                # ele continua na Team, "sem sinal"


def test_mankind_counts_only_subagents_known_to_be_active():
    world = World()
    world.apply(at(0, {"type": "subagent.started"}, agent="a1"))
    assert world.snapshot(T0 + timedelta(minutes=1))["mankind"]["active_subagents"] == 1
    assert world.snapshot(T0 + timedelta(minutes=6))["mankind"]["active_subagents"] == 0


def test_the_snapshot_depends_only_on_events_and_the_given_time():
    world = World()
    world.apply(at(0, {"type": "idle"}))
    first = world.snapshot(T0 + timedelta(minutes=30))
    world.snapshot(T0 + timedelta(hours=5))                      # outra hora não deixa rastro
    assert world.snapshot(T0 + timedelta(minutes=30)) == first
    assert world.snapshot(T0 + timedelta(minutes=30)) != world.snapshot(T0)


def test_without_a_time_nothing_time_derived_is_claimed():
    world = World()
    world.apply(at(0, {"type": "idle"}))
    world.apply(at(0, {"type": "subagent.started"}, agent="a1"))
    ego = ego_snapshot(world)
    assert ego["asleep"] is False and ego["team"][0]["no_signal"] is False


def test_the_time_must_be_timezone_aware():
    with pytest.raises(ValueError):
        World().snapshot(datetime(2026, 10, 7, 10, 0, 0))  # noqa: DTZ001 - sem fuso, de propósito


def test_an_unparseable_timestamp_never_breaks_the_snapshot():
    world = World()
    world.apply(make_event(id="claude:s1:bad", ts="não é uma data", provider="claude", source="claude/transcript",
                           realm="the-orb", alter_ego="claude:s1", agent=None, seq=1, kind="x", body={},
                           signal={"type": "idle"}))
    assert ego_at(world, 600)["asleep"] is False                 # sem hora confiável, não afirma nada


def test_the_world_tells_what_only_time_can_change():
    world = World()
    world.apply(at(0, {"type": "subagent.started"}, agent="a1"))
    world.apply(at(0, {"type": "idle"}))
    early = world.time_key(T0 + timedelta(minutes=1))
    assert world.time_key(T0 + timedelta(minutes=2)) == early        # o tempo passou, nada mudou
    assert world.time_key(T0 + timedelta(minutes=6)) != early        # o subagente ficou sem sinal
    assert world.time_key(T0 + timedelta(minutes=20)) != world.time_key(T0 + timedelta(minutes=6))   # a sessão dormiu
    with pytest.raises(ValueError):
        world.time_key(datetime(2026, 10, 7, 10, 0, 0))  # noqa: DTZ001 - sem fuso, de propósito


def test_the_snapshot_counts_subagents_with_signal_per_alter_ego():
    world = World()
    world.apply(at(0, {"type": "subagent.started"}, agent="a1"))
    world.apply(at(4, {"type": "subagent.started"}, agent="a2"))
    assert ego_at(world, 4.5)["active_subagents"] == 2
    assert ego_at(world, 6)["active_subagents"] == 1                 # a1 ficou sem sinal; a2 não
    assert world.snapshot(T0 + timedelta(minutes=6))["mankind"]["active_subagents"] == 1


# ---------- nome histórico (R37, D-063 a D-067) ----------

def test_a_session_gets_a_historical_name_when_it_appears_and_keeps_it():
    world = World(names=NameBook())
    world.apply(ev({"type": "session.started"}))
    name = ego_snapshot(world)["name"]
    assert name
    world.apply(ev({"type": "activity", "activity": "CODING"}))
    world.apply(ev({"type": "session.updated", "title": "outra coisa"}))
    assert ego_snapshot(world)["name"] == name                     # fica com a sessão para sempre


def test_without_a_name_book_the_alter_ego_has_no_name_and_nothing_is_invented():
    world = World()
    world.apply(ev({"type": "session.started"}))
    assert ego_snapshot(world)["name"] is None


def test_subagents_get_no_name_and_keep_the_kind_given_by_the_cli():
    world = World(names=NameBook())
    world.apply(ev({"type": "subagent.started", "kind": "Explore"}, agent="a1"))
    team = ego_snapshot(world)["team"]
    assert team[0]["kind"] == "Explore" and "name" not in team[0]


def test_the_bag_is_global_so_two_realms_never_share_a_name():
    world = World(names=NameBook(rng=random.Random(4)))
    for n in range(12):
        event = ev({"type": "session.started"}, ego=f"claude:s{n}")
        event["realm"] = f"realm-{n % 3}"
        world.apply(event)
    names = [e["name"] for r in world.snapshot()["realms"] for e in r["alter_egos"]]
    assert len(names) == 12 and len(set(names)) == 12


def test_two_characters_in_the_same_room_never_show_the_same_name():
    # A sacola deu a volta: "Einstein" voltou a ser sorteável enquanto a sessão s1 ainda o usa na sala.
    book = NameBook(assigned={"claude:s1": "Einstein"}, bag=NameBag(["Einstein", "Newton"]))
    world = World(names=book)
    world.apply(ev({"type": "session.started"}, ego="claude:s1"))
    world.apply(ev({"type": "session.started"}, ego="claude:s2"))
    names = sorted(e["name"] for e in world.snapshot()["realms"][0]["alter_egos"])
    assert names == ["Einstein", "Newton"]                                         # tira-se o seguinte


def test_the_same_name_may_appear_in_two_different_rooms():
    book = NameBook(assigned={"claude:s1": "Einstein", "claude:s2": "Einstein"})  # um nome sorteado em outra época
    world = World(names=book)
    world.apply(ev({"type": "session.started"}, ego="claude:s1"))
    other = ev({"type": "session.started"}, ego="claude:s2")
    other["realm"] = "outro"
    world.apply(other)
    assert [e["name"] for r in world.snapshot()["realms"] for e in r["alter_egos"]] == ["Einstein", "Einstein"]


def test_a_rejected_event_does_not_use_up_a_name():
    book = NameBook()
    world = World(names=book)
    bad = ev({"type": "session.started"})
    bad["seq"] = -1                                                                 # inválido para o Protocol
    assert world.apply(bad) is False
    assert len(book.bag.remaining) == 60 and book.assigned == {}



# --- a sala e o Histórico do realm (R28, R28a, D-027, D-059): quem está na sala depende só da hora recebida ---

def room_ids(world, days):
    snap = world.snapshot(T0 + timedelta(days=days))
    return {e["id"] for r in snap["realms"] for e in r["alter_egos"] if e["in_room"]}


def test_the_room_window_is_one_value_in_the_rules_table():
    assert rules.RECENT_SESSION_SECONDS == 10 * 24 * 3600                 # R28a: o ticket 07 torna configurável


def test_a_session_stays_in_the_room_for_ten_days_after_its_last_event_then_goes_to_history():
    world = World()
    world.apply(at(0, {"type": "idle"}))
    assert room_ids(world, 0) == {"claude:s1"}
    assert room_ids(world, 10) == {"claude:s1"}                          # exatamente 10 dias ainda é da sala
    assert room_ids(world, 10.01) == set()                               # passou: Histórico do realm


def test_a_session_that_left_the_room_is_never_deleted_and_comes_back_with_new_activity():
    world = World()
    world.apply(at(0, {"type": "session.ended"}))
    gone = world.snapshot(T0 + timedelta(days=30))["realms"][0]["alter_egos"]
    assert [(e["id"], e["in_room"], e["ended"]) for e in gone] == [("claude:s1", False, True)]    # R28: continua existindo
    world.apply(at(30 * 24 * 60, {"type": "activity", "activity": "CODING"}))
    assert room_ids(world, 30) == {"claude:s1"}                          # voltou a trabalhar: volta para a sala


def test_a_realm_without_a_session_in_the_window_is_night_and_lights_up_with_a_new_one():
    world = World()
    world.apply(at(0, {"type": "idle"}))
    assert world.snapshot(T0 + timedelta(days=1))["realms"][0]["night"] is False
    assert world.snapshot(T0 + timedelta(days=11))["realms"][0]["night"] is True        # D-059
    world.apply(at(11 * 24 * 60, {"type": "session.started"}, ego="claude:s2"))
    assert world.snapshot(T0 + timedelta(days=11))["realms"][0]["night"] is False


def test_a_known_realm_with_no_session_at_all_is_night():
    world = World()
    world.add_realm("parado")
    world.add_realm("parado")                                            # idempotente
    realm = world.snapshot(T0)["realms"][0]
    assert (realm["id"], realm["alter_egos"], realm["night"]) == ("parado", [], True)


def test_the_window_can_be_changed_without_touching_the_rules():
    world = World(recent_seconds=3600)
    world.apply(at(0, {"type": "idle"}))
    assert world.snapshot(T0 + timedelta(minutes=59))["realms"][0]["alter_egos"][0]["in_room"] is True
    assert world.snapshot(T0 + timedelta(minutes=61))["realms"][0]["alter_egos"][0]["in_room"] is False


def test_without_a_trusted_hour_nobody_is_sent_to_history():
    world = World()
    world.apply(at(0, {"type": "idle"}))
    snap = world.snapshot()                                              # sem hora: o mundo não afirma nada que dependa do tempo
    assert snap["realms"][0]["alter_egos"][0]["in_room"] is True and snap["realms"][0]["night"] is False


def test_the_world_tells_when_a_session_leaves_the_room():
    world = World()
    world.apply(at(0, {"type": "idle"}))
    assert world.time_key(T0 + timedelta(days=9)) != world.time_key(T0 + timedelta(days=11))
