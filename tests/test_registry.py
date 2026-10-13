"""Registro local do Orb (R36, D-062): SQLite na pasta do Orb, só com o que o Orb derivou."""
import random
import sqlite3
from pathlib import Path

from orb.core import NAMES
from orb.registry import REGISTRY_FILE, LocalRegistry, orb_home


def tables(path: Path) -> dict[str, list[str]]:
    conn = sqlite3.connect(path)
    try:
        names = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        return {name: [col[1] for col in conn.execute(f"PRAGMA table_info({name})")] for name in names}
    finally:
        conn.close()


def test_the_registry_creates_its_file_in_the_folder_it_was_given(tmp_path):
    folder = tmp_path / "the-orb"
    registry = LocalRegistry(folder)
    assert (folder / REGISTRY_FILE).is_file() and registry.error is None


def test_it_stores_only_what_the_orb_derived_never_session_content(tmp_path):
    registry = LocalRegistry(tmp_path)
    registry.name_for("claude:s1", frozenset())
    assert tables(tmp_path / REGISTRY_FILE) == {"names": ["key", "name"], "bag": ["position", "name"]}


def test_a_session_keeps_its_name_after_the_orb_restarts(tmp_path):
    name = LocalRegistry(tmp_path).name_for("claude:s1", frozenset())
    assert name in NAMES
    assert LocalRegistry(tmp_path).name_for("claude:s1", frozenset()) == name


def test_a_name_is_kept_even_when_it_is_in_use_by_another_visible_character(tmp_path):
    registry = LocalRegistry(tmp_path)
    name = registry.name_for("claude:s1", frozenset())
    assert registry.name_for("claude:s1", frozenset({name})) == name        # o nome é identidade: não muda


def test_the_bag_goes_on_across_restarts_without_repeating_a_name(tmp_path):
    drawn = [LocalRegistry(tmp_path, rng=random.Random(n)).name_for(f"codex:{n}", frozenset()) for n in range(60)]
    assert sorted(drawn) == sorted(NAMES)                                    # reabrir não embaralha de novo


def test_after_sixty_sessions_the_bag_is_shuffled_again(tmp_path):
    registry = LocalRegistry(tmp_path, rng=random.Random(1))
    first = [registry.name_for(f"s{n}", frozenset()) for n in range(60)]
    second = [registry.name_for(f"s{n}", frozenset()) for n in range(60, 120)]
    assert sorted(first) == sorted(second) == sorted(NAMES)


def test_a_name_in_use_in_the_room_is_skipped_for_a_new_session(tmp_path):
    first = LocalRegistry(tmp_path, rng=random.Random(2))
    wanted = LocalRegistry(tmp_path / "other", rng=random.Random(2)).name_for("x", frozenset())
    assert first.name_for("claude:s1", frozenset({wanted})) != wanted        # o primeiro da sacola estava em uso


def test_the_folder_is_created_when_it_does_not_exist_yet(tmp_path):
    folder = tmp_path / "a" / "b" / "the-orb"
    LocalRegistry(folder)
    assert folder.is_dir()


def test_a_broken_registry_file_degrades_to_names_in_memory_and_says_so(tmp_path):
    (tmp_path / REGISTRY_FILE).write_bytes(b"isto nao e um banco sqlite " * 40)
    registry = LocalRegistry(tmp_path)
    first = registry.name_for("claude:s1", frozenset())
    assert first in NAMES and registry.name_for("claude:s1", frozenset()) == first    # estável nesta execução
    assert registry.error
    assert (tmp_path / REGISTRY_FILE).read_bytes().startswith(b"isto nao e")           # nunca apaga nem sobrescreve


def test_a_folder_that_cannot_be_created_degrades_the_same_way(tmp_path):
    blocker = tmp_path / "arquivo"
    blocker.write_text("x", encoding="utf-8")
    registry = LocalRegistry(blocker / "the-orb")                                      # pai é um arquivo
    assert registry.name_for("claude:s1", frozenset()) in NAMES and registry.error


def test_a_registry_from_a_newer_orb_is_not_touched(tmp_path):
    path = tmp_path / REGISTRY_FILE
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA user_version = 99")
    conn.commit()
    conn.close()
    registry = LocalRegistry(tmp_path)
    assert registry.name_for("claude:s1", frozenset()) in NAMES and "99" in (registry.error or "")
    assert tables(path) == {}                                                          # nada foi criado nele


def test_the_orb_folder_follows_the_platform_without_touching_the_real_one():
    assert orb_home({"LOCALAPPDATA": r"C:\Dados\Local"}, home=Path("/h")) == Path(r"C:\Dados\Local") / "the-orb"
    assert orb_home({"XDG_DATA_HOME": "/x/share"}, home=Path("/h")) == Path("/x/share") / "the-orb"
    assert orb_home({}, home=Path("/h")) == Path("/h") / ".local" / "share" / "the-orb"
