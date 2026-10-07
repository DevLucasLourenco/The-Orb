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


def classify_command(command: str | None) -> str:
    """Atividade do mundo para um comando de shell. Nunca levanta."""
    if not command or not isinstance(command, str):
        return "EXECUTING"
    head = first_command(command)
    for activity, pattern in _COMPILED:
        if pattern.match(head):
            return activity
    return "EXECUTING"
