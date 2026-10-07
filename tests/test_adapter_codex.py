import asyncio
import json
import time
from pathlib import Path

from orb.adapters.codex import AppServerObserver, AppServerTranslator, RolloutReader
from orb.core import World
from orb.protocol import validate

TID = "019a0000-0000-7000-8000-000000000001"


def note(method, **params):
    return {"jsonrpc": "2.0", "method": method, "params": params}


def item(method, item_obj, **extra):
    key = "startedAtMs" if method == "item/started" else "completedAtMs"
    return note(method, item=item_obj, threadId=TID, turnId="turn1", **{key: 1_760_000_000_000}, **extra)


def test_turn_flow_keeps_codex_vocabulary():
    t = AppServerTranslator("demo")
    msgs = [
        note("thread/started", thread={"id": TID, "cwd": "C:/proj", "model": "gpt-5.6-luna", "parentThreadId": None}),
        note("turn/started", threadId=TID, turn={"id": "turn1"}),
        item("item/started", {"type": "userMessage", "id": "i1", "content": [{"type": "text", "text": "leia o MVP"}]}),
        item("item/completed", {"type": "agentMessage", "id": "i2", "text": "Vou ler o arquivo…", "phase": "commentary"}),
        item("item/started", {"type": "commandExecution", "id": "i3", "command": "Get-Content docs/MVP.md",
                              "commandActions": [{"type": "unknown", "command": "Get-Content docs/MVP.md"}], "status": "inProgress"}),
        note("item/commandExecution/outputDelta", threadId=TID, turnId="turn1", itemId="i3", delta="..."),
        item("item/completed", {"type": "commandExecution", "id": "i3", "command": "Get-Content docs/MVP.md",
                                "aggregatedOutput": "# MVP", "exitCode": 0, "status": "completed", "commandActions": []}),
        item("item/completed", {"type": "reasoning", "id": "i4", "summary": [], "content": []}),
        item("item/completed", {"type": "reasoning", "id": "i5", "summary": ["Plano: ler e resumir"], "content": []}),
        note("thread/tokenUsage/updated", threadId=TID, turnId="turn1", tokenUsage={
            "last": {"inputTokens": 100, "outputTokens": 20, "cachedInputTokens": 50, "reasoningOutputTokens": 5, "totalTokens": 120},
            "total": {"inputTokens": 100, "outputTokens": 20, "cachedInputTokens": 50, "reasoningOutputTokens": 5, "totalTokens": 120}}),
        note("turn/completed", threadId=TID, turn={"id": "turn1"}),
    ]
    events = [e for e in (t.translate(m) for m in msgs) if e is not None]
    assert all(validate(e) is None for e in events)
    assert [e["native"]["kind"] for e in events] == [
        "thread/started", "turn/started", "item/started:userMessage", "item/completed:agentMessage",
        "item/started:commandExecution", "item/completed:commandExecution", "item/completed:reasoning",
        "item/completed:reasoning", "thread/tokenUsage/updated", "turn/completed"]
    by = {e["native"]["kind"] + str(i): e for i, e in enumerate(events)}
    assert events[2]["inner"] == {"role": "prompt", "text": "leia o MVP"} and events[2]["signal"] is None
    assert events[4]["signal"]["activity"] == "READING" and events[4]["inner"]["text"] == "Get-Content docs/MVP.md"
    assert events[6]["inner"] is None and events[6]["signal"]["activity"] == "THINKING"   # sem summary
    assert events[7]["inner"]["fidelity"] == "summary"
    assert events[8]["signal"]["reasoning_tokens"] == 5
    assert events[9]["signal"] == {"type": "idle"}
    assert len(by) == len(events)


def test_approval_requests_become_waiting_and_resolution_clears_it():
    t = AppServerTranslator("demo")
    t.translate(note("thread/started", thread={"id": TID}))
    request = {"jsonrpc": "2.0", "id": 7, "method": "item/commandExecution/requestApproval",
               "params": {"threadId": TID, "turnId": "turn1", "itemId": "i3", "startedAtMs": 1, "command": "git push"}}
    world = World()
    world.apply(t.translate(request))
    assert world.snapshot()["mankind"]["waiting"] == 1
    world.apply(t.translate(note("serverRequest/resolved", threadId=TID, requestId=7)))
    assert world.snapshot()["mankind"]["waiting"] == 0


def test_waiting_flag_from_thread_status():
    t = AppServerTranslator("demo")
    waiting = t.translate(note("thread/status/changed", threadId=TID, status={"type": "active", "activeFlags": ["waitingOnApproval"]}))
    assert waiting["signal"]["type"] == "waiting"
    resolved = t.translate(note("thread/status/changed", threadId=TID, status={"type": "idle"}))
    assert resolved["signal"]["type"] == "waiting.resolved"


def test_two_identical_waits_are_two_facts():
    t = AppServerTranslator("demo")
    world = World()
    for status in ({"type": "active", "activeFlags": ["waitingOnApproval"]}, {"type": "idle"},
                   {"type": "active", "activeFlags": ["waitingOnApproval"]}):
        world.apply(t.translate(note("thread/status/changed", threadId=TID, status=status)))
    assert world.snapshot()["mankind"]["waiting"] == 1


def test_subagent_threads_join_the_parent_team():
    t = AppServerTranslator("demo")
    t.translate(note("thread/started", thread={"id": TID}))
    child = t.translate(note("thread/started", thread={"id": "child-1", "parentThreadId": TID, "agentRole": "explorer"}))
    assert child["alter_ego"] == f"codex:{TID}" and child["agent"] == "child-1"
    assert child["signal"] == {"type": "subagent.started", "kind": "explorer", "parent": None}
    grandchild = t.translate(note("thread/started", thread={"id": "child-2", "parentThreadId": "child-1"}))
    assert grandchild["alter_ego"] == f"codex:{TID}" and grandchild["signal"]["parent"] == "child-1"


def test_messages_without_thread_and_responses_are_ignored():
    t = AppServerTranslator("demo")
    assert t.translate({"jsonrpc": "2.0", "id": 1, "result": {}}) is None
    assert t.translate(note("account/rateLimits/updated", rateLimits={})) is None
    assert t.translate("lixo") is None


class FakeConn:
    def __init__(self):
        self.sent = []

    async def send(self, data):
        self.sent.append(json.loads(data))

    async def recv(self):
        await asyncio.sleep(3600)


def test_observer_never_answers_server_requests():
    async def scenario():
        conn, got = FakeConn(), []
        obs = AppServerObserver(conn, AppServerTranslator("demo"), got.append)
        await obs.start()
        before = len(conn.sent)
        await obs.handle(json.dumps({"jsonrpc": "2.0", "id": 99, "method": "item/commandExecution/requestApproval",
                                     "params": {"threadId": TID, "turnId": "t", "itemId": "i", "startedAtMs": 1}}))
        await obs.handle(json.dumps({"jsonrpc": "2.0", "id": 100, "method": "item/tool/requestUserInput",
                                     "params": {"threadId": TID}}))
        await obs.handle("{nao json")
        return conn, got, obs, before

    conn, got, obs, before = asyncio.run(scenario())
    assert len(conn.sent) == before                          # nenhuma resposta, nem recusa
    assert not any("result" in m or "error" in m for m in conn.sent)
    assert obs.ignored_requests == 2 and got[0]["signal"]["type"] == "waiting"


def test_observer_subscribes_to_new_threads():
    async def scenario():
        conn = FakeConn()
        obs = AppServerObserver(conn, AppServerTranslator("demo"), lambda e: None)
        await obs.handle(json.dumps(note("thread/started", thread={"id": TID})))
        await obs.handle(json.dumps(note("thread/started", thread={"id": TID})))
        return conn

    conn = asyncio.run(scenario())
    assert [m["method"] for m in conn.sent] == ["thread/resume"]


# --- nível 0: rollouts ---------------------------------------------------------------------

def rollout(tmp_path: Path, name: str, entries, jsonl):
    path = tmp_path / ".codex" / "sessions" / "2026" / "10" / "07" / f"rollout-2026-10-07T10-00-00-{name}.jsonl"
    jsonl(path, entries)
    return path


def meta(thread_id, cwd, parent=None):
    payload = {"id": thread_id, "cwd": cwd, "cli_version": "0.160.1", "timestamp": "2026-10-07T10:00:00Z"}
    if parent:
        payload.update(parent_thread_id=parent, agent_role="explorer")
    return {"timestamp": "2026-10-07T10:00:00Z", "ordinal": 0, "type": "session_meta", "payload": payload}


def line(ordinal, etype, payload, **extra):
    return {"timestamp": "2026-10-07T10:00:01Z", "ordinal": ordinal, "type": etype, "payload": payload, **extra}


def test_rollout_reader_translates_verified_structure(tmp_path, jsonl):
    cwd = r"C:\proj\demo"
    rollout(tmp_path, TID, [
        meta(TID, cwd),
        line(1, "response_item", {"type": "message", "role": "developer", "content": [{"type": "input_text", "text": "instruções"}]}),
        line(2, "response_item", {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "<environment_context>x"}]}),
        line(3, "response_item", {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "leia o MVP"}]},
             metadata={"client_authored": False, "user_input_order": 1}),
        line(4, "event_msg", {"type": "task_started", "turn_id": "t1"}),
        line(41, "turn_context", {"model": "gpt-5.6-luna", "cwd": cwd, "effort": "medium"}),
        line(42, "turn_context", {"model": "gpt-5.6-luna", "cwd": cwd, "effort": "medium"}),   # sem mudança: nada
        line(5, "response_item", {"type": "reasoning", "summary": [{"type": "summary_text", "text": "Plano"}], "encrypted_content": "zzz"}),
        line(6, "response_item", {"type": "custom_tool_call", "name": "exec", "input": "Get-Content docs/MVP.md", "call_id": "c1"}),
        line(7, "response_item", {"type": "custom_tool_call_output", "call_id": "c1", "output": "# MVP"}),
        line(8, "response_item", {"type": "message", "role": "assistant", "phase": "final_answer", "content": [{"type": "output_text", "text": "MVP"}]}),
        line(9, "token_usage_record", {"usage": {"input_tokens": 9, "output_tokens": 2, "cached_input_tokens": 1, "reasoning_output_tokens": 0}}),
        line(10, "event_msg", {"type": "token_count", "info": {}}),
        line(11, "event_msg", {"type": "task_complete", "turn_id": "t1"}),
    ], jsonl)
    rollout(tmp_path, "other", [meta("other", r"C:\outra\pasta")], jsonl)
    events = RolloutReader(cwd, realm="demo", since=time.time() - 5, home=tmp_path).poll()
    assert all(validate(e) is None for e in events)
    assert [e["native"]["kind"] for e in events] == [
        "session_meta", "response_item/message", "response_item/message", "event_msg/task_started",
        "turn_context", "response_item/reasoning", "response_item/custom_tool_call", "response_item/custom_tool_call_output",
        "response_item/message", "token_usage_record", "event_msg/task_complete"]
    assert events[1]["inner"]["role"] == events[2]["inner"]["role"] == "prompt"   # como o Codex gravou
    assert events[4]["signal"] == {"type": "session.updated", "model": "gpt-5.6-luna"}
    assert "encrypted_content" not in events[5]["native"]["body"]
    assert events[6]["signal"]["activity"] == "READING"
    assert {e["alter_ego"] for e in events} == {f"codex:{TID}"}


def test_rollout_subagent_and_start_from_end(tmp_path, jsonl):
    cwd = r"C:\proj\demo"
    rollout(tmp_path, TID, [meta(TID, cwd)], jsonl)
    child = rollout(tmp_path, "child", [meta("child", cwd, parent=TID)], jsonl)
    r = RolloutReader(cwd, realm="demo", since=time.time() - 5, home=tmp_path)
    events = r.poll()
    sub = next(e for e in events if e["agent"] == "child")
    assert sub["alter_ego"] == f"codex:{TID}" and sub["signal"]["type"] == "subagent.started"
    jsonl(child, [line(1, "event_msg", {"type": "task_complete"})], append=True)
    assert [e["native"]["kind"] for e in r.poll()] == ["event_msg/task_complete"]
