"""Arquivos e bancos falsos dos 4 CLIs, com a FORMA verificada de cada um (docs/adapters/). Nenhum dado real."""
import json
import sqlite3

from orb.adapters.claude import project_dir


def rollout(tmp_path, jsonl, thread_id, cwd, *, parent=None, day="07"):
    """Um rollout do Codex: só a primeira linha (`session_meta`) importa para o índice."""
    payload = {"id": thread_id, "cwd": cwd, "cli_version": "0.160.1", "timestamp": f"2026-10-{day}T10:00:00Z"}
    if parent:
        payload["parent_thread_id"] = parent
    path = tmp_path / ".codex" / "sessions" / "2026" / "10" / day / f"rollout-2026-10-{day}T10-00-00-{thread_id}.jsonl"
    jsonl(path, [{"timestamp": payload["timestamp"], "ordinal": 0, "type": "session_meta", "payload": payload}])
    return path


def transcript(home, cwd, session_id, entries=None):
    """Um transcript do Claude numa pasta de projeto (`~/.claude/projects/<cwd codificado>/<id>.jsonl`)."""
    folder = project_dir(cwd, home=home)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{session_id}.jsonl"
    lines = entries if entries is not None else [{"type": "user", "uuid": "u1", "cwd": cwd, "message": {"content": "oi"}}]
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    return path


def hermes_db(home):
    """O `state.db` do Hermes, com as colunas de `sessions` que o índice lê (e uma extra, de versão futura)."""
    home.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(home / "state.db")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, source TEXT, model TEXT, parent_session_id TEXT, cwd TEXT,
                               title TEXT, started_at REAL, last_activity_at REAL, git_repo_root TEXT, extra_future_column TEXT);
        CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, content TEXT);
    """)
    return conn


def opencode_db(data_dir):
    """O `opencode.db`, com `session_v2` e uma tabela de credenciais que ninguém pode tocar."""
    data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(data_dir / "opencode.db")
    conn.executescript("""
        CREATE TABLE session_v2 (id TEXT PRIMARY KEY, parent_id TEXT, directory TEXT, title TEXT, model TEXT,
                                 time_created INTEGER, time_updated INTEGER);
        CREATE TABLE credential (id TEXT, value TEXT);
        INSERT INTO credential VALUES ('c1', 'SEGREDO');
    """)
    return conn
