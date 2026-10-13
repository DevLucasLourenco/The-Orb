"""Arquivo de preferências do Orb (R29, D-030, D-032): JSON na pasta do Orb, nunca nos providers."""
import json

import pytest

from orb.registry import PREFERENCES_FILE, SETTINGS, Preferences, PreferencesFile


def test_without_a_file_the_defaults_apply_and_nothing_is_written(tmp_path):
    prefs = PreferencesFile(tmp_path / "orb").load()
    assert (prefs.hidden_realms, prefs.recent_days) == ((), 10)
    assert prefs.recent_seconds == 10 * 24 * 3600
    assert not (tmp_path / "orb").exists()                                  # só quem grava cria a pasta


def test_saving_and_loading_round_trip_in_the_orb_folder(tmp_path):
    file = PreferencesFile(tmp_path / "orb")
    file.save(Preferences(hidden_realms=("c:\a", "c:\b"), recent_days=3))
    assert (tmp_path / "orb" / PREFERENCES_FILE).is_file()
    loaded = PreferencesFile(tmp_path / "orb").load()
    assert (loaded.hidden_realms, loaded.recent_days) == (("c:\a", "c:\b"), 3)
    assert json.loads((tmp_path / "orb" / PREFERENCES_FILE).read_text(encoding="utf-8"))["version"] == 1


def test_options_this_version_does_not_know_are_kept_for_the_tickets_that_add_them(tmp_path):
    folder = tmp_path / "orb"
    folder.mkdir()
    (folder / PREFERENCES_FILE).write_text(json.dumps({"version": 1, "recent_days": 5, "line_filter": {"md": False}}), encoding="utf-8")
    file = PreferencesFile(folder)
    file.save(file.load().updated(recent_days=7))
    assert json.loads((folder / PREFERENCES_FILE).read_text(encoding="utf-8"))["line_filter"] == {"md": False}


def test_a_broken_file_gives_the_defaults_says_why_and_is_kept_aside_on_the_next_save(tmp_path):
    folder = tmp_path / "orb"
    folder.mkdir()
    (folder / PREFERENCES_FILE).write_text("{ isto nao e json", encoding="utf-8")
    file = PreferencesFile(folder)
    assert file.load().recent_days == 10 and file.error
    file.save(Preferences(recent_days=4))
    assert (folder / (PREFERENCES_FILE + ".bad")).read_text(encoding="utf-8") == "{ isto nao e json"      # nada se perde
    assert file.error is None and PreferencesFile(folder).load().recent_days == 4


def test_wrong_types_in_the_file_fall_back_to_the_defaults_one_by_one(tmp_path):
    folder = tmp_path / "orb"
    folder.mkdir()
    (folder / PREFERENCES_FILE).write_text(json.dumps({"recent_days": "dez", "hidden_realms": [1, r"c:\ok", None]}), encoding="utf-8")
    prefs = PreferencesFile(folder).load()
    assert prefs.recent_days == 10 and prefs.hidden_realms == (r"c:\ok",)


@pytest.mark.parametrize("value", [0, 0.5, 366, -3, float("nan"), True, "10", None])
def test_the_recent_window_only_accepts_numbers_inside_its_range(value):
    with pytest.raises(ValueError):
        Preferences().updated(recent_days=value)


def test_a_change_with_an_unknown_option_is_refused():
    with pytest.raises(ValueError):
        Preferences().updated(nao_existe=1)


def test_the_settings_screen_gets_its_numeric_options_from_a_table():
    by_key = {s.key: s for s in SETTINGS}
    assert by_key["recent_days"].default == 10 and by_key["recent_days"].unit == "dias"      # os tickets 09 e 11 acrescentam linhas aqui


def test_saving_never_touches_anything_outside_the_orb_folder(tmp_path):
    PreferencesFile(tmp_path / "orb").save(Preferences())
    assert sorted(p.name for p in tmp_path.iterdir()) == ["orb"]
    assert sorted(p.name for p in (tmp_path / "orb").iterdir()) == [PREFERENCES_FILE]        # sem arquivo temporário sobrando
