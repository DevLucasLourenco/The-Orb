"""Nível 1 do Claude Code: hooks observadores injetados SÓ na sessão hospedada (`claude --settings`).

Nunca no settings.json do Lucas (ADR 0005). Transporte: hook `command` ASSÍNCRONO com `curl` de
timeout curto, para um Orb travado não atrasar o agente (medido no Spike 3). O receptor responde
`{}`: nenhuma decisão, nenhum contexto. Campos verificados ao vivo: docs/adapters/CLAUDE.md §6.
"""
from __future__ import annotations

from typing import Any

from ...protocol import Event
from .._shared import EventFactory, now_iso
from . import mapping

SOURCE = "claude/hooks"

# Eventos que o Orb observa. Hooks que podem DECIDIR algo nunca recebem resposta com decisão.
HOOK_EVENTS: tuple[str, ...] = (
    "SessionStart", "SessionEnd", "UserPromptSubmit", "Stop", "PreToolUse", "PostToolUse",
    "PostToolUseFailure", "PermissionRequest", "PermissionDenied", "SubagentStart", "SubagentStop",
    "Notification", "TaskCreated", "TaskCompleted",
)


def session_settings(port: int, token_env: str = "ORB_TOKEN", events: tuple[str, ...] = HOOK_EVENTS) -> dict[str, Any]:
    """Conteúdo do arquivo passado a `claude --settings`: só observação, só nesta sessão."""
    hooks: dict[str, Any] = {}
    for name in events:
        command = (f'curl -s -m 1 -X POST -H "X-Orb-Token: ${token_env}" -H "Content-Type: application/json" '
                   f'--data-binary @- http://127.0.0.1:{port}/hook/{name}')
        hooks[name] = [{"hooks": [{"type": "command", "command": command, "async": True, "timeout": 5}]}]
    return {"hooks": hooks}


class HookTranslator:
    """Payload de hook -> evento. Uma instância por receptor; separa as sessões por `session_id`."""

    def __init__(self, realm: str) -> None:
        self.realm = realm
        self._factories: dict[str, EventFactory] = {}
        self._pending: dict[str, dict[str, str]] = {}      # session -> {tool_name: request}
        self._arrivals = 0

    def _factory(self, session: str) -> EventFactory:
        factory = self._factories.get(session)
        if factory is None:
            factory = self._factories[session] = EventFactory(
                provider=mapping.PROVIDER, source=SOURCE, realm=self.realm, session=session)
        return factory

    def translate(self, name: str, payload: Any, received_at: str | None = None) -> Event | None:
        """None quando o payload não é utilizável (sem sessão) — descartado na borda."""
        if not isinstance(payload, dict) or not isinstance(payload.get("session_id"), str):
            return None
        session = payload["session_id"]
        factory = self._factory(session)
        agent = payload.get("agent_id") if isinstance(payload.get("agent_id"), str) else None
        self._arrivals += 1     # hooks não têm id próprio: dois iguais em momentos diferentes são dois fatos
        key = f"{name}:{payload['tool_use_id']}" if isinstance(payload.get("tool_use_id"), str) else f"{name}#{self._arrivals}"
        ts = received_at or now_iso()
        inner, signal = self._map(session, name, payload, agent)
        return factory.make(key, ts, name, payload, agent=agent, inner=inner, signal=signal)

    def _map(self, session: str, name: str, payload: dict[str, Any], agent: str | None):
        tool = str(payload.get("tool_name") or "")
        tool_input = payload.get("tool_input")
        pending = self._pending.setdefault(session, {})
        if name == "PreToolUse":
            return ({"origin": "agent", "role": "tool", "text": mapping.tool_text(tool, tool_input)},
                    {"type": "activity", "activity": mapping.activity_for_tool(tool, tool_input),
                     "target": mapping.tool_target(tool_input)})
        if name in ("PostToolUse", "PostToolUseFailure", "PermissionDenied"):
            request = pending.pop(tool, None)
            if request is None:
                return None, None
            # A decisão do Lucas não tem hook próprio: é DEDUZIDA pelo que veio depois.
            decision = "approved" if name == "PostToolUse" else ("denied" if name == "PermissionDenied" else "unknown")
            return None, {"type": "waiting.resolved", "request": request, "decision": decision, "deduced": True}
        if name == "PermissionRequest":
            request = f"perm-{self._arrivals}"
            pending[tool] = request
            return None, {"type": "waiting", "request": request, "action": mapping.tool_text(tool, tool_input)}
        if name == "SubagentStart":
            return None, {"type": "subagent.started", "kind": payload.get("agent_type")}
        if name == "SubagentStop":
            return None, {"type": "subagent.ended", "outcome": "completed"}
        if name == "Stop" and agent is None:
            return None, {"type": "idle"}
        if name == "SessionStart":
            return None, {"type": "session.started", "cwd": payload.get("cwd"), "model": payload.get("model")}
        if name == "SessionEnd":
            return None, {"type": "session.ended", "reason": payload.get("reason")}
        if name == "UserPromptSubmit":
            prompt = str(payload.get("prompt") or "")
            if mapping.hook_prompt_is_human(prompt):
                return ({"origin": "human", "role": "prompt", "text": prompt},
                        {"type": "human.input", "kind": "prompt", "channel": "terminal"})
            return {"origin": "agent", "role": "system", "text": prompt}, None
        return None, None
