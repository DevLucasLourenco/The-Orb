"""O contador de linhas (R19, D-053 a D-056): pasta de projeto falsa -> linhas; só lê, nunca grava."""
import os
import shutil
import subprocess

import pytest

from orb.core.rules import GENERATED_FILE_PATTERNS, LineFilter
from orb.probes import count_lines, fingerprint, git_tracked_files, list_countable


def project(tmp_path, files):
    root = tmp_path / "proj"
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    return root


def tracked(*names):
    return lambda root: list(names)


def lines(root, names, flt=None):
    flt = flt or LineFilter()
    return count_lines(root, list_countable(root, flt, tracked(*names))).loc


def test_it_counts_non_empty_lines_and_comments_count(tmp_path):
    root = project(tmp_path, {"a.py": "x = 1\n\n   \n# comentário\ny = 2\n", "b.py": "z\n"})
    assert lines(root, ["a.py", "b.py"]) == 4                                   # linha só com espaço não conta; comentário conta


def test_markdown_is_left_out_by_default_and_counted_when_the_filter_says_so(tmp_path):
    root = project(tmp_path, {"a.py": "x\n", "README.md": "um\ndois\n"})
    assert lines(root, ["a.py", "README.md"]) == 1
    assert lines(root, ["a.py", "README.md"], LineFilter(include_markdown=True)) == 3


def test_generated_files_of_the_visible_list_do_not_count(tmp_path):
    root = project(tmp_path, {"src/a.py": "x\n", "package-lock.json": "{\n}\n", "web/app.min.js": "var a;\n", "dist/out.js": "a\n"})
    names = ["src/a.py", "package-lock.json", "web/app.min.js", "dist/out.js"]
    assert lines(root, names) == 1
    assert {"package-lock.json", "*.min.js"} <= set(GENERATED_FILE_PATTERNS)           # a lista é fixa e visível
    assert lines(root, names, LineFilter(exclude=())) == 1 + 2 + 1 + 1                 # sem exclusões, tudo conta


def test_a_pattern_without_a_slash_matches_the_name_anywhere_and_one_with_a_slash_matches_the_path(tmp_path):
    root = project(tmp_path, {"a/gen.py": "x\n", "b/gen.py": "y\n", "keep.py": "z\n"})
    names = ["a/gen.py", "b/gen.py", "keep.py"]
    assert lines(root, names, LineFilter(exclude=("gen.py",))) == 1
    assert lines(root, names, LineFilter(exclude=("a/*",))) == 2


def test_binary_huge_missing_and_non_file_entries_are_skipped_without_failing(tmp_path):
    root = project(tmp_path, {"ok.py": "x\n", "img.png": b"\x89PNG\x00\x00\x00data\nmore\n", "big.txt": "a\n" * 10})
    (root / "submodulo").mkdir()
    entries = list_countable(root, LineFilter(), tracked("ok.py", "img.png", "big.txt", "sumiu.py", "submodulo"), max_file_bytes=5)
    result = count_lines(root, entries)
    assert result.loc == 1 and result.files == 1                                    # binário, grande, ausente e pasta ficam de fora


@pytest.mark.skipif(os.name != "nt", reason="o teste do link usa o comportamento do Windows")
def test_it_never_follows_a_link_out_of_the_project(tmp_path):
    outside = tmp_path / "fora.py"
    outside.write_text("a\nb\n", encoding="utf-8")
    root = project(tmp_path, {"ok.py": "x\n"})
    try:
        (root / "link.py").symlink_to(outside)
    except OSError:
        pytest.skip("sem permissão para criar links")
    assert lines(root, ["ok.py", "link.py"]) == 1


def test_the_fingerprint_changes_only_when_a_counted_file_or_the_filter_changes(tmp_path):
    root = project(tmp_path, {"a.py": "x\n", "b.py": "y\n"})
    flt = LineFilter()
    first = fingerprint(list_countable(root, flt, tracked("a.py", "b.py")), flt)
    assert first == fingerprint(list_countable(root, flt, tracked("a.py", "b.py")), flt)          # nada mudou
    (root / "a.py").write_text("x\nnovo\n", encoding="utf-8")
    assert fingerprint(list_countable(root, flt, tracked("a.py", "b.py")), flt) != first          # arquivo mudou
    other = LineFilter(include_markdown=True)
    assert fingerprint(list_countable(root, other, tracked("a.py", "b.py")), other) != first      # filtro mudou


def test_counting_never_writes_anything_in_the_project(tmp_path):
    root = project(tmp_path, {"a.py": "x\n"})
    before = sorted(str(p.relative_to(root)) for p in root.rglob("*")), (root / "a.py").stat().st_mtime_ns
    lines(root, ["a.py"])
    assert (sorted(str(p.relative_to(root)) for p in root.rglob("*")), (root / "a.py").stat().st_mtime_ns) == before


@pytest.mark.skipif(shutil.which("git") is None, reason="precisa do git instalado")
def test_with_a_real_repository_only_tracked_and_not_ignored_files_count(tmp_path):
    root = project(tmp_path, {"a.py": "x\ny\n", "solto.py": "nao rastreado\n", ".gitignore": "ignorado.py\n", "ignorado.py": "zzz\n"})
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}

    def run(*args):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, env=env)

    run("init", "-q")
    run("add", "a.py", ".gitignore")
    run("add", "-f", "ignorado.py")                                                # rastreado, mas o .gitignore o ignora
    stamp = (root / ".git" / "index").stat().st_mtime_ns
    files = git_tracked_files(root)
    assert sorted(files) == [".gitignore", "a.py"]                                 # sem os não rastreados e sem os ignorados
    assert (root / ".git" / "index").stat().st_mtime_ns == stamp                   # só lê: nada é gravado no .git


def test_a_folder_that_is_not_a_repository_gives_no_file_list(tmp_path):
    (tmp_path / "pasta").mkdir()
    assert git_tracked_files(tmp_path / "pasta") is None                           # sem dado: nada, nunca zero


def test_utf16_files_with_a_byte_order_mark_are_text_and_count(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "a.py").write_text("um\n\ndois\n", encoding="utf-16")                   # com BOM: o Windows grava assim
    assert lines(root, ["a.py"]) == 2


def test_the_comparison_of_patterns_does_not_depend_on_the_operating_system(tmp_path):
    root = project(tmp_path, {"A.LOCK": "x\n", "b.py": "y\n"})
    assert lines(root, ["A.LOCK", "b.py"], LineFilter(exclude=("*.lock",))) == 2         # maiúsculas contam como diferentes em qualquer sistema
