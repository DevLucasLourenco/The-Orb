"""O contador de linhas do projeto (R19, D-053 a D-056): um Probe, só leitura.

Conta as linhas **não vazias** (comentários contam) dos arquivos que o git acompanha, sem os que o `.gitignore`
ignora, sem a lista visível de arquivos gerados e, por padrão, sem `.md`. A lista de arquivos vem do `git ls-files`
(com `--no-optional-locks`): nada é gravado no projeto nem no `.git`, e nenhum arquivo do projeto é executado. Sem
repositório ou sem git, não há lista e portanto não há contagem: o prédio fica sem número, nunca com um zero inventado.

Pasta de projeto grande custa leitura: por isso o Probe separa **listar** (barato: `git ls-files` e um `stat` por
arquivo), **identificar mudança** (`fingerprint`) e **contar** (lê os arquivos). Quem agenda só conta de novo quando a
impressão digital muda.
"""
from __future__ import annotations

import fnmatch
import hashlib
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

MAX_FILE_BYTES = 2 * 1024 * 1024     # arquivo maior que isto não é código de verdade (dump, dado): fica de fora
GIT_TIMEOUT_SECONDS = 30.0
_PEEK_BYTES = 8192                   # um byte nulo no começo marca arquivo binário


class Filter(Protocol):
    """O que o Probe precisa do filtro de tipos e exclusões (`orb.core.rules.LineFilter` é o padrão do Orb)."""
    include_markdown: bool
    exclude: tuple[str, ...]


@dataclass(frozen=True)
class Entry:
    rel: str            # caminho relativo à raiz do projeto, com `/`
    size: int
    mtime_ns: int


@dataclass(frozen=True)
class Count:
    loc: int            # linhas não vazias
    files: int          # arquivos de texto que entraram na conta


def _git(root: Path, *args: str) -> list[str] | None:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)          # no Windows, sem abrir uma janela de console
    try:
        done = subprocess.run(["git", "--no-optional-locks", "-C", str(root), *args], capture_output=True,
                              timeout=GIT_TIMEOUT_SECONDS, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
                              creationflags=flags, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    return [name for name in done.stdout.decode("utf-8", errors="replace").split("\0") if name]


def git_tracked_files(root: Path) -> list[str] | None:
    """Os arquivos que o git acompanha em `root`, menos os que o `.gitignore` ignora; `None` se não der para saber."""
    tracked = _git(root, "ls-files", "-z")
    if tracked is None:
        return None
    ignored = _git(root, "ls-files", "-z", "-c", "-i", "--exclude-standard")
    skip = set(ignored or ())
    return [name for name in tracked if name not in skip]


def _excluded(rel: str, flt: Filter) -> bool:
    if not flt.include_markdown and rel.lower().endswith(".md"):
        return True
    name = rel.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(rel if "/" in pattern else name, pattern) for pattern in flt.exclude)


def list_countable(root: Path, flt: Filter, tracked: Callable[[Path], list[str] | None] = git_tracked_files,
                   *, max_file_bytes: int = MAX_FILE_BYTES) -> list[Entry] | None:
    """Os arquivos que entram na conta, com tamanho e data. Link, pasta (submódulo), arquivo sumido ou grande demais ficam
    de fora. `None` quando o git não diz quais são os arquivos."""
    names = tracked(root)
    if names is None:
        return None
    entries = []
    for name in names:
        rel = name.replace("\\", "/")
        if _excluded(rel, flt):
            continue
        path = root / rel
        try:
            stat = os.lstat(path)
        except OSError:
            continue
        if not os.path.isfile(path) or os.path.islink(path) or stat.st_size > max_file_bytes:
            continue
        entries.append(Entry(rel, stat.st_size, stat.st_mtime_ns))
    return entries


def fingerprint(entries: list[Entry], flt: Filter) -> str:
    """Muda quando um arquivo que conta é criado, apagado ou alterado, ou quando o filtro muda."""
    digest = hashlib.sha1(usedforsecurity=False)
    digest.update(repr((flt.include_markdown, tuple(flt.exclude))).encode("utf-8"))
    for entry in sorted(entries, key=lambda e: e.rel):
        digest.update(f"\0{entry.rel}\0{entry.size}\0{entry.mtime_ns}".encode())
    return digest.hexdigest()


def _count_file(path: Path) -> int | None:
    """Linhas não vazias, ou `None` se o arquivo é binário ou não abre."""
    try:
        with open(path, "rb") as handle:
            if b"\0" in handle.read(_PEEK_BYTES):
                return None
            handle.seek(0)
            return sum(1 for line in handle if line.strip())
    except OSError:
        return None


def count_lines(root: Path, entries: list[Entry]) -> Count:
    loc = files = 0
    for entry in entries:
        counted = _count_file(root / entry.rel)
        if counted is not None:
            loc += counted
            files += 1
    return Count(loc, files)
