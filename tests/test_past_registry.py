"""O ponto de parada da leitura do passado no registro local (ticket 25, R48 camada 3, D-088, D-203): quais sessões já foram lidas, por versão da tabela de XP."""
import json
import sqlite3

from orb.registry import REGISTRY_FILE, LocalRegistry

from .test_past_xp import commit, entry, stamp


def test_a_finished_old_session_is_marked_together_with_its_entries_and_the_mark_survives_reopening(tmp_path):
    registry = LocalRegistry(tmp_path)
    assert registry.past_done(1) == set()
    registry.record_past("claude:o1", [entry(ref="a"), entry("X-FIX", 25, "f")], "claude", "o1", 1, stamp(0))
    again = LocalRegistry(tmp_path)                                        # o Orb fechou e abriu
    assert again.past_done(1) == {("claude", "o1")}
    assert [e.ref for e in again.entries_of("claude:o1", 1)] == ["a", "f"]


def test_the_mark_belongs_to_the_table_version_so_a_new_version_reads_the_past_again(tmp_path):
    registry = LocalRegistry(tmp_path)
    registry.record_past("claude:o1", [entry(ref="a")], "claude", "o1", 1, stamp(0))
    assert registry.past_done(2) == set()
    registry.record_past("claude:o1", [entry(ref="a", version=2, xp=9)], "claude", "o1", 2, stamp(1))
    assert registry.past_done(2) == {("claude", "o1")}
    assert [e.xp for e in registry.entries_of("claude:o1", 1)] == [5]                                   # a v1 fica intacta
    assert [e.xp for e in registry.entries_of("claude:o1", 2)] == [9]


def test_an_entry_the_registry_already_has_is_not_overwritten_by_the_past(tmp_path):
    registry = LocalRegistry(tmp_path)
    registry.record("claude:o1", commit(state="confirmed", xp=12))         # o git já confirmou este commit
    registry.record_past("claude:o1", [commit(state="provisional", xp=10)], "claude", "o1", 1, stamp(0))
    (kept,) = registry.entries_of("claude:o1", 1)
    assert (kept.state, kept.xp) == ("confirmed", 12)


def test_a_registry_from_the_previous_schema_gets_the_past_table_and_keeps_its_entries(tmp_path):
    conn = sqlite3.connect(tmp_path / REGISTRY_FILE)
    conn.executescript("""
        CREATE TABLE names (key TEXT PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE bag (position INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE xp_ledger (ego TEXT NOT NULL, ts TEXT NOT NULL, rule TEXT NOT NULL, xp INTEGER NOT NULL, ref TEXT NOT NULL,
                                evidence TEXT NOT NULL, version INTEGER NOT NULL, state TEXT NOT NULL DEFAULT 'confirmed',
                                PRIMARY KEY (ego, rule, ref, version));
        INSERT INTO xp_ledger VALUES ('claude:s1', '2026-10-07T10:00:00Z', 'X-TEST', 5, 'e1', '{"event": "e1"}', 1, 'confirmed');
        PRAGMA user_version = 3;
    """)
    conn.commit()
    conn.close()
    registry = LocalRegistry(tmp_path)
    assert registry.error is None and registry.past_done(1) == set() and len(registry.entries_of("claude:s1", 1)) == 1


def test_when_the_disk_fails_the_session_is_not_marked_as_read_not_even_in_memory_and_the_error_says_so(tmp_path):
    blocker = tmp_path / "arquivo"
    blocker.write_text("x", encoding="utf-8")
    registry = LocalRegistry(blocker / "the-orb")                          # o pai é um arquivo
    registry.record_past("claude:o1", [entry(ref="a")], "claude", "o1", 1, stamp(0))
    assert registry.error
    assert registry.past_done(1) == set() and registry.entries_of("claude:o1", 1) == []       # a marca nunca fica à frente do extrato


def test_a_transaction_that_fails_in_the_middle_leaves_neither_the_mark_nor_the_entries_anywhere(tmp_path, monkeypatch):
    registry = LocalRegistry(tmp_path)
    original = json.dumps

    def broken(value, **kwargs):
        if isinstance(value, dict) and value.get("boom"):
            raise OSError("disco falhou no meio")
        return original(value, **kwargs)

    monkeypatch.setattr("orb.registry.store.json.dumps", broken)
    registry.record_past("claude:o1", [entry(ref="a"), entry(ref="b", boom=True)], "claude", "o1", 1, stamp(0))
    assert registry.error and registry.past_done(1) == set() and registry.entries_of("claude:o1", 1) == []
    monkeypatch.undo()
    assert LocalRegistry(tmp_path).past_done(1) == set()                    # nem no disco: a transação voltou inteira
    registry.record_past("claude:o1", [entry(ref="a")], "claude", "o1", 1, stamp(1))      # na próxima abertura o disco volta e a sessão é lida
    assert registry.error is None and registry.past_done(1) == {("claude", "o1")}
