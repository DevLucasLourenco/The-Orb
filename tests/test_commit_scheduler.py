"""Quando perguntar ao git pelos commits das sessões (ticket 23, R53): só os realms que têm commit a conferir, só publicando o que mudou."""
from datetime import UTC, datetime, timedelta

from orb.core import World
from orb.gateway.probes import CommitScheduler, Realm
from orb.protocol import make_event, validate

T0 = datetime(2026, 10, 7, 10, 0, 0, tzinfo=UTC)
SHA = "0123456789abcdef0123456789abcdef01234567"


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class Wall:
    def __init__(self):
        self.now = T0 + timedelta(minutes=30)

    def __call__(self):
        return self.now


class Reader:
    """Um leitor de git falso: devolve o que o teste puser em `answer` (uma função das perguntas) e guarda o que lhe perguntaram."""

    def __init__(self, answer=None):
        self.answer = answer or (lambda queries: [fact(q.key) for q in queries])
        self.asked = []

    def __call__(self, root, queries):
        self.asked.append((str(root), [q.key for q in queries]))
        return self.answer(queries)


def fact(key, *, on_main=False, reverted=False, lines=3):
    return {"key": key, "sha": SHA, "exists": True, "lines": lines, "on_main": on_main, "reverted": reverted}


def evidence(minutes=0, sha=SHA, key="e1"):
    return make_event(id=f"claude:s1:{key}", ts=(T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z"), provider="claude",
                      source="claude/transcript", realm="proj", alter_ego="claude:s1", agent=None, seq=1, kind="x", body={},
                      signal={"type": "command.result", "ok": True, "activity": "EXECUTING", "commit": {"sha": sha} if sha else {}})


def make(reader=None, hidden=frozenset(), **kw):
    world = World()
    world.apply(evidence())
    realms = {"proj": Realm("proj", "C:/x/proj")}
    clock, wall = Clock(), Wall()
    reader = reader or Reader()
    scheduler = CommitScheduler(lambda: realms, lambda: hidden, world.pending_commits, reader=reader, clock=clock, wall=wall, **kw)
    return scheduler, world, clock, wall, reader


def test_a_realm_with_a_commit_to_check_is_read_and_the_event_is_a_valid_realm_event():
    scheduler, _, _, _, reader = make()
    assert scheduler.run_once() == 1
    [event] = scheduler.drain()
    assert validate(event) is None and event["alter_ego"] is None and event["realm"] == "proj" and event["source"] == "probe/commits"
    assert event["signal"]["type"] == "realm.commits" and event["signal"]["commits"] == [fact(SHA)]
    assert [keys for _, keys in reader.asked] == [[SHA]]


def test_a_realm_with_nothing_to_check_is_never_read():
    world = World()
    realms = {"proj": Realm("proj", "C:/x/proj")}
    reader = Reader()
    scheduler = CommitScheduler(lambda: realms, lambda: frozenset(), world.pending_commits, reader=reader, clock=Clock(), wall=Wall())
    assert scheduler.run_once() == 0 and reader.asked == [] and scheduler.drain() == []


def test_the_same_answer_is_not_published_twice_but_a_different_one_is():
    scheduler, _, clock, _, reader = make()
    scheduler.run_once()
    scheduler.drain()
    clock.now += 61
    assert scheduler.run_once() == 0 and scheduler.drain() == []                       # o git respondeu a mesma coisa
    reader.answer = lambda queries: [fact(q.key, on_main=True) for q in queries]
    clock.now += 61
    assert scheduler.run_once() == 1 and scheduler.drain()[0]["signal"]["commits"][0]["on_main"] is True


def test_an_unchanged_answer_is_published_again_on_a_new_day_so_the_expiry_is_looked_at():
    scheduler, _, clock, wall, _ = make()
    scheduler.run_once()
    scheduler.drain()
    clock.now += 61
    wall.now += timedelta(days=1)
    assert scheduler.run_once() == 1


def test_a_realm_is_checked_at_most_once_a_minute():
    scheduler, _, clock, _, reader = make()
    scheduler.run_once()
    clock.now += 10
    assert scheduler.run_once() == 0 and len(reader.asked) == 1


def test_a_folder_that_is_not_a_repository_gives_a_note_and_no_event():
    scheduler, _, _, _, _ = make(Reader(lambda queries: None))
    assert scheduler.run_once() == 0 and scheduler.drain() == []
    assert "git" in scheduler.notes["proj"]


def test_a_hidden_realm_is_not_read():
    scheduler, _, _, _, reader = make(hidden=frozenset({"proj"}))
    assert scheduler.run_once() == 0 and reader.asked == []


def test_a_failure_in_the_reader_is_kept_and_does_not_break_the_scheduler():
    def boom(queries):
        raise RuntimeError("git quebrou")
    scheduler, _, _, _, _ = make(Reader(boom))
    assert scheduler.run_once() == 0
    assert "git quebrou" in scheduler.errors["proj"]


def test_the_answer_confirms_the_commit_in_the_world_end_to_end():
    reader = Reader(lambda queries: [fact(q.key, on_main=True, lines=45) for q in queries])
    scheduler, world, _, _, _ = make(reader)
    scheduler.run_once()
    [event] = scheduler.drain()
    assert world.apply(event) is True
    ego = world.alter_ego("claude:s1")
    (entry,) = [e for e in ego.xp.entries if e.rule == "X-COMMIT"]
    assert (entry.state, entry.xp) == ("confirmed", 12) and ego.xp.total == 12
    assert world.pending_commits("proj", T0 + timedelta(hours=1)) == [{"key": SHA, "sha": SHA, "at": evidence().get("ts")}]    # ainda na janela de reversão
