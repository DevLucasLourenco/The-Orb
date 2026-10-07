"""Nível 0 do Claude Code: lê os transcripts (JSONL) somente leitura e produz eventos.

Local: ~/.claude/projects/<cwd codificado>/<session_id>.jsonl, e os subagentes em
<session_id>/subagents/agent-<id>.jsonl (+ .meta.json). Cada arquivo de sessão é um Alter Ego.
Formatos em docs/adapters/CLAUDE.md §2.
"""
from __future__ import annotations

import json
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ...protocol import Event
from .._shared import EventFactory, JsonlFollower, realm_id_for
from . import mapping

SOURCE = "claude/transcript"
_SEEN_MESSAGES = 2048     # ids de mensagem lembrados para não contar `usage` repetido


def encode_cwd(cwd: str) -> str:
    """Pasta de transcripts do Claude Code: tudo que não é alfanumérico vira '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def project_dir(cwd: str, home: Path | None = None) -> Path:
    return (home or Path.home()) / ".claude" / "projects" / encode_cwd(cwd)


@dataclass
class _Subagent:
    agent_id: str
    follower: JsonlFollower
    meta: dict[str, Any] = field(default_factory=dict)
    announced: bool = False


@dataclass
class _Session:
    session_id: str
    follower: JsonlFollower
    factory: EventFactory
    subagents: dict[str, _Subagent] = field(default_factory=dict)
    foreground_tools: dict[str, str] = field(default_factory=dict)   # toolUseId -> agentId
    usage_seen: "OrderedDict[str, None]" = field(default_factory=OrderedDict)


class TranscriptReader:
    """Acompanha as sessões de um realm (uma pasta) a partir de `since`.

    - Com `session_id` (modo Hospedar), só aquela sessão e os subagentes dela.
    - Sem `session_id` (modo Observar), toda sessão da pasta ativa depois de `since`.
    - Arquivo criado antes de `since` começa do fim, a menos que `replay=True`.
    """

    def __init__(self, cwd: str, *, realm: str | None = None, session_id: str | None = None,
                 since: float | None = None, home: Path | None = None, replay: bool = False) -> None:
        self.cwd = cwd
        self.realm = realm or realm_id_for(cwd)
        self.session_id = session_id
        self.since = time.time() if since is None else since
        self.home = home
        self.replay = replay
        self._sessions: dict[Path, _Session] = {}

    # --- descoberta -------------------------------------------------------------------------
    def _discover(self) -> None:
        root = project_dir(self.cwd, self.home)
        if not root.is_dir():
            return
        pattern = f"{self.session_id}.jsonl" if self.session_id else "*.jsonl"
        for path in root.glob(pattern):
            if path in self._sessions:
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            if stat.st_mtime < self.since:
                continue      # transcript parado: não é uma sessão ativa
            born = getattr(stat, "st_birthtime", stat.st_ctime)
            self._sessions[path] = _Session(
                session_id=path.stem,
                follower=JsonlFollower(path, start_at_end=not self.replay and born < self.since),
                factory=EventFactory(provider=mapping.PROVIDER, source=SOURCE, realm=self.realm,
                                     session=path.stem))
        for session_path, session in self._sessions.items():
            folder = session_path.parent / session.session_id / "subagents"
            if not folder.is_dir():
                continue
            for sub_path in folder.glob("agent-*.jsonl"):
                agent_id = sub_path.stem.removeprefix("agent-")
                if agent_id not in session.subagents:
                    session.subagents[agent_id] = _Subagent(agent_id, JsonlFollower(sub_path))

    # --- leitura ----------------------------------------------------------------------------
    def poll(self) -> list[Event]:
        self._discover()
        events: list[Event] = []
        for session in self._sessions.values():
            # Anuncia subagentes novos antes de ler o líder: o resultado da ferramenta que os
            # encerra pode vir nesta mesma leitura.
            for sub in session.subagents.values():
                if not sub.announced:
                    events.append(self._announce(session, sub))
            for offset, entry in session.follower.poll():
                events.extend(self._translate(session, entry, offset, agent=None))
            for sub in session.subagents.values():
                for offset, entry in sub.follower.poll():
                    events.extend(self._translate(session, entry, offset, agent=sub.agent_id))
        return events

    def _announce(self, session: _Session, sub: _Subagent) -> Event:
        meta_path = sub.follower.path.with_suffix(".meta.json")
        try:
            sub.meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            sub.meta = {}
        sub.announced = True
        tool_use = sub.meta.get("toolUseId")
        if isinstance(tool_use, str) and sub.meta.get("requestShape") == "foreground":
            session.foreground_tools[tool_use] = sub.agent_id
        body = {"agentId": sub.agent_id, **{k: v for k, v in sub.meta.items() if k != "prompt"}}
        return session.factory.make(
            f"{sub.agent_id}#meta", None, "subagent/meta", body, agent=sub.agent_id,
            inner={"origin": "agent", "role": "system",
                   "text": f"{sub.meta.get('agentType', 'subagente')}: {sub.meta.get('description', '')}".strip()},
            signal={"type": "subagent.started", "kind": sub.meta.get("agentType")})

    def _translate(self, session: _Session, entry: dict[str, Any], offset: int,
                   agent: str | None) -> list[Event]:
        """Uma linha do transcript -> zero ou mais eventos. Tolerante a campos desconhecidos."""
        kind = entry.get("type")
        ts = entry.get("timestamp") if isinstance(entry.get("timestamp"), str) else None
        key = entry.get("uuid") if isinstance(entry.get("uuid"), str) else f"@{agent or ''}{offset}"
        message = entry.get("message") if isinstance(entry.get("message"), dict) else {}
        content = message.get("content")
        make = session.factory.make
        out: list[Event] = []

        if kind == "user":
            if isinstance(content, str):
                out.append(self._prompt(session, entry, content, key, ts, agent))
                return out
            texts = []
            for index, block in enumerate(content if isinstance(content, list) else []):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_result":
                    out.append(make(f"{key}#{index}", ts, "user/tool_result", block, agent=agent,
                                    inner={"origin": "agent", "role": "result",
                                           "text": _result_text(block)}))
                    ended = session.foreground_tools.pop(block.get("tool_use_id"), None)
                    if ended:
                        out.append(make(f"{key}#{index}#ended", ts, "user/tool_result", {"tool_use_id": block.get("tool_use_id")},
                                        agent=ended, signal={"type": "subagent.ended", "outcome": "failed" if block.get("is_error") else "completed"}))
                elif block.get("type") == "text":
                    texts.append(block.get("text") or "")
            if texts:
                out.append(self._prompt(session, entry, "\n".join(texts), key, ts, agent))
            return out

        if kind != "assistant" or not isinstance(content, list):
            return out
        for index, block in enumerate(content):
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            ekey = f"{key}#{index}"
            if btype == "tool_use":
                name = str(block.get("name") or "?")
                tool_input = block.get("input")
                activity = mapping.activity_for_tool(name, tool_input)
                out.append(make(ekey, ts, "assistant/tool_use", block, agent=agent,
                                inner={"origin": "agent", "role": "tool", "text": mapping.tool_text(name, tool_input)},
                                signal={"type": "activity", "activity": activity, "target": mapping.tool_target(tool_input)}))
            elif btype == "text" and block.get("text"):
                out.append(make(ekey, ts, "assistant/text", block, agent=agent,
                                inner={"origin": "agent", "role": "narration", "text": block["text"]}))
            elif btype == "thinking" and block.get("thinking"):
                # Regra do protocolo: sem texto de pensamento, nada de entrada `thought`.
                body = {k: v for k, v in block.items() if k != "signature"}
                out.append(make(ekey, ts, "assistant/thinking", body, agent=agent,
                                inner={"origin": "agent", "role": "thought", "text": block["thinking"], "fidelity": "raw"},
                                signal={"type": "activity", "activity": "THINKING"}))
        message_id = message.get("id")
        usage = mapping.usage_signal(message.get("usage"))
        if usage and isinstance(message_id, str) and message_id not in session.usage_seen:
            session.usage_seen[message_id] = None
            if len(session.usage_seen) > _SEEN_MESSAGES:
                session.usage_seen.popitem(last=False)
            out.append(make(f"{message_id}#usage", ts, "assistant/usage", message.get("usage"), agent=agent, signal=usage))
        if message.get("stop_reason") == "end_turn" and agent is None:
            out.append(make(f"{key}#stop", ts, "assistant/stop", {"stop_reason": "end_turn"}, signal={"type": "idle"}))
        return out

    def _prompt(self, session: _Session, entry: dict[str, Any], text: str, key: str, ts: str | None,
                agent: str | None) -> Event:
        origin, prompt_kind = mapping.prompt_origin(entry, text)
        if agent is not None or origin != "human":
            return session.factory.make(key, ts, "user/system", {"content": text}, agent=agent,
                                        inner={"origin": "agent", "role": "system", "text": text})
        return session.factory.make(
            key, ts, "user/prompt", {"content": text, "origin": entry.get("origin"), "promptId": entry.get("promptId")},
            inner={"origin": "human", "role": "prompt", "text": text},
            signal={"type": "human.input", "kind": prompt_kind, "channel": "terminal"})


def _result_text(block: dict[str, Any]) -> str:
    content = block.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    else:
        text = ""
    return ("[erro] " if block.get("is_error") else "") + text
