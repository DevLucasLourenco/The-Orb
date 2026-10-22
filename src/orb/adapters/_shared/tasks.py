"""A lista de tarefas do próprio CLI -> o sinal `tasks.updated` (R50, D-093). Só traduz o que o provider gravou: nada é estimado.

Cada provider escreve o estado de uma tarefa a seu modo (`in_progress`, `inProgress`...); aqui eles viram os três do protocolo. Estado
fora deles (cancelada, apagada, desconhecido) não entra na conta.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ...protocol import MAX_TASK_TITLE, MAX_TASKS, TASK_STATUSES, clip_text

STATUS_ALIASES: dict[str, str] = {
    "pending": "pending", "in_progress": "in_progress", "inProgress": "in_progress", "completed": "completed",
}
assert set(STATUS_ALIASES.values()) == set(TASK_STATUSES)


def tasks_signal(raw: Iterable[tuple[Any, Any]] | None) -> dict[str, Any] | None:
    """`raw`: pares (título, estado nativo) na ordem da lista do provider. Sem lista (não é uma sequência), nenhum sinal; lista vazia é uma lista
    apagada. `total` e `done` contam todas as tarefas conhecidas e `items` traz as primeiras `MAX_TASKS`."""
    if raw is None or isinstance(raw, (str, bytes, dict)):
        return None
    try:
        pairs = list(raw)
    except TypeError:
        return None
    items: list[dict[str, str]] = []
    total = done = 0
    for pair in pairs:
        title, native = pair
        status = STATUS_ALIASES.get(native) if isinstance(native, str) else None
        text = title.strip() if isinstance(title, str) else ""
        if status is None or not text:
            continue
        total += 1
        done += status == "completed"
        if len(items) < MAX_TASKS:
            items.append({"content": clip_text(text, MAX_TASK_TITLE), "status": status})
    return {"type": "tasks.updated", "done": done, "total": total, "items": items}


def native_pairs(entries: Any, *, title: str, status: str = "status") -> list[tuple[Any, Any]] | None:
    """A lista nativa de um provider (`[{"content": ..., "status": ...}]`) como pares (título, estado). Algo que não é uma lista de objetos não é
    uma lista de tarefas."""
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        return None
    return [(entry.get(title), entry.get(status)) for entry in entries]
