"""Nomes históricos dos Alter Egos (R37, D-063 a D-067): a sacola e o livro de nomes, sem disco."""
import random
import re
from pathlib import Path

from orb.core import NAMES, NameBag, NameBook

VISUAL = Path(__file__).resolve().parents[1] / "docs" / "VISUAL.md"


def test_the_sixty_names_are_the_ones_approved_in_visual_md():
    section = VISUAL.read_text(encoding="utf-8").split("## 9. Os nomes dos Alter Egos", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\| (\d+) \| ([^|]+?) \|", section, flags=re.MULTILINE)
    assert [int(n) for n, _ in rows] == list(range(1, 61))
    assert tuple(name for _, name in rows) == NAMES
    assert len(set(NAMES)) == 60


def test_a_bag_gives_every_name_once_before_any_name_comes_back():
    bag = NameBag(rng=random.Random(7))
    first = [bag.draw() for _ in range(60)]
    assert sorted(first) == sorted(NAMES) and bag.remaining == ()
    second = [bag.draw() for _ in range(60)]
    assert sorted(second) == sorted(NAMES)                       # esvaziou: embaralha de novo


def test_the_same_seed_gives_the_same_order_and_another_seed_another_order():
    order = lambda seed: NameBag(rng=random.Random(seed)).remaining
    assert order(1) == order(1)
    assert order(1) != order(2)


def test_a_name_in_use_is_skipped_and_stays_in_the_bag_for_the_next_draw():
    bag = NameBag(["Einstein", "Newton", "Tesla"])
    assert bag.draw(avoid={"Einstein"}) == "Newton"              # tira-se o seguinte
    assert bag.remaining == ("Einstein", "Tesla")                # o pulado não foi consumido
    assert bag.draw() == "Einstein"


def test_when_every_name_left_is_in_use_a_new_bag_is_shuffled():
    bag = NameBag(["Einstein"], rng=random.Random(3))
    name = bag.draw(avoid={"Einstein"})
    assert name != "Einstein" and name in NAMES
    assert len(bag.remaining) == 59


def test_when_all_sixty_are_in_use_a_repeat_is_unavoidable_and_still_works():
    assert NameBag(rng=random.Random(3)).draw(avoid=set(NAMES)) in NAMES


def test_the_book_keeps_the_name_of_a_session_forever():
    book = NameBook(rng=random.Random(5))
    einstein_or_other = book.name_for("claude:s1")
    assert [book.name_for("claude:s1", avoid=frozenset({einstein_or_other})) for _ in range(3)] == [einstein_or_other] * 3
    assert book.name_for("codex:s1") != einstein_or_other        # sessão nova, nome novo (sacola global)


def test_sessions_of_different_providers_never_share_a_name_until_the_bag_empties():
    book = NameBook(rng=random.Random(11))
    names = [book.name_for(f"{provider}:{n}") for n in range(15) for provider in ("claude", "codex", "hermes", "opencode")]
    assert len(set(names)) == 60
