"""Pasta de uma sessão -> projeto (R3, R3b, R3d; D-029, D-031).

O Lucas nunca informa caminhos: a pasta onde cada sessão rodou vira o projeto assim.

1. Vence a raiz que o próprio provider informa (Hermes: `git_repo_root`), se ela contém a pasta.
2. Senão sobe da pasta até o repositório git, **só lendo arquivos** (nada é executado, nada é gravado):
   `.git` como pasta é o repositório; como arquivo, num worktree (`commondir`) leva ao repositório
   principal, e num submódulo (sem `commondir`) a própria pasta é o projeto.
3. Sem repositório, a própria pasta da sessão é o projeto.

Ficam de fora: a pasta do usuário em si, pastas de sistema e temporárias (`AppData`, `Temp`,
`Downloads`...), a raiz do disco, e qualquer pasta que não exista mais no disco.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..adapters._shared import norm_path

# Variáveis de ambiente do Windows que apontam para pastas de sistema (nunca são projeto).
_SYSTEM_VARIABLES = ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramData")
_TEMP_VARIABLES = ("TEMP", "TMP", "TMPDIR")


@dataclass(frozen=True)
class Exclusions:
    """O que não é projeto: `exact` só a própria pasta (a do usuário); `inside` a pasta e tudo dentro."""
    exact: tuple[str, ...] = ()
    inside: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "exact", tuple(norm_path(str(p)) for p in self.exact))
        object.__setattr__(self, "inside", tuple(norm_path(str(p)) for p in self.inside))

    def covers(self, path: str) -> bool:
        key = norm_path(path)
        return key in self.exact or any(_inside(key, root) for root in self.inside)


def default_exclusions(home: Path | str | None = None, env: Mapping[str, str] | None = None) -> Exclusions:
    """As exclusões desta máquina. `home` e `env` entram por parâmetro (testes)."""
    real = env is None
    env = os.environ if env is None else env
    home = Path(home) if home else Path.home()
    inside: list[str] = [str(home / "AppData"), str(home / "Downloads")]
    inside += [env[name] for name in _TEMP_VARIABLES + _SYSTEM_VARIABLES if env.get(name)]
    if real:
        inside.append(tempfile.gettempdir())
        if os.name != "nt":
            inside.append("/tmp")
    return Exclusions(exact=(str(home),), inside=tuple(inside))


class ProjectResolver:
    """Decide a qual projeto pertence a pasta de uma sessão (ou `None`: não é projeto)."""

    def __init__(self, exclusions: Exclusions | None = None) -> None:
        self.exclusions = exclusions or default_exclusions()

    def project_of(self, cwd: Any, provider_root: Any = None, *, fallback: bool = True) -> str | None:
        """O projeto da pasta, ou `None`. Com `fallback=False` só vale evidência (raiz do provider ou
        repositório git): sem ela devolve `None` em vez de tratar a própria pasta como projeto, para quem
        quiser antes reaproveitar um projeto já conhecido que a contenha."""
        folder = _clean(cwd)
        if folder is None or not self._valid(folder):
            return None
        root = _clean(provider_root)
        if root is not None and self._valid(root) and _inside(norm_path(folder), norm_path(root)):
            repo = root if os.path.exists(os.path.join(root, ".git")) else None
            project = self._project_for_repo(repo) if repo else root
        else:
            repo = self._repo_above(folder)
            if repo is None and not fallback:
                return None
            project = self._project_for_repo(repo) if repo else folder
        return project if project is not None and self._valid(project) else None

    def _valid(self, path: str) -> bool:
        """Existe no disco, não é a raiz do disco e não está nas exclusões."""
        return os.path.dirname(path) != path and os.path.isdir(path) and not self.exclusions.covers(path)

    def _repo_above(self, folder: str) -> str | None:
        """A pasta mais próxima, de `folder` para cima, que tem `.git`. Para antes de qualquer pasta
        excluída (ex.: um repositório de dotfiles na pasta do usuário não engole os projetos abaixo)."""
        current = folder
        while not self.exclusions.covers(current) and os.path.dirname(current) != current:
            if os.path.exists(os.path.join(current, ".git")):
                return current
            current = os.path.dirname(current)
        return None

    @staticmethod
    def _project_for_repo(repo: str) -> str | None:
        """O projeto de uma pasta que tem `.git`; `None` para worktree cujo principal sumiu."""
        git = os.path.join(repo, ".git")
        if os.path.isdir(git):
            return repo
        pointer = _first_line(git)
        if pointer is None or not pointer.startswith("gitdir:"):
            return repo                                    # `.git` ilegível: a pasta é o projeto
        git_dir = os.path.normpath(os.path.join(repo, pointer.removeprefix("gitdir:").strip()))
        if not os.path.isdir(git_dir):
            return None                                    # worktree órfão
        common = _first_line(os.path.join(git_dir, "commondir"))
        if common is None:
            return repo                                    # submódulo: tem a própria pasta
        main_git = os.path.normpath(os.path.join(git_dir, common))
        main = os.path.dirname(main_git) if os.path.basename(main_git).lower() == ".git" else main_git
        return main if os.path.isdir(main) else None


def _clean(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip() or not os.path.isabs(value):
        return None
    return os.path.normpath(value)


def _inside(path: str, root: str) -> bool:
    """`path` já normalizado (`norm_path`) é `root` ou está dentro dele?"""
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def _first_line(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            line = fh.readline(4096).strip()
    except OSError:
        return None
    return line or None
