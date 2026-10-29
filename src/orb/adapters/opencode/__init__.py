"""Adapter do opencode (docs/adapters/OPENCODE.md).

Nível 0: `OpencodeDbReader` lê o SQLite `opencode.db` SOMENTE LEITURA, só as tabelas de sessão
(nunca as de credenciais). Estrutura levantada no opencode 2.0.23.
"""
from .index import OpencodeDbIndex
from .mapping import CAPABILITIES, PROVIDER
from .past import OpencodeDbPast
from .state_db import ALLOWED_TABLES, OpencodeDbReader, opencode_data_dir

__all__ = ["ALLOWED_TABLES", "CAPABILITIES", "OpencodeDbIndex", "OpencodeDbPast", "OpencodeDbReader", "PROVIDER", "opencode_data_dir"]
