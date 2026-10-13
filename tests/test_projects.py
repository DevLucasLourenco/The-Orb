"""Pasta de uma sessão -> projeto (R3, R3b, R3d), com pastas falsas em disco. Nenhum dado real."""
from pathlib import Path

import pytest

from orb.gateway.projects import Exclusions, ProjectResolver, default_exclusions


@pytest.fixture
def world(tmp_path):
    """Uma 'máquina' falsa: home do usuário, pastas de sistema e temporárias, e a pasta dos projetos."""
    home = tmp_path / "home"
    for folder in ("AppData/Local/Temp", "Downloads", "work"):
        (home / folder).mkdir(parents=True)
    system = tmp_path / "Windows"
    system.mkdir()
    resolver = ProjectResolver(Exclusions(exact=[home], inside=[home / "AppData", home / "Downloads", system]))
    return resolver, home, system


def repo(path: Path) -> Path:
    (path / ".git").mkdir(parents=True)
    return path


def same(a, b):
    return Path(a).resolve() == Path(b).resolve()


def test_a_folder_outside_a_repository_is_its_own_project(world):
    resolver, home, _ = world
    folder = home / "work" / "scripts"
    folder.mkdir()
    assert same(resolver.project_of(str(folder)), folder)


def test_climbs_from_a_subfolder_to_the_git_repository(world):
    resolver, home, _ = world
    project = repo(home / "work" / "trisafe")
    deep = project / "src" / "core"
    deep.mkdir(parents=True)
    assert same(resolver.project_of(str(deep)), project)


def test_a_worktree_counts_for_the_main_project(world):
    resolver, home, _ = world
    main = repo(home / "work" / "trisafe-enhanced")
    git_dir = main / ".git" / "worktrees" / "wt1"
    git_dir.mkdir(parents=True)
    (git_dir / "commondir").write_text("../..\n", encoding="utf-8")
    worktree = home / "work" / "wt1-checkout"                       # fora da pasta do projeto
    worktree.mkdir()
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")
    inside = main / ".claude" / "worktrees" / "wt2"                  # dentro da pasta do projeto, gitdir relativo
    (main / ".git" / "worktrees" / "wt2").mkdir(parents=True)
    (main / ".git" / "worktrees" / "wt2" / "commondir").write_text("../..\n", encoding="utf-8")
    (inside / "src").mkdir(parents=True)
    (inside / ".git").write_text("gitdir: ../../../.git/worktrees/wt2\n", encoding="utf-8")
    assert same(resolver.project_of(str(worktree)), main)
    assert same(resolver.project_of(str(inside / "src")), main)


def test_a_git_file_without_commondir_is_its_own_project(world):
    """Submódulo: o `.git` é um arquivo, mas aponta para `.git/modules/...` (sem `commondir`)."""
    resolver, home, _ = world
    sub = home / "work" / "super" / "libs" / "sub"
    sub.mkdir(parents=True)
    (home / "work" / "super" / ".git" / "modules" / "sub").mkdir(parents=True)
    (sub / ".git").write_text(f"gitdir: {home / 'work' / 'super' / '.git' / 'modules' / 'sub'}\n", encoding="utf-8")
    assert same(resolver.project_of(str(sub)), sub)


def test_the_root_the_provider_informs_wins(world):
    resolver, home, _ = world
    project = repo(home / "work" / "alpha")
    folder = project / "pkg"
    folder.mkdir()
    other = home / "work" / "beta"
    other.mkdir()
    assert same(resolver.project_of(str(folder), str(project)), project)
    assert same(resolver.project_of(str(folder), str(other)), project)    # raiz que não contém a pasta: ignorada
    assert same(resolver.project_of(str(folder), "C:/nao/existe"), project)


def test_user_folder_system_and_temporary_folders_are_not_projects(world):
    resolver, home, system = world
    assert resolver.project_of(str(home)) is None                         # a pasta do usuário em si
    assert resolver.project_of(str(home / "AppData" / "Local" / "Temp")) is None
    assert resolver.project_of(str(home / "AppData")) is None
    assert resolver.project_of(str(home / "Downloads")) is None
    (home / "Downloads" / "algo").mkdir()
    assert resolver.project_of(str(home / "Downloads" / "algo")) is None  # e tudo que está dentro delas
    assert resolver.project_of(str(system)) is None
    assert resolver.project_of(str(home.anchor)) is None                  # raiz do disco


def test_a_repository_in_the_user_folder_does_not_swallow_the_projects_below_it(world):
    resolver, home, _ = world
    (home / ".git").mkdir()                                               # ex.: repositório de dotfiles
    plain = home / "work" / "scripts"
    plain.mkdir()
    assert same(resolver.project_of(str(plain)), plain)


def test_folders_that_do_not_exist_are_not_projects(world):
    resolver, home, _ = world
    assert resolver.project_of(str(home / "work" / "apagado")) is None
    assert resolver.project_of(None) is None
    assert resolver.project_of("") is None
    assert resolver.project_of(42) is None
    gone = home / "work" / "wt-orfao"                                      # worktree cujo repositório principal sumiu
    gone.mkdir()
    (gone / ".git").write_text(f"gitdir: {home / 'work' / 'sumiu' / '.git' / 'worktrees' / 'x'}\n", encoding="utf-8")
    assert resolver.project_of(str(gone)) is None


def test_default_exclusions_come_from_the_machine(tmp_path):
    home = tmp_path / "me"
    rules = default_exclusions(home=home, env={"TEMP": str(tmp_path / "tmpdir"), "SystemRoot": str(tmp_path / "Win"),
                                               "ProgramFiles": str(tmp_path / "PF")})
    resolver = ProjectResolver(rules)
    for folder in (home, home / "AppData" / "Local", home / "Downloads", tmp_path / "tmpdir" / "x", tmp_path / "Win" / "System32",
                   tmp_path / "PF" / "app"):
        folder.mkdir(parents=True, exist_ok=True)
        assert resolver.project_of(str(folder)) is None, folder
    (home / "Documents" / "proj").mkdir(parents=True)
    assert resolver.project_of(str(home / "Documents" / "proj")) is not None


def test_without_the_fallback_only_evidence_makes_a_project(world):
    resolver, home, _ = world
    plain = home / "work" / "scripts"
    plain.mkdir()
    project = repo(home / "work" / "alpha")
    assert resolver.project_of(str(plain), fallback=False) is None
    assert same(resolver.project_of(str(project), fallback=False), project)
    assert same(resolver.project_of(str(plain), str(plain), fallback=False), plain)   # a raiz do provider é evidência

