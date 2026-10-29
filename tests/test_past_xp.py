"""A XP das sessões antigas e a calibração da curva (ticket 25, R48 camada 3, R54, D-088, D-107, D-108, PROGRESSION.md §4 e §7).
Ponto de teste: o mundo. A leitura do passado entrega ao mundo o extrato de cada sessão antiga; o mundo soma nos níveis do Realm e de Mankind, deixa o git
decidir os commits e responde com o relatório da distribuição de níveis."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from orb.core import Entry, Ledger, World, calibration, rules
from orb.core.past import PastEgo

T0 = datetime(2026, 10, 7, 10, 0, 0, tzinfo=UTC)
SHA = "0123456789abcdef0123456789abcdef01234567"


def stamp(minutes=0):
    return (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def entry(rule="X-TEST", xp=5, ref="e1", *, state="confirmed", minutes=0, version=1, **evidence):
    return Entry(ts=stamp(minutes), rule=rule, xp=xp, ref=ref, evidence=evidence or {"event": ref}, version=version, state=state)


def commit(ref=SHA, *, state="provisional", minutes=0, xp=10):
    return entry("X-COMMIT", xp, ref, state=state, minutes=minutes, event="ev", at=stamp(minutes), sha=ref)


class Memory:
    """O registro local de mentira: guarda o que o mundo mandou gravar."""
    error = None

    def __init__(self):
        self.saved = []

    def entries_of(self, ego_id, version):
        return []

    def record(self, ego_id, new):
        self.saved.append((ego_id, new))


# --- Ledger.absorb: o extrato de um personagem recebe o que a releitura do passado gravou -------------------------------

def test_absorb_adds_only_what_the_ledger_does_not_have_and_counts_it():
    ledger = Ledger(entries=[entry(ref="a")])
    added = ledger.absorb([entry(ref="a", xp=99), entry(ref="b", xp=7), entry(ref="old", version=0)])
    assert [e.ref for e in added] == ["b"]                              # o que já estava fica como estava; outra versão da tabela fica de fora
    assert ledger.total == 12 and [e.ref for e in ledger.entries] == ["a", "b"]


def test_absorb_respects_the_daily_cap_and_the_test_gap_that_the_past_already_used():
    ledger = Ledger()
    ledger.absorb([entry("X-TEST", 5, "t1", minutes=0), entry("X-DELEG", 30, "d1", minutes=1)])
    assert ledger._day_xp[("X-DELEG", T0.date())] == 30 and ledger._last_test == T0


# --- o mundo soma o passado nas escalas -----------------------------------------------------------------------------------

def snapshot_xp(world):
    snap = world.snapshot(T0)
    return {r["id"]: r["xp"] for r in snap["realms"]}, snap["mankind"]["xp"]


def test_an_old_session_counts_for_its_realm_and_for_mankind_and_the_provider_board():
    world = World()
    world.add_past("claude:old", "the-orb", "claude", [entry(xp=400, ref="a"), entry("X-DELEG", 100, "d")])
    realms, mankind = snapshot_xp(world)
    assert realms["the-orb"]["total"] == 500 and realms["the-orb"]["level"] == 1
    assert mankind["total"] == 500 and mankind["by_provider"]["claude"] == 500 and mankind["by_provider"]["codex"] == 0
    assert world.snapshot(T0)["realms"][0]["alter_egos"] == []         # não é um personagem: não está na cidade como sessão


def test_reading_the_same_old_session_again_replaces_it_and_never_counts_it_twice():
    world = World()
    world.add_past("claude:old", "the-orb", "claude", [entry(xp=400, ref="a")])
    world.add_past("claude:old", "the-orb", "claude", [entry(xp=400, ref="a"), entry(xp=50, ref="b")])
    assert snapshot_xp(world)[0]["the-orb"]["total"] == 450


def test_xp_of_the_wrong_table_version_is_not_counted():
    world = World()
    world.add_past("claude:old", "the-orb", "claude", [entry(xp=400, ref="a", version=2)])
    assert snapshot_xp(world)[0]["the-orb"]["total"] == 0


def test_a_hidden_realm_keeps_its_old_xp_out_of_mankind():
    world = World()
    world.add_past("claude:a", "open", "claude", [entry(xp=300)])
    world.add_past("claude:b", "shut", "claude", [entry(xp=900)])
    world.set_hidden(["shut"])
    assert snapshot_xp(world)[1]["total"] == 300


def test_a_session_that_is_alive_in_the_world_receives_the_old_entries_in_its_own_extract():
    from orb.protocol import make_event
    world = World()
    event = make_event(id="claude:s1:e", ts=stamp(0), provider="claude", source="claude/x", realm="the-orb", alter_ego="claude:s1", agent=None,
                       seq=1, kind="x", body={}, signal={"type": "activity", "activity": "THINKING"})
    assert world.apply(event)
    world.add_past("claude:s1", "the-orb", "claude", [entry("X-FIX", 25, "f1")])
    assert world.past == {} and world.alter_ego("claude:s1").xp.total == 25


def test_an_old_session_that_comes_back_to_the_room_stops_being_counted_apart():
    from orb.protocol import make_event
    world = World()
    world.add_past("claude:s1", "the-orb", "claude", [entry(xp=40)])
    event = make_event(id="claude:s1:e", ts=stamp(0), provider="claude", source="claude/x", realm="the-orb", alter_ego="claude:s1", agent=None,
                       seq=1, kind="x", body={}, signal={"type": "activity", "activity": "THINKING"})
    assert world.apply(event)
    assert world.past["the-orb"] == {}


# --- o git decide os commits do passado ------------------------------------------------------------------------------------

def test_the_commits_of_an_old_session_are_asked_to_the_git_and_settled_like_any_other():
    memory = Memory()
    world = World(xp=memory)
    world.add_past("claude:old", "the-orb", "claude", [commit(minutes=0)])
    assert world.pending_commits("the-orb", T0 + timedelta(days=1)) == [{"key": SHA, "sha": SHA, "at": stamp(0)}]
    assert snapshot_xp(world)[0]["the-orb"] == {**snapshot_xp(world)[0]["the-orb"], "total": 0, "provisional": 10}
    from orb.protocol import make_event
    asked = make_event(id="the-orb:commits:1", ts=stamp(60), provider=None, source="probe/commits", realm="the-orb", alter_ego=None, agent=None, seq=1,
                       kind="realm/commits", body={}, signal={"type": "realm.commits", "commits": [
                           {"key": SHA, "sha": SHA, "exists": True, "lines": 40, "on_main": True, "reverted": False}]})
    assert world.apply(asked)
    realm = snapshot_xp(world)[0]["the-orb"]
    assert (realm["total"], realm["provisional"]) == (12, 0)              # 10 + 40 // 20, confirmada
    (ego, saved), = memory.saved
    assert ego == "claude:old" and saved.state == "confirmed" and saved.xp == 12


def test_an_old_commit_that_never_reached_the_main_branch_expires_with_the_deadline():
    memory = Memory()
    world = World(xp=memory)
    world.add_past("claude:old", "the-orb", "claude", [commit(minutes=0)])
    world.expire_commits(T0 + timedelta(days=rules.XP_TABLE.commit_expire_days + 1))
    assert snapshot_xp(world)[0]["the-orb"]["provisional"] == 0 and memory.saved[0][1].state == "expired"


def test_past_egos_have_their_own_levels_in_the_replay_of_the_whole_history():
    ego = PastEgo.from_entries(rules.XP_TABLE, "claude:o", "r", "claude", [entry(xp=10, ref="a"), commit(state="confirmed")])
    assert (ego.total, ego.provisional) == (20, 0)


# --- a calibração da curva ------------------------------------------------------------------------------------------------------

def test_judge_counts_sessions_per_level_and_checks_the_goal_of_d107():
    sessions = [10, 120, 150, 320, 330, 610, 700, 1100, 1400, 3500]       # k = 50: níveis 1, 2, 2, 3, 3, 4, 4, 5, 5, 8
    verdict = calibration.judge(sessions, 50)
    assert verdict["levels"] == {1: 1, 2: 2, 3: 2, 4: 2, 5: 2, 8: 1}
    assert verdict["median_level"] == 3 and verdict["typical_share"] == 0.6 and verdict["above_share"] == 0.0
    assert verdict["meets"] is True


def test_the_goal_fails_when_the_typical_session_is_too_high_or_too_many_pass_level_8():
    assert calibration.judge([5000] * 5, 50)["meets"] is False                # a mediana está no nível 10
    assert calibration.judge([300] * 18 + [20000] * 2, 50)["meets"] is False  # 10% passam do nível 8
    assert calibration.judge([], 50)["meets"] is False and calibration.judge([], 50)["median_level"] is None


def test_the_k_range_that_meets_the_goal_is_found_and_none_is_reported_as_none():
    sessions = [300] * 20
    fit = calibration.fit_range(sessions)
    assert fit is not None and calibration.judge(sessions, fit["min"])["meets"] and not calibration.judge(sessions, fit["min"] - 5)["meets"]
    assert calibration.judge(sessions, fit["max"])["meets"] and not calibration.judge(sessions, fit["max"] + 5)["meets"]
    assert calibration.fit_range([]) is None


def test_the_report_compares_the_curve_in_use_with_the_candidates_and_scales_realm_and_mankind_by_the_same_ratio():
    sessions = [0, 0, 100, 300, 700]
    report = calibration.report(rules.XP_TABLE, sessions, [1100], 1100)
    assert report["version"] == 1 and report["sessions"] == {"total": 5, "with_xp": 3, "zero": 2}      # sem recibo, a sessão não diz nada da curva
    assert report["current"]["k"] == 50 and report["current"]["levels"] == {2: 1, 3: 1, 4: 1}
    assert [c["k"] for c in report["candidates"]] == [25, 75, 100, 150, 200]                            # a em uso não se repete
    assert report["current"]["realm_k"] == 500 and report["current"]["mankind_k"] == 2500
    doubled = next(c for c in report["candidates"] if c["k"] == 100)
    assert doubled["realm_k"] == 1000 and doubled["mankind_k"] == 5000                                   # a proporção 1 : 10 : 50 se mantém
    assert report["xp"] == {"median": 300, "p90": 700, "p99": 700, "max": 700}


def test_the_world_reports_every_shown_session_the_live_ones_and_the_old_ones():
    from orb.protocol import make_event
    world = World()
    world.add_past("claude:a", "open", "claude", [entry(xp=400)])
    world.add_past("claude:b", "shut", "claude", [entry(xp=9000)])
    world.set_hidden(["shut"])
    world.add_realm("empty")
    event = make_event(id="codex:c:e", ts=stamp(0), provider="codex", source="codex/x", realm="open", alter_ego="codex:c", agent=None, seq=1,
                       kind="x", body={}, signal={"type": "activity", "activity": "THINKING"})
    world.apply(event)
    report = world.xp_report()
    assert report["sessions"] == {"total": 2, "with_xp": 1, "zero": 1}                  # a escondida fica fora, como em Mankind
    assert report["mankind_xp"] == 400 and report["realms"] == 2 and report["current"]["mankind_level"] == 1


def test_the_report_changes_with_the_table_in_use():
    world = World(xp_table=replace(rules.XP_TABLE, version=2, k=100, k_realm=1000, k_mankind=5000))
    world.add_past("claude:a", "open", "claude", [entry(xp=400, version=2)])
    report = world.xp_report()
    assert report["version"] == 2 and report["current"]["k"] == 100 and report["current"]["levels"] == {2: 1}


@pytest.mark.parametrize("xp, k, level", [(0, 50, 1), (99, 50, 1), (100, 50, 2), (299, 50, 2), (300, 50, 3)])
def test_levels_still_follow_the_curve_the_report_uses(xp, k, level):
    assert calibration.judge([xp], k)["levels"] == {level: 1}
