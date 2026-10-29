"""A leitura única do passado, em segundo plano (ticket 25, R48 camada 3, D-088, D-108, D-203): o ponto de parada no registro local, o indicador de progresso,
o ritmo que não pesa no Orb e o caminho até o mundo. Ponto de teste: o mundo e os leitores dos CLIs com históricos sintéticos."""
import os
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from itertools import count

import pytest

from orb.adapters._shared import SessionMeta
from orb.core import World
from orb.core.rules import XP_TABLE
from orb.gateway import Hub
from orb.gateway.past import REST_RATIO, PastXp
from orb.protocol import make_event
from orb.registry import LocalRegistry

from .fakes import transcript
from .test_realms import Machine

NOW = datetime(2026, 10, 29, 12, 0, 0, tzinfo=UTC)
T0 = datetime(2026, 8, 15, 11, 0, 0, tzinfo=UTC)
_ids = count(1)


@pytest.fixture
def machine(short_tmp, jsonl, monkeypatch):
    """A máquina falsa dos testes de realms (pastas dos CLIs e do usuário em pasta temporária curta), sem espera entre varreduras."""
    monkeypatch.setattr("orb.adapters.codex.rollout.DISCOVER_EVERY", 0.0)
    monkeypatch.setattr("orb.adapters.claude.transcript.DISCOVER_EVERY", 0.0)
    return Machine(short_tmp, jsonl)


def meta(provider, sid, updated="2026-08-15T12:00:00Z"):
    return SessionMeta(provider=provider, session_id=sid, cwd="C:/p", updated_at=updated)


def passed(ego, provider, minutes):
    """Um teste que passou, `minutes` depois de T0 (sinal de sessão `command.result`)."""
    n = next(_ids)
    return make_event(id=f"{ego}:t{n}", ts=(T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z"), provider=provider, source=f"{provider}/x",
                      realm="demo", alter_ego=ego, agent=None, seq=n, kind="x", body={},
                      signal={"type": "command.result", "ok": True, "exit_code": 0, "activity": "TESTING"})


class Source:
    """Uma fonte do passado de mentira: cada sessão tem lotes de eventos prontos; guarda quantas vezes cada uma foi aberta e quantos lotes saíram."""

    def __init__(self, provider, sessions, *, fail_on=None):
        self.provider = provider
        self.sessions = sessions            # id -> lotes (cada lote = lista de minutos de testes que passaram)
        self.opened: list[str] = []
        self.batches = 0
        self.fail_on = fail_on or set()

    def read(self, meta, realm):
        self.opened.append(meta.session_id)
        ego = f"{self.provider}:{meta.session_id}"
        for index, minutes in enumerate(self.sessions[meta.session_id]):
            if meta.session_id in self.fail_on and index == 1:
                raise OSError("disco falhou")
            self.batches += 1
            yield [passed(ego, self.provider, m) for m in minutes]


def run_all(past, *, limit=1000):
    steps = 0
    while steps < limit and past.run_once():
        steps += 1
    return steps


def make(tmp_path, sources, leaders, **kw):
    registry = kw.pop("registry", None) or LocalRegistry(tmp_path)
    past = PastXp(lambda: leaders, {s.provider: s for s in sources}, registry, wall=lambda: NOW, **kw)
    return past, registry


# --- o ponto de parada: nunca lê a mesma sessão duas vezes -------------------------------------------------------------------

def test_every_old_session_is_read_once_and_the_xp_goes_to_the_world(tmp_path):
    source = Source("claude", {"a": [[0, 20]], "b": [[0], [30]]})
    leaders = [(meta("claude", "a"), "demo"), (meta("claude", "b"), "demo")]
    past, registry = make(tmp_path, [source], leaders)
    run_all(past)
    assert sorted(source.opened) == ["a", "b"] and past.progress()["state"] == "done"
    world = World(xp=registry)
    for result in past.drain():
        world.add_past(result.ego, result.realm, result.provider, result.entries)
    assert world.snapshot(NOW)["mankind"]["xp"]["total"] == 10 + 10                  # a: 2 testes; b: 2 testes (um por 10 min)
    assert registry.past_done(1) == {("claude", "a"), ("claude", "b")}


def test_reopening_the_orb_does_not_read_the_finished_sessions_again_and_reads_only_the_new_ones(tmp_path):
    first = Source("claude", {"a": [[0]], "b": [[0]]})
    leaders = [(meta("claude", "a"), "demo"), (meta("claude", "b"), "demo")]
    past, _ = make(tmp_path, [first], leaders)
    run_all(past)
    second = Source("claude", {"a": [[0]], "b": [[0]], "c": [[0]]})                  # o Orb fechou e abriu; uma sessão nova apareceu
    again, _ = make(tmp_path, [second], [*leaders, (meta("claude", "c"), "demo")], registry=LocalRegistry(tmp_path))
    run_all(again)
    assert second.opened == ["c"] and again.progress()["done"] == 3 and again.progress()["state"] == "done"


def test_a_reading_cut_in_the_middle_resumes_at_the_unfinished_session_and_never_repeats_the_finished_ones(tmp_path):
    source = Source("claude", {"a": [[0], [30]], "b": [[0], [30]], "c": [[0], [30]]})
    leaders = [(meta("claude", s, f"2026-08-15T12:0{n}:00Z"), "demo") for n, s in enumerate("abc")]      # a mais recente é a c
    past, registry = make(tmp_path, [source], leaders)
    for _ in range(4):                                                               # c inteira (2 lotes + fechar) e o começo da b
        past.run_once()
    assert source.opened == ["c", "b"] and registry.past_done(1) == {("claude", "c")}
    resumed = Source("claude", source.sessions)
    again, _ = make(tmp_path, [resumed], leaders, registry=LocalRegistry(tmp_path))
    run_all(again)
    assert sorted(resumed.opened) == ["a", "b"] and again.progress()["done"] == 3     # c não volta; b recomeça porque não terminou


def test_the_most_recent_sessions_are_read_first(tmp_path):
    source = Source("claude", {"old": [[0]], "new": [[0]], "mid": [[0]]})
    leaders = [(meta("claude", "old", "2026-01-01T00:00:00Z"), "demo"), (meta("claude", "new", "2026-10-01T00:00:00Z"), "demo"),
               (meta("claude", "mid", "2026-05-01T00:00:00Z"), "demo")]
    past, _ = make(tmp_path, [source], leaders)
    run_all(past)
    assert source.opened == ["new", "mid", "old"]


def test_a_session_that_fails_is_left_without_the_mark_and_the_others_are_read(tmp_path):
    source = Source("claude", {"a": [[0], [30]], "b": [[0]]}, fail_on={"a"})
    leaders = [(meta("claude", "a", "2026-10-01T00:00:00Z"), "demo"), (meta("claude", "b"), "demo")]
    past, registry = make(tmp_path, [source], leaders)
    run_all(past)
    assert registry.past_done(1) == {("claude", "b")} and "claude:a" in past.errors and past.progress()["errors"] == 1
    again = Source("claude", source.sessions)
    retry, _ = make(tmp_path, [again], leaders, registry=LocalRegistry(tmp_path))
    run_all(retry)
    assert again.opened == ["a"] and retry.progress()["state"] == "done"            # o que falhou volta na próxima abertura, e só ele


def test_a_session_whose_file_was_not_found_is_not_marked_as_read_and_is_tried_again_next_time(tmp_path):
    class Vanished(Source):
        def read(self, meta, realm):
            self.opened.append(meta.session_id)
            raise FileNotFoundError("sumiu")
            yield []
    gone = Vanished("claude", {"a": []})
    leaders = [(meta("claude", "a"), "demo")]
    past, registry = make(tmp_path, [gone], leaders)
    run_all(past)
    assert registry.past_done(1) == set() and past.progress()["errors"] == 1 and past.progress()["state"] == "done"
    assert past.drain() == []                                                        # nada vai ao mundo: não se afirma XP de uma sessão que não se leu
    again = Source("claude", {"a": [[0]]})
    retry, _ = make(tmp_path, [again], leaders, registry=LocalRegistry(tmp_path))
    run_all(retry)
    assert again.opened == ["a"] and retry.progress()["errors"] == 0


def test_a_new_table_version_reads_the_past_again_and_keeps_the_old_extract(tmp_path):
    source = Source("claude", {"a": [[0]]})
    leaders = [(meta("claude", "a"), "demo")]
    past, registry = make(tmp_path, [source], leaders)
    run_all(past)
    v2 = replace(XP_TABLE, version=2, test_xp=7)
    again = Source("claude", source.sessions)
    redo, _ = make(tmp_path, [again], leaders, registry=LocalRegistry(tmp_path), table=v2)
    run_all(redo)
    assert again.opened == ["a"]
    assert [e.xp for e in registry.entries_of("claude:a", 1)] == [5] and [e.xp for e in LocalRegistry(tmp_path).entries_of("claude:a", 2)] == [7]


# --- o ritmo: não pesa no Orb --------------------------------------------------------------------------------------------------

def test_each_step_takes_at_most_one_batch_of_one_session(tmp_path):
    source = Source("claude", {"a": [[0], [30], [60]], "b": [[0]]})
    past, _ = make(tmp_path, [source], [(meta("claude", "a"), "demo"), (meta("claude", "b", "2026-01-01T00:00:00Z"), "demo")])
    past.run_once()
    assert source.batches == 1 and source.opened == ["a"]                            # o primeiro passo abre a sessão e lê um lote
    past.run_once()
    assert source.batches == 2
    assert run_all(past) >= 2


def test_the_thread_rests_a_multiple_of_the_time_it_worked(tmp_path):
    past, _ = make(tmp_path, [Source("claude", {})], [])
    assert REST_RATIO >= 3 and past.rest_after(0.2) == 0.2 * REST_RATIO and past.rest_after(0.0) == 0.0
    fast, _ = make(tmp_path / "x", [Source("claude", {})], [], rest_ratio=1.0)
    assert fast.rest_after(0.5) == 0.5


def test_the_reading_runs_by_itself_in_a_thread_and_stops_when_it_finishes(tmp_path):
    source = Source("claude", {"a": [[0]], "b": [[0]]})
    past, _ = make(tmp_path, [source], [(meta("claude", "a"), "demo"), (meta("claude", "b"), "demo")], rest_ratio=0.0)
    past.start()
    deadline = time.monotonic() + 10
    while past.progress()["state"] != "done" and time.monotonic() < deadline:
        time.sleep(0.02)
    past.stop()
    assert past.progress()["state"] == "done" and len(past.drain()) == 2 and not past.running


# --- o indicador de progresso -------------------------------------------------------------------------------------------------

def test_the_progress_indicator_counts_sessions_per_provider_and_says_what_state_it_is_in(tmp_path):
    claude, codex = Source("claude", {"a": [[0]], "b": [[0]]}), Source("codex", {"c": [[0]]})
    leaders = [(meta("claude", "a"), "demo"), (meta("claude", "b"), "demo"), (meta("codex", "c"), "demo"), (meta("hermes", "h"), "demo")]
    past, _ = make(tmp_path, [claude, codex], leaders)
    assert past.progress()["state"] == "waiting" and past.progress()["total"] == 0
    past.run_once()
    now = past.progress()
    assert now["state"] == "running" and now["total"] == 3 and now["done"] == 0                  # o provider sem fonte não entra na conta
    run_all(past)
    assert past.progress() == {"state": "done", "version": 1, "total": 3, "done": 3, "errors": 0,
                               "providers": {"claude": {"total": 2, "done": 2}, "codex": {"total": 1, "done": 1}}}


def test_without_the_index_there_is_nothing_to_read_yet_and_the_state_stays_waiting(tmp_path):
    past, _ = make(tmp_path, [Source("claude", {})], [])
    assert past.run_once() is False and past.progress()["state"] == "waiting"


def test_while_the_registry_cannot_write_the_reading_waits_because_there_would_be_no_stop_point(tmp_path):
    blocker = tmp_path / "arquivo"
    blocker.write_text("x", encoding="utf-8")                                        # o pai da pasta do Orb é um arquivo: o disco falha
    registry = LocalRegistry(blocker / "orb")
    source = Source("claude", {"a": [[0]]})
    past, _ = make(tmp_path, [source], [(meta("claude", "a"), "demo")], registry=registry)
    assert past.run_once() is False and source.opened == [] and past.progress()["state"] == "paused"
    blocker.unlink()                                                                 # a falha passou
    run_all(past)
    assert past.progress()["state"] == "done" and registry.past_done(1) == {("claude", "a")} and registry.error is None


def test_a_registry_from_a_newer_orb_never_recovers_so_the_reading_stays_paused(tmp_path):
    import sqlite3
    conn = sqlite3.connect(tmp_path / "registry.db")
    conn.execute("PRAGMA user_version = 99")
    conn.commit()
    conn.close()
    source = Source("claude", {"a": [[0]]})
    past, _ = make(tmp_path, [source], [(meta("claude", "a"), "demo")])
    assert past.run_once() is False and source.opened == [] and past.progress()["state"] == "paused"


# --- até o mundo, pelos leitores de verdade ---------------------------------------------------------------------------------

def claude_old_session(machine, cwd, sid, runs, *, commit_at=None):
    entries = [{"type": "user", "uuid": "u0", "cwd": str(cwd), "timestamp": "2026-08-15T10:59:00Z", "message": {"content": "oi"}}]
    for n in range(runs):
        minute = n * 20                                                            # 20 min entre um teste e outro: cada um rende
        entries += [
            {"type": "assistant", "uuid": f"a{n}", "timestamp": f"2026-08-15T11:{minute % 60:02d}:01Z", "message": {"id": f"m{n}", "content": [
                {"type": "tool_use", "id": f"t{n}", "name": "Bash", "input": {"command": "pytest -q"}}], "stop_reason": "tool_use"}},
            {"type": "user", "uuid": f"u{n}", "timestamp": f"2026-08-15T11:{minute % 60:02d}:05Z",
             "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{n}", "content": "ok"}]}},
        ]
    path = transcript(machine.home, str(cwd), sid, entries)
    os.utime(path, (time.time() - 90 * 86400, time.time() - 90 * 86400))
    return path


def test_the_whole_way_from_old_files_to_the_levels_of_the_city(machine):
    demo = machine.project("demo")
    claude_old_session(machine, demo, "s-old-1", 3)                                  # 3 testes (15 XP) em 3 janelas de ofício (3 XP)
    claude_old_session(machine, demo, "s-old-2", 1)                                  # 1 teste (5 XP) em 1 janela (1 XP)
    machine.codex(demo)                                                              # um rollout sem comando de teste: 0 XP
    registry = LocalRegistry(machine.home / "orb")
    observatory = machine.observatory()
    past = PastXp(observatory.leaders, observatory.past, registry, wall=lambda: NOW)
    hub = Hub(observatory, names=registry, xp=registry, past=past, clock=lambda: NOW)
    hub.poll_once()                                                                  # a primeira varredura do índice
    assert past.progress()["state"] == "waiting"
    run_all(past)
    _applied, changed = hub.poll_once()
    snapshot = hub.snapshot()
    assert changed is True and snapshot["xp_past"]["state"] == "done" and snapshot["xp_past"]["total"] == 3
    (realm,) = [r for r in snapshot["realms"] if r["id"] == "demo"]
    assert realm["xp"]["total"] == 24 and snapshot["mankind"]["xp"]["by_provider"]["claude"] == 24
    assert realm["alter_egos"] == [] or all(not e["in_room"] for e in realm["alter_egos"])      # o passado não vira personagem na sala
    assert hub.xp_report()["sessions"] == {"total": 3, "with_xp": 2, "zero": 1}


def test_the_hub_reports_a_change_when_only_the_progress_moved_and_not_otherwise(machine):
    demo = machine.project("demo")
    claude_old_session(machine, demo, "s-old-1", 1)
    registry = LocalRegistry(machine.home / "orb")
    observatory = machine.observatory()
    past = PastXp(observatory.leaders, observatory.past, registry, wall=lambda: NOW)
    hub = Hub(observatory, names=registry, xp=registry, past=past, clock=lambda: NOW)
    hub.poll_once()
    hub.poll_once()
    assert hub.poll_once()[1] is False                                              # nada mudou: ninguém precisa de um mundo novo
    past.run_once()
    assert hub.poll_once()[1] is True                                               # o indicador andou: os clientes veem


def test_a_hub_without_the_past_reading_has_no_indicator_and_nothing_changes(machine):
    hub = Hub(machine.observatory())
    assert "xp_past" not in hub.snapshot()


def test_an_old_commit_that_never_reached_the_main_branch_expires_and_a_recent_one_waits_for_the_git(machine):
    demo = machine.project("demo")
    sha_old, sha_new = "a" * 40, "b" * 40
    entries = [{"type": "user", "uuid": "u0", "cwd": str(demo), "timestamp": "2026-08-15T10:59:00Z", "message": {"content": "oi"}}]
    for n, (sha, day) in enumerate([(sha_old, "2026-08-15"), (sha_new, "2026-10-27")]):
        entries += [
            {"type": "assistant", "uuid": f"a{n}", "timestamp": f"{day}T11:00:01Z", "message": {"id": f"m{n}", "content": [
                {"type": "tool_use", "id": f"t{n}", "name": "Bash", "input": {"command": "git commit -m x"}}], "stop_reason": "tool_use"}},
            {"type": "user", "uuid": f"u{n}", "timestamp": f"{day}T11:00:05Z", "toolUseResult": {"interrupted": False, "gitOperation": {"commit": {"sha": sha}}},
             "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{n}", "content": "ok"}]}},
        ]
    path = transcript(machine.home, str(demo), "s-c", entries)
    os.utime(path, (time.time() - 90 * 86400, time.time() - 90 * 86400))
    registry = LocalRegistry(machine.home / "orb")
    observatory = machine.observatory()
    past = PastXp(observatory.leaders, observatory.past, registry, wall=lambda: NOW)
    hub = Hub(observatory, names=registry, xp=registry, past=past, clock=lambda: NOW)
    hub.poll_once()
    run_all(past)
    hub.poll_once()
    states = {e.ref: e.state for e in registry.entries_of("claude:s-c", 1)}
    assert states == {sha_old: "expired", sha_new: "provisional"}                    # passou de 30 dias: expira sozinho; o recente espera o git
    assert [q["key"] for q in hub.world.pending_commits("demo", NOW)] == [sha_new]  # o Probe dos commits vai conferir só o recente
    assert hub.snapshot()["mankind"]["xp"]["provisional"] == 10


def test_reading_the_past_changes_nothing_in_the_files_of_the_providers(machine):
    demo = machine.project("demo")
    path = claude_old_session(machine, demo, "s-old-1", 2)
    before = (path.stat().st_size, path.stat().st_mtime_ns, path.read_bytes())
    registry = LocalRegistry(machine.home / "orb")
    observatory = machine.observatory()
    past = PastXp(observatory.leaders, observatory.past, registry, wall=lambda: NOW)
    Hub(observatory, names=registry, xp=registry, past=past, clock=lambda: NOW).poll_once()
    run_all(past)
    assert (path.stat().st_size, path.stat().st_mtime_ns, path.read_bytes()) == before         # R16: só leitura
