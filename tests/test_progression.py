"""XP básica (ticket 22, R53, R54, D-101 a D-105, D-110, PROGRESSION.md §3 e §4): ponto de teste = o mundo.
Eventos sintéticos entram; o extrato do Alter Ego (data, regra, evidência, versão da tabela) e o nível saem, por tabela de casos."""
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from itertools import count

import pytest

from orb.core import Entry, Ledger, World, level_of, replay, rules
from orb.protocol import make_event
from orb.registry import REGISTRY_FILE, LocalRegistry

_n = count(1)
T0 = datetime(2026, 10, 7, 10, 0, 0, tzinfo=UTC)
EGO = "claude:s1"


def ev(minutes, signal, *, agent=None, ego=EGO, key=None):
    n = next(_n)
    ts = (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")
    return make_event(id=f"{ego}:{key or n}", ts=ts, provider="claude", source="claude/transcript", realm="the-orb", alter_ego=ego,
                      agent=agent, seq=n, kind="x", body={}, signal=signal)


def ran(minutes, ok, *, exit_code=None, activity="TESTING", agent=None, key=None, ego=EGO):
    signal = {"type": "command.result", "ok": ok, "activity": activity}
    if exit_code is not None:
        signal["exit_code"] = exit_code
    return ev(minutes, signal, agent=agent, key=key, ego=ego)


def activity(minutes, name, *, agent=None):
    return ev(minutes, {"type": "activity", "activity": name}, agent=agent)


def delegated(minutes, agent, outcome=None):
    return ev(minutes, {"type": "subagent.ended", **({"outcome": outcome} if outcome else {})}, agent=agent)


def run(*events, table=rules.XP_TABLE, source=None):
    world = World(xp=source, xp_table=table)
    for event in events:
        world.apply(event)
    return world


def ego_xp(world, ego=EGO):
    return next(e for r in world.snapshot()["realms"] for e in r["alter_egos"] if e["id"] == ego)["xp"]


def entries(world, ego=EGO):
    return world.alter_ego(ego).xp.entries


def rules_of(world, ego=EGO):
    return [e.rule for e in entries(world, ego)]


# --- X-TEST: teste que passou ----------------------------------------------------------------------------

def test_a_passing_test_earns_5_xp_with_the_receipt():
    world = run(ran(0, True, exit_code=0, key="t1"))
    (entry,) = entries(world)
    assert (entry.rule, entry.xp, entry.version) == ("X-TEST", 5, rules.XP_TABLE.version)
    assert entry.ts.startswith("2026-10-07T10:00") and entry.evidence == {"event": "claude:s1:t1", "exit_code": 0}
    assert ego_xp(world)["total"] == 5


def test_the_receipt_has_no_exit_code_when_the_provider_does_not_give_one():
    (entry,) = entries(run(ran(0, True, key="t1")))                    # o Claude não grava o código de saída (R42)
    assert entry.evidence == {"event": "claude:s1:t1"}


@pytest.mark.parametrize("event", [
    ran(0, False, exit_code=1),                                       # falhou
    ran(0, True, activity="EXECUTING"),                               # passou, mas não é teste
    ran(0, True, activity="READING"),
])
def test_only_a_test_that_passed_earns_xp(event):
    assert entries(run(event)) == []
    assert ego_xp(run(event))["total"] == 0


def test_one_test_xp_every_ten_minutes_per_session_so_a_loop_earns_nothing_more():
    world = run(ran(0, True), ran(3, True), ran(9.9, True), ran(10, True), ran(12, True))
    assert [e.ts[11:16] for e in entries(world)] == ["10:00", "10:10"]


def test_each_session_has_its_own_ten_minute_limit():
    world = run(ran(0, True, ego="claude:s1"), ran(1, True, ego="claude:s2"))
    assert ego_xp(world, "claude:s1")["total"] == 5 and ego_xp(world, "claude:s2")["total"] == 5


# --- X-FIX: vermelho -> verde ---------------------------------------------------------------------------

def test_a_red_then_green_earns_the_fix_with_both_runs_as_the_receipt():
    world = run(ran(0, False, key="red"), ran(1, True, key="green"))
    assert rules_of(world) == ["X-TEST", "X-FIX"]
    fix = entries(world)[1]
    assert (fix.xp, fix.evidence) == (25, {"failed": "claude:s1:red", "passed": "claude:s1:green"})
    assert ego_xp(world)["total"] == 30


def test_the_fix_comes_once_per_repaired_failure_even_with_many_reds_before_it():
    world = run(ran(0, False), ran(1, False), ran(2, False), ran(3, True), ran(4, True))
    assert rules_of(world).count("X-FIX") == 1
    world = run(ran(0, False), ran(1, True), ran(2, False), ran(3, True))
    assert rules_of(world).count("X-FIX") == 2                              # duas falhas consertadas, duas vezes


def test_a_green_without_a_red_before_is_not_a_fix_and_the_red_of_another_session_does_not_count():
    assert "X-FIX" not in rules_of(run(ran(0, True), ran(20, True)))
    world = run(ran(0, False, ego="claude:s2"), ran(1, True, ego="claude:s1"))
    assert rules_of(world, "claude:s1") == ["X-TEST"]


def test_the_fix_is_not_held_back_by_the_ten_minute_test_limit():
    world = run(ran(0, True), ran(1, False), ran(2, True))
    assert rules_of(world) == ["X-TEST", "X-FIX"]                           # o verde de 2 min não rende X-TEST de novo, mas conserta


def test_a_late_event_does_not_move_the_ten_minute_limit_back():
    world = run(ran(20, True), ran(5, True), ran(26, True))
    assert "10:26" not in [e.ts[11:16] for e in entries(world)]             # 6 min depois do teste mais recente já pago: ainda não vale


@pytest.mark.parametrize("ts", ["2026-10-07T10:00:00", "isto não é uma hora", "0001-01-01T00:00:00+05:00", ""])
def test_an_event_without_a_readable_time_with_a_zone_earns_nothing_and_breaks_nothing(ts):
    event = ran(0, True)
    event["ts"] = ts
    assert Ledger().observe(event) == []


# --- X-DELEG: subagente concluído (para o líder) -------------------------------------------------------

def test_a_finished_subagent_earns_3_xp_for_the_leader():
    world = run(delegated(0, "a1", "completed"), delegated(1, "a2"))
    assert rules_of(world) == ["X-DELEG", "X-DELEG"] and ego_xp(world)["total"] == 6
    assert entries(world)[0].evidence == {"agent": "a1"}


def test_a_subagent_that_failed_or_ended_twice_earns_nothing_more():
    world = run(delegated(0, "a1", "failed"), delegated(1, "a2"), delegated(2, "a2"))
    assert [e.evidence["agent"] for e in entries(world)] == ["a2"]


def test_subagent_xp_is_capped_at_30_per_session_per_day_and_the_next_day_pays_again():
    world = run(*[delegated(i, f"a{i}") for i in range(12)])
    assert sum(e.xp for e in entries(world)) == 30
    world.apply(delegated(24 * 60 + 1, "late"))
    assert sum(e.xp for e in entries(world)) == 33


# --- X-CRAFT: ofício ---------------------------------------------------------------------------------------

def test_work_earns_1_xp_per_five_minute_window_with_activity_and_never_twice_in_one_window():
    world = run(activity(0, "CODING"), activity(1, "READING"), activity(4.9, "TESTING"), activity(5, "REVIEWING"), activity(17, "RESEARCHING"))
    assert rules_of(world) == ["X-CRAFT"] * 3 and ego_xp(world)["total"] == 3


@pytest.mark.parametrize("name", ["THINKING", "EXECUTING", "DELEGATING", "BLOCKED", "COMPLETED"])
def test_what_is_not_work_does_not_earn_craft(name):
    assert entries(run(activity(0, name))) == []


def test_the_work_of_a_subagent_counts_for_the_leader_in_the_same_windows():
    world = run(activity(0, "CODING"), activity(1, "READING", agent="a1"), activity(6, "READING", agent="a1"))
    assert rules_of(world) == ["X-CRAFT", "X-CRAFT"]


def test_craft_is_capped_at_30_per_session_per_day():
    world = run(*[activity(5 * i, "CODING") for i in range(40)])
    assert sum(e.xp for e in entries(world)) == 30


# --- o que nunca rende e a XP nunca negativa -----------------------------------------------------------------

def test_tokens_messages_waiting_and_errors_earn_nothing_and_take_nothing_away():
    world = run(ran(0, True))
    before = ego_xp(world)["total"]
    for signal in ({"type": "usage", "input_tokens": 9_999_999, "cost_usd": 99.0}, {"type": "waiting", "request": "r", "action": "x"},
                   {"type": "waiting.resolved", "request": "r"}, {"type": "error", "message": "boom"}, {"type": "idle"},
                   {"type": "session.started"}, {"type": "session.ended"}):
        world.apply(ev(1, signal))
    assert ego_xp(world)["total"] == before
    world.apply(ran(30, False))
    assert ego_xp(world)["total"] == before and all(e.xp > 0 for e in entries(world))


def test_a_repeated_event_is_counted_once():
    world = World()
    event = ran(0, True, key="same")
    assert world.apply(event) is True and world.apply(event) is False
    assert ego_xp(world)["total"] == 5


# --- os níveis (curva k·n·(n-1), k = 50) -------------------------------------------------------------------------

@pytest.mark.parametrize("xp, level", [
    (0, 1), (99, 1), (100, 2), (299, 2), (300, 3), (599, 3), (600, 4), (999, 4), (1000, 5), (1500, 6), (2800, 8), (4500, 10),
    (10500, 15), (18999, 19), (19000, 20),
])
def test_the_level_follows_the_curve_k_n_n_minus_1(xp, level):
    assert level_of(xp, 50)["level"] == level


def test_the_level_says_where_the_bar_starts_and_ends():
    assert level_of(340, 50) == {"level": 3, "xp": 340, "floor": 300, "next": 600}
    assert level_of(0, 50) == {"level": 1, "xp": 0, "floor": 0, "next": 100}


def test_the_alter_ego_snapshot_carries_total_level_and_the_bar():
    world = run(*[ran(11 * i, True) for i in range(21)])              # 21 testes verdes, 10 minutos entre eles: 105 XP
    assert ego_xp(world) == {"total": 105, "provisional": 0, "level": 2, "floor": 100, "next": 300}


def test_a_session_that_earned_nothing_is_level_1_with_an_empty_bar():
    assert ego_xp(run(activity(0, "THINKING"))) == {"total": 0, "provisional": 0, "level": 1, "floor": 0, "next": 100}


# --- a tabela é versionada e recalculável ---------------------------------------------------------------------------

def test_the_table_is_versioned_and_every_entry_names_its_version():
    assert rules.XP_TABLE.version == 1 and rules.XP_TABLE.k == 50
    assert {e.version for e in entries(run(ran(0, False), ran(1, True), delegated(2, "a")))} == {1}


def test_changing_the_table_recalculates_the_same_events_with_the_new_version():
    events = [ran(0, False), ran(1, True), delegated(2, "a1")]
    v2 = replace(rules.XP_TABLE, version=2, test_xp=10, fix_xp=50, deleg_xp=6)
    old, new = run(*events), run(*events, table=v2)
    assert (ego_xp(old)["total"], ego_xp(new)["total"]) == (33, 66)
    assert {e.version for e in entries(new)} == {2}


def test_replaying_the_events_in_order_gives_the_same_extract_as_the_live_world():
    events = [ran(0, False), ran(1, True), delegated(2, "a1"), activity(3, "CODING"), activity(9, "READING")]
    live = run(*events)
    assert replay(rules.XP_TABLE, events).entries == entries(live)
    assert replay(rules.XP_TABLE, events).total == ego_xp(live)["total"]


# --- o extrato no registro local ---------------------------------------------------------------------------------------

def test_the_extract_goes_to_the_local_registry_and_survives_a_restart(tmp_path):
    events = [ran(0, False, key="r"), ran(1, True, key="g"), delegated(2, "a1"), activity(3, "CODING")]
    first = run(*events, source=LocalRegistry(tmp_path))
    total = ego_xp(first)["total"]
    assert total == 5 + 25 + 3 + 1
    again = World(xp=LocalRegistry(tmp_path))
    again.apply(ev(60, {"type": "session.started"}))                      # o Alter Ego reaparece depois de o Orb reabrir
    assert ego_xp(again)["total"] == total
    assert entries(again) == entries(first)


def test_reading_the_same_events_again_after_a_restart_does_not_pay_twice(tmp_path):
    events = [ran(0, False, key="r"), ran(1, True, key="g"), delegated(2, "a1"), activity(3, "CODING")]
    run(*events, source=LocalRegistry(tmp_path))
    again = run(*events, source=LocalRegistry(tmp_path))
    assert ego_xp(again)["total"] == 34 and len(entries(again)) == 4


def test_the_limits_survive_a_restart_too(tmp_path):
    run(ran(0, True), source=LocalRegistry(tmp_path))
    again = run(ran(3, True, key="after"), source=LocalRegistry(tmp_path))
    assert len(entries(again)) == 1                                         # os 10 minutos contam a partir do extrato guardado


def test_entries_of_another_table_version_are_not_loaded_so_the_new_version_starts_clean(tmp_path):
    run(ran(0, True), delegated(1, "a"), source=LocalRegistry(tmp_path))
    v2 = replace(rules.XP_TABLE, version=2)
    again = run(ran(3, True), table=v2, source=LocalRegistry(tmp_path))
    assert ego_xp(again)["total"] == 5 and {e.version for e in entries(again)} == {2}
    assert [e.rule for e in LocalRegistry(tmp_path).entries_of(EGO, 1)] == ["X-TEST", "X-DELEG"]            # a v1 segue guardada, só não é usada


def test_the_registry_keeps_the_extract_with_date_rule_receipt_and_version_only(tmp_path):
    run(ran(0, True, exit_code=0, key="t1"), source=LocalRegistry(tmp_path))
    conn = sqlite3.connect(tmp_path / REGISTRY_FILE)
    try:
        columns = [c[1] for c in conn.execute("PRAGMA table_info(xp_ledger)")]
        (row,) = conn.execute("SELECT ego, ts, rule, xp, ref, evidence, version FROM xp_ledger").fetchall()
    finally:
        conn.close()
    assert columns == ["ego", "ts", "rule", "xp", "ref", "evidence", "version", "state"]
    assert row[0] == EGO and row[2:5] == ("X-TEST", 5, "claude:s1:t1") and row[6] == 1
    assert "exit_code" in row[5] and "claude:s1:t1" in row[5]


def test_a_damaged_row_of_the_extract_is_left_out_and_the_rest_still_counts(tmp_path):
    registry = LocalRegistry(tmp_path)
    run(ran(0, True, key="a"), ran(20, True, key="b"), source=registry)
    conn = sqlite3.connect(tmp_path / REGISTRY_FILE)
    try:
        conn.execute("UPDATE xp_ledger SET evidence = 'nao e json' WHERE ref = 'claude:s1:a'")
        conn.commit()
    finally:
        conn.close()
    assert [e.ref for e in LocalRegistry(tmp_path).entries_of(EGO, 1)] == ["claude:s1:b"]


def test_the_registry_keeps_one_row_per_receipt_and_a_later_write_updates_it(tmp_path):
    registry = LocalRegistry(tmp_path)
    entry = Entry(ts="2026-10-07T10:00:00Z", rule="X-TEST", xp=5, ref="e1", evidence={"event": "e1"}, version=1)
    registry.record(EGO, entry)
    registry.record(EGO, replace(entry, xp=99))
    assert [e.xp for e in registry.entries_of(EGO, 1)] == [99]                  # o git mudou o que valia: o mesmo recibo, a XP nova


def test_a_broken_registry_does_not_stop_the_xp_which_goes_on_in_memory(tmp_path):
    (tmp_path / REGISTRY_FILE).write_bytes(b"isto nao e um banco sqlite " * 40)
    registry = LocalRegistry(tmp_path)
    world = run(ran(0, True), delegated(1, "a"), source=registry)
    assert ego_xp(world)["total"] == 8 and registry.error is not None
    assert [e.rule for e in registry.entries_of(EGO, 1)] == ["X-TEST", "X-DELEG"]          # a cópia em memória segue o que foi ganho


def test_the_ledger_does_not_pay_a_receipt_that_is_already_in_the_extract():
    entry = Entry(ts="2026-10-07T10:00:00Z", rule="X-TEST", xp=5, ref="e1", evidence={"event": "e1"}, version=1)
    ledger = Ledger(rules.XP_TABLE, [entry])
    assert ledger.total == 5 and ledger.entries == [entry]
    assert ledger.observe(ran(0, True, key="e1")) == []                # o recibo e1 já está no extrato: não paga de novo
