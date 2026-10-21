"""Classificador de comandos de shell -> atividade no mundo (tabela declarativa).

Só alimenta o sinal de mundo: o comando continua aparecendo no Inner World como o provider o
escreveu. Usado quando o provider não diz o que o comando faz (Codex sem `Read`, `Bash` do Claude).
Padrão seguro: EXECUTING.
"""
from __future__ import annotations

import re

# (atividade, padrão aplicado ao INÍCIO do primeiro comando, já sem o invólucro de shell).
# A ordem importa: o primeiro que casar vence.
COMMAND_TABLE: tuple[tuple[str, str], ...] = (
    ("TESTING", r"(python3?|py)(\.exe)?\s+-m\s+(pytest|unittest)\b"),
    ("TESTING", r"(pytest|jest|vitest|mocha|tox|nox|phpunit|rspec)\b"),
    ("TESTING", r"(npm|pnpm|yarn|bun)\s+(run\s+)?test\b"),
    ("TESTING", r"(go|cargo|dotnet|mvn|gradle|\./gradlew|mix|deno)\s+test\b"),
    ("TESTING", r"invoke-pester\b"),
    ("REVIEWING", r"gh\s+pr\s+(view|diff|review|checks)\b"),
    ("READING", r"git\s+(status|log|diff|show|blame|grep|ls-files)\b"),
    ("READING", r"(get-content|gc|cat|type|head|tail|less|more|bat|nl|wc)\b"),
    ("READING", r"(select-string|sls|grep|rg|ag|findstr)\b"),
    ("READING", r"(get-childitem|gci|ls|dir|tree|find|fd|resolve-path|test-path)\b"),
    ("RESEARCHING", r"(curl|wget|invoke-webrequest|iwr|invoke-restmethod|irm)\b"),
)

_COMPILED = tuple((activity, re.compile(pattern, re.IGNORECASE)) for activity, pattern in COMMAND_TABLE)

# Invólucros de shell: `powershell.exe -NoProfile -Command "..."`, `bash -lc '...'`, `cmd /c ...`.
_WRAPPER = re.compile(
    r"""^\s*["']?(?:[^"'\s]*[\\/])?(?:powershell|pwsh|bash|sh|zsh|cmd)(?:\.exe)?["']?"""
    r"""(?:\s+-(?:NoProfile|NoLogo|NonInteractive|ExecutionPolicy\s+\S+|l))*"""
    r"""\s+(?:-Command|-c|-lc|/c)\s+(.*)$""",
    re.IGNORECASE | re.DOTALL,
)
_SEPARATORS = re.compile(r"\s*(?:;|&&|\|\||\||\n)\s*")


def unwrap(command: str) -> str:
    """Tira o invólucro de shell e as aspas externas, se houver."""
    text = command.strip()
    match = _WRAPPER.match(text)
    if match:
        text = match.group(1).strip()
        if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
            text = text[1:-1]
    return text.strip()


def first_command(command: str) -> str:
    inner = unwrap(command)
    for part in _SEPARATORS.split(inner):
        part = part.strip().lstrip("&").strip()
        if part:
            return part
    return ""


def exit_code_of(value: object) -> int | None:
    """O código de saída que um provider gravou: só um inteiro de verdade (`bool` não é código). Nada mais afirma resultado."""
    return value if isinstance(value, int) and not isinstance(value, bool) else None


# `git commit` em qualquer ponto de uma linha de comando (depois de `&&`, `;`, `|`, de um invólucro de shell ou de opções do git como
# `-C pasta` e `-c chave=valor`). `commit-tree` e afins não são: depois de `commit` vem espaço ou o fim.
_GIT_COMMIT = re.compile(r"(?:^|[\s;&|\"'(])git(?:\s+-[Cc]\s+\S+|\s+--[\w-]+(?:=\S+)?)*\s+commit(?=\s|$|[\"'])", re.IGNORECASE)
_DRY_RUN = re.compile(r"\s--dry-run\b")
_ECHO = re.compile(r"^\s*(echo|write-host|write-output|printf)\b", re.IGNORECASE)


def is_git_commit(command: str | None) -> bool:
    """O comando faz um `git commit` de verdade? Usado só pelos providers que não dizem isso (Claude diz: `gitOperation`, D-090). Não
    conta `--dry-run`, nem um `echo` que cita o comando."""
    if not command or not isinstance(command, str) or _ECHO.match(unwrap(command)):
        return False
    return any(_GIT_COMMIT.search(part) and not _DRY_RUN.search(part) for part in _SEPARATORS.split(unwrap(command)))


def result_signal(command: str | None, *, ok: bool, exit_code: int | None = None, activity: str | None = None,
                  commit: bool | None = None, sha: str | None = None) -> dict[str, object]:
    """O sinal `command.result` de um comando de shell: passou ou falhou, a atividade dele (a que o provider deu ou, senão, a do
    classificador) e o código de saída só quando o provider o informa (o Claude não informa: R42, D-084). `commit`: o comando fez um
    commit (e deu certo); o provider que sabe diz (`True`/`False`, com o `sha` se tem), os outros deixam `None` e vale o texto do comando."""
    signal: dict[str, object] = {"type": "command.result", "ok": ok, "activity": activity or classify_command(command)}
    if exit_code_of(exit_code) is not None:
        signal["exit_code"] = exit_code
    if ok and (is_git_commit(command) if commit is None else commit):
        signal["commit"] = {"sha": sha} if sha else {}
    return signal


def classify_command(command: str | None) -> str:
    """Atividade do mundo para um comando de shell. Nunca levanta."""
    if not command or not isinstance(command, str):
        return "EXECUTING"
    head = first_command(command)
    for activity, pattern in _COMPILED:
        if pattern.match(head):
            return activity
    return "EXECUTING"
