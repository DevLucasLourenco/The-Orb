"""Regras do mundo, como dados (docs/PROTOCOL.md §5). Mudar uma regra é mudar uma tabela aqui."""
from __future__ import annotations

from dataclasses import dataclass

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
RECENT_SESSION_SECONDS = 10 * 24 * 3600      # R28a, D-027, D-059: a sala guarda as sessões dos últimos 10 dias;
                                             # as mais antigas vão para o Histórico do realm (o ticket 07 torna isto configurável)


# As 6 classes de prédio por faixa de linhas de código (R19, D-051, D-052, D-091, VISUAL.md §8). Cada faixa começa no
# número da tabela (fechada embaixo): 500 mil linhas já é Arranha-céu. Formas, alturas e andares vêm no ticket 10.
BUILDING_CLASSES: tuple[tuple[str, int], ...] = (
    ("Casa", 0), ("Sobrado", 1_000), ("Prédio", 5_000), ("Edifício", 20_000), ("Torre", 100_000), ("Arranha-céu", 500_000),
)

# A lista fixa e visível de arquivos gerados que não contam como linhas (D-054), além do `.gitignore`. Um padrão sem `/`
# vale para o nome em qualquer pasta; com `/`, para o caminho a partir da raiz do projeto. O Lucas a edita nas configurações.
GENERATED_FILE_PATTERNS: tuple[str, ...] = (
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json", "poetry.lock", "Pipfile.lock", "uv.lock",
    "Cargo.lock", "Gemfile.lock", "composer.lock", "go.sum", "*.min.js", "*.min.css", "*.map", "dist/*", "build/*",
)


@dataclass(frozen=True)
class LineFilter:
    """O que entra na contagem de linhas (D-054, D-056): padrão só código, sem `.md`, sem a lista de gerados."""
    include_markdown: bool = False
    exclude: tuple[str, ...] = GENERATED_FILE_PATTERNS


def building_class(lines: int) -> str:
    """A classe do prédio de um projeto com `lines` linhas (as faixas são fixas, nunca relativas aos outros prédios)."""
    name = BUILDING_CLASSES[0][0]
    for candidate, lower in BUILDING_CLASSES:
        if lines >= lower:
            name = candidate
    return name


def area_for(state: str) -> str | None:
    return AREA_BY_STATE.get(state)


def is_asleep(*, ended: bool, state: str, idle_seconds: float | None) -> bool:
    """Alter Ego "dormindo": a sessão terminou, ou está parada (IDLE) há mais que o limite.
    Quem trabalha, espera o Lucas ou erra nunca dorme só pela idade. Sem hora confiável
    (`idle_seconds` None) não se afirma nada."""
    if ended:
        return True
    return state == "IDLE" and idle_seconds is not None and idle_seconds > ASLEEP_AFTER_SECONDS


def in_room(*, idle_seconds: float | None, recent_seconds: float = RECENT_SESSION_SECONDS) -> bool:
    """A sessão fica na sala enquanto o último evento dela for dos últimos `recent_seconds`; depois vai para
    o Histórico do realm (nunca some, R28). Sem hora confiável não se afirma nada: fica na sala."""
    return idle_seconds is None or idle_seconds <= recent_seconds


def subagent_without_signal(*, active: bool, idle_seconds: float | None) -> bool:
    """Subagente ativo, sem sinal de fim, sem atividade há mais que o limite. No nível 0 o fim de
    um subagente em segundo plano não é observável (adapters/CLAUDE.md §1.6): ele não some, fica
    "sem sinal"."""
    return active and idle_seconds is not None and idle_seconds > SUBAGENT_NO_SIGNAL_AFTER_SECONDS


def leader_state(base: str, *, no_signal: bool, waiting: bool, error: bool, active_subagents: int) -> str:
    """Estado visível do líder (Alter Ego). O fim do turno não encerra a Team: com subagentes
    ativos o líder aparece DELEGATING (verificado no Claude: a ferramenta Agent é assíncrona).
    `active_subagents` conta só os que têm sinal: um subagente "sem sinal" (sem atividade há mais de
    5 min e sem aviso de fim) não segura o líder em DELEGATING (R7, ticket 01)."""
    flags = {"NO_SIGNAL": no_signal, "WAITING": waiting, "ERROR": error}
    for overlay in OVERLAYS:
        if flags[overlay]:
            return overlay
    if base == "IDLE" and active_subagents:
        return "DELEGATING"
    return base
