"""Adapter do Codex (docs/adapters/CODEX.md).

Nível 0: `RolloutReader` (lê ~/.codex/sessions). Nível 1: `AppServerObserver` + `AppServerTranslator`
(app-server próprio do Orb, TUI com `codex --remote`; o observador nunca responde ao servidor).
"""
from .app_server import AppServerObserver, AppServerTranslator, app_server_command
from .mapping import CAPABILITIES, PROVIDER
from .rollout import RolloutReader, sessions_root

__all__ = ["AppServerObserver", "AppServerTranslator", "CAPABILITIES", "PROVIDER", "RolloutReader",
           "app_server_command", "sessions_root"]
