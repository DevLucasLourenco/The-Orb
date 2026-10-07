"""Mapa do provider opencode: linhas de `session_message` -> sinal de mundo e entrada de Inner World.

Base: estrutura do `opencode.db` do opencode 2.0.23, lida nesta máquina (só nomes de campos e
contagens). Detalhes em docs/adapters/OPENCODE.md.
"""
from __future__ import annotations

from typing import Any

from .._shared import Capabilities, classify_command

PROVIDER = "opencode"

CAPABILITIES = Capabilities(
    thought_fidelity=("raw",),              # blocos `reasoning`; raw ou resumo conforme o modelo (a confirmar)
    approvals="none",                        # tabela `permission` existe, sem linhas observadas ainda
    subagents=True,                          # session_v2.parent_id
    realtime=False,                          # nível 1 (servidor próprio + --server) a validar
    usage=True,
)

# Ferramenta nativa -> atividade. `bash` usa o classificador de comandos.
TOOL_ACTIVITY: dict[str, str] = {
    "read": "READING", "glob": "READING", "grep": "READING", "list": "READING", "ls": "READING",
    "edit": "CODING", "write": "CODING", "patch": "CODING", "multiedit": "CODING",
    "webfetch": "RESEARCHING", "websearch": "RESEARCHING",
    "task": "DELEGATING",
    "todowrite": "THINKING", "todoread": "THINKING",
}
SHELL_TOOLS = frozenset({"bash", "shell"})
TARGET_KEYS: tuple[str, ...] = ("filePath", "path", "command", "pattern", "url", "query", "description")

# session_message.type -> papel da linha no Inner World (o tipo nativo continua no rótulo).
MESSAGE_TYPES: dict[str, str] = {"user": "prompt", "synthetic": "system", "system": "system"}
FINISHED_TOOL_STATUS = frozenset({"completed", "error"})


def activity_for_tool(name: str, tool_input: Any) -> str:
    lowered = (name or "").lower()
    if lowered in SHELL_TOOLS:
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        return classify_command(command if isinstance(command, str) else None)
    if lowered.startswith("mcp") or "_mcp_" in lowered:
        return "RESEARCHING"
    return TOOL_ACTIVITY.get(lowered, "EXECUTING")


def tool_text(name: str, tool_input: Any) -> str:
    if isinstance(tool_input, dict):
        for key in TARGET_KEYS:
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return f"{name} {value}"
    return name


def tool_target(tool_input: Any) -> str | None:
    if isinstance(tool_input, dict):
        for key in TARGET_KEYS:
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def content_text(value: Any) -> str:
    """Texto de um campo que pode ser texto, lista de partes ou objeto."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(content_text(part) for part in value if part is not None)
    if isinstance(value, dict):
        return str(value.get("text") or value.get("output") or "")
    return ""


def usage_signal(data: dict[str, Any]) -> dict[str, Any] | None:
    tokens = data.get("tokens")
    if not isinstance(tokens, dict):
        return None
    cache = tokens.get("cache") if isinstance(tokens.get("cache"), dict) else {}
    signal: dict[str, Any] = {"type": "usage", "input_tokens": int(tokens.get("input") or 0),
                              "output_tokens": int(tokens.get("output") or 0),
                              "reasoning_tokens": int(tokens.get("reasoning") or 0),
                              "cache_read_tokens": int(cache.get("read") or 0)}
    if isinstance(data.get("cost"), (int, float)) and not isinstance(data.get("cost"), bool):
        signal["cost_usd"] = float(data["cost"])
    return signal
