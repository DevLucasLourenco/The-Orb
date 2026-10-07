"""Mensagens cliente -> Gateway (docs/PROTOCOL.md §9), validadas na borda.

`handle_client_message` NUNCA levanta: mensagem inválida é descartada e devolve o motivo; a sessão
continua (uma mensagem malformada derrubava a sessão inteira no Spike 2).
"""
from __future__ import annotations

import base64
import binascii
import json
from typing import Protocol

MAX_CLIENT_MESSAGE = 1_000_000


class Writable(Protocol):
    def write(self, data: str) -> None: ...
    def resize(self, cols: int, rows: int) -> None: ...


def handle_client_message(term: Writable, raw: str) -> str | None:
    """Aplica UMA mensagem ao terminal. None se ok; senão o motivo do descarte.

    {"type":"input","data":"texto"} | {"type":"input","data_b64":"..."} (seguro para bytes
    arbitrários; o JSON do Godot não escapa caracteres de controle) | {"type":"resize","cols":N,"rows":N}
    """
    if not isinstance(raw, str):
        return "mensagem deve ser texto"
    if len(raw) > MAX_CLIENT_MESSAGE:
        return "mensagem grande demais"
    try:
        msg = json.loads(raw)
    except (json.JSONDecodeError, RecursionError):
        return "mensagem não é JSON válido"
    if not isinstance(msg, dict):
        return "mensagem deve ser um objeto"
    kind = msg.get("type")
    if kind == "input":
        if isinstance(msg.get("data_b64"), str):
            try:
                text = base64.b64decode(msg["data_b64"], validate=True).decode("utf-8", "replace")
            except (binascii.Error, ValueError):
                return "data_b64 inválido"
        elif isinstance(msg.get("data"), str):
            text = msg["data"]
        else:
            return "input sem data"
        term.write(text)
        return None
    if kind == "resize":
        cols, rows = msg.get("cols"), msg.get("rows")
        valid = (isinstance(cols, int) and isinstance(rows, int) and not isinstance(cols, bool)
                 and not isinstance(rows, bool) and 1 <= cols <= 1000 and 1 <= rows <= 500)
        if not valid:
            return "resize inválido"
        term.resize(cols, rows)
        return None
    return f"tipo de mensagem desconhecido: {kind!r}"
