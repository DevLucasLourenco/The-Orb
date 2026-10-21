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

# O perfil de trabalho do Alter Ego (R40, D-069, D-096): as áreas que contam como "trabalho" e o papel de quem mais fez em cada uma. A
# contagem é a das atividades do líder que caem numa destas áreas (a atividade vai para a área por `AREA_BY_STATE`); o resto não entra:
# pensar, delegar e bloquear não têm área, e concluir cai na Task Board, que não é uma área de trabalho. A ordem é a das barras no overview.
ROLE_BY_AREA: dict[str, str] = {
    "Development Center": "desenvolvedor",
    "Testing Lab": "testador",
    "Research Center": "pesquisador",
    "Code Review": "revisor",
}
ATTRIBUTE_AREAS: tuple[str, ...] = tuple(ROLE_BY_AREA)

# A sala cheia (R33, D-057): os lugares do Rooftop Room e quantos personagens cada um mostra. O resto vira o contador "+N".
LOBBY, DORM = "__lobby", "__dorm"        # quem pensa, espera ou está parado; quem dorme ou terminou
PLACES: tuple[str, ...] = ("Development Center", "Testing Lab", "Research Center", "Code Review", "Task Board", LOBBY, DORM)
PLACE_CAP = 8

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

# A altura do prédio em níveis (uma fileira de janelas), por classe (R19, D-052, VISUAL.md §8): de/até. Dentro da classe a
# altura cresce com o logaritmo das linhas; entre as classes há um salto (3→5, 8→11, 16→20, 28→34), para as vizinhas nunca ficarem
# parecidas. O Arranha-céu não tem fim de faixa: cresce `SKYSCRAPER_LEVELS_PER_DOUBLING` níveis a cada vez que as linhas dobram, até o teto.
BUILDING_LEVELS: dict[str, tuple[int, int]] = {
    "Casa": (1, 1), "Sobrado": (2, 3), "Prédio": (5, 8), "Edifício": (11, 16), "Torre": (20, 28), "Arranha-céu": (34, 48),
}
SKYSCRAPER_LEVELS_PER_DOUBLING = 4

# A marca de cada classe no topo, que lê a classe de longe (D-052, R20c): quantas cintas de luz neutra, uma a mais por classe.
BUILDING_TRIM: dict[str, int] = {"Casa": 0, "Sobrado": 1, "Prédio": 2, "Edifício": 3, "Torre": 4, "Arranha-céu": 5}
ANTENNA_CLASSES: frozenset[str] = frozenset({"Arranha-céu"})

# A fachada (R20, R20d, VISUAL.md §6): quantas posições de janela tem cada andar (por nível: `FACADE_FACES` lados de `FACADE_COLS`
# colunas) e quanto vale uma janela acesa (x% das linhas alteradas, configurável nas preferências, D-042).
FACADE_FACES = 4
FACADE_COLS = 8
WINDOW_PERCENT = 5.0

# O traçado da cidade (R32, D-047, VISUAL.md §7), em unidades do mundo. Mudar o desenho da cidade é mudar esta tabela.
CITY_LOT = 46            # lado de um lote: o prédio (a maior base, `CITY_MAX_BASE`) cabe mesmo no maior deslocamento e giro
CITY_MAX_BASE = 30       # a maior largura de uma forma de prédio (o pódio da Torre e do Arranha-céu, VISUAL.md §8)
CITY_PAD = 14            # calçada do bairro, em volta dos lotes; no canto fica a placa com a letra
CITY_STREET = 18         # largura da rua entre dois bairros (cenário, R12a)
CITY_JITTER = 6          # deslocamento máximo do prédio dentro do lote, em cada eixo
CITY_TURN = 0.12         # giro máximo do prédio, em radianos (cerca de 7 graus)
CITY_ASPECT = 16 / 9     # a cidade é mais larga que alta, como a tela

# A lista fixa e visível de arquivos gerados que não contam como linhas (D-054), além do `.gitignore`. Um padrão sem `/`
# vale para o nome em qualquer pasta; com `/`, para o caminho a partir da raiz do projeto. O Lucas a edita nas configurações.
GENERATED_FILE_PATTERNS: tuple[str, ...] = (
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json", "poetry.lock", "Pipfile.lock", "uv.lock",
    "Cargo.lock", "Gemfile.lock", "composer.lock", "go.sum", "*.min.js", "*.min.css", "*.map", "dist/*", "build/*",
)


@dataclass(frozen=True)
class XpTable:
    """A tabela de XP (R53, R54, D-101 a D-105, PROGRESSION.md §3 e §4): versionada, porque o extrato guardado é de uma versão só e
    trocar a versão recalcula tudo a partir das fontes. Mudar um valor é uma versão nova; o extrato antigo fica de lado, intacto."""
    version: int
    k: int                              # a curva dos níveis do Alter Ego: a XP para chegar ao nível n é k·n·(n−1)
    k_realm: int                        #   ... a do Realm (a soma dos seus Alter Egos)
    k_mankind: int                      #   ... a de Mankind (a soma de todos os realms)
    test_xp: int                        # X-TEST: teste que passou
    test_gap_seconds: int               #   ... no máximo um a cada tanto tempo por sessão (rodar em laço não rende)
    fix_xp: int                         # X-FIX: vermelho → verde, um por falha consertada
    deleg_xp: int                       # X-DELEG: subagente concluído, para o líder
    deleg_cap: int                      #   ... teto por sessão por dia
    craft_xp: int                       # X-CRAFT: ofício, por janela de tempo com atividade de trabalho
    craft_window_seconds: int
    craft_cap: int                      #   ... teto por sessão por dia
    craft_activities: frozenset[str]    #   ... as atividades que contam como trabalho
    commit_xp: int                      # X-COMMIT: commit feito pela sessão (provisório até chegar à branch principal)
    commit_lines_per_xp: int            #   ... mais 1 XP a cada tanto de linhas alteradas pelo commit
    commit_cap: int                     #   ... teto por commit
    commit_expire_days: int             #   ... sem chegar à principal em tantos dias, expira; também a janela em que uma reversão ainda anula


# A tabela v1 (PROGRESSION.md §3). k = 50 é provisório até o ticket 25 calibrar com o histórico real (§4).
XP_TABLE = XpTable(
    version=1, k=50, k_realm=500, k_mankind=2500, test_xp=5, test_gap_seconds=10 * 60, fix_xp=25, deleg_xp=3, deleg_cap=30,
    craft_xp=1, craft_window_seconds=5 * 60, craft_cap=30,
    craft_activities=frozenset({"CODING", "TESTING", "READING", "RESEARCHING", "REVIEWING"}),
    commit_xp=10, commit_lines_per_xp=20, commit_cap=40, commit_expire_days=30,
)

# Os providers do placar de Mankind (R54): a XP de cada um, lado a lado, mesmo quando ainda é zero.
PROVIDERS: tuple[str, ...] = ("claude", "codex", "hermes", "opencode")


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
