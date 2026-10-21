"""XP de commits e as três escalas (ticket 23, R53, R54, D-090, D-103, D-104, D-106, PROGRESSION.md §3 e §4): ponto de teste = o mundo.
Evidência de commit (eventos de sessão) + o que o git disse (eventos de realm) -> extrato com estados, nível do Alter Ego, do Realm e de Mankind."""
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from itertools import count

import pytest

from orb.core import Entry, Ledger, World, rules
from orb.protocol import make_event, validate
from orb.registry import REGISTRY_FILE, LocalRegistry

_n = count(1)
T0 = datetime(2026, 10, 7, 10, 0, 0, tzinfo=UTC)
EGO = "claude:s1"
SHA = "0123456789abcdef0123456789abcdef01234567"


def stamp(minutes):
    return (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def made(minutes, sha=SHA, *, ego=EGO, provider="claude", realm="the-orb", agent=None, ok=True, key=None):
    """Um comando que fez um commit (sinal de sessão `command.result` com `commit`)."""
    n = next(_n)
    commit = {"sha": sha} if sha else {}
    return make_event(id=f"{ego}:{key or n}", ts=stamp(minutes), provider=provider, source=f"{provider}/x", realm=realm, alter_ego=ego,
                      agent=agent, seq=n, kind="x", body={}, signal={"type": "command.result", "ok": ok, "activity": "EXECUTING", "commit": commit})


def seen(minutes, *facts, realm="the-orb"):
    """O que o git disse (evento de realm do Probe de commits)."""
    n = next(_n)
    event = make_event(id=f"{realm}:commits:{n}", ts=stamp(minutes), provider=None, source="probe/commits", realm=realm, alter_ego=None,
                       agent=None, seq=n, kind="realm/commits", body={}, signal={"type": "realm.commits", "commits": list(facts)})
    assert validate(event) is None
    return event


def fact(key=SHA, *, sha=SHA, exists=True, lines=3, on_main=False, reverted=False):
    return {"key": key, "sha": sha, "exists": exists, "lines": lines, "on_main": on_main, "reverted": reverted}


def run(*events, table=rules.XP_TABLE, source=None):
    world = World(xp=source, xp_table=table)
    for event in events:
        assert world.apply(event) is True
    return world


def entries(world, ego=EGO):
    return [e for e in world.alter_ego(ego).xp.entries if e.rule == "X-COMMIT"]


def xp(world, ego=EGO):
    return next(e for r in world.snapshot()["realms"] for e in r["alter_egos"] if e["id"] == ego)["xp"]


# --- a evidência vira XP provisória ---------------------------------------------------------------------------------

def test_a_commit_made_by_a_session_starts_as_provisional_xp_that_does_not_count_for_the_level():
    world = run(made(0))
    (entry,) = entries(world)
    assert (entry.rule, entry.state, entry.xp, entry.ref) == ("X-COMMIT", "provisional", 10, SHA)
    assert entry.evidence == {"event": entry.evidence["event"], "at": stamp(0), "sha": SHA}
    assert xp(world) == {"total": 0, "provisional": 10, "level": 1, "floor": 0, "next": 100}


def test_a_commit_without_a_hash_is_kept_by_the_event_that_reported_it():
    (entry,) = entries(run(made(0, None, key="c1")))
    assert entry.ref == "claude:s1:c1" and "sha" not in entry.evidence


def test_a_failed_command_or_a_command_that_did_not_commit_earns_nothing():
    failed = made(0, ok=False)
    assert entries(run(failed)) == []


def test_a_commit_reported_twice_is_one_commit():
    world = run(made(0), made(5))                                                   # o mesmo hash
    assert len(entries(world)) == 1


def test_the_work_of_a_subagent_commits_for_the_leader_and_each_session_has_its_own_commits():
    world = run(made(0, agent="a1"), made(1, "f" * 40, ego="claude:s2"))
    assert [e.ref for e in entries(world, EGO)] == [SHA] and [e.ref for e in entries(world, "claude:s2")] == ["f" * 40]


# --- o que o git diz: linhas, principal, revertido ---------------------------------------------------------------------

@pytest.mark.parametrize("lines, expected", [(0, 10), (19, 10), (20, 11), (45, 12), (100, 15), (600, 40), (10_000, 40), (None, 10)])
def test_the_xp_of_a_commit_is_10_plus_1_per_20_changed_lines_capped_at_40(lines, expected):
    world = run(made(0), seen(5, fact(lines=lines)))
    assert entries(world)[0].xp == expected


def test_it_is_confirmed_only_when_it_reaches_the_main_branch_and_then_it_counts_for_the_level():
    world = run(made(0), seen(5, fact(lines=45)))
    assert entries(world)[0].state == "provisional" and xp(world)["total"] == 0
    world.apply(seen(10, fact(lines=45, on_main=True)))
    assert entries(world)[0].state == "confirmed"
    assert xp(world) == {"total": 12, "provisional": 0, "level": 1, "floor": 0, "next": 100}


def test_a_commit_the_repository_does_not_know_stays_provisional():
    world = run(made(0), seen(5, fact(sha=None, exists=False, lines=None)))
    assert entries(world)[0].state == "provisional" and entries(world)[0].xp == 10


def test_a_reverted_commit_is_annulled_and_the_level_can_fall():
    world = run(made(0), seen(5, fact(lines=600, on_main=True)))
    assert xp(world)["total"] == 40
    world.apply(seen(60, fact(lines=600, on_main=True, reverted=True)))
    assert entries(world)[0].state == "annulled" and xp(world)["total"] == 0


def test_the_level_can_fall_when_a_confirmed_commit_is_reverted():
    table = replace(rules.XP_TABLE, k=10)                                          # nível 2 com 20 XP
    world = run(made(0), seen(5, fact(lines=600, on_main=True)), table=table)
    assert xp(world)["level"] == 2
    world.apply(seen(60, fact(lines=600, on_main=True, reverted=True)))
    assert xp(world)["level"] == 1


def test_an_annulled_commit_is_final_even_if_the_repository_says_otherwise_later():
    world = run(made(0), seen(5, fact(on_main=True, reverted=True)), seen(9, fact(on_main=True, reverted=False)))
    assert entries(world)[0].state == "annulled"


def test_a_commit_that_never_reaches_main_expires_after_30_days_and_never_comes_back():
    world = run(made(0), seen(60, fact(on_main=False)))
    assert entries(world)[0].state == "provisional"
    thirty_days = 30 * 24 * 60
    world.apply(seen(thirty_days + 1, fact(on_main=False)))
    assert entries(world)[0].state == "expired" and xp(world)["provisional"] == 0 and xp(world)["total"] == 0
    world.apply(seen(thirty_days + 60, fact(on_main=True)))
    assert entries(world)[0].state == "expired"


def test_a_commit_that_arrives_in_time_is_confirmed_even_close_to_the_30_days():
    world = run(made(0), seen(30 * 24 * 60 - 5, fact(on_main=True)))
    assert entries(world)[0].state == "confirmed"


def test_what_the_git_says_about_a_commit_nobody_reported_earns_nothing():
    world = run(made(0), seen(5, fact(), fact("outro", sha="e" * 40, lines=900, on_main=True)))     # um commit do Lucas, sem sessão
    assert [e.ref for e in entries(world)] == [SHA]
    other = World()
    other.apply(seen(5, fact("so-git", on_main=True)))
    assert other.snapshot()["mankind"]["xp"]["total"] == 0


def test_a_hash_found_by_time_is_recorded_for_a_commit_that_came_without_one():
    world = run(made(0, None, key="c1"), seen(5, fact("claude:s1:c1", sha="b" * 40, lines=25, on_main=True)))
    (entry,) = entries(world)
    assert entry.state == "confirmed" and entry.xp == 11 and entry.evidence["sha"] == "b" * 40


# --- o que o Probe precisa perguntar ---------------------------------------------------------------------------------------

def test_the_world_asks_about_provisional_commits_and_about_confirmed_ones_still_inside_30_days():
    world = run(made(0), made(1, "a" * 40), made(2, "b" * 40), seen(5, fact("a" * 40, sha="a" * 40, on_main=True),
                                                                  fact("b" * 40, sha="b" * 40, on_main=True, reverted=True)))
    asked = {q["key"]: q for q in world.pending_commits("the-orb", T0 + timedelta(days=1))}
    assert set(asked) == {SHA, "a" * 40}                                               # a anulada não se pergunta mais
    assert asked["a" * 40] == {"key": "a" * 40, "sha": "a" * 40, "at": stamp(1)}
    later = world.pending_commits("the-orb", T0 + timedelta(days=31))
    assert {q["key"] for q in later} == {SHA}                                          # a confirmada saiu da janela de reversão; a provisória ainda é perguntada até expirar
    assert world.pending_commits("outro-realm", T0) == []


def test_a_commit_without_a_hash_is_asked_with_no_hash_and_the_time_of_the_evidence():
    world = run(made(0, None, key="c1"))
    assert world.pending_commits("the-orb", T0) == [{"key": "claude:s1:c1", "sha": None, "at": stamp(0)}]


# --- Realm e Mankind --------------------------------------------------------------------------------------------------------

def test_the_realm_level_sums_the_confirmed_xp_of_all_its_sessions_even_the_ones_out_of_the_room():
    table = replace(rules.XP_TABLE, k_realm=10, k_mankind=100)
    world = run(made(0, "a" * 40, ego="claude:s1"), made(1, "b" * 40, ego="codex:s2", provider="codex"),
                seen(5, fact("a" * 40, sha="a" * 40, lines=600, on_main=True), fact("b" * 40, sha="b" * 40, lines=600, on_main=True)), table=table)
    realm = world.snapshot(T0 + timedelta(days=30))["realms"][0]                    # 30 dias depois as duas já saíram da sala (10 dias)
    assert all(not e["in_room"] for e in realm["alter_egos"])
    assert realm["xp"] == {"total": 80, "provisional": 0, "level": 3, "floor": 60, "next": 120}


def test_mankind_sums_the_realms_and_keeps_a_scoreboard_by_provider():
    table = replace(rules.XP_TABLE, k_realm=10, k_mankind=10)
    world = run(made(0, "a" * 40, ego="claude:s1", realm="a"), made(1, "b" * 40, ego="codex:s2", provider="codex", realm="b"),
                made(2, "c" * 40, ego="claude:s3", realm="b"),
                seen(5, fact("a" * 40, sha="a" * 40, lines=600, on_main=True), realm="a"),
                seen(6, fact("b" * 40, sha="b" * 40, lines=200, on_main=True), fact("c" * 40, sha="c" * 40, lines=0, on_main=True), realm="b"),
                table=table)
    mankind = world.snapshot()["mankind"]["xp"]
    assert mankind["total"] == 40 + 20 + 10
    assert mankind["by_provider"] == {"claude": 50, "codex": 20, "hermes": 0, "opencode": 0}
    assert (mankind["level"], mankind["floor"], mankind["next"]) == (3, 60, 120)


def test_a_hidden_realm_leaves_the_mankind_total_like_it_leaves_the_city():
    world = run(made(0, realm="a"), seen(5, fact(on_main=True, lines=600), realm="a"))
    world.set_hidden(["a"])
    assert world.snapshot()["mankind"]["xp"]["total"] == 0


def test_every_realm_and_the_world_have_a_level_even_with_no_xp_yet():
    world = run(made(0))
    snap = world.snapshot()
    assert snap["realms"][0]["xp"] == {"total": 0, "provisional": 10, "level": 1, "floor": 0, "next": 1000}
    assert snap["mankind"]["xp"]["next"] == 5000 and snap["mankind"]["xp"]["by_provider"]["claude"] == 0


# --- o extrato guardado e a versão da tabela -----------------------------------------------------------------------------------

def test_the_state_changes_are_kept_in_the_registry_and_survive_a_restart(tmp_path):
    first = run(made(0), seen(5, fact(lines=45, on_main=True)), source=LocalRegistry(tmp_path))
    assert xp(first)["total"] == 12
    again = World(xp=LocalRegistry(tmp_path))
    again.apply(made(100, "9" * 40))                                                  # a sessão reaparece
    assert [(e.ref, e.state, e.xp) for e in entries(again)] == [(SHA, "confirmed", 12), ("9" * 40, "provisional", 10)]
    again.apply(seen(110, fact(on_main=True, reverted=True)))
    assert entries(again)[0].state == "annulled"
    third = World(xp=LocalRegistry(tmp_path))
    third.apply(made(200, "8" * 40))
    assert entries(third)[0].state == "annulled"                                      # a anulação também foi guardada


def test_a_registry_from_the_previous_version_gets_the_state_column_and_keeps_its_entries_confirmed(tmp_path):
    path = tmp_path / REGISTRY_FILE
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE names (key TEXT PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE bag (position INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE xp_ledger (ego TEXT NOT NULL, ts TEXT NOT NULL, rule TEXT NOT NULL, xp INTEGER NOT NULL, ref TEXT NOT NULL,
                                evidence TEXT NOT NULL, version INTEGER NOT NULL, PRIMARY KEY (ego, rule, ref, version));
        INSERT INTO xp_ledger VALUES ('claude:s1', '2026-10-07T10:00:00Z', 'X-TEST', 5, 'e1', '{"event": "e1"}', 1);
        PRAGMA user_version = 2;
    """)
    conn.commit()
    conn.close()
    registry = LocalRegistry(tmp_path)
    assert registry.error is None
    (stored,) = registry.entries_of("claude:s1", 1)
    assert (stored.rule, stored.xp, stored.state) == ("X-TEST", 5, "confirmed")


def test_the_table_has_the_commit_values_of_the_progression_document():
    table = rules.XP_TABLE
    assert (table.commit_xp, table.commit_lines_per_xp, table.commit_cap, table.commit_expire_days) == (10, 20, 40, 30)
    assert (table.k, table.k_realm, table.k_mankind) == (50, 500, 2500)


def test_the_ledger_rebuilt_from_a_stored_extract_keeps_what_each_state_means():
    stored = [Entry("2026-10-07T10:00:00Z", "X-COMMIT", 12, SHA, {"event": "e", "at": "2026-10-07T10:00:00Z", "sha": SHA}, 1, "confirmed"),
              Entry("2026-10-07T10:01:00Z", "X-COMMIT", 10, "b" * 40, {"event": "f", "at": "2026-10-07T10:01:00Z"}, 1, "annulled"),
              Entry("2026-10-07T10:02:00Z", "X-TEST", 5, "t", {"event": "t"}, 1)]
    ledger = Ledger(rules.XP_TABLE, stored)
    assert ledger.total == 12 + 5 and ledger.provisional == 0


# --- o extrato para o painel Progressão ---------------------------------------------------------------------------------------

def test_the_extract_lists_every_session_entry_newest_first_with_who_earned_it():
    world = World(names=None)
    for event in (made(0, "a" * 40, ego="claude:s1"), made(5, "b" * 40, ego="codex:s2", provider="codex", realm="outro"),
                  seen(10, fact("a" * 40, sha="a" * 40, lines=45, on_main=True))):
        world.apply(event)
    rows = world.xp_extract()
    assert [(r["ego"], r["rule"], r["state"], r["xp"]) for r in rows] == [("codex:s2", "X-COMMIT", "provisional", 10), ("claude:s1", "X-COMMIT", "confirmed", 12)]
    assert rows[0]["provider"] == "codex" and rows[0]["realm"] == "outro" and rows[1]["evidence"]["sha"] == "a" * 40
    assert set(rows[0]) == {"ego", "name", "provider", "realm", "ts", "rule", "xp", "state", "ref", "evidence", "version"}


def test_the_extract_is_limited_and_leaves_out_the_realms_the_city_hides():
    world = run(*[made(i, f"{i:040x}") for i in range(12)], made(0, "f" * 40, ego="claude:s9", realm="escondido"))
    assert len(world.xp_extract(limit=5)) == 5
    world.set_hidden(["escondido"])
    assert all(r["realm"] != "escondido" for r in world.xp_extract())


def test_the_provisional_xp_shows_in_the_realm_and_in_mankind_too_without_counting_for_their_levels():
    world = run(made(0, "a" * 40), made(1, "b" * 40, ego="codex:s2", provider="codex"), seen(5, fact("a" * 40, sha="a" * 40, lines=600, on_main=True)))
    snap = world.snapshot()
    assert snap["realms"][0]["xp"]["provisional"] == 10 and snap["realms"][0]["xp"]["total"] == 40
    assert snap["mankind"]["xp"]["provisional"] == 10 and snap["mankind"]["xp"]["total"] == 40


def test_a_commit_that_never_reached_main_expires_with_the_time_even_if_the_git_never_answers():
    registry_free = run(made(0))
    registry_free.expire_commits(T0 + timedelta(days=29))
    assert entries(registry_free)[0].state == "provisional"
    registry_free.expire_commits(T0 + timedelta(days=31))
    assert entries(registry_free)[0].state == "expired" and xp(registry_free)["provisional"] == 0


def test_the_expiry_by_time_is_kept_in_the_registry(tmp_path):
    first = run(made(0), source=LocalRegistry(tmp_path))
    first.expire_commits(T0 + timedelta(days=31))
    again = World(xp=LocalRegistry(tmp_path))
    again.apply(made(100, "9" * 40))
    assert [e.state for e in entries(again)] == ["expired", "provisional"]


def test_a_receipt_from_a_very_long_event_id_still_fits_the_probe_event():
    world = run(made(0, None, key="x" * 400))
    (entry,) = entries(world)
    assert len(entry.ref) <= 60 and entry.ref.startswith("ev-")
    assert world.pending_commits("the-orb", T0)[0]["key"] == entry.ref
