"""Testes do spike 01. Rodar: python -m pytest -q  (dentro de spikes/01-terminal-host)"""
import json
import time
from pathlib import Path

import pytest

from terminal_host import (HostedTerminal, ProviderNotInstalled, UnknownProvider, available_providers,
                           build_cli_line, resolve_provider)
from transcript_tail import TranscriptTail, encode_cwd, project_dir, translate

REAL_PROJECTS = Path.home() / ".claude" / "projects"


def test_encode_cwd_matches_claude_folder_names():
    cwd = r"C:\Users\lucas\OneDrive\Documentos\Github Repo\Orb IA"
    assert encode_cwd(cwd) == "C--Users-lucas-OneDrive-Documentos-Github-Repo-Orb-IA"


def test_translate_prompt_tool_and_text():
    prompt = {"type": "user", "timestamp": "t", "sessionId": "s", "origin": {"kind": "human"},
              "message": {"content": "faça X"}}
    assert [e["type"] for e in translate(prompt)] == ["intrusive_thought"]

    tool = {"type": "assistant", "timestamp": "t", "sessionId": "s", "message": {"content": [
        {"type": "tool_use", "id": "u1", "name": "Edit", "input": {"file_path": "a.py"}},
        {"type": "text", "text": "ok"}]}}
    evs = list(translate(tool))
    assert [e["type"] for e in evs] == ["tool.started", "agent.message"]
    assert evs[0]["payload"]["category"] == "write"


def test_empty_thinking_emits_no_thought():
    entry = {"type": "assistant", "message": {"content": [{"type": "thinking", "thinking": "", "signature": "x"}]}}
    assert list(translate(entry)) == []


def test_unknown_entries_are_ignored():
    assert list(translate({"type": "cost-state"})) == []
    assert list(translate({"type": "algo-novo", "x": 1})) == []


def test_tail_handles_partial_lines_and_invalid_json(tmp_path):
    cwd = r"C:\proj\demo"
    folder = project_dir(cwd, home=tmp_path)
    folder.mkdir(parents=True)
    f = folder / "ses1.jsonl"
    tail = TranscriptTail(cwd=cwd, since=time.time() - 5, home=tmp_path)

    line1 = json.dumps({"type": "user", "origin": {"kind": "human"}, "message": {"content": "oi"}}).encode()
    f.write_bytes(line1[:10])                      # linha parcial
    assert tail.poll() == []
    f.write_bytes(line1 + b"\nlixo nao json\n")    # completa + linha inválida
    evs = tail.poll()
    assert [e["type"] for e in evs] == ["intrusive_thought"]


def test_tail_with_session_id_ignores_other_sessions(tmp_path):
    cwd = r"C:\proj\demo"
    folder = project_dir(cwd, home=tmp_path)
    folder.mkdir(parents=True)
    line = json.dumps({"type": "user", "origin": {"kind": "human"}, "message": {"content": "oi"}}) + "\n"
    (folder / "minha.jsonl").write_text(line)
    (folder / "outra.jsonl").write_text(line)
    tail = TranscriptTail(cwd=cwd, since=time.time() - 5, home=tmp_path, session_id="minha")
    assert len(tail.poll()) == 1


def test_clean_env_removes_inherited_markers_but_keeps_user_config():
    from terminal_host import clean_env
    env = clean_env({"CLAUDE_CODE_CHILD_SESSION": "1", "CLAUDECODE": "1",
                     "ANTHROPIC_API_KEY": "k", "CLAUDE_CODE_USE_BEDROCK": "1", "PATH": "p"})
    assert env == {"ANTHROPIC_API_KEY": "k", "CLAUDE_CODE_USE_BEDROCK": "1", "PATH": "p"}


def test_tail_ignores_old_transcripts(tmp_path):
    cwd = r"C:\proj\demo"
    folder = project_dir(cwd, home=tmp_path)
    folder.mkdir(parents=True)
    (folder / "old.jsonl").write_text(json.dumps({"type": "user", "message": {"content": "x"}}) + "\n")
    tail = TranscriptTail(cwd=cwd, since=time.time() + 100, home=tmp_path)
    assert tail.poll() == []


@pytest.mark.skipif(not REAL_PROJECTS.exists(), reason="sem transcripts reais")
def test_real_transcripts_translate_without_errors():
    total, types = 0, set()
    for f in list(REAL_PROJECTS.glob("*/*.jsonl"))[:6]:
        for raw in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            for ev in translate(entry):
                total += 1
                types.add(ev["type"])
    assert total > 0
    assert "tool.started" in types and "intrusive_thought" in types


class _FakeTerm:
    def __init__(self):
        self.written, self.size = [], None

    def write(self, data):
        self.written.append(data)

    def resize(self, cols, rows):
        self.size = (cols, rows)


def test_client_messages_are_validated_and_never_raise():
    import base64
    from server import handle_client_message
    t = _FakeTerm()
    assert handle_client_message(t, '{"type":"input","data":"ls"}') is None
    assert handle_client_message(t, '{"type":"input","data_b64":"%s"}' % base64.b64encode(b"\x1b[?1004h").decode()) is None
    assert t.written == ["ls", "\x1b[?1004h"]
    assert handle_client_message(t, '{"type":"resize","cols":90,"rows":28}') is None and t.size == (90, 28)
    # mensagens ruins: descartadas com motivo, sem exceção e sem tocar o terminal
    for bad in ['{"type":"input","data":"a\x1bb"}', "não é json", "[]", "null", '{"type":"input"}',
                '{"type":"input","data_b64":"@@@"}', '{"type":"resize","cols":0,"rows":5}',
                '{"type":"resize","cols":"9","rows":5}', '{"type":"rm"}', "x" * 1_000_001]:
        assert handle_client_message(t, bad), bad
    assert t.written == ["ls", "\x1b[?1004h"] and t.size == (90, 28)


def test_resolve_provider_from_model_name():
    assert resolve_provider(model="claude-opus-5-5") == "claude"
    assert resolve_provider(model="Sonnet 5.5") == "claude"
    assert resolve_provider(model="gpt-5-codex") == "codex"
    assert resolve_provider(model="hermes-3") == "hermes"
    assert resolve_provider(provider="codex", model="claude-x") == "codex"   # explícito vence
    with pytest.raises(UnknownProvider):
        resolve_provider(model="modelo-desconhecido")
    with pytest.raises(UnknownProvider):
        resolve_provider(provider="rm -rf")


def test_cli_line_only_from_controlled_values():
    assert build_cli_line("claude", "abc-123", "orb-abc") == "claude --session-id abc-123 -n orb-abc"
    assert build_cli_line("codex") == "codex"
    with pytest.raises(UnknownProvider):
        build_cli_line("calc.exe & del *")


def test_not_installed_provider_is_reported():
    if available_providers()["hermes"]:
        pytest.skip("hermes instalado nesta máquina")
    with pytest.raises(ProviderNotInstalled):
        HostedTerminal(cwd=".", provider="hermes").start()


def test_real_terminal_opens_shell_without_cli():
    chunks = []
    term = HostedTerminal(cwd=".", provider=None, on_output=chunks.append)
    term.start()
    time.sleep(1.5)
    term.write("echo ORB_OK" + chr(13))
    deadline = time.time() + 6
    while time.time() < deadline and "ORB_OK" not in "".join(chunks).replace("echo ORB_OK", ""):
        time.sleep(0.1)
    term.close()
    assert "ORB_OK" in "".join(chunks)


@pytest.mark.skipif(not available_providers()["claude"], reason="claude não instalado")
def test_terminal_calls_claude_automatically():
    """O terminal abre e chama o claude sozinho; o CLI sobe e o terminal continua vivo."""
    chunks = []
    term = HostedTerminal(cwd=".", provider="claude", session_id="00000000-0000-4000-8000-000000000001",
                          session_name="orb-teste", on_output=chunks.append)
    term.start()
    deadline = time.time() + 20
    while time.time() < deadline and "Claude Code" not in "".join(chunks):
        time.sleep(0.2)
    alive = term.alive()
    term.close()
    assert "Claude Code" in "".join(chunks)
    assert alive
