"""Vocabulário fechado do protocolo: atividades, sinais de mundo e entradas de Inner World.

É a única linguagem comum entre providers (ver docs/PROTOCOL.md §4 e §5). Tudo que é específico de
um provider fica no evento nativo, intacto.
"""
from __future__ import annotations

PROTOCOL_VERSION = "0.2"

# Atividades que um adapter pode declarar num sinal `activity`.
ACTIVITIES: frozenset[str] = frozenset({
    "THINKING", "READING", "RESEARCHING", "CODING", "EXECUTING",
    "TESTING", "REVIEWING", "DELEGATING", "BLOCKED", "COMPLETED",
})

# Estados que só o Core deriva (nunca vêm de um adapter).
DERIVED_STATES: frozenset[str] = frozenset({"IDLE", "WAITING", "ERROR", "NO_SIGNAL"})

ALL_STATES: frozenset[str] = ACTIVITIES | DERIVED_STATES

# Tipo de sinal -> campos obrigatórios. Vocabulário fechado: tipo novo = nova versão do protocolo.
SIGNAL_FIELDS: dict[str, frozenset[str]] = {
    "session.started": frozenset(),
    "session.ended": frozenset(),
    "session.updated": frozenset(),
    "activity": frozenset({"activity"}),
    "idle": frozenset(),
    "subagent.started": frozenset(),
    "subagent.ended": frozenset(),
    "waiting": frozenset({"request"}),
    "waiting.resolved": frozenset({"request"}),
    "usage": frozenset({"input_tokens", "output_tokens"}),
    "error": frozenset({"message"}),
    "signal.lost": frozenset(),
    "signal.restored": frozenset(),
}

# Sinais que só o sistema emite (nunca um adapter).
SYSTEM_SIGNALS: frozenset[str] = frozenset({"signal.lost", "signal.restored"})

INNER_ROLES: frozenset[str] = frozenset({"thought", "narration", "tool", "result", "prompt", "system"})
FIDELITIES: frozenset[str] = frozenset({"raw", "summary"})
