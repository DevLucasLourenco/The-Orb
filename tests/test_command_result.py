"""O resultado de um comando e o Weather (R42, R49, D-076, D-084): amostras dos quatro CLIs -> `command.result` -> céu do realm."""
import json
import time
from datetime import UTC, datetime, timedelta

import pytest

from orb.adapters import _shared
from orb.adapters.codex import AppServerTranslator, RolloutReader
from orb.adapters.hermes import StateDbReader
from orb.adapters.opencode import OpencodeDbReader
from orb.core import World, rules
from orb.protocol import make_event, validate

from . import test_adapter_claude as claude
from . import test_adapter_codex as codex
from . import test_adapter_hermes as hermes
from . import test_adapter_opencode as opencode

NOW = datetime(2026, 10, 15, 12, 0, 0, tzinfo=UTC)


def result_events(events):
    return [e for e in events if (e.get("signal") or {}).get("type") == "command.result"]


# --- o vocabulário --------------------------------------------------------------------------------------------

def session_event(signal, *, ts="2026-10-15T11:00:00Z", ego="claude:s1", key="1", realm="the-orb", agent=None):
    return make_event(id=f"{ego}:{key}", ts=ts, provider="claude", source="claude/transcript", realm=realm, alter_ego=ego,
                      agent=agent, seq=1, kind="user/tool_result", body={}, signal=signal)


def test_the_command_result_signal_has_a_closed_shape():
    ok = {"type": "command.result", "ok": True, "exit_code": 0, "activity": "TESTING"}
    assert validate(session_event(ok)) is None
    assert validate(session_event({"type": "command.result", "ok": False})) is None               # o Claude não dá o código
    for bad in ({"type": "command.result"}, {"type": "command.result", "ok": "sim"}, {"type": "command.result", "ok": 1},
                {"type": "command.result", "ok": True, "exit_code": True}, {"type": "command.result", "ok": True, "exit_code": 1.5},
                {"type": "command.result", "ok": True, "activity": "VOANDO"}):
        assert validate(session_event(bad)) is not None, bad


def test_the_shared_builder_classifies_the_command_and_keeps_the_code_only_when_the_provider_gave_it():
    assert _shared.result_signal("python -m pytest -q", ok=False, exit_code=1) == {
        "type": "command.result", "ok": False, "exit_code": 1, "activity": "TESTING"}
    assert _shared.result_signal("git status", ok=True) == {"type": "command.result", "ok": True, "activity": "READING"}
    assert _shared.result_signal(None, ok=True)["activity"] == "EXECUTING"


# --- Claude: `is_error` e `interrupted`, sem código -----------------------------------------------------------------

def claude_events(tmp_path, jsonl, command="python -m pytest -q", *, is_error=False, interrupted=None, tool="Bash", use_id="t1"):
    result = {"type": "user", "uuid": "u2", "timestamp": "2026-10-15T11:00:05Z",
              "message": {"content": [{"type": "tool_result", "tool_use_id": use_id, "content": "saída", "is_error": is_error}]}}
    if interrupted is not None:
        result["toolUseResult"] = {"stdout": "", "stderr": "", "interrupted": interrupted}
    jsonl(claude.session_file(tmp_path), [
        {"type": "assistant", "uuid": "a1", "timestamp": "2026-10-15T11:00:01Z", "message": {"id": "m1", "content": [
            {"type": "tool_use", "id": "t1", "name": tool, "input": {"command": command, "file_path": "x"}}], "stop_reason": "tool_use"}},
        result,
    ])
    events = claude.reader(tmp_path).poll()
    assert all(validate(e) is None for e in events)
    return events


def test_claude_marks_a_passed_test_run_without_inventing_an_exit_code(tmp_path, jsonl):
    [result] = result_events(claude_events(tmp_path, jsonl))
    assert result["signal"] == {"type": "command.result", "ok": True, "activity": "TESTING"}
    assert result["native"]["kind"] == "user/tool_result" and result["inner"]["role"] == "result"      # a linha do Inner World segue


def test_claude_failure_is_is_error_or_interrupted(tmp_path, jsonl):
    assert result_events(claude_events(tmp_path, jsonl, is_error=True))[0]["signal"]["ok"] is False
    short = tmp_path / "b"
    short.mkdir()
    assert result_events(claude_events(short, jsonl, interrupted=True))[0]["signal"]["ok"] is False


def test_claude_marks_other_shell_commands_with_their_own_activity_and_ignores_the_rest(tmp_path, jsonl):
    one = tmp_path / "c"
    one.mkdir()
    assert result_events(claude_events(one, jsonl, "git status"))[0]["signal"]["activity"] == "READING"
    two = tmp_path / "d"
    two.mkdir()
    assert result_events(claude_events(two, jsonl, tool="Read")) == []                         # não é comando de shell
    three = tmp_path / "e"
    three.mkdir()
    assert result_events(claude_events(three, jsonl, use_id="outro")) == []                    # resultado sem a chamada: nada se afirma


# --- Codex: `exitCode` no app-server e `item.exit_code` no rollout ----------------------------------------------------------

def test_codex_app_server_result_carries_the_exit_code():
    t = AppServerTranslator("demo")
    t.translate(codex.note("thread/started", thread={"id": codex.TID, "cwd": "C:/proj", "parentThreadId": None}))

    def done(command, code, **extra):
        return t.translate(codex.item("item/completed", {"type": "commandExecution", "id": f"i{code}", "command": command,
                                                          "aggregatedOutput": "x", "exitCode": code, "status": "completed", **extra}))

    failed, passed = done("python -m pytest -q", 1), done("python -m pytest -q", 0)
    assert failed["signal"] == {"type": "command.result", "ok": False, "exit_code": 1, "activity": "TESTING"}
    assert passed["signal"]["ok"] is True and passed["signal"]["exit_code"] == 0
    running = t.translate(codex.item("item/completed", {"type": "commandExecution", "id": "i9", "command": "pytest",
                                                         "aggregatedOutput": "", "status": "inProgress"}))
    assert running["signal"] is None                                                           # sem código, nada se afirma
    assert validate(failed) is None and failed["inner"]["role"] == "result"


def test_codex_rollout_item_completed_becomes_a_result_with_the_exit_code(tmp_path, jsonl):
    cwd = r"C:\proj\demo"
    command = {"type": "CommandExecution", "id": "x1", "command": ["powershell.exe", "-Command", "python -m pytest -q"], "exit_code": 2,
               "status": "failed", "aggregated_output": "falhou", "stdout": "grande", "stderr": ""}
    codex.rollout(tmp_path, codex.TID, [
        codex.meta(codex.TID, cwd),
        codex.line(1, "event_msg", {"type": "item_completed", "item": command, "thread_id": codex.TID, "turn_id": "t1"}),
        codex.line(2, "event_msg", {"type": "item_completed", "item": {"type": "Reasoning", "id": "r1"}}),
        codex.line(3, "event_msg", {"type": "item_completed", "item": {**command, "id": "x2", "exit_code": None}}),
    ], jsonl)
    events = RolloutReader(cwd, realm="demo", since=time.time() - 5, home=tmp_path).poll()
    assert all(validate(e) is None for e in events)
    [result] = result_events(events)
    assert result["signal"] == {"type": "command.result", "ok": False, "exit_code": 2, "activity": "TESTING"}
    assert "stdout" not in json.dumps(result["native"])                                        # a saída grande não vai no nativo
    assert [e["native"]["kind"] for e in events].count("event_msg/item_completed") == 1        # só o que tem código de saída


# --- Hermes: `exit_code` no JSON do resultado do `terminal` -----------------------------------------------------------------

def test_hermes_terminal_result_carries_the_exit_code_and_is_matched_to_its_call(tmp_path):
    home = tmp_path / "hermes"
    conn = hermes.make_db(home)
    conn.execute("INSERT INTO sessions VALUES ('S1', 'cli', 'm', NULL, ?, 't', 0, NULL)", (hermes.CWD,))
    r = StateDbReader(hermes.CWD, realm="demo", home=home)
    assert r.poll() == []
    call = lambda cid, command: [{"id": cid, "type": "function", "function": {"name": "terminal", "arguments": json.dumps({"command": command})}}]
    hermes.add(conn, "S1", "assistant", "rodando", tool_calls=call("c1", "pytest -q") + call("c2", "git status"))
    for cid, content in (("c1", json.dumps({"output": "1 failed", "exit_code": 1})), ("c2", json.dumps({"output": "", "exit_code": 0})),
                         ("c3", json.dumps({"exit_code": 0})), ("c1", "texto que não é JSON")):
        conn.execute("INSERT INTO messages (session_id, role, content, tool_call_id, timestamp, active) VALUES ('S1', 'tool', ?, ?, 1760000000.0, 1)",
                     (content, cid))
    conn.commit()
    events = r.poll()
    assert all(validate(e) is None for e in events)
    got = [e["signal"] for e in result_events(events)]
    assert got == [{"type": "command.result", "ok": False, "exit_code": 1, "activity": "TESTING"},
                   {"type": "command.result", "ok": True, "exit_code": 0, "activity": "READING"}]    # c3 sem chamada e o texto cru: nada


# --- opencode: `state.metadata.exit` do `bash` --------------------------------------------------------------------------------

def test_opencode_bash_result_carries_the_exit_code(tmp_path):
    db = opencode.Db(opencode.make_db(tmp_path / "opencode"))
    db.session("ses_root1")
    r = OpencodeDbReader(opencode.CWD, realm="demo", data_dir=tmp_path / "opencode")
    assert r.poll() == []

    def tool(tid, name, status, command, metadata=None):
        state = {"status": status, "input": {"command": command}, "content": "saída"}
        if metadata is not None:
            state["metadata"] = metadata
        return {"type": "tool", "id": tid, "name": name, "time": {}, "state": state}

    db.put("msg_a", "ses_root1", "assistant", {"content": [
        tool("t1", "bash", "completed", "pytest -q", {"exit": 1}),
        tool("t2", "bash", "completed", "pytest -q", {"exit": 0}),
        tool("t3", "bash", "error", "pytest -q"),                       # sem código: vale o estado
        tool("t4", "read", "completed", "x", {"exit": 0}),              # não é shell
        tool("t5", "bash", "running", "pytest -q", {})],                # ainda não terminou
        "time": {"created": 3}}, seq=1)
    events = r.poll()
    assert all(validate(e) is None for e in events)
    assert [e["signal"] for e in result_events(events)] == [
        {"type": "command.result", "ok": False, "exit_code": 1, "activity": "TESTING"},
        {"type": "command.result", "ok": True, "exit_code": 0, "activity": "TESTING"},
        {"type": "command.result", "ok": False, "activity": "TESTING"}]


# --- o mundo: o último teste de cada realm vira o Weather -------------------------------------------------------------------------

def a_result(ok, *, ts="2026-10-15T11:00:00Z", ego="claude:s1", key="1", realm="the-orb", exit_code=None, activity="TESTING", agent=None):
    signal = {"type": "command.result", "ok": ok, "activity": activity}
    if exit_code is not None:
        signal["exit_code"] = exit_code
    return session_event(signal, ts=ts, ego=ego, key=key, realm=realm, agent=agent)


def weather(world, realm="the-orb", now=NOW):
    return next(r for r in world.snapshot(now)["realms"] if r["id"] == realm)["weather"]


def test_a_passed_test_run_is_a_clear_sky_and_a_failed_one_is_rain():
    world = World()
    world.apply(a_result(True))
    assert weather(world) == {"sky": "clear", "at": "2026-10-15T11:00:00Z", "exit_code": None, "alter_ego": "claude:s1"}
    world.apply(a_result(False, ts="2026-10-15T11:05:00Z", key="2", exit_code=1))
    assert weather(world) == {"sky": "rain", "at": "2026-10-15T11:05:00Z", "exit_code": 1, "alter_ego": "claude:s1"}


def test_only_the_last_test_run_counts_and_a_late_one_does_not_go_back_in_time():
    world = World()
    world.apply(a_result(False, ts="2026-10-15T11:05:00Z", key="new"))
    world.apply(a_result(True, ts="2026-10-15T10:00:00Z", key="old"))                 # chegou atrasado
    assert weather(world)["sky"] == "rain"
    world.apply(a_result(True, ts="2026-10-15T11:30:00Z", key="newer", ego="codex:s2"))      # outra sessão do mesmo realm
    assert weather(world) == {"sky": "clear", "at": "2026-10-15T11:30:00Z", "exit_code": None, "alter_ego": "codex:s2"}


def test_a_command_that_is_not_a_test_run_never_changes_the_weather():
    world = World()
    world.apply(a_result(False, activity="READING"))
    world.apply(a_result(False, activity="EXECUTING", key="2"))
    assert weather(world) is None                                                          # sem dado: nada, nunca céu inventado


def test_a_subagent_test_run_counts_for_the_realm_too():
    world = World()
    world.apply(a_result(False, agent="a1"))
    assert weather(world)["sky"] == "rain"


def test_a_result_older_than_the_room_window_is_no_longer_weather_and_without_a_clock_nothing_is_said():
    world = World()
    world.apply(a_result(True, ts="2026-10-04T11:00:00Z"))                              # 11 dias antes de NOW
    assert weather(world) is None
    world.apply(a_result(True, ts="2026-10-06T11:00:00Z", key="2"))                     # 9 dias: ainda vale
    assert weather(world)["sky"] == "clear"
    assert world.snapshot()["realms"][0]["weather"] is None                                # sem hora, nada que dependa do tempo
    assert rules.RECENT_SESSION_SECONDS == timedelta(days=10).total_seconds()


def test_the_weather_follows_the_room_window_the_lucas_chose():
    world = World(recent_seconds=2 * 24 * 3600)
    world.apply(a_result(True, ts="2026-10-12T11:00:00Z"))                              # 3 dias
    assert weather(world) is None
    world.set_recent_seconds(5 * 24 * 3600)
    assert weather(world)["sky"] == "clear"


def test_a_realm_without_a_test_run_has_no_weather_and_hidden_realms_leave_the_snapshot():
    world = World()
    world.add_realm("the-orb")
    assert weather(world) is None
    world.apply(a_result(False, realm="the-orb"))
    world.set_hidden({"the-orb"})
    assert world.snapshot(NOW)["realms"] == []


@pytest.mark.parametrize("seen", [0, 1])
def test_the_command_result_does_not_change_what_the_character_is_doing(seen):
    world = World()
    world.apply(session_event({"type": "activity", "activity": "TESTING"}, key="a"))
    if seen:
        world.apply(a_result(False))
    ego = world.snapshot(NOW)["realms"][0]["alter_egos"][0]
    assert ego["state"] == "TESTING" and ego["area"] == "Testing Lab"


def test_the_end_of_the_weather_window_is_a_time_only_change_so_the_clients_are_told():
    world = World()
    world.apply(a_result(True, ts="2026-10-06T11:00:00Z"))
    before = world.time_key(NOW)
    assert world.time_key(NOW) == before
    assert world.time_key(NOW + timedelta(days=2)) != before                         # o céu limpo passou do prazo da sala
