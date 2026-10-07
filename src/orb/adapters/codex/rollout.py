"""Nível 0 do Codex: lê os rollouts (~/.codex/sessions/AAAA/MM/DD/rollout-*.jsonl) somente leitura.

Cada rollout é uma thread. A primeira linha (`session_meta`) diz o id, o `cwd` e, se for subagente,
o `parent_thread_id`. Rollouts podem ter centenas de MB: arquivo que já existia começa do FIM, e só a
primeira linha é lida à parte. Estrutura verificada em docs/adapters/CODEX.md §7 (Codex 0.160.1).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...protocol import Event
from .._shared import EventFactory, JsonlFollower, classify_command
from . import mapping

SOURCE = "codex/rollout"
DISCOVER_EVERY = 2.0      # segundos entre varreduras da árvore de sessões (centenas de arquivos)

# Ferramenta (function_call/custom_tool_call) -> atividade. `exec` usa o classificador de comandos.
TOOL_ACTIVITY: dict[str, str] = {
    "spawn_agent": "DELEGATING", "send_message": "DELEGATING", "followup_task": "DELEGATING",
    "wait_agent": "DELEGATING", "list_agents": "DELEGATING",
    "request_user_input_async": "BLOCKED",
}


def sessions_root(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".codex" / "sessions"


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


def _first_line(path: Path) -> dict[str, Any] | None:
    try:
        with open(path, "rb") as fh:              # somente leitura
            line = fh.readline(1024 * 1024)
        entry = json.loads(line)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return entry if isinstance(entry, dict) else None


@dataclass
class _Thread:
    thread_id: str
    parent: str | None
    follower: JsonlFollower
    meta: dict[str, Any]
    announced: bool = False


class RolloutReader:
    """Acompanha as threads do Codex de um realm (filtradas pelo `cwd`) ativas desde `since`."""

    def __init__(self, cwd: str | None, *, realm: str, since: float | None = None,
                 home: Path | None = None, replay: bool = False) -> None:
        self.cwd = _norm(cwd) if cwd else None
        self.realm = realm
        self.since = time.time() if since is None else since
        self.home = home
        self.replay = replay
        self._threads: dict[Path, _Thread] = {}
        self._ignored: set[Path] = set()
        self._factories: dict[str, EventFactory] = {}
        self._last_discovery = float("-inf")

    def _root(self, thread_id: str) -> str:
        by_id = {t.thread_id: t for t in self._threads.values()}
        seen: set[str] = set()
        while thread_id in by_id and by_id[thread_id].parent and thread_id not in seen:
            seen.add(thread_id)
            thread_id = by_id[thread_id].parent or thread_id
        return thread_id

    def _discover(self) -> None:
        now = time.monotonic()
        if now - self._last_discovery < DISCOVER_EVERY:
            return
        self._last_discovery = now
        root = sessions_root(self.home)
        if not root.is_dir():
            return
        for path in root.glob("*/*/*/rollout-*.jsonl"):
            if path in self._threads or path in self._ignored:
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            if stat.st_mtime < self.since:
                continue
            first = _first_line(path)
            meta = (first or {}).get("payload") if (first or {}).get("type") == "session_meta" else None
            if not isinstance(meta, dict) or not isinstance(meta.get("id"), str):
                continue             # ainda sem a primeira linha: tenta no próximo poll
            if self.cwd and (not isinstance(meta.get("cwd"), str) or _norm(meta["cwd"]) != self.cwd):
                self._ignored.add(path)
                continue
            born = getattr(stat, "st_birthtime", stat.st_ctime)
            parent = meta.get("parent_thread_id") if isinstance(meta.get("parent_thread_id"), str) else None
            self._threads[path] = _Thread(meta["id"], parent or None,
                                          JsonlFollower(path, start_at_end=not self.replay and born < self.since), meta)

    def _factory(self, root: str) -> EventFactory:
        factory = self._factories.get(root)
        if factory is None:
            factory = self._factories[root] = EventFactory(provider=mapping.PROVIDER, source=SOURCE,
                                                           realm=self.realm, session=root)
        return factory

    def poll(self) -> list[Event]:
        self._discover()
        events: list[Event] = []
        for thread in self._threads.values():
            root = self._root(thread.thread_id)
            agent = thread.thread_id if root != thread.thread_id else None
            factory = self._factory(root)
            if not thread.announced:
                thread.announced = True
                meta = {k: v for k, v in thread.meta.items() if k not in ("base_instructions", "instructions")}
                signal = ({"type": "subagent.started", "kind": meta.get("agent_role") or meta.get("agent_nickname")}
                          if agent else {"type": "session.started", "cwd": meta.get("cwd")})
                events.append(factory.make(f"{thread.thread_id}:meta", meta.get("timestamp"), "session_meta",
                                           meta, agent=agent, signal=signal))
            for offset, entry in thread.follower.poll():
                event = self._translate(factory, thread.thread_id, agent, entry, offset)
                if event is not None:
                    events.append(event)
        return events

    @staticmethod
    def _translate(factory: EventFactory, thread_id: str, agent: str | None, entry: dict[str, Any],
                   offset: int) -> Event | None:
        etype = entry.get("type")
        payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
        ptype = payload.get("type")
        ts = entry.get("timestamp") if isinstance(entry.get("timestamp"), str) else None
        ordinal = entry.get("ordinal")
        key = f"{thread_id}:{ordinal if isinstance(ordinal, int) else '@' + str(offset)}"
        kind = f"{etype}/{ptype}" if ptype else str(etype)
        inner = signal = None

        if etype == "session_meta":
            return None                      # já anunciada a partir da primeira linha
        if etype == "response_item":
            if ptype == "message":
                role = payload.get("role")
                text = "\n".join(str(part.get("text", "")) for part in payload.get("content") or []
                                 if isinstance(part, dict) and part.get("text"))
                if role == "assistant":
                    inner = {"role": "narration", "text": text}
                elif role == "user":
                    inner = {"role": "prompt", "text": text}
                else:
                    return None              # instruções de developer/system: moldam o agente, não são trabalho
            elif ptype == "reasoning":
                summary = "\n".join(str(part.get("text", "")) for part in payload.get("summary") or []
                                    if isinstance(part, dict) and part.get("text"))
                signal = {"type": "activity", "activity": "THINKING"}
                if summary:
                    inner = {"role": "thought", "text": summary, "fidelity": "summary"}
                payload = {k: v for k, v in payload.items() if k != "encrypted_content"}
            elif ptype in ("function_call", "custom_tool_call"):
                name = str(payload.get("name") or "")
                argument = payload.get("input") if ptype == "custom_tool_call" else payload.get("arguments")
                activity = classify_command(argument) if name == "exec" else TOOL_ACTIVITY.get(name, "EXECUTING")
                inner = {"role": "tool", "text": f"{name} {argument or ''}".strip()}
                signal = {"type": "activity", "activity": activity}
            elif ptype in ("function_call_output", "custom_tool_call_output"):
                output = payload.get("output")
                if isinstance(output, list):
                    output = "\n".join(str(part.get("text", "")) for part in output if isinstance(part, dict))
                inner = {"role": "result", "text": str(output or "")}
            elif ptype == "compaction":
                return None
        elif etype == "event_msg":
            if ptype in ("task_complete", "turn_aborted"):
                signal = {"type": "idle"}
            elif ptype == "task_started":
                signal = {"type": "activity", "activity": "THINKING"}
            else:
                return None                  # token_count/item_completed: redundantes com as linhas acima
        elif etype == "token_usage_record":
            usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else None
            if usage is None:
                return None
            signal = {"type": "usage", "input_tokens": int(usage.get("input_tokens") or 0),
                      "output_tokens": int(usage.get("output_tokens") or 0),
                      "cache_read_tokens": int(usage.get("cached_input_tokens") or 0),
                      "reasoning_tokens": int(usage.get("reasoning_output_tokens") or 0)}
        else:
            return None                      # turn_context, world_state, compacted…: sem trabalho visível
        return factory.make(key, ts, kind, payload, agent=agent, inner=inner, signal=signal)

