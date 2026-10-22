"""A lista de tarefas do próprio CLI (R50, D-093): o sinal `tasks.updated`, a leitura que cada provider faz dela e o que o mundo mostra.
Nada é estimado: sem lista gravada pelo provider, nenhum progresso (R12)."""
from datetime import UTC, datetime, timedelta
from itertools import count

import pytest

from orb.adapters._shared import tasks_signal
from orb.core import World, rules
from orb.protocol import MAX_TASK_TITLE, MAX_TASKS, make_event, validate

_n = count(1)
T0 = datetime(2026, 10, 22, 10, 0, 0, tzinfo=UTC)


def ev(minutes, signal, *, ego="claude:s1", provider="claude", realm="the-orb", agent=None):
    n = next(_n)
    ts = (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")
    return make_event(id=f"{ego}:{n}", ts=ts, provider=provider, source=f"{provider}/x", realm=realm, alter_ego=ego, agent=agent,
                      seq=n, kind="x", body={}, signal=signal)


def tasks(done, total, items=None, **kw):
    signal = {"type": "tasks.updated", "done": done, "total": total}
    if items is not None:
        signal["items"] = items
    return ev(kw.pop("minutes", 0), signal, **kw)


def item(content, status="pending"):
    return {"content": content, "status": status}


# --- o sinal no protocolo ----------------------------------------------------------------------------------------------

def test_a_task_list_with_counts_and_items_is_valid():
    assert validate(tasks(1, 3, [item("a", "completed"), item("b", "in_progress"), item("c")])) is None
    assert validate(tasks(0, 0)) is None                                              # lista vazia: o provider apagou a lista


@pytest.mark.parametrize("signal", [
    {"type": "tasks.updated", "done": 1},                                             # sem total
    {"type": "tasks.updated", "total": 3},                                            # sem done
    {"type": "tasks.updated", "done": -1, "total": 3},
    {"type": "tasks.updated", "done": 4, "total": 3},                                 # mais feitas que o total
    {"type": "tasks.updated", "done": True, "total": 3},
    {"type": "tasks.updated", "done": 1, "total": "3"},
    {"type": "tasks.updated", "done": 1, "total": 3, "items": "nenhuma"},
    {"type": "tasks.updated", "done": 0, "total": 1, "items": [{"content": "a", "status": "feito"}]},     # status fora do vocabulário
    {"type": "tasks.updated", "done": 0, "total": 1, "items": [{"content": "", "status": "pending"}]},
    {"type": "tasks.updated", "done": 0, "total": 1, "items": [{"content": "a" * (MAX_TASK_TITLE + 1), "status": "pending"}]},
    {"type": "tasks.updated", "done": 0, "total": 1, "items": ["a"]},
    {"type": "tasks.updated", "done": 0, "total": 1, "items": [item("a"), item("b")]},                    # mais itens que o total
    {"type": "tasks.updated", "done": 0, "total": 2, "items": [item("a", "completed"), item("b", "completed")]},   # mais concluídas que `done`
])
def test_an_invalid_task_list_is_rejected_with_a_reason(signal):
    assert validate(ev(0, signal)) is not None


def test_the_list_of_items_has_a_ceiling():
    many = [item(f"t{i}") for i in range(MAX_TASKS + 1)]
    assert validate(tasks(0, len(many), many)) is not None


# --- a leitura comum dos providers -------------------------------------------------------------------------------------

def test_the_signal_counts_every_known_status_and_keeps_the_list_order():
    raw = [("Ler o MVP", "completed"), ("Escrever o teste", "in_progress"), ("Rodar a suíte", "pending")]
    signal = tasks_signal(raw)
    assert signal == {"type": "tasks.updated", "done": 1, "total": 3,
                      "items": [item("Ler o MVP", "completed"), item("Escrever o teste", "in_progress"), item("Rodar a suíte")]}
    assert validate(ev(0, signal)) is None


def test_only_the_protocol_statuses_are_counted_and_unknown_ones_are_not():
    signal = tasks_signal([("a", "in_progress"), ("b", "cancelled"), ("c", "deleted"), ("d", "algo novo"), ("e", None), ("f", "completed"),
                           ("g", ["lista"]), ("h", "inProgress"), "par torto", ("i", "pending", "sobra")])
    assert (signal["done"], signal["total"]) == (1, 2)                                 # só o que o provider disse com um status do protocolo
    assert [i["status"] for i in signal["items"]] == ["in_progress", "completed"]


def test_titles_are_trimmed_clipped_and_empty_ones_are_dropped():
    signal = tasks_signal([("  espaço  ", "pending"), ("   ", "pending"), (None, "pending"), ("x" * 500, "pending")])
    assert [i["content"] for i in signal["items"]] == ["espaço", "x" * (MAX_TASK_TITLE - 1) + "…"]
    assert signal["total"] == 2


def test_a_long_list_keeps_the_counts_of_all_and_the_items_up_to_the_ceiling():
    raw = [(f"t{i}", "completed" if i < 30 else "pending") for i in range(MAX_TASKS + 40)]
    signal = tasks_signal(raw)
    assert signal["total"] == MAX_TASKS + 40 and signal["done"] == 30
    assert len(signal["items"]) == MAX_TASKS
    assert validate(ev(0, signal)) is None


def test_no_list_or_something_that_is_not_a_list_says_nothing():
    assert tasks_signal(None) is None
    assert tasks_signal("lista") is None
    assert tasks_signal({"a": 1}) is None
    assert tasks_signal([]) == {"type": "tasks.updated", "done": 0, "total": 0, "items": []}      # lista vazia é uma lista (apagada)


# --- o mundo ----------------------------------------------------------------------------------------------------------

def world_with(*events):
    world = World()
    for event in events:
        assert world.apply(event) is True
    return world


def ego_of(world, ego="claude:s1", minutes=1):
    return next(e for e in world.snapshot(T0 + timedelta(minutes=minutes))["realms"][0]["alter_egos"] if e["id"] == ego)


def realm_of(world, minutes=1):
    return world.snapshot(T0 + timedelta(minutes=minutes))["realms"][0]


def test_a_session_without_a_list_has_no_progress():
    world = world_with(ev(0, {"type": "activity", "activity": "CODING"}))
    assert ego_of(world)["tasks"] is None
    assert realm_of(world)["tasks"] is None


def test_the_progress_is_the_last_list_the_provider_wrote():
    world = world_with(tasks(0, 2, [item("a"), item("b")]), tasks(1, 2, [item("a", "completed"), item("b", "in_progress")], minutes=1))
    got = ego_of(world)["tasks"]
    assert (got["done"], got["total"]) == (1, 2)
    assert [i["status"] for i in got["items"]] == ["completed", "in_progress"]


def test_an_empty_list_clears_the_progress():
    world = world_with(tasks(1, 2, [item("a", "completed"), item("b")]), tasks(0, 0, [], minutes=1))
    assert ego_of(world)["tasks"] is None


def test_a_list_from_a_subagent_does_not_change_the_leader_list():
    world = world_with(tasks(1, 2, [item("a", "completed"), item("b")]),
                       ev(1, {"type": "subagent.started", "kind": "Explore"}, agent="a1"),
                       tasks(0, 5, [item("x")] * 5, minutes=2, agent="a1"))
    assert (ego_of(world)["tasks"]["done"], ego_of(world)["tasks"]["total"]) == (1, 2)


def test_the_realm_sums_the_open_tasks_of_the_sessions_in_the_room():
    world = world_with(tasks(1, 3, [item("a", "completed"), item("b", "in_progress"), item("c")], ego="claude:s1"),
                       tasks(2, 2, [item("d", "completed"), item("e", "completed")], ego="codex:s2", provider="codex"),
                       ev(0, {"type": "activity", "activity": "CODING"}, ego="claude:s3"))
    got = realm_of(world)["tasks"]
    assert (got["open"], got["done"], got["total"], got["sessions"]) == (2, 3, 5, 2)         # a sessão sem lista não conta


def test_a_finished_session_or_one_outside_the_room_does_not_count_for_the_realm():
    world = world_with(tasks(0, 2, [item("a"), item("b")], ego="claude:s1"),
                       ev(1, {"type": "session.ended"}, ego="claude:s1"),
                       tasks(0, 1, [item("c")], ego="claude:s2", minutes=1))
    assert realm_of(world)["tasks"]["open"] == 1
    old = world_with(tasks(0, 2, [item("a"), item("b")]))
    assert realm_of(old, minutes=60 * 24 * 11)["tasks"] is None                                # além do prazo da sala (R28a): Histórico


def test_a_realm_with_every_task_done_still_shows_the_list_it_has():
    world = world_with(tasks(2, 2, [item("a", "completed"), item("b", "completed")]))
    got = realm_of(world)["tasks"]
    assert (got["open"], got["done"], got["total"]) == (0, 2, 2)


def test_the_task_board_lists_the_completed_tasks_newest_session_first():
    older = tasks(1, 2, [item("antiga feita", "completed"), item("aberta")], ego="claude:s1", minutes=0)
    newer = tasks(2, 2, [item("nova um", "completed"), item("nova dois", "completed")], ego="codex:s2", provider="codex", minutes=1)
    world = world_with(older, newer)
    board = realm_of(world)["tasks"]["board"]
    assert board["items"] == [{"ego": "codex:s2", "content": "nova um"}, {"ego": "codex:s2", "content": "nova dois"},
                              {"ego": "claude:s1", "content": "antiga feita"}]
    assert board["more"] == 0


def test_the_task_board_has_a_ceiling_and_counts_what_did_not_fit():
    done = [item(f"feita {i}", "completed") for i in range(rules.TASK_BOARD_MAX + 3)]
    world = world_with(tasks(len(done), len(done), done))
    board = realm_of(world)["tasks"]["board"]
    assert len(board["items"]) == rules.TASK_BOARD_MAX and board["more"] == 3


def test_the_ego_snapshot_carries_the_completed_titles_even_when_the_items_were_clipped_at_the_ceiling():
    world = world_with(tasks(1, MAX_TASKS + 5, [item("a", "completed")]))                 # o provider mandou menos itens que o total
    got = ego_of(world)["tasks"]
    assert got["total"] == MAX_TASKS + 5 and len(got["items"]) == 1


def test_the_world_snapshot_is_json_ready():
    import json
    world = world_with(tasks(1, 2, [item("a", "completed"), item("b")]))
    json.dumps(world.snapshot(T0 + timedelta(minutes=1)))


def test_the_task_board_more_counts_the_completed_tasks_the_signal_did_not_list():
    world = world_with(tasks(40, MAX_TASKS + 60, [item(f"feita {i}", "completed") for i in range(10)]))      # 40 feitas, só 10 listadas
    board = realm_of(world)["tasks"]["board"]
    assert len(board["items"]) == rules.TASK_BOARD_MAX and board["more"] == 40 - rules.TASK_BOARD_MAX
