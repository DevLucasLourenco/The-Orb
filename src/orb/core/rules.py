"""Regras do mundo, como dados (docs/PROTOCOL.md §5). Mudar uma regra é mudar uma tabela aqui."""
from __future__ import annotations

# Atividade/estado -> área do Environment no Rooftop Room. `None` = fora das áreas (ex.: parado).
AREA_BY_STATE: dict[str, str | None] = {
    "CODING": "Development Center",
    "EXECUTING": "Development Center",
    "TESTING": "Testing Lab",
    "READING": "Research Center",
    "RESEARCHING": "Research Center",
    "REVIEWING": "Code Review",
    "COMPLETED": "Task Board",
    "THINKING": None,
    "DELEGATING": None,
    "BLOCKED": None,
    "IDLE": None,
    "WAITING": None,
    "ERROR": None,
    "NO_SIGNAL": None,
}

# Estado-base depois de cada sinal (para o personagem a quem o sinal se refere).
BASE_STATE_AFTER: dict[str, str] = {
    "session.started": "IDLE",
    "session.ended": "IDLE",
    "idle": "IDLE",
    "subagent.started": "THINKING",
}

# Ordem de precedência dos estados que SOBREPÕEM o estado-base (o primeiro que valer, vence).
OVERLAYS: tuple[str, ...] = ("NO_SIGNAL", "WAITING", "ERROR")

# Quantos ids recentes o Core guarda por Alter Ego para descartar repetidos (memória constante).
DEDUPE_WINDOW = 4096


def area_for(state: str) -> str | None:
    return AREA_BY_STATE.get(state)


def leader_state(base: str, *, no_signal: bool, waiting: bool, error: bool, active_subagents: int) -> str:
    """Estado visível do líder (Alter Ego). O fim do turno não encerra a Team: com subagentes
    ativos o líder aparece DELEGATING (verificado no Claude: a ferramenta Agent é assíncrona)."""
    flags = {"NO_SIGNAL": no_signal, "WAITING": waiting, "ERROR": error}
    for overlay in OVERLAYS:
        if flags[overlay]:
            return overlay
    if base == "IDLE" and active_subagents:
        return "DELEGATING"
    return base
