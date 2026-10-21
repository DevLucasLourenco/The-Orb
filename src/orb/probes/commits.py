"""Os commits que as sessões fizeram, vistos pelo git (R53, R16): um Probe, só leitura.

A XP de um commit é provisória até o mundo real confirmar (PROGRESSION.md §1 e §3): o commit existe, chegou à **branch principal** e
não foi revertido. Quem pergunta é o mundo (cada sessão que disse ter feito um commit); este Probe só responde o que o git sabe. Tudo
sai de `rev-parse`, `rev-list`, `show --numstat` e `log`, pelo `git.py` (sem gravar no projeto nem no `.git`). Sem repositório não há
resposta (`None`). Commits do Lucas, sem uma sessão que os reivindique, nunca são perguntados e por isso nunca rendem XP (D-106).

A **branch principal** é a padrão do remoto (`origin/HEAD`); sem ela, a local `main` e depois `master`. Com remoto, um commit só
"chegou" quando o remoto o tem (a leitura é do que o git local sabe do remoto: o `fetch` e o `push` do Lucas atualizam isso).
"""
from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..protocol import valid_sha
from .git import run_git

__all__ = ["CommitQuery", "commits_fingerprint", "git_commits", "main_branch"]

MATCH_WINDOW_SECONDS = 120.0       # sem hash, o commit é o do repositório mais perto da hora da evidência, dentro desta janela
RECENT_COMMITS = 300               # quantos commits recentes olhar ao procurar por hora


@dataclass(frozen=True)
class CommitQuery:
    key: str                       # o recibo que o mundo pediu (volta no resultado)
    sha: str | None                # o hash que o provider deu (Claude), ou `None`
    at: str                        # a hora da evidência (ISO com fuso)


def _text(raw: bytes | None) -> str:
    return raw.decode("utf-8", errors="replace").strip() if raw else ""


def main_branch(root: Path) -> str | None:
    """A branch principal do projeto: a padrão do remoto (`origin/HEAD`), senão `main`, senão `master`; `None` se não há nenhuma."""
    remote = _text(run_git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"))
    if remote and run_git(root, "rev-parse", "--verify", "--quiet", f"refs/remotes/{remote}") is not None:
        return remote
    for name in ("main", "master"):
        if run_git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}") is not None:
            return name
    return None


def _lines_of(root: Path, sha: str) -> int | None:
    """As linhas que o commit alterou (inseridas mais removidas; binário vale 1, como nas alterações locais)."""
    raw = run_git(root, "show", "--numstat", "--format=", "--no-ext-diff", "-M", sha)
    if raw is None:
        return None
    total = 0
    for line in raw.decode("utf-8", errors="replace").splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 3:
            continue
        added, removed = parts[0], parts[1]
        total += int(added) + int(removed) if added.isdigit() and removed.isdigit() else 1
    return total


def _recent(root: Path) -> list[tuple[str, float]]:
    """Os commits recentes de todas as branches (hash, hora do commit em segundos), para achar o que não veio com hash."""
    out: list[tuple[str, float]] = []
    for line in _text(run_git(root, "log", "--all", f"-n{RECENT_COMMITS}", "--format=%H%x09%ct")).splitlines():
        sha, _, stamp = line.partition("\t")
        if stamp.isdigit():
            out.append((sha, float(stamp)))
    return out


def _seconds(at: str) -> float | None:
    try:
        moment = datetime.fromisoformat(at)
    except (TypeError, ValueError):
        return None
    return moment.timestamp() if moment.utcoffset() is not None else None


def git_commits(root: Path, queries: Sequence[CommitQuery]) -> list[dict[str, Any]] | None:
    """O que o git sabe de cada commit pedido, na mesma ordem. `None` se `root` não é um repositório (ou o git não respondeu)."""
    if run_git(root, "rev-parse", "--git-dir") is None:
        return None
    if not queries:
        return []
    main = main_branch(root)
    recent: list[tuple[str, float]] | None = None
    claimed: set[str] = set()
    facts: list[dict[str, Any]] = []
    for query in queries:
        full = _text(run_git(root, "rev-parse", "--verify", "--quiet", f"{query.sha}^{{commit}}")) if query.sha and valid_sha(query.sha) else ""
        if not full and not query.sha:
            if recent is None:
                recent = _recent(root)
            when = _seconds(query.at)
            near = sorted(((abs(ts - when), sha) for sha, ts in recent if sha not in claimed), key=lambda item: item[0]) if when is not None else []
            full = near[0][1] if near and near[0][0] <= MATCH_WINDOW_SECONDS else ""
        if full:
            claimed.add(full)
        on_main = bool(full) and main is not None and run_git(root, "rev-list", "-n", "1", full, "--not", main) == b""
        reverted = bool(full) and main is not None and bool(_text(run_git(
            root, "log", main, "--fixed-strings", f"--grep=This reverts commit {full}", "-n", "1", "--format=%H")))
        facts.append({"key": query.key, "sha": full or None, "exists": bool(full), "lines": _lines_of(root, full) if full else None,
                      "on_main": on_main, "reverted": reverted})
    return facts


def commits_fingerprint(facts: Sequence[dict[str, Any]]) -> str:
    """Muda só quando algo que o mundo usa muda (o resto do evento seria repetido à toa)."""
    digest = hashlib.sha256()
    for fact in sorted(facts, key=lambda f: f["key"]):
        digest.update(repr((fact["key"], fact["sha"], fact["exists"], fact["lines"], fact["on_main"], fact["reverted"])).encode())
    return digest.hexdigest()
