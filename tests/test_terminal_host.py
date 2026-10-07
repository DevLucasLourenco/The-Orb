import time

import pytest

from orb.terminal_host import (HostedTerminal, InvalidLaunchValue, Launch, ProviderNotInstalled,
                               UnknownProvider, available_providers, clean_env, resolve_provider)

SID = "00000000-0000-4000-8000-000000000001"


class FakePty:
    def __init__(self):
        self.written, self.size, self.alive = [], None, True

    def read(self, size):
        time.sleep(0.01)
        return ""

    def write(self, data):
        self.written.append(data)

    def isalive(self):
        return self.alive

    def setwinsize(self, rows, cols):
        self.size = (rows, cols)

    def terminate(self, force=False):
        self.alive = False


def test_resolve_provider_from_model_name():
    assert resolve_provider(model="claude-opus-5-5") == "claude"
    assert resolve_provider(model="Sonnet 5.5") == "claude"
    assert resolve_provider(model="gpt-5.6-luna") == "codex"
    assert resolve_provider(model="hermes-3") == "hermes"
    assert resolve_provider(provider="codex", model="claude-x") == "codex"       # explícito vence
    with pytest.raises(UnknownProvider):
        resolve_provider(model="modelo-desconhecido")
    with pytest.raises(UnknownProvider):
        resolve_provider(provider="rm -rf")


def test_launch_lines_only_from_controlled_values():
    assert Launch("claude", session_id=SID, session_name="orb-abc").line() == f"claude --session-id {SID} -n orb-abc"
    assert Launch("claude", session_id=SID, resume=True).line() == f"claude --resume {SID}"
    assert Launch("claude", model="claude-opus-5-5").line() == "claude --model claude-opus-5-5"
    assert Launch("codex", model="gpt-5.6-luna").line() == "codex -m gpt-5.6-luna"
    assert Launch("codex", remote_url="ws://127.0.0.1:8780").line() == "codex --remote ws://127.0.0.1:8780"
    assert Launch("hermes").line() == "hermes"
    with pytest.raises(UnknownProvider):
        Launch("calc.exe & del *").line()


@pytest.mark.parametrize("launch", [
    Launch("claude", model="opus; Remove-Item -Recurse C:\\"),
    Launch("claude", model="x`whoami`"),
    Launch("claude", session_name="a b"),
    Launch("claude", session_id="nao-e-uuid"),
    Launch("codex", remote_url="ws://evil.example:80"),
])
def test_injection_attempts_are_refused(launch):
    with pytest.raises(InvalidLaunchValue):
        launch.line()


def test_clean_env_removes_inherited_markers_but_keeps_user_config():
    env = clean_env({"CLAUDE_CODE_CHILD_SESSION": "1", "CLAUDECODE": "1", "ANTHROPIC_API_KEY": "k",
                     "CLAUDE_CODE_USE_BEDROCK": "1", "PATH": "p"})
    assert env == {"ANTHROPIC_API_KEY": "k", "CLAUDE_CODE_USE_BEDROCK": "1", "PATH": "p"}


def test_terminal_types_the_cli_line_into_a_real_shell_process():
    fake = FakePty()
    seen = {}

    def factory(argv, cwd, env, dims):
        seen.update(argv=argv, cwd=cwd, dims=dims, env=env)
        return fake

    term = HostedTerminal(cwd="C:/p", launch=Launch("claude", session_id=SID), pty_factory=factory, check_installed=False)
    term.start()
    term.resize(90, 28)
    term.close()
    assert "powershell" in seen["argv"][0].lower() or "pwsh" in seen["argv"][0].lower()
    assert fake.written == [f"claude --session-id {SID}\r"] and fake.size == (28, 90)
    assert "CLAUDECODE" not in seen["env"]


def test_invalid_launch_never_opens_a_process():
    opened = []
    term = HostedTerminal(cwd=".", launch=Launch("claude", model="a b"), pty_factory=lambda *a: opened.append(a),
                          check_installed=False)
    with pytest.raises(InvalidLaunchValue):
        term.start()
    assert opened == []


def test_not_installed_provider_is_reported(monkeypatch):
    import orb.terminal_host.terminal as terminal_module

    monkeypatch.setattr(terminal_module, "available_providers", lambda: {"claude": True, "codex": True, "hermes": False})
    opened = []
    with pytest.raises(ProviderNotInstalled):
        HostedTerminal(cwd=".", launch=Launch("hermes"), pty_factory=lambda *a: opened.append(a)).start()
    assert opened == []


def test_available_providers_reports_every_known_cli():
    assert set(available_providers()) == {"claude", "codex", "hermes"}


def test_real_terminal_opens_shell_without_cli():
    pytest.importorskip("winpty", reason="pywinpty não instalado")
    chunks = []
    term = HostedTerminal(cwd=".", on_output=chunks.append)
    term.start()
    time.sleep(1.5)
    term.write("echo ORB_OK" + chr(13))
    deadline = time.time() + 8
    while time.time() < deadline and "ORB_OK" not in "".join(chunks).replace("echo ORB_OK", ""):
        time.sleep(0.1)
    term.close()
    assert "ORB_OK" in "".join(chunks)
