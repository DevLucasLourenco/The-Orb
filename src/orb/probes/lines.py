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
import stat as _stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

MAX_FILE_BYTES = 2 * 1024 * 1024     # arquivo maior que isto não é código de verdade (dump, dado): fica de fora
GIT_TIMEOUT_SECONDS = 30.0
_PEEK_BYTES = 8192                   # um byte nulo no começo marca arquivo binário
_GIT_REDIRECTS = frozenset({"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_NAMESPACE", "GIT_CEILING_DIRECTORIES"})


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
    root: int = 0       # destas, as dos arquivos que estão na raiz do projeto (o térreo do prédio)
    folders: dict[str, int] = field(default_factory=dict)      # e as de cada pasta de primeiro nível (o fundo soma na pasta)


def _git_env() -> dict[str, str]:
    """O ambiente do processo sem as variáveis que redirecionariam o git para outro repositório ou índice."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECTS}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _git(root: Path, *args: str) -> list[str] | None:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)          # no Windows, sem abrir uma janela de console
    try:
        # `core.fsmonitor=false`: um repositório não pode mandar este processo executar um programa dele.
        done = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
                              capture_output=True, stdin=subprocess.DEVNULL, timeout=GIT_TIMEOUT_SECONDS,
                              env=_git_env(), creationflags=flags, check=False)
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
    return any(fnmatch.fnmatchcase(rel if "/" in pattern else name, pattern) for pattern in flt.exclude)


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
        if not _stat.S_ISREG(stat.st_mode) or stat.st_size > max_file_bytes:
            continue                                      # `lstat`: link e pasta (submódulo) não são arquivo comum
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
            head = handle.read(_PEEK_BYTES)
            if head[:2] in (b"\xff\xfe", b"\xfe\xff"):          # UTF-16 com BOM é texto (tem bytes nulos de verdade)
                return sum(1 for line in handle_text(path) if line.strip())
            if b"\0" in head:
                return None
            handle.seek(0)
            return sum(1 for line in handle if line.strip())
    except (OSError, UnicodeError):
        return None


def handle_text(path: Path):
    """As linhas de um arquivo UTF-16 (o BOM diz a ordem dos bytes); erro de decodificação vira linha de substituição."""
    with open(path, encoding="utf-16", errors="replace") as text:
        yield from text


def count_lines(root: Path, entries: list[Entry]) -> Count:
    """Conta as linhas e as reparte entre a raiz e as pastas de primeiro nível: `root + soma(folders) == loc`."""
    loc = files = at_root = 0
    folders: dict[str, int] = {}
    for entry in entries:
        counted = _count_file(root / entry.rel)
        if counted is None:
            continue
        loc += counted
        files += 1
        top, slash, _ = entry.rel.partition("/")
        if slash:
            folders[top] = folders.get(top, 0) + counted
        else:
            at_root += counted
    return Count(loc, files, at_root, folders)
