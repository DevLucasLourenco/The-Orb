"""Ambiente do terminal hospedado.

Marcadores que o Claude Code injeta no ambiente dos filhos: se o Orb for iniciado de dentro de uma
sessão do Claude, herdá-los mudaria o comportamento do CLI hospedado (ex.: não gravar transcript,
verificado no Spike 1). Removê-los faz o CLI rodar como se aberto pelo Lucas. Configurações do
usuário (ANTHROPIC_*, CLAUDE_CODE_USE_*, etc.) são preservadas.
"""
from __future__ import annotations

import os

INHERITED_MARKERS: frozenset[str] = frozenset({
    "CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT", "AI_AGENT",
    "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_HOST_SESSION_ID",
    "CLAUDE_CODE_SESSION_ATTENDED", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_EXECPATH",
    "CLAUDE_CODE_SIMPLE", "CLAUDE_CODE_DISABLE_CRON", "CLAUDE_CODE_DISABLE_TERMINAL_TITLE",
    "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_CODE_TERMINAL_MCP_TOOLS",
    "CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH", "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING",
    "CLAUDE_CODE_EMIT_TOOL_USE_SUMMARIES", "CLAUDE_CODE_REPORT_FINDINGS",
    "CLAUDE_CODE_ENABLE_ASK_USER_QUESTION_TOOL", "CLAUDE_CODE_DESKTOP_APP_VERSION",
    "CLAUDE_PREVIEW_CLASSIFIER_FLOOR", "CLAUDE_AGENT_SDK_VERSION", "CLAUDE_AGENT_SDK_MCP_NO_PREFIX",
})


def clean_env(env: dict[str, str] | None = None) -> dict[str, str]:
    source = dict(os.environ if env is None else env)
    return {key: value for key, value in source.items() if key not in INHERITED_MARKERS}
