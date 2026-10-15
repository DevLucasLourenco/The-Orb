"""As alterações locais do projeto (R20b, R20d, R20e, R16): um Probe, só leitura.

Uma **alteração** é um arquivo com alteração local no git: modificado, adicionado, não rastreado, renomeado, apagado ou em
conflito. O **peso** dela são as linhas alteradas (inseridas mais removidas; arquivo novo = as linhas dele; binário = 1).
Arquivo ignorado pelo `.gitignore` e submódulo (outro repositório) não entram. Tudo vem de `git status` e `git diff --numstat`,
com `--no-optional-locks`: nada é gravado no projeto nem no `.git`. Sem repositório não há resposta (`None`), nunca um "limpo".
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from ..protocol import MAX_CHANGES, valid_change_path
from .git import run_git
from .lines import MAX_FILE_BYTES

__all__ = ["Change", "ChangeSet", "changes_fingerprint", "git_changes", "parse_numstat", "parse_status"]


@dataclass(frozen=True)
class Change:
    path: str          # relativo à raiz do projeto, com `/`
    type: str          # modified · added · untracked · renamed · deleted · conflict (vocabulário do protocolo)
    lines: int         # o peso: linhas alteradas, no mínimo 1


@dataclass(frozen=True)
class ChangeSet:
    items: list[Change]        # as primeiras `limit` pelo caminho
    more: int = 0              # quantas passaram do limite e ficaram de fora


def change_type(xy: str) -> str:
    """O tipo que as duas letras do `git status` (índice e árvore de trabalho) dão: renomeado e adicionado ganham de apagado e
    de modificado (um arquivo novo no índice que se editou depois continua sendo "adicionado")."""
    if "R" in xy:
        return "renamed"
    if xy[0] in "AC":
        return "added"
    if "D" in xy:
        return "deleted"
    return "modified"


def _path(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace").replace("\\", "/")


def parse_status(raw: bytes) -> list[tuple[str, str]]:
    """`git status --porcelain=v2 -z` -> (caminho, tipo). Submódulo, ignorado e registro que não se entende ficam de fora."""
    fields = raw.split(b"\0")
    out: list[tuple[str, str]] = []
    i = 0
    while i < len(fields):
        record, i = fields[i], i + 1
        kind = record[:1]
        if kind == b"?":
            out.append((_path(record[2:]), "untracked"))
        elif kind == b"1":
            parts = record.split(b" ", 8)
            if len(parts) == 9 and not parts[2].startswith(b"S"):          # "S..." é submódulo (R20e)
                out.append((_path(parts[8]), change_type(parts[1].decode("ascii", "replace"))))
        elif kind == b"2":
            parts = record.split(b" ", 9)
            if len(parts) == 10:
                i += 1                                                       # o caminho antigo vem num campo à parte
                if not parts[2].startswith(b"S"):
                    out.append((_path(parts[9]), change_type(parts[1].decode("ascii", "replace"))))
        elif kind == b"u":
            parts = record.split(b" ", 10)
            if len(parts) == 11 and not parts[2].startswith(b"S"):
                out.append((_path(parts[10]), "conflict"))
    return out


def parse_numstat(raw: bytes) -> dict[str, int]:
    """`git diff --numstat -z` -> caminho -> linhas alteradas (inseridas + removidas; binário vale 1)."""
    fields = raw.split(b"\0")
    weights: dict[str, int] = {}
    i = 0
    while i < len(fields):
        record, i = fields[i], i + 1
        parts = record.split(b"\t", 2)
        if len(parts) != 3:
            continue
        inserted, removed, path = parts
        if not path and i + 1 < len(fields):                                 # renomeado: o caminho antigo e o novo vêm em seguida
            path, i = fields[i + 1], i + 2
        if not path:
            continue
        try:
            weight = int(inserted) + int(removed)
        except ValueError:
            weight = 1                                                       # "-": arquivo binário
        weights[_path(path)] = weight
    return weights


def _base(root: Path) -> str:
    """Contra o que comparar: o último commit ou, num repositório sem commits, a árvore vazia."""
    if run_git(root, "rev-parse", "--verify", "-q", "HEAD") is not None:
        return "HEAD"
    empty = run_git(root, "hash-object", "-t", "tree", "--stdin")
    return empty.decode("ascii", "replace").strip() if empty else "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def _new_file_lines(root: Path, rel: str) -> int:
    """As linhas de um arquivo novo (todas, como o `diff --numstat` conta as de um arquivo adicionado); binário, grande demais
    ou ilegível vale 1."""
    path = root / rel
    try:
        if not path.is_file() or path.is_symlink() or os.path.getsize(path) > MAX_FILE_BYTES:
            return 1
        data = path.read_bytes()
    except OSError:
        return 1
    if b"\0" in data[:8192]:
        return 1
    return data.count(b"\n") + (0 if not data or data.endswith(b"\n") else 1)


def git_changes(root: Path, *, limit: int = MAX_CHANGES) -> ChangeSet | None:
    """As alterações locais de `root`, ordenadas pelo caminho, ou `None` se o git não responde (sem repositório, sem git)."""
    out = run_git(root, "status", "--porcelain=v2", "-z", "--untracked-files=all", "--ignore-submodules=all")
    if out is None:
        return None
    parsed = sorted(set(parse_status(out)))
    found = [item for item in parsed if valid_change_path(item[0])]     # um caminho que o protocolo recusaria derrubaria o evento todo
    chosen = found[:limit]
    diff = run_git(root, "diff", _base(root), "--numstat", "-z", "-M", "--no-ext-diff", "--no-textconv", "--ignore-submodules=all")
    weights = parse_numstat(diff) if diff is not None else {}
    items = []
    for path, kind in chosen:
        weight = _new_file_lines(root, path) if kind == "untracked" else weights.get(path, 0)
        items.append(Change(path, kind, max(1, weight)))
    return ChangeSet(items, max(0, len(parsed) - len(chosen)))


def changes_fingerprint(items: list[Change], more: int = 0) -> str:
    """Muda quando uma alteração aparece, some ou muda de tipo ou de peso, ou quando muda quantas ficaram de fora."""
    digest = hashlib.sha1(usedforsecurity=False)
    digest.update(f"{more}".encode())
    for change in items:
        digest.update(f"\0{change.path}\0{change.type}\0{change.lines}".encode())
    return digest.hexdigest()
