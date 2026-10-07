"""Adapter do Hermes Agent (docs/adapters/HERMES.md).

Nível 0: `StateDbReader` lê o SQLite `state.db` do Hermes SOMENTE LEITURA (URI `mode=ro`).
Levantado pela leitura do código-fonte do Hermes 0.20.5; ainda **não verificado ao vivo**.
"""
from .mapping import CAPABILITIES, PROVIDER
from .state_db import StateDbReader, hermes_home

__all__ = ["CAPABILITIES", "PROVIDER", "StateDbReader", "hermes_home"]
