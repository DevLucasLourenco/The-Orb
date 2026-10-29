"""A leitura única do passado nos quatro adapters (ticket 25, R48 camada 3, D-088, D-108): uma sessão antiga inteira, com a Team dela, do começo ao fim,
em lotes, só leitura. Ponto de teste: os leitores dos CLIs com históricos sintéticos (a forma verificada; nenhum dado real)."""
import json
import os
import time

import pytest

from orb.adapters._shared import family
from orb.adapters._shared import jsonl as jsonl_module
from orb.adapters._shared.index import SessionMeta
from orb.adapters.claude import TranscriptIndex, TranscriptPast
from orb.adapters.codex import RolloutIndex, RolloutPast
from orb.adapters.hermes import StateDbIndex, StateDbPast
from orb.adapters.opencode import OpencodeDbIndex, OpencodeDbPast
from orb.protocol import validate

from . import test_adapter_claude as claude
from . import test_adapter_codex as codex
from . import test_adapter_hermes as hermes
from . import test_adapter_opencode as opencode
from .test_command_result import result_events

LONG_AGO = time.time() - 90 * 86400            # muito antes da sala de 10 dias: é passado


def flat(batches):
    return [event for batch in batches for event in batch]


def passed_tests(events):
    """Os resultados de teste que passaram, na ordem em que o provider os gravou."""
    return [e for e in result_events(events) if e["signal"].get("activity") == "TESTING" and e["signal"]["ok"]]


# --- família: a sessão e as sub-sessões dela ---------------------------------------------------------------------------------

def test_a_session_family_is_the_session_and_every_descendant_and_nothing_else():
    def meta(sid, parent=None):
        return SessionMeta(provider="codex", session_id=sid, cwd="c", parent_id=parent)
    metas = [meta("a"), meta("b", "a"), meta("c", "b"), meta("x"), meta("y", "x")]
    mine = family(metas[0], metas)
    assert mine[0].session_id == "a" and {m.session_id for m in mine} == {"a", "b", "c"}
    assert {m.session_id for m in family(meta("x"), metas)} == {"x", "y"}


# --- Claude -----------------------------------------------------------------------------------------------------------------

def old_transcript(tmp_path, jsonl, sid=claude.SID, runs=3):
    entries = [{"type": "user", "uuid": "u0", "cwd": claude.CWD, "timestamp": "2026-08-15T10:59:00Z", "message": {"content": "rode os testes"}}]
    for n in range(runs):
        entries += [
            {"type": "assistant", "uuid": f"a{n}", "timestamp": f"2026-08-15T11:{n:02d}:01Z", "message": {"id": f"m{n}", "content": [
                {"type": "tool_use", "id": f"t{n}", "name": "Bash", "input": {"command": "pytest -q"}}], "stop_reason": "tool_use"}},
            {"type": "user", "uuid": f"u{n}", "timestamp": f"2026-08-15T11:{n:02d}:05Z",
             "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{n}", "content": "ok"}]}},
        ]
    jsonl(claude.session_file(tmp_path, sid), entries)
    path = claude.session_file(tmp_path, sid)
    os.utime(path, (LONG_AGO, LONG_AGO))
    return path


def claude_meta(tmp_path, sid=claude.SID):
    (found,) = [m for m in TranscriptIndex(home=tmp_path).scan() if m.session_id == sid]
    return found


def test_claude_reads_an_old_transcript_from_the_first_line_to_the_last_with_its_subagents(tmp_path, jsonl):
    old_transcript(tmp_path, jsonl)
    folder = claude.session_file(tmp_path).parent / claude.SID / "subagents"
    jsonl(folder / "agent-a1.jsonl", [{"type": "assistant", "uuid": "s1", "timestamp": "2026-08-15T11:30:00Z", "message": {"id": "ms1", "content": [
        {"type": "text", "text": "feito"}], "stop_reason": "end_turn"}}])
    events = flat(TranscriptPast(tmp_path).read(claude_meta(tmp_path), "demo"))
    assert all(validate(e) is None for e in events)
    assert len(passed_tests(events)) == 3 and {e["alter_ego"] for e in events} == {f"claude:{claude.SID}"}
    assert any(e["agent"] == "a1" for e in events)                                  # a Team vem junto
    assert events[0]["native"]["kind"] == "transcript/session"


def test_claude_reads_only_the_asked_session(tmp_path, jsonl):
    other = "22222222-2222-4222-8222-222222222222"
    old_transcript(tmp_path, jsonl, runs=2)
    old_transcript(tmp_path, jsonl, sid=other, runs=5)
    assert len(passed_tests(flat(TranscriptPast(tmp_path).read(claude_meta(tmp_path), "demo")))) == 2        # as 5 da outra sessão ficam de fora


def test_claude_reads_a_big_transcript_in_several_bounded_batches_without_losing_or_repeating_anything(tmp_path, jsonl, monkeypatch):
    old_transcript(tmp_path, jsonl, runs=40)
    monkeypatch.setattr(jsonl_module, "READ_CHUNK", 1500)                           # cada leitura pega poucos bytes
    batches = list(TranscriptPast(tmp_path).read(claude_meta(tmp_path), "demo"))
    assert len(batches) > 3
    events = flat(batches)
    assert len(passed_tests(events)) == 40 and len({e["id"] for e in events}) == len(events)


def test_claude_session_that_vanished_is_reported_so_that_it_is_not_marked_as_read(tmp_path, jsonl):
    path = old_transcript(tmp_path, jsonl)
    meta = claude_meta(tmp_path)
    path.unlink()
    with pytest.raises(FileNotFoundError):
        flat(TranscriptPast(tmp_path).read(meta, "demo"))


# --- Codex --------------------------------------------------------------------------------------------------------------------

CHILD = "019a0000-0000-7000-8000-000000000002"
STRANGER = "019a0000-0000-7000-8000-000000000003"


def commandline(n, thread, ok=True):
    done = {"type": "CommandExecution", "id": f"x{n}", "command": ["pytest", "-q"], "exit_code": 0 if ok else 1, "status": "completed",
            "aggregated_output": "", "stdout": "", "stderr": ""}
    return codex.line(n, "event_msg", {"type": "item_completed", "item": done, "thread_id": thread, "turn_id": "t1"})


def old_rollout(tmp_path, jsonl, thread, parent=None, runs=2, cwd=r"C:\proj\demo"):
    path = codex.rollout(tmp_path, thread, [codex.meta(thread, cwd, parent), *[commandline(n, thread) for n in range(1, runs + 1)]], jsonl)
    os.utime(path, (LONG_AGO, LONG_AGO))
    return path


def test_codex_reads_the_rollout_of_the_session_and_of_its_child_thread_and_no_other(tmp_path, jsonl):
    old_rollout(tmp_path, jsonl, codex.TID, runs=2)
    old_rollout(tmp_path, jsonl, CHILD, parent=codex.TID, runs=3)
    old_rollout(tmp_path, jsonl, STRANGER, runs=7)
    metas = RolloutIndex(tmp_path).scan()
    leader = next(m for m in metas if m.session_id == codex.TID)
    events = flat(RolloutPast(tmp_path).read(leader, "demo"))
    assert all(validate(e) is None for e in events)
    assert len(result_events(events)) == 5                                           # 2 do líder + 3 da thread filha; as 7 da estranha ficam de fora
    assert {e["alter_ego"] for e in events} == {f"codex:{codex.TID}"} and any(e["agent"] == CHILD for e in events)


def test_codex_reads_a_rollout_that_the_room_would_only_follow_from_the_end(tmp_path, jsonl):
    old_rollout(tmp_path, jsonl, codex.TID, runs=4)
    leader = RolloutIndex(tmp_path).scan()[0]
    assert len(result_events(flat(RolloutPast(tmp_path).read(leader, "demo")))) == 4


def test_codex_rollout_that_vanished_is_reported_so_that_it_is_not_marked_as_read(tmp_path, jsonl):
    path = old_rollout(tmp_path, jsonl, codex.TID)
    leader = RolloutIndex(tmp_path).scan()[0]
    path.unlink()
    with pytest.raises(FileNotFoundError):
        flat(RolloutPast(tmp_path).read(leader, "demo"))


# --- Hermes -------------------------------------------------------------------------------------------------------------------

def tool_pair(conn, session, n):
    call = [{"id": f"c{n}", "type": "function", "function": {"name": "terminal", "arguments": json.dumps({"command": "pytest -q"})}}]
    hermes.add(conn, session, "assistant", "rodando", tool_calls=call)
    conn.execute("INSERT INTO messages (session_id, role, content, tool_call_id, timestamp, active) VALUES (?, 'tool', ?, ?, 1760000000.0, 1)",
                 (session, json.dumps({"output": "", "exit_code": 0}), f"c{n}"))
    conn.commit()


def test_hermes_reads_every_message_of_the_session_and_of_its_subagent_session_and_no_other(tmp_path):
    home = tmp_path / "hermes"
    conn = hermes.make_db(home)
    conn.execute("INSERT INTO sessions VALUES ('S1', 'cli', 'm', NULL, ?, 't', 0, NULL)", (hermes.CWD,))
    conn.execute("INSERT INTO sessions VALUES ('S1b', 'subagent', 'm', 'S1', ?, 't', 0, NULL)", (hermes.CWD,))
    conn.execute("INSERT INTO sessions VALUES ('S2', 'cli', 'm', NULL, ?, 't', 0, NULL)", (hermes.CWD,))
    for n in range(2):
        tool_pair(conn, "S1", n)
    tool_pair(conn, "S1b", 10)
    for n in range(20, 26):
        tool_pair(conn, "S2", n)
    leader = next(m for m in StateDbIndex(home).scan() if m.session_id == "S1")
    events = flat(StateDbPast(home).read(leader, "demo"))
    assert all(validate(e) is None for e in events)
    assert len(result_events(events)) == 3 and {e["alter_ego"] for e in events} == {"hermes:S1"}


def test_hermes_reads_a_long_history_in_batches_and_stops_exactly_at_the_end(tmp_path, monkeypatch):
    from orb.adapters.hermes import state_db
    monkeypatch.setattr(state_db, "BATCH", 4)
    home = tmp_path / "hermes"
    conn = hermes.make_db(home)
    conn.execute("INSERT INTO sessions VALUES ('S1', 'cli', 'm', NULL, ?, 't', 0, NULL)", (hermes.CWD,))
    for n in range(8):                                                                # 16 mensagens: um número exato de lotes
        tool_pair(conn, "S1", n)
    leader = StateDbIndex(home).scan()[0]
    batches = list(StateDbPast(home).read(leader, "demo"))
    assert len(batches) >= 4 and len(result_events(flat(batches))) == 8


def test_hermes_without_a_database_gives_nothing_and_does_not_loop(tmp_path):
    meta = SessionMeta(provider="hermes", session_id="S1", cwd=hermes.CWD)
    assert flat(StateDbPast(tmp_path / "nada").read(meta, "demo")) == []


# --- opencode -----------------------------------------------------------------------------------------------------------------

def bash(db, mid, sid, seq):
    state = {"status": "completed", "input": {"command": "pytest -q"}, "content": "ok", "metadata": {"exit": 0}}
    db.put(mid, sid, "assistant", {"content": [{"type": "tool", "id": f"t{mid}", "name": "bash", "time": {}, "state": state}],
                                   "time": {"created": seq}}, seq=seq)


def test_opencode_reads_every_message_of_the_session_and_of_its_child_session_and_no_other(tmp_path):
    db = opencode.Db(opencode.make_db(tmp_path / "opencode"))
    db.session("ses_root1")
    db.session("ses_child1", parent="ses_root1")
    db.session("ses_other")
    for n in range(2):
        bash(db, f"msg_a{n}", "ses_root1", n)
    bash(db, "msg_c", "ses_child1", 5)
    for n in range(6):
        bash(db, f"msg_o{n}", "ses_other", n)
    leader = next(m for m in OpencodeDbIndex(data_dir=tmp_path / "opencode").scan() if m.session_id == "ses_root1")
    events = flat(OpencodeDbPast(tmp_path / "opencode").read(leader, "demo"))
    assert all(validate(e) is None for e in events)
    assert len(result_events(events)) == 3 and {e["alter_ego"] for e in events} == {"opencode:ses_root1"}


def test_opencode_never_touches_the_credential_table_while_reading_the_past(tmp_path):
    db = opencode.Db(opencode.make_db(tmp_path / "opencode"))
    db.session("ses_root1")
    bash(db, "msg_a", "ses_root1", 1)
    seen = []
    original = opencode.state_db.select

    def spy(conn, table, *args, **kwargs):
        seen.append(table)
        return original(conn, table, *args, **kwargs)

    state = pytest.MonkeyPatch()
    state.setattr(opencode.state_db, "select", spy)
    try:
        leader = OpencodeDbIndex(data_dir=tmp_path / "opencode").scan()[0]
        flat(OpencodeDbPast(tmp_path / "opencode").read(leader, "demo"))
    finally:
        state.undo()
    assert seen and set(seen) <= {"session_v2", "session_message"}
