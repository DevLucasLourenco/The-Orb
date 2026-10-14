"""As alterações locais do git (R20b, R20e, R16): repositório falso -> alterações com tipo e linhas; só lê, nunca grava."""
import os
import shutil
import subprocess

import pytest

from orb.probes import (
    Change,
    changes_fingerprint,
    git_changes,
    parse_numstat,
    parse_status,
)

HAS_GIT = shutil.which("git") is not None


def entry(*fields):
    return " ".join(fields).encode()


# --- a saída do `git status --porcelain=v2 -z` -----------------------------------------------------------------

SUB = "N..."


def status(*records):
    return b"\0".join(records) + b"\0"


def test_each_kind_of_status_record_becomes_one_change_with_its_type():
    raw = status(
        entry("1", ".M", SUB, "100644", "100644", "100644", "h1", "h2", "src/a.py"),
        entry("1", "A.", SUB, "000000", "100644", "100644", "0" * 4, "h2", "novo.py"),
        entry("1", ".D", SUB, "100644", "100644", "000000", "h1", "h2", "velho.py"),
        entry("1", "D.", SUB, "100644", "000000", "000000", "h1", "h2", "tirado.py"),
        entry("2", "R.", SUB, "100644", "100644", "100644", "h1", "h2", "R100", "novo-nome.py") + b"\0" + b"nome-antigo.py",
        b"? solto.txt",
        entry("u", "UU", SUB, "100644", "100644", "100644", "100644", "h1", "h2", "h3", "conflito.py"),
    )
    got = {path: kind for path, kind in parse_status(raw)}
    assert got == {"src/a.py": "modified", "novo.py": "added", "velho.py": "deleted", "tirado.py": "deleted",
                   "novo-nome.py": "renamed", "solto.txt": "untracked", "conflito.py": "conflict"}


@pytest.mark.parametrize(("xy", "kind"), [
    ("M.", "modified"), (".M", "modified"), ("MM", "modified"), ("T.", "modified"), (".T", "modified"),
    ("A.", "added"), ("AM", "added"), ("C.", "added"),                    # novo no índice continua "adicionado" mesmo editado depois
    ("D.", "deleted"), (".D", "deleted"), ("MD", "deleted"),
    ("R.", "renamed"), ("RM", "renamed"),
])
def test_the_two_status_letters_choose_the_type_of_a_change(xy, kind):
    raw = status(entry("1", xy, SUB, "100644", "100644", "100644", "h1", "h2", "f.py"))
    assert parse_status(raw) == [("f.py", kind)]


def test_a_submodule_does_not_light_a_window_of_the_parent_project():
    raw = status(entry("1", ".M", "S.M.", "160000", "160000", "160000", "h1", "h2", "vendor/outro"),
                 entry("1", ".M", SUB, "100644", "100644", "100644", "h1", "h2", "ok.py"))
    assert parse_status(raw) == [("ok.py", "modified")]                  # R20e: o submódulo é outro repositório


def test_paths_with_spaces_and_accents_survive_and_slashes_are_always_forward():
    raw = status(entry("1", ".M", SUB, "100644", "100644", "100644", "h1", "h2", "pasta com espaço/ação.py"), b"? dir\\sub.txt")
    assert [p for p, _ in parse_status(raw)] == ["pasta com espaço/ação.py", "dir/sub.txt"]


def test_unknown_or_broken_records_are_ignored_instead_of_failing():
    raw = status(b"# branch.oid abc", b"! ignorado.log", b"1 so-um-pedaco", b"", entry("1", ".M", SUB, "1", "1", "1", "h", "h", "bom.py"))
    assert parse_status(raw) == [("bom.py", "modified")]


# --- o `git diff --numstat -z` ---------------------------------------------------------------------------------

def test_the_weight_of_a_change_is_the_inserted_plus_the_removed_lines_and_binary_counts_one():
    raw = b"3\t1\tsrc/a.py\0" b"-\t-\timg.png\0" b"0\t7\tapagado.py\0"
    assert parse_numstat(raw) == {"src/a.py": 4, "img.png": 1, "apagado.py": 7}


def test_a_rename_in_the_numstat_is_weighed_under_the_new_path():
    assert parse_numstat(b"2\t0\t\0antigo.py\0novo.py\0") == {"novo.py": 2}


# --- um repositório de verdade ---------------------------------------------------------------------------------

def repo(tmp_path, committed=None):
    root = tmp_path / "proj"
    root.mkdir()
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}

    def run(*args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(root), *args], check=True, capture_output=True, env=env)

    run("init", "-q")
    for name, text in (committed or {}).items():
        write(root, name, text)
    if committed:
        run("add", "-A")
        run("commit", "-q", "-m", "inicio")
    return root, run


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))


@pytest.mark.skipif(not HAS_GIT, reason="precisa do git instalado")
def test_a_real_repository_gives_the_type_and_the_changed_lines_of_each_file(tmp_path):
    root, run = repo(tmp_path, {"a.py": "1\n2\n3\n", "b.py": "x\ny\n", "pasta/c.py": "p\n", ".gitignore": "*.log\n"})
    write(root, "a.py", "1\n2 mudou\n3\n4\n5\n")                       # modificado: 1 removida + 3 inseridas
    write(root, "novo.py", "um\n\ndois\ntres\n")                       # não rastreado: 4 linhas (todas, como o diff conta as de um adicionado)
    write(root, "bin.dat", b"\x00\x01\x02")                            # não rastreado e binário: peso 1
    write(root, "ignorado.log", "isto não conta\n")                    # ignorado pelo .gitignore
    (root / "b.py").unlink()                                            # apagado: as 2 linhas que tinha
    write(root, "staged.py", "s1\ns2\n")
    run("add", "staged.py")                                             # adicionado no índice
    run("mv", "pasta/c.py", "pasta/d.py")                               # renomeado
    result = git_changes(root)
    by_path = {c.path: (c.type, c.lines) for c in result.items}
    assert by_path == {"a.py": ("modified", 4), "novo.py": ("untracked", 4), "bin.dat": ("untracked", 1),
                       "b.py": ("deleted", 2), "staged.py": ("added", 2), "pasta/d.py": ("renamed", 1)}
    assert [c.path for c in result.items] == sorted(by_path) and result.more == 0       # ordem estável pelo caminho


@pytest.mark.skipif(not HAS_GIT, reason="precisa do git instalado")
def test_reading_the_changes_never_writes_anything_in_the_git_folder(tmp_path):
    root, _ = repo(tmp_path, {"a.py": "1\n"})
    write(root, "a.py", "1\n2\n")
    before = {p: p.stat().st_mtime_ns for p in (root / ".git").rglob("*") if p.is_file()}
    git_changes(root)
    git_changes(root)
    after = {p: p.stat().st_mtime_ns for p in (root / ".git").rglob("*") if p.is_file()}
    assert after == before                                              # nem o índice é atualizado só por olhar (R16)


@pytest.mark.skipif(not HAS_GIT, reason="precisa do git instalado")
def test_a_repository_without_commits_still_shows_its_new_files(tmp_path):
    root, run = repo(tmp_path)
    write(root, "a.py", "1\n2\n")
    write(root, "b.py", "x\n")
    run("add", "a.py")
    got = {c.path: (c.type, c.lines) for c in git_changes(root).items}
    assert got == {"a.py": ("added", 2), "b.py": ("untracked", 1)}


@pytest.mark.skipif(not HAS_GIT, reason="precisa do git instalado")
def test_a_clean_repository_has_no_changes_and_a_folder_without_git_has_no_answer(tmp_path):
    root, _ = repo(tmp_path, {"a.py": "1\n"})
    assert git_changes(root).items == []                                # limpo: nenhuma janela acesa (e isso é dado)
    (tmp_path / "solta").mkdir()
    assert git_changes(tmp_path / "solta") is None                      # sem repositório: sem dado, nunca "limpo"


@pytest.mark.skipif(not HAS_GIT, reason="precisa do git instalado")
def test_a_huge_number_of_changes_is_cut_and_the_rest_is_counted(tmp_path):
    root, _ = repo(tmp_path, {"a.py": "1\n"})
    for n in range(30):
        write(root, f"gerado/f{n:03d}.txt", "x\n")
    result = git_changes(root, limit=10)
    assert len(result.items) == 10 and result.more == 20                 # as primeiras pelo caminho; o resto vira contagem


def test_a_path_the_protocol_would_refuse_is_left_out_and_counted_instead_of_breaking_the_event(monkeypatch, tmp_path):
    long_path = "x" * 600 + "/" + "y" * 600 + ".txt"                            # 1.201 caracteres: passa de 1.024
    out = status(b"? ok.txt", b"? " + long_path.encode(), b"? a//b.txt")

    def fake_git(root, *args):
        return {"status": out, "rev-parse": b"abc", "diff": b""}.get(args[0])

    monkeypatch.setattr("orb.probes.changes.run_git", fake_git)
    result = git_changes(tmp_path)
    assert [c.path for c in result.items] == ["ok.txt"] and result.more == 2    # o que o protocolo recusaria sai, e conta como "de fora"


def test_the_fingerprint_changes_only_when_the_changes_change():
    a = [Change("a.py", "modified", 3), Change("b.py", "added", 1)]
    assert changes_fingerprint(a, 0) != changes_fingerprint(a, 5)                # quantas ficaram de fora também conta
    assert changes_fingerprint(a) == changes_fingerprint(list(a))
    assert changes_fingerprint(a) != changes_fingerprint([Change("a.py", "modified", 4), Change("b.py", "added", 1)])
    assert changes_fingerprint(a) != changes_fingerprint([Change("a.py", "deleted", 3), Change("b.py", "added", 1)])
