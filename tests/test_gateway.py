import base64
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
    config = GatewayConfig(cwd=str(tmp_path), token="tok", home=tmp_path, poll_seconds=0.05)
    ptys = []

    def factory(*args):
        ptys.append(FakePty())
        return ptys[-1]

    client = TestClient(create_app(config, pty_factory=factory, check_installed=False))
    with pytest.raises(Exception):
        with client.websocket_connect("/ws?token=errado", headers={"origin": "http://127.0.0.1"}) as ws:
            ws.receive_json()
    with client.websocket_connect("/ws?token=tok&provider=claude", headers={"origin": "http://127.0.0.1"}) as ws:
        info = ws.receive_json()
        assert info["channel"] == "system" and info["info"] == "provider=claude"
        assert ws.receive_json()["channel"] == "world"
        ws.send_text('{"type":"input","data":"oi"}')
        ws.send_text("lixo")
        assert ws.receive_json() == {"channel": "system", "error": "mensagem não é JSON válido"}
    assert ptys[0].written[0].startswith("claude --session-id ") and "oi" in ptys[0].written
    with client.websocket_connect("/ws?token=tok&provider=auto&model=a%20b", headers={"origin": "http://127.0.0.1"}) as ws:
        assert "não foi possível abrir" in ws.receive_json()["error"]
    assert len(ptys) == 1                                     # modelo inválido não abriu terminal
