"""Adapter do Claude Code (docs/adapters/CLAUDE.md).

Nível 0: `TranscriptReader` (lê ~/.claude/projects). Nível 1: `session_settings` + `HookTranslator`
(hooks por sessão via `claude --settings`).
"""
from .hooks import HOOK_EVENTS, HookTranslator, session_settings
from .mapping import CAPABILITIES, PROVIDER
from .transcript import TranscriptReader, encode_cwd, project_dir

__all__ = ["CAPABILITIES", "HOOK_EVENTS", "HookTranslator", "PROVIDER", "TranscriptReader",
           "encode_cwd", "project_dir", "session_settings"]
