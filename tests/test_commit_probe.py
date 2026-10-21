"""O Probe dos commits (ticket 23, R53, R16): repositório de verdade -> o que o git diz de cada commit que uma sessão disse ter feito.
Só lê, nunca grava no `.git`; sem repositório não há resposta."""
import os
import shutil
import subprocess
from datetime import UTC, datetime, timedelta

import pytest

from orb.probes import CommitQuery, commits_fingerprint, git_commits, main_branch

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="precisa do git instalado")

ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}


class Repo:
    def __init__(self, root):
        self.root = root
        root.mkdir()
        self("init", "-q", "-b", "main")

    def __call__(self, *args):
        done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(self.root), *args],
                              check=True, capture_output=True, env=ENV, text=True)
        return done.stdout.strip()

    def commit(self, name="a.py", lines=3, message="mexe"):
        (self.root / name).write_text("".join(f"{name} {i}\n" for i in range(lines)), encoding="utf-8")
        self("add", "-A")
        self("commit", "-q", "-m", message)
        return self("rev-parse", "HEAD")


def facts(root, *queries):
    result = git_commits(root, [CommitQuery(*q) if isinstance(q, tuple) else q for q in queries])
    assert result is not None
    return {f["key"]: f for f in result}


def q(key, sha=None, at="2026-10-21T10:00:00Z"):
    return CommitQuery(key, sha, at)


def test_a_commit_that_exists_on_main_reports_its_hash_lines_and_that_it_reached_main(tmp_path):
    repo = Repo(tmp_path / "p")
    sha = repo.commit("a.py", lines=45)
    fact = facts(repo.root, q("k1", sha))["k1"]
    assert fact == {"key": "k1", "sha": sha, "exists": True, "lines": 45, "on_main": True, "reverted": False}


def test_a_short_hash_is_resolved_to_the_full_one(tmp_path):
    repo = Repo(tmp_path / "p")
    sha = repo.commit()
    assert facts(repo.root, q("k", sha[:8]))["k"]["sha"] == sha


def test_a_hash_the_repository_does_not_know_does_not_exist_and_has_no_lines(tmp_path):
    repo = Repo(tmp_path / "p")
    repo.commit()
    fact = facts(repo.root, q("k", "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"))["k"]
    assert fact == {"key": "k", "sha": None, "exists": False, "lines": None, "on_main": False, "reverted": False}


def test_a_commit_on_another_branch_has_not_reached_main_until_it_is_merged(tmp_path):
    repo = Repo(tmp_path / "p")
    repo.commit("base.py")
    repo("switch", "-q", "-c", "feature")
    sha = repo.commit("f.py", lines=2)
    assert facts(repo.root, q("k", sha))["k"]["on_main"] is False
    repo("switch", "-q", "main")
    repo("merge", "-q", "--no-ff", "-m", "junta", "feature")
    assert facts(repo.root, q("k", sha))["k"]["on_main"] is True


def test_with_a_remote_the_main_branch_is_the_default_of_the_remote_so_an_unpushed_commit_has_not_arrived(tmp_path):
    repo = Repo(tmp_path / "p")
    repo.commit("base.py")
    repo("update-ref", "refs/remotes/origin/main", "HEAD")
    repo("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    sha = repo.commit("novo.py")
    assert main_branch(repo.root) == "origin/main"
    assert facts(repo.root, q("k", sha))["k"]["on_main"] is False                    # existe, mas o remoto ainda não o tem
    repo("update-ref", "refs/remotes/origin/main", "HEAD")                            # o push chegou
    assert facts(repo.root, q("k", sha))["k"]["on_main"] is True


@pytest.mark.parametrize("name", ["main", "master"])
def test_without_a_remote_the_main_branch_is_main_and_then_master(tmp_path, name):
    repo = Repo(tmp_path / "p")
    repo.commit()
    if name == "master":
        repo("branch", "-m", "master")
    assert main_branch(repo.root) == name


def test_a_repository_with_neither_main_nor_master_has_no_main_branch_and_nothing_arrives(tmp_path):
    repo = Repo(tmp_path / "p")
    sha = repo.commit()
    repo("branch", "-m", "trabalho")
    assert main_branch(repo.root) is None
    fact = facts(repo.root, q("k", sha))["k"]
    assert fact["exists"] is True and fact["on_main"] is False


def test_a_commit_that_main_later_reverted_is_reported_as_reverted(tmp_path):
    repo = Repo(tmp_path / "p")
    repo.commit("base.py")
    sha = repo.commit("ruim.py", lines=5)
    assert facts(repo.root, q("k", sha))["k"]["reverted"] is False
    repo("revert", "--no-edit", sha)
    fact = facts(repo.root, q("k", sha))["k"]
    assert fact["reverted"] is True and fact["on_main"] is True


def test_without_a_hash_the_commit_is_found_by_the_time_of_the_evidence(tmp_path):
    repo = Repo(tmp_path / "p")
    sha = repo.commit("meu.py", lines=7)
    now = datetime.now(UTC).isoformat()
    assert facts(repo.root, q("k", None, now))["k"]["sha"] == sha
    far = (datetime.now(UTC) - timedelta(hours=3)).isoformat()
    fact = facts(repo.root, q("k2", None, far))["k2"]
    assert fact["exists"] is False and fact["sha"] is None                           # nada perto dessa hora: não se adivinha


def test_a_commit_found_by_time_is_not_given_to_two_pieces_of_evidence(tmp_path):
    repo = Repo(tmp_path / "p")
    sha = repo.commit("meu.py")
    now = datetime.now(UTC).isoformat()
    found = facts(repo.root, q("a", None, now), q("b", None, now))
    assert [found["a"]["sha"], found["b"]["sha"]] == [sha, None]


def test_the_probe_never_writes_to_the_dot_git(tmp_path):
    repo = Repo(tmp_path / "p")
    sha = repo.commit()
    before = {p: p.stat().st_mtime_ns for p in (repo.root / ".git").rglob("*") if p.is_file()}
    git_commits(repo.root, [q("k", sha), q("t", None, datetime.now(UTC).isoformat())])
    after = {p: p.stat().st_mtime_ns for p in (repo.root / ".git").rglob("*") if p.is_file()}
    assert before == after


def test_a_folder_that_is_not_a_repository_has_no_answer(tmp_path):
    (tmp_path / "vazia").mkdir()
    assert git_commits(tmp_path / "vazia", [q("k", "abcdef1")]) is None


def test_no_questions_no_work(tmp_path):
    repo = Repo(tmp_path / "p")
    repo.commit()
    assert git_commits(repo.root, []) == []


def test_the_fingerprint_changes_only_when_something_the_world_cares_about_changes(tmp_path):
    repo = Repo(tmp_path / "p")
    sha = repo.commit()
    first = git_commits(repo.root, [q("k", sha)])
    assert commits_fingerprint(first) == commits_fingerprint(git_commits(repo.root, [q("k", sha)]))
    repo("revert", "--no-edit", sha)
    assert commits_fingerprint(git_commits(repo.root, [q("k", sha)])) != commits_fingerprint(first)


def test_a_second_commit_in_the_same_window_that_no_session_reported_is_not_guessed(tmp_path):
    repo = Repo(tmp_path / "p")
    repo.commit("meu.py")
    repo.commit("do-lucas.py")                                     # outro commit dentro da janela, sem sessão por trás (D-106)
    now = datetime.now(UTC).isoformat()
    fact = facts(repo.root, q("k", None, now))["k"]
    assert fact["exists"] is False and fact["sha"] is None


def test_two_commits_and_two_pieces_of_evidence_in_the_same_window_each_find_their_own(tmp_path):
    repo = Repo(tmp_path / "p")
    first = repo.commit("um.py")
    second = repo.commit("dois.py")
    now = datetime.now(UTC).isoformat()
    found = facts(repo.root, q("a", None, now), q("b", None, now))
    assert sorted(f["sha"] for f in found.values()) == sorted([first, second])


def test_a_commit_with_a_hash_is_never_taken_by_evidence_without_one(tmp_path):
    repo = Repo(tmp_path / "p")
    sha = repo.commit("meu.py")
    now = datetime.now(UTC).isoformat()
    found = facts(repo.root, q("sem", None, now), q("com", sha, now))
    assert found["com"]["sha"] == sha and found["sem"]["sha"] is None


def test_a_remote_default_branch_whose_name_looks_like_an_option_never_reaches_git_as_one(tmp_path):
    repo = Repo(tmp_path / "p")
    sha = repo.commit("meu.py")
    repo("update-ref", "refs/remotes/origin/main", "HEAD")
    repo("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    repo("update-ref", "refs/remotes/--output=x", "HEAD")
    repo("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/--output=x")
    assert main_branch(repo.root) == "--output=x"                                                       # o nome é só um nome: o git recebe o ref completo
    facts(repo.root, q("k", sha))
    assert not (repo.root / "x").exists() and not (repo.root / ".git" / "x").exists()               # e nada foi gravado
