import base64
import json
import time
from pathlib import Path

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
    from orb.gateway import Hub, Observatory
    project = r"C:\p\TOTEM INTEGRADOR"        # a pasta não precisa existir: só identifica o realm
    other = r"C:\p\Outro"
    _claude_session(tmp_path, project, "11111111-1111-4111-8111-111111111111", "Integração do totem")
    _codex_session(tmp_path, project, "019a0000-0000-7000-8000-000000000001")
    _claude_session(tmp_path, other, "22222222-2222-4222-8222-222222222222", "Outro projeto")
    hub = Hub(Observatory([project, other], home=tmp_path))
    hub.poll_once()
    realms = {r["id"]: r for r in hub.snapshot()["realms"]}
    assert set(realms) == {"totem-integrador", "outro"}
    # Um leitor só por loja global (Codex, Hermes, opencode) para a cidade inteira; Claude por realm.
    assert sorted(hub.observatory.readers) == ["claude:outro", "claude:totem-integrador", "codex", "hermes", "opencode"]
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


@pytest.fixture
def short_tmp():
    """Pasta temporária de caminho curto: nomes codificados do Claude estouram os 260 do Windows."""
    import shutil
    import tempfile
    path = Path(tempfile.mkdtemp(prefix="orb")).resolve()
    yield path
    shutil.rmtree(path, ignore_errors=True)


def test_root_makes_every_project_folder_a_realm_and_worktrees_count_for_it(short_tmp):
    from orb.gateway import Hub, Observatory
    tmp_path = short_tmp
    root = tmp_path / "P"
    for name in ("trisafe", "trisafe-enhanced", ".oculta"):
        (root / name).mkdir(parents=True)
    enhanced = str((root / "trisafe-enhanced").resolve())
    trisafe = str((root / "trisafe").resolve())
    worktree = enhanced + r"\.claude\worktrees\distracted-wescoff"
    # Sessão do Claude num worktree do trisafe-enhanced, e uma no trisafe (nome codificado é prefixo!).
    from orb.adapters.claude import project_dir
    for cwd, sid in ((worktree, "11111111-1111-4111-8111-111111111111"), (trisafe, "22222222-2222-4222-8222-222222222222")):
        folder = project_dir(cwd, home=tmp_path)
        folder.mkdir(parents=True)
        (folder / f"{sid}.jsonl").write_text(json.dumps({"type": "user", "uuid": "u1", "cwd": cwd,
                                                         "message": {"content": "oi"}}) + "\n", encoding="utf-8")
    _codex_session(tmp_path, worktree, "019a0000-0000-7000-8000-000000000009")
    hub = Hub(Observatory(roots=[str(root)], home=tmp_path))
    hub.poll_once()
    realms = {r["id"]: r for r in hub.snapshot()["realms"]}
    assert set(realms) == {"trisafe", "trisafe-enhanced"}                      # pasta oculta fica de fora
    providers = sorted(e["provider"] for e in realms["trisafe-enhanced"]["alter_egos"])
    assert providers == ["claude", "codex"]                                     # o worktree conta para o projeto
    assert [e["provider"] for e in realms["trisafe"]["alter_egos"]] == ["claude"]
    (root / "novo-projeto").mkdir()
    hub.observatory.sync_roots(force=True)
    assert "novo-projeto" in {r["id"] for r in hub.snapshot()["realms"]}        # pasta nova entra sozinha


def test_hub_derives_time_states_at_its_clock_and_notices_time_passing(tmp_path):
    """O servidor pede o mundo com a hora dele e avisa os clientes quando só o tempo mudou algo."""
    import asyncio
    from datetime import UTC, datetime, timedelta

    from orb.gateway import Hub, Observatory
    from orb.protocol import make_event

    clock = [datetime(2026, 10, 7, 10, 0, tzinfo=UTC)]
    hub = Hub(Observatory(home=tmp_path), clock=lambda: clock[0])

    def event(key, signal, *, agent=None):
        return make_event(id=f"claude:s1:{key}", ts="2026-10-07T10:00:00Z", provider="claude",
                          source="claude/transcript", realm="the-orb", alter_ego="claude:s1", agent=agent,
                          seq=1, kind="x", body={}, signal=signal)

    hub.world.apply(event("a", {"type": "subagent.started"}, agent="a1"))
    hub.world.apply(event("b", {"type": "idle"}))
    client: asyncio.Queue = asyncio.Queue()
    hub.clients.add(client)

    def ego():
        return hub.snapshot()["realms"][0]["alter_egos"][0]

    hub.publish_world()
    assert client.get_nowait()["world"]["realms"][0]["alter_egos"][0]["asleep"] is False
    assert hub.time_changed() is False                           # nada mudou: ninguém é avisado à toa

    clock[0] += timedelta(minutes=6)                             # o subagente fica sem sinal; a sessão ainda não dorme
    assert ego()["team"][0]["no_signal"] is True and ego()["asleep"] is False
    assert hub.time_changed() is True
    hub.publish_world()
    assert client.get_nowait()["world"]["realms"][0]["alter_egos"][0]["team"][0]["no_signal"] is True
    assert hub.time_changed() is False

    clock[0] += timedelta(minutes=10)                            # 16 min parada: dorme
    assert hub.time_changed() is True
    hub.publish_world()
    assert client.get_nowait()["world"]["realms"][0]["alter_egos"][0]["asleep"] is True
