"""Envelope de evento do The Orb (docs/PROTOCOL.md §2-§4): construção, limites e validação.

Eventos são dicts JSON-prontos. `make_event` é a única forma de criar um; `validate` é a porta de
entrada do Core e do Gateway (validação na borda: nunca levanta, devolve o motivo).
"""
from __future__ import annotations

import json
from typing import Any

from .vocab import (ACTIVITIES, CHANNELS, FIDELITIES, HUMAN_INPUT_KINDS, INNER_ROLES, ORIGINS,
                    PROTOCOL_VERSION, SIGNAL_FIELDS)

MAX_BODY_BYTES = 16 * 1024    # native.body serializado
MAX_STRING = 4 * 1024         # cada string dentro de native.body
MAX_INNER_TEXT = 4000         # inner.text, em caracteres
_ELLIPSIS = "…"

Event = dict[str, Any]


def clip_text(text: str, limit: int = MAX_INNER_TEXT) -> str:
    """Corta texto preservando o início; marca o corte com reticências."""
    return text if len(text) <= limit else text[: limit - 1] + _ELLIPSIS


def _clip_value(value: Any, limit: int) -> tuple[Any, bool]:
    if isinstance(value, str):
        return (value, False) if len(value) <= limit else (value[: limit - 1] + _ELLIPSIS, True)
    if isinstance(value, dict):
        out, cut = {}, False
        for key, item in value.items():
            out[key], item_cut = _clip_value(item, limit)
            cut |= item_cut
        return out, cut
    if isinstance(value, list):
        out_list, cut = [], False
        for item in value:
            clipped, item_cut = _clip_value(item, limit)
            out_list.append(clipped)
            cut |= item_cut
        return out_list, cut
    return value, False


def _size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, default=str).encode("utf-8"))


def clip_body(body: Any) -> tuple[dict[str, Any], bool]:
    """Limita o corpo nativo (§3): corta valores, preserva chaves. Devolve (corpo, cortado)."""
    if not isinstance(body, dict):
        body = {"value": body}
    clipped, cut = _clip_value(body, MAX_STRING)
    for limit in (1024, 256, 64):          # aperta até caber
        if _size(clipped) <= MAX_BODY_BYTES:
            return clipped, cut
        clipped, _ = _clip_value(clipped, limit)
        cut = True
    if _size(clipped) <= MAX_BODY_BYTES:
        return clipped, True
    return {"_omitted": True, "keys": sorted(map(str, body))[:200]}, True


def make_event(*, id: str, ts: str, provider: str | None, source: str, realm: str,
               alter_ego: str | None, agent: str | None, seq: int, kind: str, body: Any,
               inner: dict[str, Any] | None = None, signal: dict[str, Any] | None = None) -> Event:
    native_body, truncated = clip_body(body)
    if inner is not None and isinstance(inner.get("text"), str):
        inner = {**inner, "text": clip_text(inner["text"])}
    return {
        "v": PROTOCOL_VERSION, "id": id, "ts": ts, "provider": provider, "source": source,
        "realm": realm, "alter_ego": alter_ego, "agent": agent, "seq": seq,
        "native": {"kind": kind, "body": native_body, "truncated": truncated},
        "inner": inner, "signal": signal,
    }


def _is_str(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def validate(event: Any) -> str | None:
    """None se o evento é válido; senão o motivo. Nunca levanta."""
    if not isinstance(event, dict):
        return "evento deve ser um objeto"
    version = event.get("v")
    if not isinstance(version, str) or version.split(".")[0] != PROTOCOL_VERSION.split(".")[0]:
        return f"versão de protocolo não suportada: {version!r}"
    for key in ("id", "ts", "source", "realm"):
        if not _is_str(event.get(key)):
            return f"campo obrigatório ausente ou vazio: {key}"
    for key in ("provider", "alter_ego", "agent"):
        if event.get(key) is not None and not _is_str(event.get(key)):
            return f"campo deve ser texto ou null: {key}"
    if not isinstance(event.get("seq"), int) or isinstance(event.get("seq"), bool) or event["seq"] < 0:
        return "seq deve ser inteiro >= 0"
    native = event.get("native")
    if not isinstance(native, dict) or not _is_str(native.get("kind")) or not isinstance(native.get("body"), dict):
        return "native deve ter kind (texto) e body (objeto)"
    inner = event.get("inner")
    if inner is not None:
        problem = _validate_inner(inner)
        if problem:
            return problem
    signal = event.get("signal")
    if signal is not None:
        problem = _validate_signal(signal)
        if problem:
            return problem
    return None


def _validate_inner(inner: Any) -> str | None:
    if not isinstance(inner, dict):
        return "inner deve ser um objeto"
    if inner.get("origin") not in ORIGINS:
        return f"inner.origin inválido: {inner.get('origin')!r}"
    if inner.get("role") not in INNER_ROLES:
        return f"inner.role inválido: {inner.get('role')!r}"
    if not isinstance(inner.get("text"), str):
        return "inner.text deve ser texto"
    if inner.get("role") == "thought" and inner.get("fidelity") not in FIDELITIES:
        return "inner.fidelity obrigatório (raw|summary) em pensamento"
    return None


def _validate_signal(signal: Any) -> str | None:
    if not isinstance(signal, dict):
        return "signal deve ser um objeto"
    kind = signal.get("type")
    required = SIGNAL_FIELDS.get(kind) if isinstance(kind, str) else None
    if required is None:
        return f"signal.type desconhecido: {kind!r}"
    missing = [field for field in required if field not in signal]
    if missing:
        return f"signal {kind} sem campos: {', '.join(sorted(missing))}"
    if kind == "activity" and signal["activity"] not in ACTIVITIES:
        return f"atividade inválida: {signal['activity']!r}"
    if kind == "human.input" and (signal["kind"] not in HUMAN_INPUT_KINDS or signal["channel"] not in CHANNELS):
        return "human.input com kind/channel inválido"
    return None
