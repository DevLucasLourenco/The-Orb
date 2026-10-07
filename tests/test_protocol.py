import json

from orb.protocol import MAX_BODY_BYTES, MAX_INNER_TEXT, clip_body, make_event, validate


def _event(**over):
    base = dict(id="claude:s1:u1#0", ts="2026-10-07T10:00:00Z", provider="claude", source="claude/transcript",
                realm="the-orb", alter_ego="claude:s1", agent=None, seq=1, kind="assistant/tool_use",
                body={"name": "Read", "input": {"file_path": "a.py"}})
    base.update(over)
    return make_event(**base)


def test_valid_event_keeps_native_intact():
    event = _event(inner={"origin": "agent", "role": "tool", "text": "Read a.py"},
                   signal={"type": "activity", "activity": "READING", "target": "a.py"})
    assert validate(event) is None
    assert event["native"] == {"kind": "assistant/tool_use", "body": {"name": "Read", "input": {"file_path": "a.py"}},
                               "truncated": False}


def test_signal_vocabulary_is_closed():
    assert validate(_event(signal={"type": "algo.novo"})) is not None
    assert validate(_event(signal={"type": "activity", "activity": "DANCING"})) is not None
    assert validate(_event(signal={"type": "activity"})) is not None          # falta o campo
    assert validate(_event(signal={"type": "human.input", "kind": "prompt", "channel": "fax"})) is not None


def test_thought_requires_fidelity_and_inferred_is_not_allowed():
    assert validate(_event(inner={"origin": "agent", "role": "thought", "text": "x"})) is not None
    assert validate(_event(inner={"origin": "agent", "role": "thought", "text": "x", "fidelity": "inferred"})) is not None
    assert validate(_event(inner={"origin": "agent", "role": "thought", "text": "x", "fidelity": "summary"})) is None


def test_invalid_shapes_are_rejected_without_raising():
    for bad in [None, [], {"v": "9.0"}, {**_event(), "seq": -1}, {**_event(), "seq": True},
                {**_event(), "native": {"kind": "", "body": {}}}, {**_event(), "id": ""}]:
        assert validate(bad), bad


def test_big_bodies_are_clipped_but_keep_keys():
    body = {"output": "x" * 100_000, "items": ["y" * 5000] * 50, "name": "Bash"}
    clipped, truncated = clip_body(body)
    assert truncated
    assert set(clipped) == {"output", "items", "name"} and clipped["name"] == "Bash"
    assert len(json.dumps(clipped).encode()) <= MAX_BODY_BYTES


def test_inner_text_is_clipped():
    event = _event(inner={"origin": "agent", "role": "narration", "text": "z" * 10_000})
    assert len(event["inner"]["text"]) == MAX_INNER_TEXT and event["inner"]["text"].endswith("…")
