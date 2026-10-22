"""Vocabulário fechado do protocolo: atividades, sinais de mundo e entradas de Inner World.

É a única linguagem comum entre providers (ver docs/PROTOCOL.md §4 e §5). Tudo que é específico de
um provider fica no evento nativo, intacto.
"""
from __future__ import annotations

PROTOCOL_VERSION = "0.3"

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
    "command.result": frozenset({"ok"}),
    "signal.lost": frozenset(),
    "signal.restored": frozenset(),
    # 0.3 (R49, D-085): sinais de realm (`alter_ego` nulo), produzidos pelos Probes. Os outros sinais da 0.3
    # (`account.limits`) entra no ticket dele; `command.result` é de sessão (ticket 19).
    "realm.metrics": frozenset({"loc"}),
    "realm.changes": frozenset({"changes"}),
    "realm.commits": frozenset({"commits"}),          # ticket 23: o que o git diz dos commits que as sessões fizeram (R53)
    "tasks.updated": frozenset({"done", "total"}),    # ticket 14: a lista de tarefas que o próprio CLI mantém (R50, D-093); sinal de sessão
}

# Sinais que só o sistema emite (nunca um adapter).
SYSTEM_SIGNALS: frozenset[str] = frozenset({"signal.lost", "signal.restored"})

# Sinais de realm: só Probes os emitem, e o evento tem `alter_ego: null`.
REALM_SIGNALS: frozenset[str] = frozenset({"realm.metrics", "realm.changes", "realm.commits"})

# Os tipos de alteração local do git (R20a): a ordem é a da fachada (VISUAL.md §6) e a das cores (VISUAL.md §5).
CHANGE_TYPES: tuple[str, ...] = ("modified", "added", "untracked", "renamed", "deleted", "conflict")

# Os estados de uma tarefa da lista do CLI (R50): cada provider os escreve a seu modo e o adapter traduz para estes três. O que o provider
# disser fora disto (cancelada, apagada, desconhecida) não entra na conta: nada é inventado (R12).
TASK_STATUSES: tuple[str, ...] = ("pending", "in_progress", "completed")

INNER_ROLES: frozenset[str] = frozenset({"thought", "narration", "tool", "result", "prompt", "system"})
FIDELITIES: frozenset[str] = frozenset({"raw", "summary"})
