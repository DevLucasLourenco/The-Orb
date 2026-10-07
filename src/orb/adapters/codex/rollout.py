"""Nível 0 do Codex: lê os rollouts (~/.codex/sessions/AAAA/MM/DD/rollout-*.jsonl) somente leitura.

Cada rollout é uma thread. A primeira linha (`session_meta`) diz o id, o `cwd` e, se for subagente,
o `parent_thread_id`. Rollouts podem ter centenas de MB: arquivo que já existia começa do FIM, e só a
primeira linha é lida à parte. Estrutura verificada em docs/adapters/CODEX.md §7 (Codex 0.160.1).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...protocol import Event
from .._shared import EventFactory, JsonlFollower, RealmOf, classify_command, single_realm
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


def session_index(home: Path | None = None) -> Path:
    """`~/.codex/session_index.jsonl`: `{id, thread_name, updated_at}` por linha (o nome da conversa)."""
    return (home or Path.home()) / ".codex" / "session_index.jsonl"



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
    realm: str
    announced: bool = False
    model: str | None = None
    title: str | None = None


class RolloutReader:
    """Acompanha as threads do Codex ativas desde `since`. Uma instância serve um realm (`cwd` +
    `realm`) ou vários (`realm_of`: a loja do Codex é única, então lê-la uma vez basta)."""

    def __init__(self, cwd: str | None = None, *, realm: str = "", since: float | None = None,
                 home: Path | None = None, replay: bool = False, realm_of: RealmOf | None = None) -> None:
        self.realm_of = realm_of or single_realm(cwd, realm)
        self.since = time.time() if since is None else since
        self.home = home
        self.replay = replay
        self._threads: dict[Path, _Thread] = {}
        self._ignored: set[Path] = set()
        self._factories: dict[str, EventFactory] = {}
        self._last_discovery = float("-inf")
        self._titles: dict[str, str] = {}
        self._titles_mtime: float | None = None

    @staticmethod
    def _root(thread_id: str, by_id: dict[str, "_Thread"]) -> str:
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
            realm = self.realm_of(meta.get("cwd"))
            if realm is None:
                self._ignored.add(path)           # outra pasta: não é de nenhum realm observado
                continue
            born = getattr(stat, "st_birthtime", stat.st_ctime)
            parent = meta.get("parent_thread_id") if isinstance(meta.get("parent_thread_id"), str) else None
            self._threads[path] = _Thread(meta["id"], parent or None,
                                          JsonlFollower(path, start_at_end=not self.replay and born < self.since), meta, realm)

    def _factory(self, realm: str, root: str) -> EventFactory:
        factory = self._factories.get(root)
        if factory is None:
            factory = self._factories[root] = EventFactory(provider=mapping.PROVIDER, source=SOURCE,
                                                           realm=realm, session=root)
        return factory

    def _load_titles(self) -> None:
        """Relê o índice de nomes só quando ele muda (arquivo pequeno, somente leitura)."""
        path = session_index(self.home)
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return
        if mtime == self._titles_mtime:
            return
        self._titles_mtime = mtime
        titles: dict[str, str] = {}
        try:
            with open(path, "rb") as fh:
                for raw in fh:
                    try:
                        entry = json.loads(raw)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                    if isinstance(entry, dict) and isinstance(entry.get("id"), str) and isinstance(entry.get("thread_name"), str):
                        titles[entry["id"]] = entry["thread_name"]       # a última linha vence
        except OSError:
            return
        self._titles = titles

    def poll(self) -> list[Event]:
        self._discover()
        self._load_titles()
        events: list[Event] = []
        by_id = {t.thread_id: t for t in self._threads.values()}
        for thread in self._threads.values():
            root = self._root(thread.thread_id, by_id)
            agent = thread.thread_id if root != thread.thread_id else None
            factory = self._factory(by_id[root].realm if root in by_id else thread.realm, root)
            if not thread.announced:
                thread.announced = True
                meta = {k: v for k, v in thread.meta.items() if k not in ("base_instructions", "instructions")}
                thread.title = self._titles.get(thread.thread_id)
                signal = ({"type": "subagent.started", "kind": meta.get("agent_role") or meta.get("agent_nickname")}
                          if agent else {"type": "session.started", "cwd": meta.get("cwd"), "title": thread.title})
                events.append(factory.make(f"{thread.thread_id}:meta", meta.get("timestamp"), "session_meta",
                                           meta, agent=agent, signal=signal))
            title = self._titles.get(thread.thread_id)
            if agent is None and title and title != thread.title:
                thread.title = title
                events.append(factory.make(f"{thread.thread_id}:title:{len(title)}:{title[:40]}", None, "session_index",
                                           {"id": thread.thread_id, "thread_name": title},
                                           signal={"type": "session.updated", "title": title}))
            for offset, entry in thread.follower.poll():
                event = self._translate(factory, thread, agent, entry, offset)
                if event is not None:
                    events.append(event)
        return events

    @staticmethod
    def _translate(factory: EventFactory, thread: _Thread, agent: str | None, entry: dict[str, Any],
                   offset: int) -> Event | None:
        thread_id = thread.thread_id
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
        elif etype == "turn_context" and agent is None:
            model = payload.get("model")
            if not isinstance(model, str) or model == thread.model:
                return None
            thread.model = model             # o modelo da sessão vem do contexto de cada turno
            payload = {"model": model, "effort": payload.get("effort"), "cwd": payload.get("cwd")}
            signal = {"type": "session.updated", "model": model}
        else:
            return None                      # world_state, compacted…: sem trabalho visível
        return factory.make(key, ts, kind, payload, agent=agent, inner=inner, signal=signal)

