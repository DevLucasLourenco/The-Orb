"""Índice de metadados das sessões (R48, camada 1): pasta, datas, título, provider e modelo de TODAS as
sessões, sem filtro por pasta e sem ler o conteúdo. Arquivos e bancos sintéticos; nenhum dado real."""
import json
import sqlite3

import pytest

from orb.adapters.claude import TranscriptIndex, project_dir
from orb.adapters.codex import RolloutIndex
from orb.adapters.hermes import SessionsIndex as HermesIndex
from orb.adapters.opencode import SessionsIndex as OpencodeIndex

CWD = r"C:\proj\demo"


# --- Codex ---------------------------------------------------------------------------------

def rollout(tmp_path, jsonl, thread_id, cwd, *, parent=None, day="07"):
    payload = {"id": thread_id, "cwd": cwd, "cli_version": "0.160.1", "timestamp": f"2026-10-{day}T10:00:00Z"}
    if parent:
        payload["parent_thread_id"] = parent
    path = tmp_path / ".codex" / "sessions" / "2026" / "10" / day / f"rollout-2026-10-{day}T10-00-00-{thread_id}.jsonl"
    jsonl(path, [{"timestamp": payload["timestamp"], "ordinal": 0, "type": "session_meta", "payload": payload}])
    return path


def test_codex_lists_every_rollout_with_folder_dates_and_title(tmp_path, jsonl):
    rollout(tmp_path, jsonl, "t-demo", CWD)
    rollout(tmp_path, jsonl, "t-outra", r"D:\outra\pasta", day="08")                 # sem filtro por pasta
    rollout(tmp_path, jsonl, "t-filha", CWD, parent="t-demo")
    jsonl(tmp_path / ".codex" / "session_index.jsonl", [{"id": "t-demo", "thread_name": "Revisar o login", "updated_at": "x"}])
    metas = {m.session_id: m for m in RolloutIndex(home=tmp_path).scan()}
    assert set(metas) == {"t-demo", "t-outra", "t-filha"}
    demo = metas["t-demo"]
    assert (demo.provider, demo.cwd, demo.title, demo.parent_id) == ("codex", CWD, "Revisar o login", None)
    assert demo.started_at == "2026-10-07T10:00:00Z" and demo.updated_at is not None
    assert metas["t-filha"].parent_id == "t-demo"
    assert metas["t-outra"].cwd == r"D:\outra\pasta" and metas["t-outra"].title is None


def test_codex_index_never_reads_past_the_first_line_and_reads_each_file_once(tmp_path, jsonl, monkeypatch):
    path = rollout(tmp_path, jsonl, "t-demo", CWD)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("{isto nem é json\n")                                              # conteúdo ilegível não atrapalha
    rollout(tmp_path, jsonl, "t-novo", CWD, day="08")
    broken = tmp_path / ".codex" / "sessions" / "2026" / "10" / "09" / "rollout-2026-10-09T10-00-00-t-quebrado.jsonl"
    broken.parent.mkdir(parents=True)
    broken.write_text('{"type": "session_meta", "payload": {"id"', encoding="utf-8")   # 1ª linha ainda incompleta
    index = RolloutIndex(home=tmp_path)
    assert {m.session_id for m in index.scan()} == {"t-demo", "t-novo"}
    from orb.adapters.codex import index as codex_index
    opened = []
    real = codex_index.first_entry
    monkeypatch.setattr(codex_index, "first_entry", lambda p: opened.append(p.name) or real(p))
    index.scan()
    assert opened == [broken.name]                                                  # só o que ainda não se conseguiu ler


def test_codex_without_sessions_folder_is_empty(tmp_path):
    assert RolloutIndex(home=tmp_path).scan() == []


# --- Claude --------------------------------------------------------------------------------

def transcript(home, cwd, session_id, entries=None):
    folder = project_dir(cwd, home=home)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{session_id}.jsonl"
    lines = entries if entries is not None else [{"type": "user", "uuid": "u1", "cwd": cwd, "message": {"content": "oi"}}]
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    return path


def test_claude_lists_every_session_of_every_project_folder(short_tmp):
    transcript(short_tmp, CWD, "s1")
    transcript(short_tmp, CWD, "s2")
    transcript(short_tmp, r"D:\outra\pasta", "s3")
    sub = project_dir(CWD, home=short_tmp) / "s1" / "subagents"
    sub.mkdir(parents=True)
    (sub / "agent-a1.jsonl").write_text("{}\n", encoding="utf-8")                    # subagente não é sessão
    metas = {m.session_id: m for m in TranscriptIndex(home=short_tmp).scan()}
    assert set(metas) == {"s1", "s2", "s3"}
    assert metas["s1"].provider == "claude" and metas["s1"].cwd == CWD
    assert metas["s3"].cwd == r"D:\outra\pasta"
    assert metas["s1"].updated_at is not None and metas["s1"].started_at is not None


def test_claude_folder_without_a_recorded_folder_is_skipped_until_it_has_one(short_tmp):
    path = transcript(short_tmp, CWD, "s1", entries=[{"type": "summary", "summary": "x"}])
    index = TranscriptIndex(home=short_tmp)
    assert index.scan() == []                                                         # sem `cwd` gravado: não dá para saber
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"type": "user", "uuid": "u2", "cwd": CWD, "message": {"content": "oi"}}) + "\n")
    assert [m.cwd for m in index.scan()] == [CWD]


def test_claude_without_projects_folder_is_empty(tmp_path):
    assert TranscriptIndex(home=tmp_path).scan() == []


# --- Hermes --------------------------------------------------------------------------------

def hermes_db(home):
    home.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(home / "state.db")
    conn.executescript("""
        CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT, model TEXT, parent_session_id TEXT, cwd TEXT,
                               title TEXT, started_at REAL, last_activity_at REAL, git_repo_root TEXT, extra_future_column TEXT);
        CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, content TEXT);
    """)
    return conn


def test_hermes_lists_every_session_with_the_root_the_provider_informs(tmp_path):
    conn = hermes_db(tmp_path / "hermes")
    conn.execute("INSERT INTO sessions VALUES ('H1', 'cli', 'm', NULL, ?, 'Plano', 1760000000.0, 1760000900.0, ?, NULL)",
                 (CWD + r"\pkg", CWD))
    conn.execute("INSERT INTO sessions VALUES ('H2', 'subagent', 'm', 'H1', ?, NULL, 1760000100.0, NULL, NULL, NULL)", (CWD,))
    conn.execute("INSERT INTO sessions VALUES ('H3', 'cli', NULL, NULL, NULL, NULL, 1760000200.0, NULL, NULL, NULL)")   # sem pasta
    conn.commit()
    metas = {m.session_id: m for m in HermesIndex(home=tmp_path / "hermes").scan()}
    assert set(metas) == {"H1", "H2"}                                                 # sem pasta: não dá para atribuir
    h1 = metas["H1"]
    assert (h1.cwd, h1.project_root, h1.title, h1.model, h1.parent_id) == (CWD + r"\pkg", CWD, "Plano", "m", None)
    assert h1.started_at == "2025-10-09T08:53:20.000+00:00" and h1.updated_at == "2025-10-09T09:08:20.000+00:00"
    assert metas["H2"].parent_id == "H1" and metas["H2"].project_root is None


def test_hermes_without_database_or_with_another_schema_is_empty(tmp_path):
    assert HermesIndex(home=tmp_path / "nada").scan() == []
    home = tmp_path / "outro"
    home.mkdir()
    sqlite3.connect(home / "state.db").executescript("CREATE TABLE sessions (id TEXT);")
    assert HermesIndex(home=home).scan() == []


# --- opencode ------------------------------------------------------------------------------

def opencode_db(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(data_dir / "opencode.db")
    conn.executescript("""
        CREATE TABLE session_v2 (id TEXT PRIMARY KEY, parent_id TEXT, directory TEXT, title TEXT, model TEXT,
                                 time_created INTEGER, time_updated INTEGER);
        CREATE TABLE credential (id TEXT, value TEXT);
        INSERT INTO credential VALUES ('c1', 'SEGREDO');
    """)
    return conn


def test_opencode_lists_every_session_without_touching_credentials(tmp_path, monkeypatch):
    conn = opencode_db(tmp_path / "opencode")
    conn.execute("INSERT INTO session_v2 VALUES ('ses_1', NULL, ?, 'Corrigir bug', 'prov/m', 1760000000000, 1760000900000)", (CWD,))
    conn.execute("INSERT INTO session_v2 VALUES ('ses_2', 'ses_1', ?, NULL, NULL, 1760000100000, 1760000100000)", (r"D:\outra",))
    conn.commit()
    from orb.adapters.opencode import state_db
    asked = []
    real = state_db._select
    monkeypatch.setattr(state_db, "_select", lambda conn, table, *a, **k: asked.append(table) or real(conn, table, *a, **k))
    metas = {m.session_id: m for m in OpencodeIndex(data_dir=tmp_path / "opencode").scan()}
    assert set(metas) == {"ses_1", "ses_2"}
    one = metas["ses_1"]
    assert (one.provider, one.cwd, one.title, one.model, one.project_root) == ("opencode", CWD, "Corrigir bug", "prov/m", None)
    assert one.started_at == "2025-10-09T08:53:20.000+00:00" and metas["ses_2"].parent_id == "ses_1"
    assert set(asked) == {"session_v2"}                                              # nunca as tabelas de credenciais


def test_opencode_without_database_is_empty(tmp_path):
    assert OpencodeIndex(data_dir=tmp_path / "nada").scan() == []


@pytest.mark.parametrize("make", [lambda p: RolloutIndex(home=p), lambda p: TranscriptIndex(home=p),
                                  lambda p: HermesIndex(home=p / "hermes"), lambda p: OpencodeIndex(data_dir=p / "opencode")])
def test_every_index_is_a_noop_on_an_empty_machine(tmp_path, make):
    assert make(tmp_path).scan() == []
