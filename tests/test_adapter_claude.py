import json
import time
from pathlib import Path

import pytest

from orb.adapters.claude import HookTranslator, TranscriptReader, encode_cwd, project_dir, session_settings
from orb.core import World
from orb.protocol import validate

CWD = r"C:\proj\demo"
SID = "11111111-1111-4111-8111-111111111111"


def reader(tmp_path, **kw):
    return TranscriptReader(CWD, realm="demo", session_id=kw.pop("session_id", SID),
                            since=time.time() - 5, home=tmp_path, **kw)


def session_file(tmp_path, sid=SID) -> Path:
    return project_dir(CWD, home=tmp_path) / f"{sid}.jsonl"


def kinds(events):
    return [e["native"]["kind"] for e in events]


def test_encode_cwd_matches_claude_folder_names():
    assert encode_cwd(r"C:\Users\x\Documents\Sistemas e Projetos\The Orb") == "C--Users-x-Documents-Sistemas-e-Projetos-The-Orb"


def test_native_kinds_inner_and_signals(tmp_path, jsonl):
    jsonl(session_file(tmp_path), [
        {"type": "user", "uuid": "u1", "timestamp": "2026-10-07T10:00:00Z", "origin": {"kind": "human"},
         "message": {"content": "leia o MVP"}},
        {"type": "assistant", "uuid": "a1", "timestamp": "2026-10-07T10:00:01Z", "message": {"id": "m1", "content": [
            {"type": "thinking", "thinking": "", "signature": "sig"},
            {"type": "text", "text": "Vou ler."},
            {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "docs/MVP.md"}}],
            "usage": {"input_tokens": 10, "output_tokens": 3, "cache_read_input_tokens": 7}, "stop_reason": "tool_use"}},
        {"type": "assistant", "uuid": "a2", "timestamp": "2026-10-07T10:00:01Z", "message": {"id": "m1", "content": [],
            "usage": {"input_tokens": 10, "output_tokens": 3}}},     # mesma mensagem: usage repetido
        {"type": "user", "uuid": "u2", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "# MVP"}]}},
        {"type": "assistant", "uuid": "a3", "message": {"id": "m2", "content": [{"type": "text", "text": "Pronto."}],
                                                        "stop_reason": "end_turn"}},
    ])
    events = reader(tmp_path).poll()
    assert all(validate(e) is None for e in events)
    assert kinds(events) == ["user/text", "assistant/text", "assistant/tool_use", "assistant/usage",
                             "user/tool_result", "assistant/text", "assistant/stop"]
    by_kind = {e["native"]["kind"]: e for e in events}
    assert by_kind["user/text"]["inner"] == {"role": "prompt", "text": "leia o MVP"}
    assert by_kind["user/text"]["signal"] is None
    assert by_kind["user/text"]["native"]["body"]["origin"] == {"kind": "human"}      # nativo intacto
    tool = by_kind["assistant/tool_use"]
    assert tool["native"]["body"]["name"] == "Read"                  # nativo intacto
    assert tool["inner"]["text"] == "Read docs/MVP.md"
    assert tool["signal"] == {"type": "activity", "activity": "READING", "target": "docs/MVP.md"}
    assert by_kind["assistant/usage"]["signal"]["cache_read_tokens"] == 7
    assert by_kind["assistant/stop"]["signal"] == {"type": "idle"}
    assert {e["alter_ego"] for e in events} == {f"claude:{SID}"}


def test_empty_thinking_is_not_a_thought_but_text_is_raw(tmp_path, jsonl):
    jsonl(session_file(tmp_path), [{"type": "assistant", "uuid": "a1", "message": {"content": [
        {"type": "thinking", "thinking": "", "signature": "x"},
        {"type": "thinking", "thinking": "pensando", "signature": "y"}]}}])
    events = reader(tmp_path).poll()
    assert len(events) == 1
    assert events[0]["inner"] == {"role": "thought", "text": "pensando", "fidelity": "raw"}
    assert "signature" not in events[0]["native"]["body"]


@pytest.mark.parametrize("entry", [
    {"origin": {"kind": "human"}, "message": {"content": "oi"}},
    {"message": {"content": [{"type": "text", "text": "oi"}]}},
    {"origin": {"kind": "task-notification"}, "message": {"content": "<task-notification>x"}},
    {"origin": {"kind": "peer"}, "isMeta": True, "message": {"content": "outra sessão"}},
])
def test_user_messages_appear_as_the_session_recorded_them(tmp_path, jsonl, entry):
    """O Orb não classifica quem escreveu (ADR 0003): toda mensagem `user` aparece como é."""
    jsonl(session_file(tmp_path), [{"type": "user", "uuid": "u1", **entry}])
    (event,) = reader(tmp_path).poll()
    assert event["native"]["kind"] == "user/text" and event["inner"]["role"] == "prompt"
    assert event["signal"] is None


def test_partial_lines_invalid_json_and_incremental_reads(tmp_path):
    path = session_file(tmp_path)
    path.parent.mkdir(parents=True)
    line = json.dumps({"type": "user", "uuid": "u1", "origin": {"kind": "human"}, "message": {"content": "oi"}}).encode()
    path.write_bytes(line[:10])
    r = reader(tmp_path)
    assert r.poll() == []
    path.write_bytes(line + b"\nlixo nao json\n")
    assert kinds(r.poll()) == ["user/text"]
    assert r.poll() == []                                                     # nada lido duas vezes


def test_session_id_isolates_other_sessions_and_old_files_are_ignored(tmp_path, jsonl):
    line = [{"type": "user", "uuid": "u1", "origin": {"kind": "human"}, "message": {"content": "oi"}}]
    jsonl(session_file(tmp_path), line)
    jsonl(session_file(tmp_path, "22222222-2222-4222-8222-222222222222"), line)
    assert len(reader(tmp_path).poll()) == 1
    observer = TranscriptReader(CWD, realm="demo", since=time.time() - 5, home=tmp_path)
    assert {e["alter_ego"] for e in observer.poll()} == {f"claude:{SID}", "claude:22222222-2222-4222-8222-222222222222"}
    future = TranscriptReader(CWD, realm="demo", since=time.time() + 100, home=tmp_path)
    assert future.poll() == []


def test_subagent_joins_the_team_and_ends_with_foreground_result(tmp_path, jsonl):
    folder = project_dir(CWD, home=tmp_path) / SID / "subagents"
    jsonl(folder / "agent-ab12.jsonl", [
        {"type": "user", "uuid": "s1", "isSidechain": True, "message": {"content": "conte os .md"}},
        {"type": "assistant", "uuid": "s2", "isSidechain": True, "message": {"content": [
            {"type": "tool_use", "id": "t9", "name": "Glob", "input": {"pattern": "*.md"}}]}}])
    (folder / "agent-ab12.meta.json").write_text(json.dumps(
        {"agentType": "Explore", "description": "contar", "toolUseId": "tA", "requestShape": "foreground", "spawnDepth": 1}))
    jsonl(session_file(tmp_path), [
        {"type": "assistant", "uuid": "a1", "message": {"content": [{"type": "tool_use", "id": "tA", "name": "Agent", "input": {}}]}},
        {"type": "user", "uuid": "u2", "message": {"content": [{"type": "tool_result", "tool_use_id": "tA", "content": "3"}]}}])
    events = reader(tmp_path).poll()
    world = World()
    for event in events:
        world.apply(event)
    (ego,) = world.snapshot()["realms"][0]["alter_egos"]
    (sub,) = ego["team"]
    assert sub["id"] == "ab12" and sub["kind"] == "Explore" and sub["active"] is False
    sub_events = [e for e in events if e["agent"] == "ab12"]
    assert sub_events[0]["signal"]["type"] == "subagent.started"


def test_hook_settings_are_observer_only_and_per_session():
    settings = session_settings(8770)
    for name, groups in settings["hooks"].items():
        hook = groups[0]["hooks"][0]
        assert hook["type"] == "command" and hook["async"] is True
        assert "-m 1" in hook["command"] and "127.0.0.1:8770" in hook["command"]


def test_hook_translation_with_verified_fields():
    t = HookTranslator("demo")
    base = {"session_id": SID, "transcript_path": "x", "cwd": CWD, "prompt_id": "p"}
    pre = t.translate("PreToolUse", {**base, "tool_name": "Bash", "tool_input": {"command": "pytest -q"}, "tool_use_id": "t1"})
    assert pre["signal"]["activity"] == "TESTING" and pre["native"]["kind"] == "PreToolUse"
    ask = t.translate("PermissionRequest", {**base, "tool_name": "Bash", "tool_input": {"command": "git push"}})
    assert ask["signal"]["type"] == "waiting"
    done = t.translate("PostToolUse", {**base, "tool_name": "Bash", "tool_response": {}, "tool_use_id": "t2"})
    assert done["signal"] == {"type": "waiting.resolved", "request": ask["signal"]["request"], "decision": "approved", "deduced": True}
    sys_prompt = t.translate("UserPromptSubmit", {**base, "prompt": "<task-notification>fim</task-notification>"})
    assert sys_prompt["signal"] is None and sys_prompt["inner"]["role"] == "prompt"
    sub = t.translate("PreToolUse", {**base, "agent_id": "ag1", "agent_type": "Explore", "tool_name": "Read",
                                     "tool_input": {"file_path": "a"}, "tool_use_id": "t3"})
    assert sub["agent"] == "ag1"
    assert t.translate("Stop", {"no": "session"}) is None
    world = World()
    for _ in range(2):                                          # dois pedidos iguais, em sequência
        world.apply(t.translate("PermissionRequest", {**base, "tool_name": "Edit", "tool_input": {"file_path": "a"}}))
        assert world.snapshot()["mankind"]["waiting"] == 1
        world.apply(t.translate("PostToolUse", {**base, "tool_name": "Edit", "tool_response": {}}))
        assert world.snapshot()["mankind"]["waiting"] == 0
