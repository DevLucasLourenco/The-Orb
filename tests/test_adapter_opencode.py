"""Esquema abaixo é um SUBCONJUNTO do opencode.db do opencode 2.0.23 (nomes de tabela, coluna e
campos JSON levantados nesta máquina, sem conteúdo). Nenhum dado real."""
import json
import sqlite3

import pytest

from orb.adapters.opencode import ALLOWED_TABLES, OpencodeDbReader, opencode_data_dir
from orb.adapters.opencode import state_db
from orb.core import World
from orb.protocol import validate

CWD = r"C:\proj\demo"


def make_db(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(data_dir / "opencode.db")
    conn.executescript("""
        CREATE TABLE session_v2 (id TEXT PRIMARY KEY, parent_id TEXT, directory TEXT, title TEXT, model TEXT,
                                 agent TEXT, fork_session_id TEXT, time_created INTEGER);
        CREATE TABLE session_message (id TEXT PRIMARY KEY, session_id TEXT, type TEXT, seq INTEGER,
                                      time_created INTEGER, time_updated INTEGER, data TEXT);
        CREATE TABLE credential (id TEXT, value TEXT);
        INSERT INTO credential VALUES ('c1', 'SEGREDO');
    """)
    return conn


class Db:
    def __init__(self, conn):
        self.conn, self.clock = conn, 1_790_000_000_000

    def session(self, sid, directory=CWD, parent=None, agent="build"):
        self.conn.execute("INSERT INTO session_v2 VALUES (?, ?, ?, 't', NULL, ?, NULL, 0)", (sid, parent, directory, agent))
        self.conn.commit()

    def put(self, mid, sid, mtype, data, seq=0):
        self.clock += 1
        self.conn.execute("INSERT OR REPLACE INTO session_message VALUES (?, ?, ?, ?, COALESCE((SELECT time_created FROM "
                          "session_message WHERE id = ?), ?), ?, ?)",
                          (mid, sid, mtype, seq, mid, self.clock, self.clock, json.dumps(data)))
        self.conn.commit()


@pytest.fixture
def db(tmp_path):
    return Db(make_db(tmp_path / "opencode"))


def reader(tmp_path, **kw):
    return OpencodeDbReader(CWD, realm="demo", data_dir=tmp_path / "opencode", **kw)


def kinds(events):
    return [e["native"]["kind"] for e in events]


def test_starts_from_the_end_then_reads_streaming_rows_once(tmp_path, db):
    db.session("ses_root1")
    db.put("msg_old", "ses_root1", "user", {"text": "antigo", "time": {"created": 1}})
    r = reader(tmp_path)
    assert r.poll() == []                                              # começa do fim
    db.put("msg_u", "ses_root1", "user", {"text": "rode os testes", "time": {"created": 2}}, seq=1)
    tool = {"type": "tool", "id": "t1", "name": "bash", "time": {}, "state": {"status": "running", "input": {"command": "pytest -q"}}}
    db.put("msg_a", "ses_root1", "assistant", {"content": [tool], "time": {"created": 3}}, seq=2)
    first = r.poll()
    assert kinds(first) == ["session_v2", "session_message/user", "session_message/assistant:tool"]
    assert first[1]["inner"]["role"] == "prompt" and first[1]["signal"] is None
    assert first[2]["signal"]["activity"] == "TESTING" and first[2]["inner"]["text"] == "bash pytest -q"
    # a mesma linha é REESCRITA conforme o streaming avança
    done = {**tool, "state": {"status": "completed", "input": {"command": "pytest -q"}, "content": "3 passed"}}
    db.put("msg_a", "ses_root1", "assistant", {"content": [done, {"type": "text", "text": "Feito."}],
                                               "time": {"created": 3, "completed": 4}, "finish": "stop",
                                               "tokens": {"input": 10, "output": 2, "reasoning": 1, "cache": {"read": 5, "write": 0}},
                                               "cost": 0.01}, seq=2)
    db.put("msg_i", "ses_root1", "idle", {"outcome": "completed", "time": {"created": 5}}, seq=3)
    second = r.poll()
    assert kinds(second) == ["session_message/assistant:tool_result", "session_message/assistant:text",
                             "session_message/assistant:usage", "session_message/idle"]
    assert second[2]["signal"]["cache_read_tokens"] == 5 and second[2]["signal"]["cost_usd"] == 0.01
    assert all(validate(e) is None for e in first + second)
    assert r.poll() == []


def test_synthetic_and_system_messages_keep_their_native_type(tmp_path, db):
    db.session("ses_root1")
    r = reader(tmp_path, replay=True)
    db.put("m1", "ses_root1", "synthetic", {"text": "lembrete injetado"})
    db.put("m2", "ses_root1", "system", {"text": "sistema"})
    events = [e for e in r.poll() if e["native"]["kind"].startswith("session_message")]
    assert [e["native"]["kind"] for e in events] == ["session_message/synthetic", "session_message/system"]
    assert [e["inner"]["role"] for e in events] == ["system", "system"]
    assert all(e["signal"] is None for e in events)


def test_text_waits_for_the_message_to_finish(tmp_path, db):
    db.session("ses_root1")
    r = reader(tmp_path, replay=True)
    db.put("m1", "ses_root1", "assistant", {"content": [{"type": "text", "text": "Vou le"}], "time": {"created": 1}})
    assert [k for k in kinds(r.poll()) if "text" in k] == []
    db.put("m1", "ses_root1", "assistant", {"content": [{"type": "text", "text": "Vou ler o arquivo."},
                                                        {"type": "reasoning", "text": "pensando"}],
                                            "time": {"created": 1, "completed": 2}})
    events = r.poll()
    text = next(e for e in events if e["native"]["kind"].endswith(":text"))
    thought = next(e for e in events if e["native"]["kind"].endswith(":reasoning"))
    assert text["inner"]["text"] == "Vou ler o arquivo."
    assert thought["inner"]["fidelity"] == "raw"


def test_child_sessions_join_the_team_and_other_folders_are_ignored(tmp_path, db):
    db.session("ses_root1")
    db.session("ses_child1", parent="ses_root1", agent="explore")
    db.session("ses_other1", directory=r"C:\outra")
    r = reader(tmp_path, replay=True)
    db.put("m1", "ses_child1", "assistant", {"content": [{"type": "tool", "name": "read", "state": {"status": "running", "input": {"filePath": "a.py"}}}]})
    db.put("m2", "ses_other1", "user", {"text": "não é deste realm"})
    events = r.poll()
    world = World()
    for e in events:
        world.apply(e)
    (ego,) = world.snapshot()["realms"][0]["alter_egos"]
    assert ego["id"] == "opencode:ses_root1"
    assert ego["team"][0]["id"] == "ses_child1" and ego["team"][0]["kind"] == "explore" and ego["team"][0]["state"] == "READING"


def test_never_touches_credential_tables(tmp_path, db, monkeypatch):
    assert ALLOWED_TABLES == {"session_v2", "session_message"}
    queries = []
    real_connect = state_db.connect_readonly

    def spy(path):
        conn = real_connect(path)
        conn.set_trace_callback(queries.append)
        return conn

    monkeypatch.setattr(state_db, "connect_readonly", spy)
    db.session("ses_root1")
    r = reader(tmp_path, replay=True)
    db.put("m1", "ses_root1", "user", {"text": "oi"})
    r.poll()
    assert queries and not any("credential" in q.lower() or "account" in q.lower() for q in queries)
    with pytest.raises(PermissionError):
        state_db.select(sqlite3.connect(":memory:"), "credential", ["value"], "", ())


def test_missing_db_and_data_dir():
    assert OpencodeDbReader(CWD, realm="demo", data_dir=opencode_data_dir({"XDG_DATA_HOME": "Z:/nada"})).poll() == []
    assert opencode_data_dir({"XDG_DATA_HOME": "X:/d"}).as_posix() == "X:/d/opencode"


def test_reasoning_block_with_the_observed_shape_is_declared_raw(tmp_path, db):
    """Fixa a declaração de hoje para a forma levantada no opencode 2.0.23 (só estrutura): bloco `{type, text, time}`
    sem item cifrado nem assinatura, e todo o texto guardado explica os `output` tokens. Não discrimina nada: o
    opencode não tem marcador estrutural de resumo (Q-T02-3, docs/adapters/OPENCODE.md §2)."""
    db.session("ses_root1")
    r = reader(tmp_path, replay=True)
    db.put("m1", "ses_root1", "assistant", {
        "agent": "build", "model": {"providerID": "p", "id": "m"},
        "content": [{"type": "reasoning", "text": "pensando", "time": {"created": 1, "completed": 2}},
                    {"type": "text", "text": "Feito."}],
        "tokens": {"input": 10, "output": 5, "reasoning": 0, "cache": {"read": 0, "write": 0}},
        "time": {"created": 1, "completed": 2}})
    thought = next(e for e in r.poll() if e["native"]["kind"].endswith(":reasoning"))
    assert validate(thought) is None
    assert thought["inner"] == {"role": "thought", "text": "pensando", "fidelity": "raw"}


# --- a lista de tarefas (ticket 14, R50): o `todowrite` guarda a lista inteira em `state.input.todos` ----------------------------

def todowrite_block(index, todos, status="completed"):
    return {"type": "tool", "id": f"t{index}", "name": "todowrite", "time": {},
            "state": {"status": status, "input": {"todos": todos}, "content": [{"type": "text", "text": "ok"}],
                      "metadata": {"todos": todos, "truncated": False}}}


def task_signals(events):
    return [e["signal"] for e in events if e["signal"] and e["signal"]["type"] == "tasks.updated"]


def test_todowrite_becomes_the_task_list_once_the_tool_finishes(tmp_path, db):
    db.session("ses_root1")
    r = reader(tmp_path)
    r.poll()
    todos = [{"content": "Ler o MVP", "status": "completed", "priority": "high"},
             {"content": "Escrever o teste", "status": "in_progress", "priority": "high"},
             {"content": "Rodar a suíte", "status": "pending", "priority": "medium"}]
    db.put("msg_a", "ses_root1", "assistant", {"content": [todowrite_block(0, todos, status="running")], "time": {"created": 3}}, seq=1)
    assert task_signals(r.poll()) == []                                            # ainda rodando: a lista pode mudar
    db.put("msg_a", "ses_root1", "assistant", {"content": [todowrite_block(0, todos)], "time": {"created": 3}}, seq=1)
    events = r.poll()
    assert all(validate(e) is None for e in events)
    assert task_signals(events) == [{"type": "tasks.updated", "done": 1, "total": 3, "items": [
        {"content": "Ler o MVP", "status": "completed"}, {"content": "Escrever o teste", "status": "in_progress"},
        {"content": "Rodar a suíte", "status": "pending"}]}]
    db.put("msg_a", "ses_root1", "assistant", {"content": [todowrite_block(0, todos)], "time": {"created": 3}}, seq=1)
    assert task_signals(r.poll()) == []                                            # a linha reescrita não repete a lista


def test_todowrite_of_a_subagent_session_is_not_the_leader_list(tmp_path, db):
    db.session("ses_root1")
    db.session("ses_child", parent="ses_root1", agent="explore")
    r = reader(tmp_path)
    r.poll()
    db.put("msg_c", "ses_child", "assistant", {"content": [todowrite_block(0, [{"content": "x", "status": "pending"}])],
                                              "time": {"created": 3}}, seq=1)
    assert task_signals(r.poll()) == []


def test_a_cancelled_task_is_not_counted(tmp_path, db):
    db.session("ses_root1")
    r = reader(tmp_path)
    r.poll()
    todos = [{"content": "a", "status": "completed", "priority": "low"}, {"content": "b", "status": "cancelled", "priority": "low"}]
    db.put("msg_a", "ses_root1", "assistant", {"content": [todowrite_block(0, todos)], "time": {"created": 3}}, seq=1)
    (signal,) = task_signals(r.poll())
    assert (signal["done"], signal["total"]) == (1, 1)
