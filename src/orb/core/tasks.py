"""A lista de tarefas do próprio CLI no mundo (R50, D-093): o resumo do realm e o que o Task Board mostra.

Só a lista que o provider gravou entra: sem ela, nada aparece (R12). O que vale é a última lista de cada sessão; o resumo do realm soma as das sessões
da sala que ainda não terminaram. Funções puras sobre os snapshots dos Alter Egos, sem relógio.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from . import rules


def from_signal(signal: dict[str, Any]) -> dict[str, Any] | None:
    """A lista que o sinal `tasks.updated` trouxe; `None` quando o provider a apagou (zero tarefas)."""
    total = signal["total"]
    if total == 0:
        return None
    return {"done": signal["done"], "total": total, "items": [dict(entry) for entry in signal.get("items") or []]}


def realm_summary(egos: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    """O que os Alter Egos da sala (e não encerrados) têm em lista: tarefas abertas, feitas, total e quantas sessões têm lista, mais o Task Board
    (as concluídas, da sessão mais recente para a mais antiga). Sem nenhuma lista, `None`."""
    listed = [ego for ego in egos if ego.get("tasks") and not ego.get("ended")]
    if not listed:
        return None
    done = sum(ego["tasks"]["done"] for ego in listed)
    total = sum(ego["tasks"]["total"] for ego in listed)
    finished = [{"ego": ego["id"], "content": entry["content"]}
                for ego in sorted(listed, key=lambda e: (e.get("last_ts") or "", e["id"]), reverse=True)
                for entry in ego["tasks"]["items"] if entry["status"] == "completed"]
    return {"open": total - done, "done": done, "total": total, "sessions": len(listed),
            "board": {"items": finished[:rules.TASK_BOARD_MAX], "more": max(0, done - rules.TASK_BOARD_MAX)}}      # `done` conta também as que o sinal não listou
