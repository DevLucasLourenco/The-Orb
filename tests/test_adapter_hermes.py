"""O esquema abaixo é um SUBCONJUNTO do state.db do Hermes 0.20.5, com os nomes de coluna lidos no
código-fonte (hermes_state_common.py). Não usa dados reais."""
import json
import sqlite3

from orb.adapters.hermes import StateDbReader, hermes_home
from orb.core import World
from orb.protocol import validate

CWD = r"C:\proj\demo"


def make_db(home):
    home.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(home / "state.db")
    conn.executescript("""
        CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT, model TEXT, parent_session_id TEXT, cwd TEXT,
                               title TEXT, started_at REAL, extra_future_column TEXT);
        CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT,
                               tool_call_id TEXT, tool_calls TEXT, tool_name TEXT, timestamp REAL,
                               finish_reason TEXT, reasoning TEXT, codex_reasoning_items TEXT, active INTEGER DEFAULT 1);
    """)
    return conn


def add(conn, session, role, content="", **kw):
    conn.execute("INSERT INTO messages (session_id, role, content, tool_calls, timestamp, finish_reason, reasoning, "
                 "codex_reasoning_items, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (session, role, content, json.dumps(kw.get("tool_calls")) if kw.get("tool_calls") else None,
                  1_760_000_000.0, kw.get("finish_reason"), kw.get("reasoning"),
                  json.dumps(kw.get("codex_reasoning_items")) if kw.get("codex_reasoning_items") else None, kw.get("active", 1)))
    conn.commit()


def test_reads_only_new_rows_from_the_end_and_maps_them(tmp_path):
    home = tmp_path / "hermes"
    conn = make_db(home)
    conn.execute("INSERT INTO sessions VALUES ('S1', 'cli', 'm', NULL, ?, 't', 0, NULL)", (CWD,))
    conn.execute("INSERT INTO sessions VALUES ('S2', 'cli', 'm', NULL, 'C:/outra', 't', 0, NULL)")
    add(conn, "S1", "user", "antigo")                       # já existia: não é relido
    r = StateDbReader(CWD, realm="demo", home=home)
    assert r.poll() == []
    add(conn, "S1", "user", "rode os testes")
    add(conn, "S1", "assistant", "Vou rodar.", reasoning="preciso do pytest",
        tool_calls=[{"id": "c1", "type": "function", "function": {"name": "terminal", "arguments": json.dumps({"command": "pytest -q"})}}])
    add(conn, "S1", "tool", "3 passed")
    add(conn, "S1", "assistant", "ok", active=0)            # reescrito por /retry: ignorado
    add(conn, "S1", "assistant", "Feito.", finish_reason="stop")
    add(conn, "S2", "user", "outra pasta")
    events = r.poll()
    assert all(validate(e) is None for e in events)
    assert events[0]["signal"] == {"type": "session.started", "cwd": CWD, "title": "t", "model": "m"}
    events = events[1:]
    assert [e["native"]["kind"] for e in events] == [
        "messages/user", "messages/assistant.reasoning", "messages/assistant", "messages/assistant.tool_call",
        "messages/tool", "messages/assistant", "messages/assistant.stop"]
    assert events[0]["inner"]["role"] == "prompt" and events[0]["signal"] is None
    assert events[3]["signal"]["activity"] == "TESTING"
    assert {e["alter_ego"] for e in events} == {"hermes:S1"}
    assert r.poll() == []


def test_subagent_sessions_join_the_parent_team(tmp_path):
    home = tmp_path / "hermes"
    conn = make_db(home)
    conn.execute("INSERT INTO sessions VALUES ('P', 'cli', 'm', NULL, ?, 't', 0, NULL)", (CWD,))
    conn.execute("INSERT INTO sessions VALUES ('C', 'subagent', 'm', 'P', ?, 't', 0, NULL)", (CWD,))
    conn.execute("INSERT INTO sessions VALUES ('K', 'cli', 'm', 'P', ?, 't', 0, NULL)", (CWD,))   # compactação
    conn.commit()
    r = StateDbReader(CWD, realm="demo", home=home, replay=True)
    r.poll()
    add(conn, "C", "assistant", "procurando", tool_calls=[{"id": "x", "function": {"name": "search_files", "arguments": "{}"}}])
    add(conn, "K", "user", "continuação")
    events = r.poll()
    world = World()
    for e in events:
        world.apply(e)
    egos = {e["id"]: e for e in world.snapshot()["realms"][0]["alter_egos"]}
    assert egos["hermes:P"]["team"][0]["id"] == "C"
    assert "hermes:K" in egos                                # compactação não é subagente


def test_missing_db_and_home_resolution(tmp_path):
    assert StateDbReader(CWD, realm="demo", home=tmp_path / "nada").poll() == []
    assert hermes_home({"HERMES_HOME": "X:/h"}).as_posix() == "X:/h"
    assert hermes_home({"LOCALAPPDATA": "C:/L"}).as_posix() == "C:/L/hermes"


def thoughts(events):
    return [e["inner"]["fidelity"] for e in events if e["inner"] and e["inner"]["role"] == "thought"]


def test_thought_fidelity_follows_the_structure_of_the_row(tmp_path):
    """O texto de `reasoning` é `summary` quando a linha traz itens de raciocínio da Responses API
    (`codex_reasoning_items`: resumo + blob cifrado); sem esse marcador é a cadeia de pensamento como veio (`raw`)."""
    home = tmp_path / "hermes"
    conn = make_db(home)
    conn.execute("INSERT INTO sessions VALUES ('S1', 'cli', 'm', NULL, ?, 't', 0, NULL)", (CWD,))
    conn.commit()
    r = StateDbReader(CWD, realm="demo", home=home, replay=True)
    r.poll()
    item = {"type": "reasoning", "id": "rs_1", "summary": [{"type": "summary_text", "text": "plano"}], "encrypted_content": "zzz"}
    add(conn, "S1", "assistant", "", reasoning="pensei em voz alta")
    add(conn, "S1", "assistant", "Feito.", reasoning="plano", codex_reasoning_items=[item])
    add(conn, "S1", "assistant", "", reasoning="outro", codex_reasoning_items=[{"type": "compaction", "encrypted_content": "zzz"}])
    events = r.poll()
    assert all(validate(e) is None for e in events)
    assert thoughts(events) == ["raw", "summary", "raw"]      # compactação não é pensamento resumido
    assert all("codex_reasoning_items" not in e["native"]["body"] for e in events)   # o blob cifrado não vai no evento


def test_thought_is_raw_when_the_schema_has_no_reasoning_items_column(tmp_path):
    home = tmp_path / "hermes"
    conn = make_db(home)
    conn.execute("ALTER TABLE messages DROP COLUMN codex_reasoning_items")     # esquema de outra versão do Hermes
    conn.execute("INSERT INTO sessions VALUES ('S1', 'cli', 'm', NULL, ?, 't', 0, NULL)", (CWD,))
    conn.execute("INSERT INTO messages (session_id, role, content, timestamp, reasoning) VALUES ('S1', 'assistant', '', 1.0, 'x')")
    conn.commit()
    r = StateDbReader(CWD, realm="demo", home=home, replay=True)
    r.poll()                                      # o primeiro poll só fixa o cursor
    assert thoughts(r.poll()) == ["raw"]


def test_session_opening_carries_the_time_of_the_message_that_revealed_it(tmp_path):
    """D-128: a abertura não usa a hora da leitura; leva a da primeira mensagem vista da sessão."""
    home = tmp_path / "hermes"
    conn = make_db(home)
    conn.execute("INSERT INTO sessions VALUES ('S1', 'cli', 'm', NULL, ?, 't', 0, NULL)", (CWD,))
    conn.commit()
    r = StateDbReader(CWD, realm="demo", home=home, replay=True)
    r.poll()
    add(conn, "S1", "user", "oi")                              # timestamp 1_760_000_000.0
    opening = r.poll()[0]
    assert opening["signal"]["type"] == "session.started" and opening["ts"].startswith("2025-10-09T08:53:20")

