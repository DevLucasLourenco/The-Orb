"""A evidência de commit (ticket 23, R53, D-084, D-090, PROGRESSION.md X-COMMIT): o sinal `command.result` leva `commit` quando o comando
fez um commit. Claude: o `gitOperation.commit` do resultado, com o hash; os outros: um `git commit` que deu certo, sem hash."""
import pytest

from orb.adapters import _shared
from orb.adapters.codex.mapping import command_result
from orb.protocol import make_event, validate

from . import test_adapter_claude as claude


@pytest.mark.parametrize("command", [
    "git commit -m 'ajusta'", "git add -A && git commit -m x", "git add . ; git commit -am x", "git -C repo commit -m x",
    "git commit --amend --no-edit", 'powershell.exe -NoProfile -Command "git add .; git commit -m x"', "bash -lc 'git commit -m x'",
    "cd proj && git -c user.name=x commit -m y", "GIT_AUTHOR_NAME=x git commit -m y", "git commit",
])
def test_a_git_commit_command_is_recognised(command):
    assert _shared.is_git_commit(command) is True


@pytest.mark.parametrize("command", [
    None, "", "git status", "git log --grep commit", "echo git commit", "git commit --dry-run -m x", "git commit-tree abc",
    "git show HEAD~1", "pytest -q", "git push origin main", "gh pr create", "git config commit.gpgsign false",
])
def test_what_is_not_a_commit_is_not_recognised(command):
    assert _shared.is_git_commit(command) is False


def test_a_command_that_committed_carries_the_commit_and_one_that_failed_does_not():
    assert _shared.result_signal("git commit -m x", ok=True)["commit"] == {}                    # sem hash: o provider não diz qual
    assert "commit" not in _shared.result_signal("git commit -m x", ok=False)                   # falhou: nada foi commitado
    assert "commit" not in _shared.result_signal("pytest -q", ok=True)
    assert _shared.result_signal(None, ok=True, commit=True, sha="abc1234")["commit"] == {"sha": "abc1234"}
    assert "commit" not in _shared.result_signal("git commit -m x", ok=True, commit=False)       # o provider disse que não: vale o que ele disse


def event(signal):
    return make_event(id="claude:s1:1", ts="2026-10-15T11:00:00Z", provider="claude", source="claude/transcript", realm="the-orb",
                      alter_ego="claude:s1", agent=None, seq=1, kind="user/tool_result", body={}, signal=signal)


@pytest.mark.parametrize("commit, valid", [
    ({}, True), ({"sha": "abc1234"}, True), ({"sha": "A" * 40}, True), ({"sha": "f" * 64}, True),
    ({"sha": "abc"}, False), ({"sha": "xyz1234"}, False), ({"sha": 12345678}, False), ({"sha": "a" * 65}, False),
    ("abc1234", False), ([], False), (True, False),
])
def test_the_commit_field_is_an_object_with_an_optional_hexadecimal_hash(commit, valid):
    signal = {"type": "command.result", "ok": True, "commit": commit}
    assert (validate(event(signal)) is None) is valid


def claude_commit_events(tmp_path, jsonl, git_operation, *, command="git commit -m x", is_error=False):
    result = {"type": "user", "uuid": "u2", "timestamp": "2026-10-15T11:00:05Z",
              "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "saída", "is_error": is_error}]}}
    if git_operation is not None:
        result["toolUseResult"] = {"stdout": "", "stderr": "", "interrupted": False, "gitOperation": git_operation}
    jsonl(claude.session_file(tmp_path), [
        {"type": "assistant", "uuid": "a1", "timestamp": "2026-10-15T11:00:01Z", "message": {"id": "m1", "content": [
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": command}}], "stop_reason": "tool_use"}},
        result,
    ])
    events = claude.reader(tmp_path).poll()
    assert all(validate(e) is None for e in events)
    [signal] = [e["signal"] for e in events if (e.get("signal") or {}).get("type") == "command.result"]
    return signal


def test_claude_takes_the_commit_and_its_hash_from_the_git_operation_not_from_the_command(tmp_path, jsonl):
    signal = claude_commit_events(tmp_path, jsonl, {"commit": {"sha": "0123456789abcdef0123456789abcdef01234567", "kind": "committed", "branch": "main"}})
    assert signal["commit"] == {"sha": "0123456789abcdef0123456789abcdef01234567"}


def test_claude_does_not_guess_a_commit_from_the_command_text_without_the_git_operation(tmp_path, jsonl):
    assert "commit" not in claude_commit_events(tmp_path, jsonl, None)                          # D-090: nada de interpretar o comando
    assert "commit" not in claude_commit_events(tmp_path / "b", jsonl, {"push": {"branch": "main"}}, command="git push")


def test_claude_ignores_a_git_operation_hash_that_is_not_a_hash_and_a_failed_commit(tmp_path, jsonl):
    assert claude_commit_events(tmp_path, jsonl, {"commit": {"sha": "nao-e-hash"}})["commit"] == {}      # houve commit, mas sem hash confiável
    assert "commit" not in claude_commit_events(tmp_path / "b", jsonl, {"commit": {"sha": "abc1234"}}, is_error=True)


def test_codex_app_server_sees_a_commit_command_with_its_text():
    item = {"type": "commandExecution", "id": "c1", "command": "git commit -m x", "exitCode": 0, "status": "completed"}
    assert command_result(item)["commit"] == {}
    assert "commit" not in command_result({**item, "exitCode": 1})
