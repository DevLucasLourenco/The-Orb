"""O mundo do The Orb: Realm -> Alter Ego (sessão, líder) -> Subagentes.

Puro: só aplica eventos já validados e devolve snapshots. Sem disco, rede ou relógio (o tempo vem
do `ts` dos eventos e da hora que quem pede o snapshot informa). Mesmos eventos na mesma ordem e a
mesma hora -> mesmo mundo.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, NamedTuple

from ..protocol import Event, validate
from . import building, city, facade, profile, room, rules
from .names import NameSource
from .progression import Ledger, XpSource, scale

_TOKEN_FIELDS = ("input_tokens", "output_tokens", "cache_read_tokens", "reasoning_tokens")
_ACTION_CHARS = 240     # tamanho do "fazendo agora" no overview


class _FacadeCache(NamedTuple):
    """A fachada de um realm e de que leituras (e x) ela saiu: só se refaz quando uma delas muda."""
    read: dict[str, Any]
    counted: dict[str, Any]
    percent: float
    built: dict[str, Any]


def _require_aware(now: datetime | None) -> None:
    if now is not None and now.utcoffset() is None:
        raise ValueError("a hora do mundo precisa ter fuso horário")


def _idle_seconds(last_ts: str | None, now: datetime | None) -> float | None:
    """Segundos entre o último evento e `now`. None quando não dá para saber (sem hora, sem evento,
    data ilegível ou sem fuso): o mundo não afirma nada que dependa do tempo."""
    if now is None or last_ts is None:
        return None
    try:
        then = datetime.fromisoformat(last_ts)
    except ValueError:
        return None
    if then.utcoffset() is None:
        return None
    return (now - then).total_seconds()


@dataclass
class Subagent:
    id: str
    kind: str | None = None
    parent: str | None = None
    base: str = "THINKING"
    target: str | None = None
    active: bool = True
    outcome: str | None = None
    ended_at: str | None = None      # a hora do `subagent.ended` (R51): o cliente o leva até o líder antes de tirá-lo de cena
    last_action: str | None = None
    last_ts: str | None = None

    def touch(self, ts: str) -> None:
        """Qualquer evento do subagente é atividade (não só os que trazem sinal)."""
        if self.last_ts is None or ts > self.last_ts:
            self.last_ts = ts

    def without_signal(self, now: datetime | None) -> bool:
        return rules.subagent_without_signal(active=self.active, idle_seconds=_idle_seconds(self.last_ts, now))

    def snapshot(self, now: datetime | None = None) -> dict[str, Any]:
        base = self.base if self.active else "COMPLETED"
        no_signal = self.without_signal(now)
        # Sem sinal, o subagente não some nem muda de lugar: o estado vira NO_SIGNAL e a área
        # continua a do último estado conhecido (R7, D-045).
        return {"id": self.id, "kind": self.kind, "parent": self.parent,
                "state": "NO_SIGNAL" if no_signal else base, "area": rules.area_for(base),
                "target": self.target, "active": self.active, "no_signal": no_signal,
                "outcome": self.outcome, "ended_at": self.ended_at, "last_action": self.last_action, "last_ts": self.last_ts}


@dataclass
class AlterEgo:
    id: str
    realm: str
    provider: str | None
    base: str = "IDLE"
    target: str | None = None
    title: str | None = None
    model: str | None = None
    cwd: str | None = None
    name: str | None = None      # nome histórico: identidade, não dado (R37); None sem livro de nomes
    ended: bool = False
    no_signal: bool = False
    error: str | None = None
    waiting: dict[str, str | None] = field(default_factory=dict)   # request -> ação
    subagents: dict[str, Subagent] = field(default_factory=dict)
    usage: dict[str, float] = field(default_factory=dict)
    work: dict[str, int] = field(default_factory=dict)       # atividades do líder por área (R40): o papel e os atributos saem daqui
    xp: Ledger = field(default_factory=Ledger)               # o extrato e a conta de XP (R53): os subagentes rendem para o líder
    events: int = 0
    seq_gaps: int = 0
    last_action: str | None = None   # a última ferramenta/ação, com o texto do provider
    last_ts: str | None = None
    _last_seq: dict[str, int] = field(default_factory=dict, repr=False)      # por fonte
    _seen: set[str] = field(default_factory=set, repr=False)
    _seen_order: deque[str] = field(default_factory=deque, repr=False)

    @property
    def session(self) -> str:
        return self.id.split(":", 1)[1] if ":" in self.id else self.id

    def remember(self, event_id: str) -> bool:
        """Registra o id; falso se já visto (janela limitada)."""
        if event_id in self._seen:
            return False
        self._seen.add(event_id)
        self._seen_order.append(event_id)
        if len(self._seen_order) > rules.DEDUPE_WINDOW:
            self._seen.discard(self._seen_order.popleft())
        return True

    def active_subagents(self, now: datetime | None = None) -> int:
        """Subagentes sabidamente ativos: ativos e com sinal. Um "sem sinal" não conta (R7): não se
        sabe que ele ainda trabalha, então não mantém o líder em DELEGATING nem entra nos totais."""
        return sum(1 for sub in self.subagents.values() if sub.active and not sub.without_signal(now))

    def state(self, now: datetime | None = None) -> str:
        return rules.leader_state(self.base, no_signal=self.no_signal, waiting=bool(self.waiting),
                                  error=self.error is not None, active_subagents=self.active_subagents(now))

    def asleep(self, now: datetime | None = None) -> bool:
        return rules.is_asleep(ended=self.ended, state=self.state(now),
                               idle_seconds=_idle_seconds(self.last_ts, now))

    def in_room(self, now: datetime | None = None, recent_seconds: float = rules.RECENT_SESSION_SECONDS) -> bool:
        return rules.in_room(idle_seconds=_idle_seconds(self.last_ts, now), recent_seconds=recent_seconds)

    def snapshot(self, now: datetime | None = None, recent_seconds: float = rules.RECENT_SESSION_SECONDS) -> dict[str, Any]:
        state = self.state(now)
        return {
            "id": self.id, "provider": self.provider, "session": self.session, "name": self.name,
            "title": self.title, "model": self.model, "cwd": self.cwd, "state": state, "area": rules.area_for(state),
            "target": self.target, "last_action": self.last_action,
            "ended": self.ended, "asleep": self.asleep(now), "in_room": self.in_room(now, recent_seconds),
            "error": self.error,
            "active_subagents": self.active_subagents(now),
            "waiting": [{"request": r, "action": a} for r, a in self.waiting.items()],
            "events": self.events, "seq_gaps": self.seq_gaps,
            "usage": dict(self.usage), "last_ts": self.last_ts,
            "role": profile.role(self.work), "attributes": profile.attributes(self.work), "xp": self.xp.snapshot(),
            "team": [{**self.subagents[agent].snapshot(now), "depth": depth}
                     for agent, depth in profile.team_order({a: sub.parent for a, sub in self.subagents.items()})],
        }


class World:
    """Estado de todo o Orb. `apply` é idempotente por `id` de evento.

    `names` dá o nome histórico de cada sessão que aparece (R37); sem ele os Alter Egos ficam sem nome. `xp` guarda o extrato de XP
    de cada sessão (R53): sem ele a XP vale só enquanto o Orb está aberto. `xp_table` é a tabela de XP em uso (R53, versionada)."""

    def __init__(self, names: NameSource | None = None, *, recent_seconds: float = rules.RECENT_SESSION_SECONDS,
                 window_percent: float = rules.WINDOW_PERCENT, xp: XpSource | None = None,
                 xp_table: rules.XpTable = rules.XP_TABLE) -> None:
        self.realms: dict[str, dict[str, AlterEgo]] = {}
        self.rejected = 0
        self.names = names
        self.xp = xp
        self.xp_table = xp_table
        self._recent_seconds = recent_seconds       # o prazo da sala (R28a): quem sai dele vai para o Histórico do realm
        self.hidden: frozenset[str] = frozenset()   # realms que o Lucas escondeu (R3c): saem do estado da cidade
        self.metrics: dict[str, dict[str, Any]] = {}          # estado por realm (D-085): última contagem de linhas
        self.changes: dict[str, dict[str, Any]] = {}          # estado por realm (D-085): última leitura das alterações locais (git)
        self.tests: dict[str, dict[str, Any]] = {}            # estado por realm (D-085): o último resultado de um comando de teste (Weather)
        self.window_percent = window_percent                  # quanto vale uma janela acesa (R20d); o Hub o muda pelas preferências
        self._facades: dict[str, _FacadeCache] = {}           # fachada por realm, até algo mudar
        self._realm_seen: deque[str] = deque(maxlen=256)      # ids recentes de eventos de realm (dedupe)
        self._city: tuple[tuple[str, ...], dict[str, Any]] = ((), city.plan(()))     # o traçado da última lista de realms

    def set_recent_seconds(self, seconds: float) -> None:
        """O prazo da sala mudou na tela de configurações (R28a, R29)."""
        self._recent_seconds = seconds

    def set_window_percent(self, percent: float) -> None:
        """O x das janelas mudou na tela de configurações (R20d, R29): as fachadas se refazem na próxima leitura."""
        self.window_percent = percent

    def set_hidden(self, realm_ids: Iterable[str]) -> None:
        """Esconde estes realms da cidade (R3c). Eles continuam detectados e recebendo eventos: nada é apagado."""
        self.hidden = frozenset(realm_ids)

    def add_realm(self, realm_id: str) -> None:
        """Um realm conhecido (detectado pelos providers) existe na cidade mesmo sem nenhuma sessão: fica de
        "noite" até surgir uma (D-059). Idempotente."""
        self.realms.setdefault(realm_id, {})

    def alter_ego(self, ego_id: str) -> AlterEgo | None:
        for egos in self.realms.values():
            if ego_id in egos:
                return egos[ego_id]
        return None

    def apply(self, event: Event) -> bool:
        """Aplica um evento. Falso se inválido, repetido ou sem Alter Ego."""
        if validate(event) is not None:
            self.rejected += 1
            return False
        ego_id = event["alter_ego"]
        if ego_id is None:
            return self._apply_to_realm(event)
        egos = self.realms.setdefault(event["realm"], {})
        ego = egos.get(ego_id)
        if ego is None:
            stored = self.xp.entries_of(ego_id, self.xp_table.version) if self.xp is not None else ()
            ego = egos[ego_id] = AlterEgo(id=ego_id, realm=event["realm"], provider=event["provider"],
                                          name=self._name_for(ego_id, egos), xp=Ledger(self.xp_table, stored))
        if not ego.remember(event["id"]):
            return False
        ego.events += 1
        if ego.last_ts is None or event["ts"] > ego.last_ts:
            ego.last_ts = event["ts"]
        self._track_seq(ego, event)
        inner = event.get("inner")
        if inner and inner.get("role") == "tool":
            action = inner["text"][:_ACTION_CHARS]
            if event["agent"] is None:
                ego.last_action = action
            else:
                self._subagent(ego, event["agent"]).last_action = action
        signal = event.get("signal")
        for entry in ego.xp.observe(event):          # os subagentes rendem para o líder: o evento é da sessão, com ou sem `agent`
            if self.xp is not None:
                self.xp.record(ego_id, entry)
        if signal and signal["type"] == "command.result":
            self._record_test(event, signal)
        if signal:
            if event["agent"] is None:
                self._apply_to_leader(ego, signal)
            else:
                self._apply_to_subagent(ego, event["agent"], signal, event["ts"])
        sub = ego.subagents.get(event["agent"]) if event["agent"] is not None else None
        if sub is not None:
            sub.touch(event["ts"])
        return True

    def _record_test(self, event: Event, signal: dict[str, Any]) -> None:
        """O resultado de um comando de teste vale para o realm inteiro (R42): fica o mais novo, venha de que sessão vier. Comando que
        não é teste não é Weather."""
        if signal.get("activity") != "TESTING":
            return
        current = self.tests.get(event["realm"])
        if current is None or event["ts"] >= current["at"]:
            self.tests[event["realm"]] = {"ok": signal["ok"], "at": event["ts"], "exit_code": signal.get("exit_code"),
                                          "alter_ego": event["alter_ego"]}

    def _realm_weather(self, realm_id: str, now: datetime | None) -> dict[str, Any] | None:
        """O céu sobre o prédio (R42): limpo se o último teste rodado passou, chuva se falhou. Sem resultado, ou com um resultado mais
        velho que a sala (R28a) ou sem hora para dizer a idade, não há Weather: nada é inventado (R12)."""
        read = self.tests.get(realm_id)
        if read is None:
            return None
        age = _idle_seconds(read["at"], now)
        if age is None or age > self._recent_seconds:
            return None
        return {"sky": "clear" if read["ok"] else "rain", "at": read["at"], "exit_code": read["exit_code"], "alter_ego": read["alter_ego"]}

    def _name_for(self, ego_id: str, room: dict[str, AlterEgo]) -> str | None:
        """O nome da sessão que acabou de aparecer; os outros personagens da sala não se repetem (D-064).
        Só o líder tem nome: subagentes vivem dentro do Alter Ego e ficam com o tipo do CLI (D-065)."""
        if self.names is None:
            return None
        return self.names.name_for(ego_id, frozenset(ego.name for ego in room.values() if ego.name))

    def _apply_to_realm(self, event: Event) -> bool:
        """Evento de realm (`alter_ego` nulo, protocolo 0.3): só os Probes os emitem. A leitura mais nova vence;
        uma que chega atrasada não volta no tempo."""
        signal = event.get("signal") or {}
        kind = signal.get("type")
        if kind not in ("realm.metrics", "realm.changes", "realm.commits") or event["id"] in self._realm_seen:
            return False
        self._realm_seen.append(event["id"])
        self.realms.setdefault(event["realm"], {})
        if kind == "realm.commits":
            self._settle_commits(event["realm"], signal["commits"], event["ts"])
        elif kind == "realm.metrics":
            current = self.metrics.get(event["realm"])
            if current is None or event["ts"] >= current["counted_at"]:
                self.metrics[event["realm"]] = {"loc": signal["loc"], "files": signal.get("files"), "counted_at": event["ts"],
                                                "root": signal.get("root"), "folders": signal.get("folders")}
        else:
            current = self.changes.get(event["realm"])
            if current is None or event["ts"] >= current["counted_at"]:
                self.changes[event["realm"]] = {"items": [facade.Change(c["path"], c["type"], c["lines"]) for c in signal["changes"]],
                                                "more": signal.get("more") or 0, "counted_at": event["ts"]}
        return True

    def _settle_commits(self, realm_id: str, commits: list[dict[str, Any]], ts: str) -> None:
        """O que o git disse dos commits das sessões deste realm (R53): confirma, anula ou expira a XP de cada um. Só entra quem uma
        sessão reivindicou: o git falar de um commit que ninguém reportou não faz nada (D-106)."""
        for ego in self.realms.get(realm_id, {}).values():
            for entry in ego.xp.settle(commits, ts):
                if self.xp is not None:
                    self.xp.record(ego.id, entry)

    def expire_commits(self, now: datetime) -> None:
        """O prazo de 30 dias dos commits que não chegaram à principal vale com o git respondendo ou não (sem repositório, realm escondido,
        Probe parado): quem avança o mundo chama isto com a hora dele. O que expira é guardado no extrato como qualquer mudança."""
        _require_aware(now)
        for egos in self.realms.values():
            for ego in egos.values():
                for entry in ego.xp.settle([], now.isoformat()):
                    if self.xp is not None:
                        self.xp.record(ego.id, entry)

    def pending_commits(self, realm_id: str, now: datetime) -> list[dict[str, Any]]:
        """O que perguntar ao git sobre os commits deste realm (quem lê o git é o Probe, na borda): os provisórios e os confirmados
        ainda na janela de reversão. O mesmo recibo de duas sessões é perguntado uma vez."""
        _require_aware(now)
        asked: dict[str, dict[str, Any]] = {}
        for ego in self.realms.get(realm_id, {}).values():
            for query in ego.xp.commit_queries(now):
                asked.setdefault(query["key"], query)
        return list(asked.values())

    def xp_extract(self, limit: int = 200) -> list[dict[str, Any]]:
        """O extrato de XP do que o Orb viu (painel Progressão, V-HUD-12): as entradas de todas as sessões dos realms que a cidade mostra, as mais
        novas primeiro, cada uma com quem ganhou e o recibo (só ids e números)."""
        rows = [{"ego": ego.id, "name": ego.name, "provider": ego.provider, "realm": realm_id, "ts": entry.ts, "rule": entry.rule,
                 "xp": entry.xp, "state": entry.state, "ref": entry.ref, "evidence": entry.evidence, "version": entry.version}
                for realm_id, egos in self.realms.items() if realm_id not in self.hidden
                for ego in egos.values() for entry in ego.xp.entries]
        rows.sort(key=lambda row: row["ts"], reverse=True)
        return rows[:limit]

    def _xp_scales(self, realms: list[dict[str, Any]]) -> tuple[dict[str, dict[str, int]], dict[str, Any]]:
        """Os níveis do Realm e de Mankind (R54): a XP confirmada de todos os Alter Egos do realm, também os do Histórico, e a soma dos
        realms que a cidade mostra, com o placar por provider."""
        by_realm, by_provider = {}, {provider: 0 for provider in rules.PROVIDERS}
        provisional = 0
        for realm in realms:
            egos = self.realms[realm["id"]].values()
            pending = sum(ego.xp.provisional for ego in egos)
            by_realm[realm["id"]] = {**scale(sum(ego.xp.total for ego in egos), self.xp_table.k_realm), "provisional": pending}
            provisional += pending
            for ego in egos:
                if ego.provider is not None:
                    by_provider[ego.provider] = by_provider.get(ego.provider, 0) + ego.xp.total
        mankind = {**scale(sum(by_provider.values()), self.xp_table.k_mankind), "provisional": provisional, "by_provider": by_provider}
        return by_realm, mankind

    def _realm_facade(self, realm_id: str, metrics: dict[str, Any] | None) -> dict[str, Any] | None:
        """As janelas acesas do prédio (R20): dos andares que a contagem de linhas deu e das alterações locais que o git deu.
        Sem uma das duas leituras não há onde nem o que acender, e o prédio fica sem janelas (nunca janelas apagadas inventadas)."""
        read = self.changes.get(realm_id)
        if read is None or metrics is None or metrics["floors"] is None:
            return None
        cached = self._facades.get(realm_id)
        if cached is not None and cached.read is read and cached.counted is self.metrics[realm_id] and cached.percent == self.window_percent:
            return cached.built
        built = {"windows": facade.windows(metrics["floors"], read["items"], self.window_percent),
                 "changes": len(read["items"]), "more": read["more"], "cols": rules.FACADE_COLS, "faces": rules.FACADE_FACES}
        self._facades[realm_id] = _FacadeCache(read, self.metrics[realm_id], self.window_percent, built)
        return built

    def _realm_metrics(self, realm_id: str) -> dict[str, Any] | None:
        """As linhas reais do projeto e a classe que as faixas fixas dão; sem contagem, nada (R12)."""
        current = self.metrics.get(realm_id)
        if current is None:
            return None
        name, loc = rules.building_class(current["loc"]), current["loc"]
        height = building.levels(loc)
        split = current["folders"] is not None or current["root"] is not None      # sem a divisão por pasta, não há andares a inventar
        floors = building.floors(height=height, loc=loc, root=current["root"] or 0, folders=current["folders"] or {}) if split else None
        return {"loc": loc, "files": current["files"], "counted_at": current["counted_at"], "class": name, "levels": height,
                "bands": rules.BUILDING_TRIM[name], "antenna": name in rules.ANTENNA_CLASSES, "floors": floors}

    @staticmethod
    def _track_seq(ego: AlterEgo, event: Event) -> None:
        last = ego._last_seq.get(event["source"])
        if last is not None and event["seq"] > last + 1:
            ego.seq_gaps += 1
        if last is None or event["seq"] > last:
            ego._last_seq[event["source"]] = event["seq"]

    @staticmethod
    def _apply_to_leader(ego: AlterEgo, signal: dict[str, Any]) -> None:
        kind = signal["type"]
        if kind in rules.BASE_STATE_AFTER and kind != "subagent.started":
            ego.base = rules.BASE_STATE_AFTER[kind]
            ego.target = None
        if kind == "session.started":
            ego.ended = False
            ego.title = signal.get("title") or ego.title
            ego.model = signal.get("model") or ego.model
            ego.cwd = signal.get("cwd") or ego.cwd
        elif kind == "session.updated":           # identidade da sessão (título, modelo), sem mudar estado
            ego.title = signal.get("title") or ego.title
            ego.model = signal.get("model") or ego.model
            ego.cwd = signal.get("cwd") or ego.cwd
        elif kind == "session.ended":
            ego.ended = True
            ego.waiting.clear()
        elif kind == "activity":
            ego.base, ego.target, ego.error = signal["activity"], signal.get("target"), None
            profile.tally(ego.work, signal["activity"])
        elif kind == "waiting":
            ego.waiting[str(signal["request"])] = signal.get("action")
        elif kind == "waiting.resolved":
            ego.waiting.pop(str(signal["request"]), None)
        elif kind == "usage":
            for name in _TOKEN_FIELDS:
                value = signal.get(name)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    ego.usage[name] = ego.usage.get(name, 0) + value
            if isinstance(signal.get("cost_usd"), (int, float)):
                ego.usage["cost_usd"] = ego.usage.get("cost_usd", 0.0) + signal["cost_usd"]
        elif kind == "error":
            ego.error = str(signal["message"])
        elif kind == "signal.lost":
            ego.no_signal = True
        elif kind == "signal.restored":
            ego.no_signal = False

    @staticmethod
    def _subagent(ego: AlterEgo, agent_id: str) -> Subagent:
        sub = ego.subagents.get(agent_id)
        if sub is None:
            sub = ego.subagents[agent_id] = Subagent(id=agent_id)
        return sub

    def _apply_to_subagent(self, ego: AlterEgo, agent_id: str, signal: dict[str, Any], event_ts: str) -> None:
        sub = self._subagent(ego, agent_id)
        kind = signal["type"]
        if kind == "subagent.started":
            sub.kind = signal.get("kind") or sub.kind
            parent = signal.get("parent")
            if isinstance(parent, str) and parent:          # o protocolo não valida o tipo de `parent`: só um id de verdade entra na árvore
                sub.parent = parent
            sub.active, sub.base, sub.ended_at = True, "THINKING", None
        elif kind == "subagent.ended":
            sub.active, sub.outcome = False, signal.get("outcome") or "completed"
            sub.ended_at = event_ts
        elif kind == "activity":
            sub.base, sub.target = signal["activity"], signal.get("target")
        elif kind == "idle":
            sub.base = "IDLE"
        elif kind == "waiting":
            ego.waiting[str(signal["request"])] = signal.get("action")
        elif kind == "waiting.resolved":
            ego.waiting.pop(str(signal["request"]), None)

    def any_active(self, now: datetime) -> bool:
        """Alguma sessão da sala está ativa (não dorme)? Quem lê os providers usa isto para escolher o ritmo da leitura (D-087)."""
        _require_aware(now)
        return any(not ego.asleep(now) and ego.in_room(now, self._recent_seconds)
                   for egos in self.realms.values() for ego in egos.values())

    def layout(self) -> dict[str, Any]:
        """O traçado da cidade (R32, VISUAL.md §7): de **todos** os realms conhecidos, também os escondidos, para o
        realm escondido deixar o lote vago e os vizinhos não andarem. Só muda quando a lista de realms muda."""
        ids = tuple(sorted(self.realms))
        if self._city[0] != ids:
            self._city = (ids, city.plan(ids))
        return self._city[1]

    def snapshot(self, now: datetime | None = None) -> dict[str, Any]:
        """O estado do mundo. `now` (com fuso) é a hora de quem pede: com ela o mundo deriva o que
        depende do tempo (dormindo, sem sinal; R47). Sem `now`, nada que dependa do tempo é afirmado."""
        _require_aware(now)
        realms = []
        total_egos = active_subs = waiting = 0
        plan = self.layout()
        for realm_id in sorted(self.realms):
            if realm_id in self.hidden:
                continue
            egos = [ego.snapshot(now, self._recent_seconds) for ego in self.realms[realm_id].values()]
            metrics = self._realm_metrics(realm_id)
            # "Noite" (D-059, R47): nenhuma sessão na sala. O cliente só desenha a sala do teto apagada.
            realms.append({"id": realm_id, "alter_egos": egos, "night": not any(ego["in_room"] for ego in egos),
                           "room": room.occupancy(ego for ego in egos if ego["in_room"]),
                           "metrics": metrics, "facade": self._realm_facade(realm_id, metrics), "weather": self._realm_weather(realm_id, now),
                           "place": plan["places"][realm_id]})
            for ego in (e for e in egos if e["in_room"]):          # Mankind conta a sala; o Histórico não entra
                total_egos += 1
                active_subs += ego["active_subagents"]
                waiting += len(ego["waiting"])
        by_realm, xp = self._xp_scales(realms)
        for realm in realms:
            realm["xp"] = by_realm[realm["id"]]
        return {"realms": realms, "city": plan, "hidden_realms": sorted(self.hidden),
                "mankind": {"alter_egos": total_egos, "active_subagents": active_subs, "waiting": waiting, "xp": xp}}

    def time_key(self, now: datetime) -> tuple:
        """O que, no estado do mundo, só o passar do tempo muda: quem dorme e quem está sem sinal.
        Quem distribui o mundo compara esta chave para avisar os clientes sem esperar um evento novo.
        Fora da sala (R28a) também só o tempo muda. O ticket "hoje" (20) estende a chave quando criar estados novos de tempo."""
        _require_aware(now)
        return (tuple((ego.id, ego.asleep(now), ego.in_room(now, self._recent_seconds),
                       tuple(sub.without_signal(now) for sub in ego.subagents.values()))
                      for egos in self.realms.values() for ego in egos.values()),
                tuple((realm_id, self._realm_weather(realm_id, now) is not None) for realm_id in sorted(self.tests)))
