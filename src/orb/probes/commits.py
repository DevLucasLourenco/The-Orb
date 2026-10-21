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
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..protocol import valid_sha
from .git import run_git

__all__ = ["CommitQuery", "commits_fingerprint", "git_commits", "main_branch"]

MATCH_WINDOW_SECONDS = 120.0       # sem hash, o commit é o do repositório mais perto da hora da evidência, dentro desta janela
RECENT_COMMITS = 300               # quantos commits recentes olhar ao procurar por hora
REVERT_SCAN = 2000                 # quantos commits da principal olhar atrás de reversões (uma varredura por leitura, não uma por commit)
_REVERTS = re.compile(r"This reverts commit ([0-9a-fA-F]{40,64})")


@dataclass(frozen=True)
class CommitQuery:
    key: str                       # o recibo que o mundo pediu (volta no resultado)
    sha: str | None                # o hash que o provider deu (Claude), ou `None`
    at: str                        # a hora da evidência (ISO com fuso)


def _text(raw: bytes | None) -> str:
    return raw.decode("utf-8", errors="replace").strip() if raw else ""


def _main_ref(root: Path) -> str | None:
    """O ref completo da branch principal (sempre `refs/...`: um nome que vem do repositório nunca vira opção do git)."""
    remote = _text(run_git(root, "symbolic-ref", "refs/remotes/origin/HEAD"))
    if remote.startswith("refs/remotes/") and run_git(root, "rev-parse", "--verify", "--quiet", remote) is not None:
        return remote
    for name in ("main", "master"):
        if run_git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}") is not None:
            return f"refs/heads/{name}"
    return None


def main_branch(root: Path) -> str | None:
    """A branch principal do projeto: a padrão do remoto (`origin/HEAD`), senão `main`, senão `master`; `None` se não há nenhuma."""
    ref = _main_ref(root)
    return None if ref is None else ref.removeprefix("refs/remotes/").removeprefix("refs/heads/")


@lru_cache(maxsize=4096)
def _lines_of(root: Path, sha: str) -> int | None:
    """As linhas que o commit alterou (inseridas mais removidas; binário vale 1, como nas alterações locais). Um commit nunca muda: o
    resultado fica guardado, e a leitura de cada minuto não o pede ao git de novo."""
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


def _reverted(root: Path, main: str) -> set[str]:
    """Os commits que a principal já reverteu: uma só varredura das mensagens de `git revert` (\"This reverts commit <hash>\")."""
    raw = _text(run_git(root, "log", main, "--fixed-strings", "--grep=This reverts commit", f"-n{REVERT_SCAN}", "--format=%B%x00"))
    return {m.group(1).lower() for m in _REVERTS.finditer(raw)}


def _link_by_time(queries: Sequence[CommitQuery], recent: list[tuple[str, float]], claimed: set[str]) -> dict[str, str]:
    """Liga cada evidência sem hash ao commit do repositório mais perto da hora dela (até `MATCH_WINDOW_SECONDS`). Se na janela há **mais**
    commits do que evidências, alguém além da sessão commitou (o Lucas): não se adivinha, e a evidência fica sem ligação (D-106)."""
    stamps = {q.key: _seconds(q.at) for q in queries}
    known = [t for t in stamps.values() if t is not None]
    linked: dict[str, str] = {}
    for query in sorted((q for q in queries if stamps[q.key] is not None), key=lambda q: stamps[q.key]):
        when = stamps[query.key]
        near = sorted((abs(ts - when), sha) for sha, ts in recent if abs(ts - when) <= MATCH_WINDOW_SECONDS and sha not in claimed)
        witnesses = sum(1 for t in known if abs(t - when) <= MATCH_WINDOW_SECONDS)
        if near and len(near) <= witnesses:
            linked[query.key] = near[0][1]
            claimed.add(near[0][1])
    return linked


def git_commits(root: Path, queries: Sequence[CommitQuery]) -> list[dict[str, Any]] | None:
    """O que o git sabe de cada commit pedido, na mesma ordem. `None` se `root` não é um repositório (ou o git não respondeu)."""
    if run_git(root, "rev-parse", "--git-dir") is None:
        return None
    if not queries:
        return []
    main = _main_ref(root)
    reverted = _reverted(root, main) if main is not None else set()
    resolved: dict[str, str] = {}
    for query in queries:                                       # primeiro quem trouxe o hash: ele vale e ninguém mais o leva
        if query.sha and valid_sha(query.sha):
            full = _text(run_git(root, "rev-parse", "--verify", "--quiet", f"{query.sha}^{{commit}}"))
            if full:
                resolved[query.key] = full
    blind = [q for q in queries if not q.sha]
    if blind:
        resolved.update(_link_by_time(blind, _recent(root), set(resolved.values())))
    facts: list[dict[str, Any]] = []
    for query in queries:
        full = resolved.get(query.key, "")
        on_main = bool(full) and main is not None and run_git(root, "rev-list", "-n", "1", full, "--not", main) == b""
        facts.append({"key": query.key, "sha": full or None, "exists": bool(full), "lines": _lines_of(root, full) if full else None,
                      "on_main": on_main, "reverted": full.lower() in reverted})
    return facts


def commits_fingerprint(facts: Sequence[dict[str, Any]]) -> str:
    """Muda só quando algo que o mundo usa muda (o resto do evento seria repetido à toa)."""
    digest = hashlib.sha256()
    for fact in sorted(facts, key=lambda f: f["key"]):
        digest.update(repr((fact["key"], fact["sha"], fact["exists"], fact["lines"], fact["on_main"], fact["reverted"])).encode())
    return digest.hexdigest()
