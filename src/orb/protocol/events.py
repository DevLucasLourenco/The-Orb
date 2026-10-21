"""Envelope de evento do The Orb (docs/PROTOCOL.md §2-§4): construção, limites e validação.

Eventos são dicts JSON-prontos. `make_event` é a única forma de criar um; `validate` é a porta de
entrada do Core e do Gateway (validação na borda: nunca levanta, devolve o motivo).
"""
from __future__ import annotations

import json
from typing import Any

from .vocab import (
    ACTIVITIES,
    CHANGE_TYPES,
    FIDELITIES,
    INNER_ROLES,
    PROTOCOL_VERSION,
    REALM_SIGNALS,
    SIGNAL_FIELDS,
)

MAX_BODY_BYTES = 16 * 1024    # native.body serializado
MAX_STRING = 4 * 1024         # cada string dentro de native.body
MAX_INNER_TEXT = 4000         # inner.text, em caracteres
MAX_FOLDERS = 64              # realm.metrics: pastas de primeiro nível listadas (as maiores; o resto fica no total)
MAX_FOLDER_NAME = 255         # realm.metrics: tamanho do nome de uma pasta
MAX_CHANGES = 5000            # realm.changes: alterações listadas (o resto vira `more`)
MAX_CHANGE_PATH = 1024        # realm.changes: tamanho do caminho de uma alteração
MAX_COMMITS = 500             # realm.commits: commits consultados por leitura
MAX_COMMIT_KEY = 200          # realm.commits: tamanho do recibo (`key`) de um commit
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
        problem = _validate_signal(signal, event)
        if problem:
            return problem
    return None


def _validate_inner(inner: Any) -> str | None:
    if not isinstance(inner, dict):
        return "inner deve ser um objeto"
    if inner.get("role") not in INNER_ROLES:
        return f"inner.role inválido: {inner.get('role')!r}"
    if not isinstance(inner.get("text"), str):
        return "inner.text deve ser texto"
    if inner.get("role") == "thought" and inner.get("fidelity") not in FIDELITIES:
        return "inner.fidelity obrigatório (raw|summary) em pensamento"
    return None


def _validate_signal(signal: Any, event: dict[str, Any]) -> str | None:
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
    if kind in REALM_SIGNALS and (event.get("alter_ego") is not None or event.get("agent") is not None):
        return f"{kind} é sinal de realm: alter_ego e agent devem ser nulos"
    if kind == "realm.metrics":
        loc = signal["loc"]
        if isinstance(loc, bool) or not isinstance(loc, int) or loc < 0:
            return "realm.metrics: loc deve ser um inteiro >= 0"
        files = signal.get("files")
        if files is not None and (isinstance(files, bool) or not isinstance(files, int) or files < 0):
            return "realm.metrics: files deve ser um inteiro >= 0"
        return _validate_split(signal, loc)
    if kind == "realm.changes":
        return _validate_changes(signal)
    if kind == "realm.commits":
        return _validate_commits(signal)
    if kind == "command.result":
        return _validate_command_result(signal)
    return None


def _validate_command_result(signal: dict[str, Any]) -> str | None:
    """`command.result`: passou ou falhou (`ok`), o código de saída só quando o provider informa e a atividade do comando."""
    if not isinstance(signal["ok"], bool):
        return "command.result: ok deve ser verdadeiro ou falso"
    code = signal.get("exit_code")
    if code is not None and (isinstance(code, bool) or not isinstance(code, int)):
        return "command.result: exit_code deve ser um inteiro"
    activity = signal.get("activity")
    if activity is not None and activity not in ACTIVITIES:
        return f"command.result: atividade inválida: {activity!r}"
    commit = signal.get("commit")
    if commit is not None:
        if not isinstance(commit, dict):
            return "command.result: commit deve ser um objeto"
        if commit.get("sha") is not None and not valid_sha(commit["sha"]):
            return "command.result: commit.sha deve ser um hash hexadecimal de 7 a 64 caracteres"
    return None


def valid_sha(value: Any) -> bool:
    """O hash de um commit: 7 a 64 caracteres hexadecimais (o git abrevia e, com SHA-256, vai a 64)."""
    return isinstance(value, str) and 7 <= len(value) <= 64 and all(ch in "0123456789abcdefABCDEF" for ch in value)


def _validate_commits(signal: dict[str, Any]) -> str | None:
    """`realm.commits`: o que o git disse de cada commit pedido (recibo, hash, se existe, linhas, se chegou à principal, se foi revertido)."""
    commits = signal["commits"]
    if not isinstance(commits, list) or len(commits) > MAX_COMMITS:
        return f"realm.commits: commits deve ser uma lista de até {MAX_COMMITS} commits"
    for commit in commits:
        if not isinstance(commit, dict):
            return "realm.commits: cada commit é um objeto"
        key = commit.get("key")
        if not isinstance(key, str) or not key or len(key) > MAX_COMMIT_KEY:
            return f"realm.commits: key deve ser um texto de 1 a {MAX_COMMIT_KEY} caracteres"
        if commit.get("sha") is not None and not valid_sha(commit["sha"]):
            return "realm.commits: sha deve ser um hash hexadecimal de 7 a 64 caracteres"
        for flag in ("exists", "on_main", "reverted"):
            if not isinstance(commit.get(flag), bool):
                return f"realm.commits: {flag} deve ser verdadeiro ou falso"
        lines = commit.get("lines")
        if lines is not None and (isinstance(lines, bool) or not isinstance(lines, int) or lines < 0):
            return "realm.commits: lines deve ser um inteiro >= 0"
    return None


def valid_change_path(path: Any) -> bool:
    """Um caminho de alteração: texto relativo à raiz do projeto, com `/`, sem segmentos vazios, `.` ou `..`, sem NUL, sem letra de
    unidade (`C:`) e de até `MAX_CHANGE_PATH` caracteres. Quem monta o evento descarta o que não passa aqui."""
    if not isinstance(path, str) or not path or len(path) > MAX_CHANGE_PATH or "\0" in path or "\\" in path:
        return False
    if len(path) > 1 and path[1] == ":":
        return False
    return all(part not in ("", ".", "..") for part in path.split("/"))


def _validate_changes(signal: dict[str, Any]) -> str | None:
    """`realm.changes`: a lista de alterações locais (caminho relativo, tipo do vocabulário, linhas) e quantas ficaram de fora."""
    changes = signal["changes"]
    if not isinstance(changes, list) or len(changes) > MAX_CHANGES:
        return f"realm.changes: changes deve ser uma lista de até {MAX_CHANGES} alterações"
    for change in changes:
        if not isinstance(change, dict):
            return "realm.changes: cada alteração é um objeto"
        path, kind, lines = change.get("path"), change.get("type"), change.get("lines")
        if not valid_change_path(path):
            return "realm.changes: path deve ser um caminho relativo com barras normais, sem segmentos vazios, `.` ou `..`"
        if kind not in CHANGE_TYPES:
            return f"realm.changes: tipo desconhecido {kind!r}"
        if isinstance(lines, bool) or not isinstance(lines, int) or lines < 0:
            return "realm.changes: lines deve ser um inteiro >= 0"
    more = signal.get("more")
    if more is not None and (isinstance(more, bool) or not isinstance(more, int) or more < 0):
        return "realm.changes: more deve ser um inteiro >= 0"
    return None


def _validate_split(signal: dict[str, Any], loc: int) -> str | None:
    """`realm.metrics`: as linhas da raiz (`root`) e de cada pasta de primeiro nível (`folders`), que juntas não passam de `loc`."""
    root = signal.get("root")
    if root is not None and (isinstance(root, bool) or not isinstance(root, int) or root < 0):
        return "realm.metrics: root deve ser um inteiro >= 0"
    folders = signal.get("folders")
    if folders is None:
        return None
    if not isinstance(folders, dict) or len(folders) > MAX_FOLDERS:
        return f"realm.metrics: folders deve ser um objeto de até {MAX_FOLDERS} pastas"
    for name, count in folders.items():
        if not isinstance(name, str) or not name or len(name) > MAX_FOLDER_NAME or "/" in name or "\\" in name:
            return f"realm.metrics: o nome de cada pasta é um texto de 1 a {MAX_FOLDER_NAME} caracteres, sem barra"
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            return "realm.metrics: as linhas de cada pasta são um inteiro >= 0"
    if (root or 0) + sum(folders.values()) > loc:
        return "realm.metrics: a raiz e as pastas somam mais que loc"
    return None
