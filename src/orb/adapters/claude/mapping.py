"""Mapa do provider Claude Code: evento nativo -> sinal de mundo e entrada de Inner World.

Só tabelas e funções puras. Formatos verificados em docs/adapters/CLAUDE.md (transcripts reais do
Claude Code 2.1.x e hooks ao vivo no Spike 3).
"""
from __future__ import annotations

import json
import re
from typing import Any

from .._shared import Capabilities, classify_command

PROVIDER = "claude"

CAPABILITIES = Capabilities(
    thought_fidelity=("raw",),          # raro: ~88% dos blocos de thinking vêm sem texto
    approvals="requested",              # PermissionRequest (nível 1); a decisão é deduzida
    subagents=True,
    human_origin="confirmed",           # origin.kind no transcript
    realtime=True,                      # nível 1: hooks por sessão (--settings)
    usage=True,
)

# Ferramenta nativa -> atividade no mundo. Bash/PowerShell usam o classificador de comandos.
TOOL_ACTIVITY: dict[str, str] = {
    "Read": "READING", "Glob": "READING", "Grep": "READING", "LS": "READING",
    "NotebookRead": "READING",
    "Edit": "CODING", "MultiEdit": "CODING", "Write": "CODING", "NotebookEdit": "CODING",
    "WebFetch": "RESEARCHING", "WebSearch": "RESEARCHING",
    "Agent": "DELEGATING", "Task": "DELEGATING",
    "TodoWrite": "THINKING", "TaskCreate": "THINKING", "TaskUpdate": "THINKING",
}
SHELL_TOOLS = frozenset({"Bash", "PowerShell"})
DELEGATING_TOOLS = frozenset({"Agent", "Task"})

# Campo do input que melhor descreve o alvo de uma ferramenta, em ordem de preferência.
TARGET_KEYS: tuple[str, ...] = ("file_path", "notebook_path", "command", "pattern", "path", "url",
                                "query", "description", "prompt")

# Origem de um prompt no transcript (verificado em 2.1.248, docs/adapters/CLAUDE.md §2.3):
# `origin.kind` "human" = o Lucas. Sem `origin`: humano só se não for `isMeta` e não começar com
# uma marca do harness. Qualquer outra origem (task-notification, peer, …) não é humana.
HUMAN_ORIGINS = frozenset({"human"})
SYSTEM_TAGS = frozenset({"task-notification", "local-command-stdout", "local-command-caveat",
                         "system-reminder", "ci-monitor-event"})
COMMAND_TAGS = frozenset({"command-name", "command-message"})
_LEADING_TAG = re.compile(r"\s*<([A-Za-z_\-]+)")


def activity_for_tool(name: str, tool_input: Any) -> str:
    if name in SHELL_TOOLS:
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        return classify_command(command)
    if name.startswith("mcp__"):
        return "RESEARCHING"
    return TOOL_ACTIVITY.get(name, "EXECUTING")


def tool_target(tool_input: Any) -> str | None:
    if not isinstance(tool_input, dict):
        return None
    for key in TARGET_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def tool_text(name: str, tool_input: Any) -> str:
    """Linha do Inner World para uma ferramenta: o nome e o alvo, como o Claude os escreveu."""
    target = tool_target(tool_input)
    if target is not None:
        return f"{name} {target}"
    return f"{name} {json.dumps(tool_input, ensure_ascii=False)}" if tool_input else name


def leading_tag(text: str) -> str | None:
    match = _LEADING_TAG.match(text or "")
    return match.group(1) if match else None


def prompt_origin(entry: dict[str, Any], text: str) -> tuple[str, str]:
    """(origem, tipo) de uma entrada `user` com texto: ("human", "prompt"|"command") ou
    ("agent", "system"). Regra de origem humana confirmada (PROTOCOL.md §7.1)."""
    if entry.get("isSidechain"):
        return "agent", "system"
    origin = (entry.get("origin") or {}).get("kind") if isinstance(entry.get("origin"), dict) else None
    tag = leading_tag(text)
    if origin is not None and origin not in HUMAN_ORIGINS:
        return "agent", "system"
    if origin is None and (entry.get("isMeta") or tag in SYSTEM_TAGS):
        return "agent", "system"
    return "human", ("command" if tag in COMMAND_TAGS else "prompt")


def hook_prompt_is_human(prompt: str) -> bool:
    """Sem transcript (só hook): heurística verificada no Spike 3."""
    return leading_tag(prompt) not in SYSTEM_TAGS


def usage_signal(usage: Any) -> dict[str, Any] | None:
    if not isinstance(usage, dict):
        return None
    signal: dict[str, Any] = {"type": "usage",
                              "input_tokens": int(usage.get("input_tokens") or 0),
                              "output_tokens": int(usage.get("output_tokens") or 0)}
    if usage.get("cache_read_input_tokens") is not None:
        signal["cache_read_tokens"] = int(usage["cache_read_input_tokens"])
    return signal
