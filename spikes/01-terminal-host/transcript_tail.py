"""Nível 0 de pegada: lê (tail) o transcript do Claude Code, somente leitura.

Nunca escreve nem trava arquivos. Traduz entradas do JSONL em eventos do protocolo (subconjunto
de PROTOCOL.md). Formatos verificados em ADAPTER-CLAUDE.md.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


def encode_cwd(cwd: str) -> str:
    """Pasta de transcripts do Claude Code: tudo que não é alfanumérico vira '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def project_dir(cwd: str, home: Path | None = None) -> Path:
    return (home or Path.home()) / ".claude" / "projects" / encode_cwd(cwd)


def _short(value: Any, limit: int = 160) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 1] + "…"


TOOL_CATEGORY = {
    "Read": "read", "Glob": "read", "Grep": "read",
    "Edit": "write", "Write": "write", "NotebookEdit": "write",
    "Bash": "execute", "PowerShell": "execute",
    "WebFetch": "research", "WebSearch": "research",
    "Agent": "delegate", "Task": "delegate",
}


def category_for(tool: str) -> str:
    if tool.startswith("mcp__"):
        return "research"
    return TOOL_CATEGORY.get(tool, "other")


def translate(entry: dict[str, Any], agent: str | None = None) -> Iterator[dict[str, Any]]:
    """Uma linha do transcript -> zero ou mais eventos. Tolerante a campos desconhecidos."""
    kind = entry.get("type")
    ts = entry.get("timestamp")
    base = {"timestamp": ts, "session": entry.get("sessionId"), "alter_ego": agent or "main"}
    message = entry.get("message") or {}
    content = message.get("content")

    if kind == "user":
        if isinstance(content, str):
            origin = (entry.get("origin") or {}).get("kind")
            if origin in (None, "human") and not entry.get("isSidechain"):
                yield {**base, "type": "intrusive_thought",
                       "payload": {"text": _short(content, 400), "kind": "prompt", "channel": "terminal"}}
            return
        for block in content or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_result":
                failed = bool(block.get("is_error"))
                yield {**base, "type": "tool.failed" if failed else "tool.completed",
                       "payload": {"tool_use_id": block.get("tool_use_id")}}
            elif block.get("type") == "text" and not entry.get("isSidechain"):
                yield {**base, "type": "intrusive_thought",
                       "payload": {"text": _short(block.get("text", ""), 400), "kind": "prompt", "channel": "terminal"}}

    elif kind == "assistant":
        for block in content or []:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "tool_use":
                name = block.get("name", "?")
                inp = block.get("input") or {}
                target = inp.get("file_path") or inp.get("command") or inp.get("pattern") or inp.get("path")
                yield {**base, "type": "tool.started",
                       "payload": {"tool": name, "category": category_for(name),
                                   "target": _short(target, 120) if target else None,
                                   "tool_use_id": block.get("id")}}
            elif btype == "text" and block.get("text"):
                yield {**base, "type": "agent.message", "payload": {"text": _short(block["text"], 400)}}
            elif btype == "thinking":
                text = block.get("thinking") or ""
                # Regra do protocolo: sem texto de pensamento, NÃO se emite `thought`.
                if text:
                    yield {**base, "type": "thought", "fidelity": "raw",
                           "payload": {"text": _short(text, 400), "kind": "reasoning"}}


@dataclass
class _Followed:
    path: Path
    agent: str | None
    offset: int = 0
    buffer: bytes = b""


@dataclass
class TranscriptTail:
    """Acompanha os transcripts de um cwd criados/modificados a partir de `since`."""
    cwd: str
    since: float = field(default_factory=time.time)
    home: Path | None = None
    session_id: str | None = None   # se conhecido, só acompanha este transcript (e seus subagentes)
    _followed: dict[Path, _Followed] = field(default_factory=dict, init=False)

    def _candidates(self) -> list[tuple[Path, str | None]]:
        root = project_dir(self.cwd, self.home)
        found: list[tuple[Path, str | None]] = []
        if not root.is_dir():
            return found
        pattern = f"{self.session_id}.jsonl" if self.session_id else "*.jsonl"
        for session_file in root.glob(pattern):
            found.append((session_file, None))
            sub = root / session_file.stem / "subagents"
            if sub.is_dir():
                for sub_file in sub.glob("agent-*.jsonl"):
                    found.append((sub_file, sub_file.stem.removeprefix("agent-")))
        return found

    def poll(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for path, agent in self._candidates():
            followed = self._followed.get(path)
            try:
                stat = path.stat()
            except OSError:
                continue
            if followed is None:
                if stat.st_mtime < self.since:
                    continue  # transcript antigo: não é desta sessão hospedada
                followed = self._followed[path] = _Followed(path=path, agent=agent)
            if stat.st_size <= followed.offset:
                continue
            try:
                with open(path, "rb") as fh:  # somente leitura
                    fh.seek(followed.offset)
                    chunk = fh.read()
            except OSError:
                continue
            followed.offset += len(chunk)
            data = followed.buffer + chunk
            *lines, rest = data.split(b"\n")
            followed.buffer = rest  # linha parcial: espera o resto
            for raw in lines:
                if not raw.strip():
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue  # linha inválida: descarta, não propaga
                events.extend(translate(entry, followed.agent))
        return events
