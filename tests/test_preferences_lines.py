"""Filtro de tipos e exclusões da contagem de linhas nas preferências (R19, D-054, D-056): para todos os realms ou por realm."""
import json

import pytest

from orb.core.rules import GENERATED_FILE_PATTERNS, LineFilter
from orb.registry import PREFERENCES_FILE, Preferences, PreferencesFile


def test_the_default_filter_is_code_only_with_the_visible_list_of_generated_files():
    assert Preferences().line_filter(None) == LineFilter(include_markdown=False, exclude=GENERATED_FILE_PATTERNS)


def test_the_filter_can_be_changed_for_every_realm():
    prefs = Preferences().updated(lines={"include_markdown": True, "exclude": ["*.lock", "vendor/*"]})
    assert prefs.line_filter(r"c:\x") == LineFilter(include_markdown=True, exclude=("*.lock", "vendor/*"))


def test_a_realm_can_override_only_what_it_needs_and_inherit_the_rest():
    prefs = Preferences().updated(lines={"exclude": ["a"]}, realm_lines={r"c:\proj": {"include_markdown": True}})
    assert prefs.line_filter(r"c:\proj") == LineFilter(include_markdown=True, exclude=("a",))      # o resto vem do geral
    assert prefs.line_filter(r"c:\outro") == LineFilter(include_markdown=False, exclude=("a",))


def test_removing_the_override_returns_the_realm_to_the_general_filter():
    prefs = Preferences().updated(realm_lines={r"c:\proj": {"include_markdown": True}})
    assert prefs.updated(realm_lines={r"c:\proj": None}).line_filter(r"c:\proj").include_markdown is False


@pytest.mark.parametrize("bad", [{"include_markdown": "sim"}, {"exclude": "*.lock"}, {"exclude": [1]}, {"exclude": [""]},
                                 {"exclude": ["x"] * 201}, {"exclude": ["x" * 201]}, {"nao_existe": 1}, "texto", None])
def test_a_filter_the_orb_cannot_use_is_refused(bad):
    with pytest.raises(ValueError):
        Preferences().updated(lines=bad)
    with pytest.raises(ValueError):
        Preferences().updated(realm_lines={r"c:\proj": bad} if bad is not None else {r"c:\proj": 5})


def test_the_filters_are_saved_in_the_file_and_come_back_after_a_restart(tmp_path):
    file = PreferencesFile(tmp_path / "orb")
    file.save(Preferences().updated(lines={"include_markdown": True}, realm_lines={r"c:\proj": {"exclude": ["x"]}}))
    again = PreferencesFile(tmp_path / "orb").load()
    assert again.line_filter(None).include_markdown is True
    assert again.line_filter(r"c:\proj").exclude == ("x",)
    assert "realm_lines" in json.loads((tmp_path / "orb" / PREFERENCES_FILE).read_text(encoding="utf-8"))


def test_a_file_with_an_unusable_filter_gives_the_default_and_says_so(tmp_path):
    folder = tmp_path / "orb"
    folder.mkdir()
    (folder / PREFERENCES_FILE).write_text(json.dumps({"lines": {"exclude": "x"}, "recent_days": 5}), encoding="utf-8")
    file = PreferencesFile(folder)
    prefs = file.load()
    assert prefs.line_filter(None).exclude == GENERATED_FILE_PATTERNS and prefs.recent_days == 5 and "lines" in file.error
