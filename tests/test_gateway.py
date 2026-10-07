import base64
import json
import time

import pytest

from orb.gateway import GatewayConfig, authorized, create_app, handle_client_message

pytest.importorskip("httpx", reason="TestClient do FastAPI precisa de httpx")
from fastapi.testclient import TestClient  # noqa: E402


class _FakeTerm:
    def __init__(self):
        self.written, self.size = [], None

    def write(self, data):
        self.written.append(data)

    def resize(self, cols, rows):
        self.size = (cols, rows)


def test_client_messages_are_validated_and_never_raise():
    t = _FakeTerm()
    assert handle_client_message(t, '{"type":"input","data":"ls"}') is None
    assert handle_client_message(t, '{"type":"input","data_b64":"%s"}' % base64.b64encode(b"\x1b[?1004h").decode()) is None
    assert t.written == ["ls", "\x1b[?1004h"]
    assert handle_client_message(t, '{"type":"resize","cols":90,"rows":28}') is None and t.size == (90, 28)
    for bad in ['{"type":"input","data":"a\x1bb"}', "não é json", "[]", "null", '{"type":"input"}',
                '{"type":"input","data_b64":"@@@"}', '{"type":"resize","cols":0,"rows":5}',
                '{"type":"resize","cols":"9","rows":5}', '{"type":"resize","cols":true,"rows":5}',
                '{"type":"rm"}', "x" * 1_000_001, None]:
        assert handle_client_message(t, bad), bad
    assert t.written == ["ls", "\x1b[?1004h"] and t.size == (90, 28)


def test_authorization_requires_token_and_local_origin():
    assert authorized("tok", "tok", "http://127.0.0.1:8765")
    assert authorized("tok", "tok", "http://localhost")
    assert not authorized("tok", "errado", "http://127.0.0.1")
    assert not authorized("tok", "tok", "https://evil.example")
    assert not authorized("tok", "tok", None)
    assert not authorized("tok", None, "http://127.0.0.1")


class FakePty:
    def __init__(self, *args):
        self.written, self.alive = [], True

    def read(self, size):
        time.sleep(0.01)
        return ""

    def write(self, data):
        self.written.append(data)

    def isalive(self):
        return self.alive

    def setwinsize(self, rows, cols):
        pass

    def terminate(self, force=False):
        self.alive = False


def test_websocket_session_with_fake_terminal(tmp_path):
    config = GatewayConfig(realms=[str(tmp_path)], token="tok", home=tmp_path, poll_seconds=0.05)
    ptys = []

    def factory(*args):
        ptys.append(FakePty())
        return ptys[-1]

    with TestClient(create_app(config, pty_factory=factory, check_installed=False)) as client:
        with pytest.raises(Exception):
            with client.websocket_connect("/ws?token=errado", headers={"origin": "http://127.0.0.1"}) as ws:
                ws.receive_json()
        with client.websocket_connect("/ws?token=tok&provider=claude", headers={"origin": "http://127.0.0.1"}) as ws:
            info = ws.receive_json()
            assert info["channel"] == "system" and info["info"] == "provider=claude"
            assert info["alter_ego"].startswith("claude:")            # o terminal sabe qual personagem é
            ws.send_text('{"type":"input","data":"oi"}')
            ws.send_text("lixo")
            assert ws.receive_json() == {"channel": "system", "error": "mensagem não é JSON válido"}
        assert ptys[0].written[0].startswith("claude --session-id ") and "oi" in ptys[0].written
        with client.websocket_connect("/ws?token=tok&provider=auto&model=a%20b", headers={"origin": "http://127.0.0.1"}) as ws:
            assert "não foi possível abrir" in ws.receive_json()["error"]
        assert len(ptys) == 1                                     # modelo inválido não abriu terminal


def _claude_session(home, cwd, sid, title):
    from orb.adapters.claude import project_dir
    folder = project_dir(cwd, home=home)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{sid}.jsonl").write_text(
        json.dumps({"type": "custom-title", "customTitle": title, "sessionId": sid}) + "\n" +
        json.dumps({"type": "assistant", "uuid": "a1", "timestamp": "2026-10-07T10:00:00Z",
                    "message": {"id": "m1", "model": "claude-opus-5-5", "content": [
                        {"type": "tool_use", "id": "t1", "name": "Edit", "input": {"file_path": "app.py"}}]}}) + "\n",
        encoding="utf-8")


def _codex_session(home, cwd, tid):
    path = home / ".codex" / "sessions" / "2026" / "10" / "07" / f"rollout-2026-10-07T10-00-00-{tid}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"timestamp": "2026-10-07T10:00:00Z", "ordinal": 0, "type": "session_meta",
                                "payload": {"id": tid, "cwd": cwd}}) + "\n", encoding="utf-8")


def test_one_realm_shows_claude_and_codex_sessions_at_the_same_time(tmp_path):
    """O Alter Ego identifica o próprio provider: num mesmo realm, Claude e Codex juntos."""
    from orb.gateway import Hub, build_observers
    project = r"C:\p\TOTEM INTEGRADOR"        # a pasta não precisa existir: só identifica o realm
    other = r"C:\p\Outro"
    _claude_session(tmp_path, project, "11111111-1111-4111-8111-111111111111", "Integração do totem")
    _codex_session(tmp_path, project, "019a0000-0000-7000-8000-000000000001")
    _claude_session(tmp_path, other, "22222222-2222-4222-8222-222222222222", "Outro projeto")
    hub = Hub(build_observers([project, other], home=tmp_path))
    hub.poll_once()
    realms = {r["id"]: r for r in hub.snapshot()["realms"]}
    assert set(realms) == {"totem-integrador", "outro"}
    egos = {e["provider"]: e for e in realms["totem-integrador"]["alter_egos"]}
    assert set(egos) == {"claude", "codex"}
    assert egos["claude"]["title"] == "Integração do totem" and egos["claude"]["model"] == "claude-opus-5-5"
    assert egos["claude"]["state"] == "CODING" and egos["claude"]["last_action"] == "Edit app.py"
    assert realms["totem-integrador"]["name"] == "TOTEM INTEGRADOR"


def test_world_stream_sends_snapshot_and_inner_world(tmp_path):
    project = r"C:\p\proj"
    _claude_session(tmp_path, project, "11111111-1111-4111-8111-111111111111", "Sessão A")
    config = GatewayConfig(realms=[project], token="tok", home=tmp_path, poll_seconds=0.05)
    with TestClient(create_app(config, check_installed=False)) as client:
        with pytest.raises(Exception):
            with client.websocket_connect("/world?token=tok", headers={"origin": "https://evil.example"}) as ws:
                ws.receive_json()
        with client.websocket_connect("/world?token=tok", headers={"origin": "http://127.0.0.1"}) as ws:
            seen = []
            deadline = time.time() + 5
            while time.time() < deadline:
                msg = ws.receive_json()
                seen.append(msg["channel"])
                if msg["channel"] == "world" and msg["world"]["realms"][0]["alter_egos"]:
                    ego = msg["world"]["realms"][0]["alter_egos"][0]
                    assert ego["title"] == "Sessão A" and ego["provider"] == "claude"
                    break
            else:
                raise AssertionError(seen)
            ws.send_text(json.dumps({"type": "feed", "alter_ego": ego["id"]}))
            while True:
                msg = ws.receive_json()
                if msg["channel"] == "feed":
                    assert [e["native"]["kind"] for e in msg["events"]] == ["assistant/tool_use"]
                    break
