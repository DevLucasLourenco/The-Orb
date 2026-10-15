"""Como os Probes falam com o git (R16): só leitura, sem tocar no `.git` e sem executar nada do projeto.

Todo comando roda com `--no-optional-locks` (o git não atualiza o índice só por olhar), `core.fsmonitor=false` (um repositório
não pode mandar este processo executar um programa dele), sem entrada, com tempo máximo e num ambiente sem as variáveis que
redirecionariam o git para outro repositório ou índice.

Limite conhecido: `git status` e `git diff` podem rodar um filtro `clean` que o próprio projeto declare no `.git/config` e no
`.gitattributes` (um programa do projeto). O Orb não consegue desligar isso de forma geral; fica anotado como risco residual.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

GIT_TIMEOUT_SECONDS = 30.0
_GIT_REDIRECTS = frozenset({"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_NAMESPACE", "GIT_CEILING_DIRECTORIES"})


def git_env() -> dict[str, str]:
    """O ambiente do processo sem as variáveis que redirecionariam o git para outro repositório ou índice."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECTS}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def run_git(root: Path, *args: str) -> bytes | None:
    """A saída do git em `root`, ou `None` se ele não existe, deu erro ou passou do tempo."""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)          # no Windows, sem abrir uma janela de console
    try:
        done = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
                              capture_output=True, stdin=subprocess.DEVNULL, timeout=GIT_TIMEOUT_SECONDS,
                              env=git_env(), creationflags=flags, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None
