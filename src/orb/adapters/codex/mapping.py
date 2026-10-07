"""Mapa do provider Codex: notificações do app-server -> sinal de mundo e entrada de Inner World.

Formatos do esquema oficial (`codex app-server generate-json-schema`, Codex 0.160.1) e das fixtures
do Spike 4. Detalhes em docs/adapters/CODEX.md. O Orb NUNCA responde pedidos do servidor (ADR 0006):
aqui eles só viram eventos `waiting`.
"""
from __future__ import annotations

import json
from typing import Any

from .._shared import Capabilities, classify_command

PROVIDER = "codex"

CAPABILITIES = Capabilities(
    thought_fidelity=("summary",),          # ~42% dos blocos de reasoning com summary; nunca raw
    approvals="requested+resolved",         # ServerRequest + serverRequest/resolved + activeFlags
    subagents=True,                         # thread.parentThreadId (formato; ainda não visto ao vivo)
    human_origin="heuristic",               # userMessage não diz se é humano (CODEX.md §5)
    realtime=True,                          # nível 1: app-server próprio do Orb + codex --remote
    usage=True,
)

# `commandActions[].type` (esquema) -> atividade. `unknown` cai no classificador de comandos.
COMMAND_ACTION_ACTIVITY: dict[str, str] = {"read": "READING", "listFiles": "READING", "search": "READING"}

# Item que COMEÇA -> atividade do personagem.
ITEM_ACTIVITY: dict[str, str] = {
    "fileChange": "CODING",
    "webSearch": "RESEARCHING",
    "mcpToolCall": "RESEARCHING",
    "dynamicToolCall": "EXECUTING",
    "collabAgentToolCall": "DELEGATING",
    "enteredReviewMode": "REVIEWING",
    "imageView": "READING",
}

# Pedidos do servidor que esperam o Lucas. O Orb só registra: nunca responde.
WAITING_REQUESTS = frozenset({
    "item/commandExecution/requestApproval", "item/fileChange/requestApproval",
    "item/permissions/requestApproval", "item/tool/requestUserInput", "mcpServer/elicitation/request",
    "applyPatchApproval", "execCommandApproval",
})
WAITING_FLAGS = frozenset({"waitingOnApproval", "waitingOnUserInput"})

# Streaming: não vira evento um a um (desempenho); o item completo traz o texto.
STREAMING_SUFFIXES: tuple[str, ...] = ("/delta", "/outputDelta", "/summaryTextDelta",
                                       "/summaryPartAdded", "/textDelta", "/patchUpdated", "/progress")


def is_streaming(method: str) -> bool:
    return method.endswith(STREAMING_SUFFIXES)


def command_activity(item: dict[str, Any]) -> str:
    for action in item.get("commandActions") or []:
        if isinstance(action, dict) and action.get("type") in COMMAND_ACTION_ACTIVITY:
            return COMMAND_ACTION_ACTIVITY[action["type"]]
    return classify_command(item.get("command"))


def user_text(content: Any) -> str:
    """Texto de um `userMessage` (lista de UserInput: só as partes `text`)."""
    parts = [str(part.get("text", "")) for part in content or [] if isinstance(part, dict) and part.get("type") == "text"]
    return "\n".join(part for part in parts if part)


def item_text(item: dict[str, Any]) -> str:
    """Linha do Inner World para um item, com o vocabulário do Codex."""
    itype = item.get("type")
    if itype == "commandExecution":
        return str(item.get("command") or "")
    if itype == "fileChange":
        paths = [str(change.get("path")) for change in item.get("changes") or [] if isinstance(change, dict)]
        return "fileChange " + ", ".join(paths)
    if itype == "webSearch":
        return f"webSearch {item.get('query') or ''}".strip()
    if itype == "mcpToolCall":
        return f"mcpToolCall {item.get('server')}.{item.get('tool')}"
    if itype in ("dynamicToolCall", "collabAgentToolCall"):
        return f"{itype} {item.get('tool') or ''} {item.get('prompt') or ''}".strip()
    if itype == "enteredReviewMode":
        return f"enteredReviewMode {item.get('review') or ''}".strip()
    return str(itype)


def result_text(item: dict[str, Any]) -> str:
    output = item.get("aggregatedOutput") or ""
    exit_code = item.get("exitCode")
    prefix = f"[exit {exit_code}] " if exit_code not in (None, 0) else ""
    return prefix + str(output)


def usage_signal(token_usage: Any) -> dict[str, Any] | None:
    last = token_usage.get("last") if isinstance(token_usage, dict) else None
    if not isinstance(last, dict):
        return None
    return {"type": "usage", "input_tokens": int(last.get("inputTokens") or 0),
            "output_tokens": int(last.get("outputTokens") or 0),
            "cache_read_tokens": int(last.get("cachedInputTokens") or 0),
            "reasoning_tokens": int(last.get("reasoningOutputTokens") or 0)}


def short_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)
