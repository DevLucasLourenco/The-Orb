"""O mundo do The Orb: Realm -> Alter Ego (sessão, líder) -> Subagentes.

Puro: só aplica eventos já validados e devolve snapshots. Sem disco, rede ou relógio (o tempo vem
do `ts` dos eventos). Mesmos eventos na mesma ordem -> mesmo mundo.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from ..protocol import Event, validate
from . import rules

_TOKEN_FIELDS = ("input_tokens", "output_tokens", "cache_read_tokens", "reasoning_tokens")


@dataclass
class Subagent:
    id: str
    kind: str | None = None
    parent: str | None = None
    base: str = "THINKING"
    target: str | None = None
    active: bool = True
    outcome: str | None = None
    last_ts: str | None = None

    def snapshot(self) -> dict[str, Any]:
        state = self.base if self.active else "COMPLETED"
        return {"id": self.id, "kind": self.kind, "parent": self.parent, "state": state,
                "area": rules.area_for(state), "target": self.target, "active": self.active,
                "outcome": self.outcome, "last_ts": self.last_ts}


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
    ended: bool = False
    no_signal: bool = False
    error: str | None = None
    waiting: dict[str, str | None] = field(default_factory=dict)   # request -> ação
    subagents: dict[str, Subagent] = field(default_factory=dict)
    usage: dict[str, float] = field(default_factory=dict)
    events: int = 0
    human_inputs: int = 0
    seq_gaps: int = 0
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

    def state(self) -> str:
        active = sum(1 for sub in self.subagents.values() if sub.active)
        return rules.leader_state(self.base, no_signal=self.no_signal, waiting=bool(self.waiting),
                                  error=self.error is not None, active_subagents=active)

    def snapshot(self) -> dict[str, Any]:
        state = self.state()
        return {
            "id": self.id, "provider": self.provider, "session": self.session, "title": self.title,
            "model": self.model, "state": state, "area": rules.area_for(state), "target": self.target,
            "ended": self.ended, "error": self.error,
            "waiting": [{"request": r, "action": a} for r, a in self.waiting.items()],
            "events": self.events, "human_inputs": self.human_inputs, "seq_gaps": self.seq_gaps,
            "usage": dict(self.usage), "last_ts": self.last_ts,
            "team": [sub.snapshot() for sub in self.subagents.values()],
        }


class World:
    """Estado de todo o Orb. `apply` é idempotente por `id` de evento."""

    def __init__(self) -> None:
        self.realms: dict[str, dict[str, AlterEgo]] = {}
        self.rejected = 0

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
            return False        # eventos de realm (probes) ainda não alteram o mundo
        egos = self.realms.setdefault(event["realm"], {})
        ego = egos.get(ego_id)
        if ego is None:
            ego = egos[ego_id] = AlterEgo(id=ego_id, realm=event["realm"], provider=event["provider"])
        if not ego.remember(event["id"]):
            return False
        ego.events += 1
        ego.last_ts = event["ts"]
        self._track_seq(ego, event)
        signal = event.get("signal")
        if signal:
            if event["agent"] is None:
                self._apply_to_leader(ego, signal, event)
            else:
                self._apply_to_subagent(ego, event["agent"], signal, event["ts"])
        return True

    @staticmethod
    def _track_seq(ego: AlterEgo, event: Event) -> None:
        last = ego._last_seq.get(event["source"])
        if last is not None and event["seq"] > last + 1:
            ego.seq_gaps += 1
        if last is None or event["seq"] > last:
            ego._last_seq[event["source"]] = event["seq"]

    @staticmethod
    def _apply_to_leader(ego: AlterEgo, signal: dict[str, Any], event: Event) -> None:
        kind = signal["type"]
        if kind in rules.BASE_STATE_AFTER and kind != "subagent.started":
            ego.base = rules.BASE_STATE_AFTER[kind]
            ego.target = None
        if kind == "session.started":
            ego.ended = False
            ego.title = signal.get("title") or ego.title
            ego.model = signal.get("model") or ego.model
            ego.cwd = signal.get("cwd") or ego.cwd
        elif kind == "session.ended":
            ego.ended = True
            ego.waiting.clear()
        elif kind == "activity":
            ego.base, ego.target, ego.error = signal["activity"], signal.get("target"), None
        elif kind == "human.input":
            ego.human_inputs += 1
            ego.error = None
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
    def _apply_to_subagent(ego: AlterEgo, agent_id: str, signal: dict[str, Any], ts: str) -> None:
        sub = ego.subagents.get(agent_id)
        if sub is None:
            sub = ego.subagents[agent_id] = Subagent(id=agent_id)
        sub.last_ts = ts
        kind = signal["type"]
        if kind == "subagent.started":
            sub.kind = signal.get("kind") or sub.kind
            sub.parent = signal.get("parent") or sub.parent
            sub.active, sub.base = True, "THINKING"
        elif kind == "subagent.ended":
            sub.active, sub.outcome = False, signal.get("outcome") or "completed"
        elif kind == "activity":
            sub.base, sub.target = signal["activity"], signal.get("target")
        elif kind == "idle":
            sub.base = "IDLE"
        elif kind == "waiting":
            ego.waiting[str(signal["request"])] = signal.get("action")
        elif kind == "waiting.resolved":
            ego.waiting.pop(str(signal["request"]), None)

    def snapshot(self) -> dict[str, Any]:
        realms = []
        total_egos = active_subs = waiting = 0
        for realm_id in sorted(self.realms):
            egos = [ego.snapshot() for ego in self.realms[realm_id].values()]
            realms.append({"id": realm_id, "alter_egos": egos})
            total_egos += len(egos)
            for ego in egos:
                active_subs += sum(1 for sub in ego["team"] if sub["active"])
                waiting += len(ego["waiting"])
        return {"realms": realms,
                "mankind": {"alter_egos": total_egos, "active_subagents": active_subs, "waiting": waiting}}
