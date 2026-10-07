"""Mapa do provider Hermes: linhas do `state.db` -> sinal de mundo e entrada de Inner World.

Base: código-fonte do Hermes 0.20.5 (docs/adapters/HERMES.md), sem execução ao vivo. A tabela de
ferramentas é por PALAVRA-CHAVE no nome (heurística declarada), porque a lista completa de
ferramentas do Hermes ainda não foi levantada.
"""
from __future__ import annotations

from .._shared import Capabilities, classify_command

PROVIDER = "hermes"

CAPABILITIES = Capabilities(
    thought_fidelity=("raw", "summary"),    # depende do modelo por trás (colunas reasoning*)
    approvals="none",                        # sem registro de aprovações no state.db
    subagents=True,                          # sessões filhas: parent_session_id + source "subagent"
    realtime=False,                          # nível 1 (sidecar da TUI) ainda não implementado
    usage=True,
)

# (atividade, palavras-chave no nome da ferramenta). A primeira que casar vence.
TOOL_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("DELEGATING", ("delegate", "subagent", "spawn")),
    ("RESEARCHING", ("web", "browser", "search_web", "fetch", "mcp")),
    ("CODING", ("write", "patch", "edit", "create_file")),
    ("READING", ("read", "search_files", "list", "grep", "glob")),
    ("TESTING", ("test",)),
)
SHELL_TOOLS = frozenset({"terminal", "shell", "bash", "execute_code"})


def activity_for_tool(name: str, arguments: object) -> str:
    lowered = name.lower()
    if lowered in SHELL_TOOLS:
        command = arguments.get("command") if isinstance(arguments, dict) else None
        return classify_command(command if isinstance(command, str) else None)
    for activity, words in TOOL_KEYWORDS:
        if any(word in lowered for word in words):
            return activity
    return "EXECUTING"
