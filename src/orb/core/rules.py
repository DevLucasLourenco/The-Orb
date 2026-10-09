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


# Limites de tempo (R47, D-086). O Core não tem relógio: quem pede o snapshot dá a hora, e estes
# valores decidem o que o tempo muda. Mudar um limite é mudar esta tabela.
ASLEEP_AFTER_SECONDS = 15 * 60               # R31, D-044: sessão parada há mais que isto "dorme"
SUBAGENT_NO_SIGNAL_AFTER_SECONDS = 5 * 60    # R7, D-045, D-050: subagente sem atividade fica "sem sinal"


def area_for(state: str) -> str | None:
    return AREA_BY_STATE.get(state)


def is_asleep(*, ended: bool, state: str, idle_seconds: float | None) -> bool:
    """Alter Ego "dormindo": a sessão terminou, ou está parada (IDLE) há mais que o limite.
    Quem trabalha, espera o Lucas ou erra nunca dorme só pela idade. Sem hora confiável
    (`idle_seconds` None) não se afirma nada."""
    if ended:
        return True
    return state == "IDLE" and idle_seconds is not None and idle_seconds > ASLEEP_AFTER_SECONDS


def subagent_without_signal(*, active: bool, idle_seconds: float | None) -> bool:
    """Subagente ativo, sem sinal de fim, sem atividade há mais que o limite. No nível 0 o fim de
    um subagente em segundo plano não é observável (adapters/CLAUDE.md §1.6): ele não some, fica
    "sem sinal"."""
    return active and idle_seconds is not None and idle_seconds > SUBAGENT_NO_SIGNAL_AFTER_SECONDS


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
