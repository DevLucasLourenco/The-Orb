"""As leituras do mundo real: pastas de CLIs falsas -> realms (R3, R3a, R3b, R3d). Sem rede, sem CLI, sem dados
reais: a 'máquina' é montada em pastas temporárias, com a forma verificada dos arquivos de cada provider."""
import os

import pytest

from orb.gateway import Hub, Observatory
from orb.gateway.projects import Exclusions

from .fakes import hermes_db, opencode_db, rollout, transcript


class Machine:
    """Uma máquina falsa: a pasta de dados dos CLIs (`home`) e a do usuário, com os projetos dele."""

    def __init__(self, root, jsonl):
        self.home = root                                     # onde ficam .claude, .codex, hermes/ e opencode/
        self.user = root / "user"
        self.jsonl = jsonl
        for folder in ("AppData/Local/Temp", "Downloads", "work"):
            (self.user / folder).mkdir(parents=True)
        self.exclusions = Exclusions(exact=[self.user], inside=[self.user / "AppData", self.user / "Downloads"])
        self._thread = 0

    def project(self, *parts, git=True):
        folder = self.user.joinpath("work", *parts)
        folder.mkdir(parents=True)
        if git:
            (folder / ".git").mkdir()
        return folder

    def observatory(self, **kw):
        return Observatory(home=self.home, exclusions=self.exclusions, index_every=0, **kw)

    def claude(self, cwd, session="s1", old=True):
        path = transcript(self.home, str(cwd), session)
        if old:
            os.utime(path, (1_700_000_000, 1_700_000_000))        # sessão antiga: o realm existe do mesmo jeito
        return path

    def codex(self, cwd, *, day="07", old=True):
        self._thread += 1
        path = rollout(self.home, self.jsonl, f"t-{self._thread}", str(cwd), day=day)
        if old:
            os.utime(path, (1_700_000_000, 1_700_000_000))
        return path


@pytest.fixture
def machine(short_tmp, jsonl, monkeypatch):
    monkeypatch.setattr("orb.adapters.codex.rollout.DISCOVER_EVERY", 0.0)      # sem espera entre varreduras
    monkeypatch.setattr("orb.adapters.claude.transcript.DISCOVER_EVERY", 0.0)
    return Machine(short_tmp, jsonl)


def detected_realms(observatory):
    observatory.poll()
    return {rid: realm for rid, realm in observatory.realms.items()}


def test_every_project_any_cli_ever_recorded_becomes_a_realm(machine):
    alpha, beta, gamma, delta = (machine.project(n) for n in ("alpha", "beta", "gamma", "delta"))
    machine.claude(alpha)
    machine.codex(beta)
    conn = hermes_db(machine.home / "hermes")
    conn.execute("INSERT INTO sessions VALUES ('H1', 'cli', 'm', NULL, ?, 't', 1700000000.0, 1700000000.0, NULL, NULL)", (str(gamma),))
    conn.commit()
    conn = opencode_db(machine.home / "opencode")
    conn.execute("INSERT INTO session_v2 VALUES ('ses_1', NULL, ?, 't', NULL, 1700000000000, 1700000000000)", (str(delta),))
    conn.commit()
    found = detected_realms(machine.observatory())
    assert set(found) == {"alpha", "beta", "gamma", "delta"}                  # nada de --root nem --lookback
    assert {r.cwd for r in found.values()} == {str(p) for p in (alpha, beta, gamma, delta)}


def test_the_user_folder_system_folders_and_missing_folders_never_become_realms(machine):
    real = machine.project("real")
    machine.claude(machine.user)                                              # a pasta do usuário em si
    machine.codex(machine.user / "Downloads")
    machine.codex(machine.user / "AppData" / "Local" / "Temp")
    machine.codex(machine.user / "work" / "apagado")                          # não existe mais no disco
    machine.claude(real)
    assert set(detected_realms(machine.observatory())) == {"real"}


def test_subfolders_and_worktrees_count_for_the_main_project(machine):
    main = machine.project("trisafe-enhanced")
    (main / "src" / "core").mkdir(parents=True)
    git_dir = main / ".git" / "worktrees" / "wt1"
    git_dir.mkdir(parents=True)
    (git_dir / "commondir").write_text("../..\n", encoding="utf-8")
    worktree = machine.user / "work" / "wt1"                                  # worktree fora da pasta do projeto
    worktree.mkdir()
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")
    machine.codex(main / "src" / "core")
    machine.codex(worktree)
    machine.claude(worktree)
    found = detected_realms(machine.observatory())
    assert set(found) == {"trisafe-enhanced"} and found["trisafe-enhanced"].cwd == str(main)


def test_a_folder_without_a_repository_is_a_realm_but_its_subfolders_do_not_split_it(machine):
    scripts = machine.project("scripts", git=False)
    (scripts / "sub").mkdir()
    machine.codex(scripts)
    machine.codex(scripts / "sub")
    assert set(detected_realms(machine.observatory())) == {"scripts"}


def test_similar_names_never_mix_and_equal_names_get_a_suffix(machine):
    trisafe, enhanced = machine.project("trisafe"), machine.project("trisafe-enhanced")
    left, right = machine.project("area-a", "app"), machine.project("area-b", "app")
    for folder in (trisafe, enhanced, left, right):
        machine.codex(folder)
    found = detected_realms(machine.observatory())
    assert set(found) == {"trisafe", "trisafe-enhanced", "app", "app-2"}
    assert found["trisafe"].cwd == str(trisafe) and found["trisafe-enhanced"].cwd == str(enhanced)
    assert {found["app"].cwd, found["app-2"].cwd} == {str(left), str(right)}
    assert found["app"].cwd == str(left)                                      # ordem estável: o caminho que vem primeiro


def test_realm_ids_do_not_change_when_a_project_with_the_same_name_appears_later(machine):
    right = machine.project("area-b", "app")
    machine.codex(right)
    observatory = machine.observatory()
    assert set(detected_realms(observatory)) == {"app"}
    left = machine.project("area-a", "app")                                   # vem antes na ordem dos caminhos
    machine.codex(left, day="08")
    found = detected_realms(observatory)
    assert found["app"].cwd == str(right) and found["app-2"].cwd == str(left)  # quem já estava na cidade não muda de id


def test_the_root_the_provider_informs_wins(machine):
    project = machine.project("alpha", git=False)                             # sem .git: só o Hermes sabe a raiz
    pkg = project / "pkg"
    pkg.mkdir()
    conn = hermes_db(machine.home / "hermes")
    conn.execute("INSERT INTO sessions VALUES ('H1', 'cli', 'm', NULL, ?, 't', 1700000000.0, 1700000000.0, ?, NULL)",
                 (str(pkg), str(project)))
    conn.commit()
    found = detected_realms(machine.observatory())
    assert {r.cwd for r in found.values()} == {str(project)}


def test_a_new_project_appears_by_itself_and_live_sessions_land_in_the_right_realm(machine):
    trisafe, enhanced = machine.project("trisafe"), machine.project("trisafe-enhanced")
    observatory = machine.observatory(lookback_minutes=60)
    assert detected_realms(observatory) == {}
    machine.codex(trisafe, old=False)
    machine.codex(enhanced, old=False)
    hub = Hub(observatory)
    hub.poll_once()
    world = {r["id"]: r for r in hub.snapshot()["realms"]}
    assert set(world) == {"trisafe", "trisafe-enhanced"}
    assert all(len(r["alter_egos"]) == 1 for r in world.values())            # cada sessão no prédio certo
    novo = machine.project("novo")
    machine.codex(novo, old=False)
    hub.poll_once()
    assert "novo" in {r["id"] for r in hub.snapshot()["realms"]}              # projeto novo cria o prédio na hora


def test_the_city_shows_realms_with_no_live_session(machine):
    machine.codex(machine.project("antigo"))
    hub = Hub(machine.observatory())
    hub.poll_once()
    snapshot = {r["id"]: r for r in hub.snapshot()["realms"]}
    assert snapshot["antigo"]["alter_egos"] == [] and snapshot["antigo"]["cwd"].endswith("antigo")


def test_debug_options_still_register_realms_without_sessions(machine):
    folder = machine.project("manual", git=False)
    observatory = machine.observatory(folders=[str(folder)])
    assert set(observatory.realms) == {"manual"}


def test_a_failing_index_does_not_stop_the_others(machine, monkeypatch):
    machine.codex(machine.project("alpha"))
    observatory = machine.observatory()

    def boom():
        raise RuntimeError("quebrou")

    monkeypatch.setattr(observatory.indexes["hermes"], "scan", boom)
    assert set(detected_realms(observatory)) == {"alpha"}
    assert "RuntimeError" in observatory.errors["index:hermes"]


def test_malformed_folders_from_a_file_never_break_a_reader(machine):
    observatory = machine.observatory()
    for value in (["x"], {"a": 1}, None, 42, "", "relativa/pasta"):
        assert observatory.realm_of(value) is None                            # valor cru de arquivo ou banco: nunca levanta


def test_a_live_session_follows_the_root_the_provider_informed_at_the_index(machine):
    project = machine.project("alpha", git=False)
    nested = project / "pkg"
    (nested / ".git").mkdir(parents=True)                                     # repositório aninhado: subir daria `pkg`
    conn = hermes_db(machine.home / "hermes")
    conn.execute("INSERT INTO sessions VALUES ('H1', 'cli', 'm', NULL, ?, 't', 1700000000.0, 1700000000.0, ?, NULL)",
                 (str(nested), str(project)))
    conn.commit()
    observatory = machine.observatory()
    assert set(detected_realms(observatory)) == {"alpha"}
    assert observatory.realm_of(str(nested)) == "alpha"                       # o leitor ao vivo usa a mesma raiz: sem prédio fantasma


def test_a_folder_that_was_not_a_project_yet_is_reevaluated_after_the_wait(machine):
    now = [0.0]
    observatory = machine.observatory(clock=lambda: now[0])
    later = machine.user / "work" / "criada-depois"
    assert observatory.realm_of(str(later)) is None                           # ainda não existe
    later.mkdir()
    now[0] = 30.0
    assert observatory.realm_of(str(later)) is None                           # a decisão negativa vale por um tempo
    now[0] = 61.0
    assert observatory.realm_of(str(later)) == "criada-depois"


@pytest.mark.skipif(os.name != "nt", reason="caixa de caminho só é indiferente no Windows")
def test_the_same_project_spelled_with_another_case_is_one_realm(machine):
    project = machine.project("MeuProjeto")
    machine.codex(str(project).upper())
    machine.codex(str(project).lower(), day="08")
    found = detected_realms(machine.observatory())
    assert list(found) == ["meuprojeto"]
    assert found["meuprojeto"].cwd == min(str(project).upper(), str(project).lower())     # a grafia vem de uma ordem fixa


def test_a_failing_index_shows_up_with_its_provider_in_the_realm_errors(machine, monkeypatch):
    machine.codex(machine.project("alpha"))
    observatory = machine.observatory()
    monkeypatch.setattr(observatory.indexes["hermes"], "scan", lambda: (_ for _ in ()).throw(RuntimeError("quebrou")))
    observatory.poll()
    assert "RuntimeError" in observatory.describe("alpha")["errors"]["hermes"]


def test_the_server_starts_with_no_arguments_and_serves_the_detected_realms(machine):
    pytest.importorskip("httpx", reason="TestClient do FastAPI precisa de httpx")
    import time

    from fastapi.testclient import TestClient

    from orb.gateway import GatewayConfig, create_app
    machine.codex(machine.project("alpha"))
    machine.claude(machine.project("beta"))
    config = GatewayConfig(token="tok", home=machine.home, poll_seconds=0.05)           # nenhum caminho de projeto
    with TestClient(create_app(config, check_installed=False, observatory=machine.observatory())) as client:
        deadline = time.time() + 5
        ids: set = set()
        while time.time() < deadline and ids != {"alpha", "beta"}:
            ids = {r["id"] for r in client.get("/config").json()["realms"]}
            time.sleep(0.05)
        assert ids == {"alpha", "beta"}



# --- a sala e o Histórico do realm (R28, R28a, R48 camada 2, D-027, D-059, D-087) ------------------------

DAY = 86400


def hermes_session(machine, sid, cwd, *, days_ago, title="t", parent=None, source="cli"):
    import time
    conn = hermes_db(machine.home / "hermes")
    stamp = time.time() - days_ago * DAY
    conn.execute("INSERT INTO sessions VALUES (?, ?, 'm', ?, ?, ?, ?, ?, NULL, NULL)", (sid, source, parent, str(cwd), title, stamp, stamp))
    conn.commit()


def egos_of(hub, realm):
    return {e["id"]: e for r in hub.snapshot()["realms"] if r["id"] == realm for e in r["alter_egos"]}


def test_a_session_of_the_last_ten_days_is_in_the_room_even_if_its_provider_says_nothing_now(machine):
    alpha = machine.project("alpha")
    hermes_session(machine, "H1", alpha, days_ago=3, title="Sessão de três dias")
    hub = Hub(machine.observatory())
    hub.poll_once()
    egos = egos_of(hub, "alpha")
    assert set(egos) == {"hermes:H1"}                                          # nenhuma mensagem nova: veio do índice
    assert egos["hermes:H1"]["in_room"] and egos["hermes:H1"]["asleep"] and egos["hermes:H1"]["title"] == "Sessão de três dias"
    hub.poll_once()
    assert len(egos_of(hub, "alpha")) == 1 and hub.world.alter_ego("hermes:H1").events == 1     # anunciada uma vez só


def test_older_sessions_stay_out_of_the_room_and_are_listed_in_the_realm_history_newest_first(machine):
    alpha = machine.project("alpha")
    hermes_session(machine, "H-recent", alpha, days_ago=2)
    hermes_session(machine, "H-old", alpha, days_ago=30, title="Velha")
    hermes_session(machine, "H-older", alpha, days_ago=60, title="Mais velha")
    hermes_session(machine, "H-sub", alpha, days_ago=40, source="subagent", parent="H-old")        # subagente não é sessão
    hub = Hub(machine.observatory())
    hub.poll_once()
    assert set(egos_of(hub, "alpha")) == {"hermes:H-recent"}                    # conteúdo e presença só da sala
    history = hub.history("alpha")
    assert [(h["session"], h["title"], h["provider"]) for h in history] == [("H-old", "Velha", "hermes"), ("H-older", "Mais velha", "hermes")]
    assert history[0]["started_at"] and history[0]["updated_at"] and history[0]["name"] is None     # nome só se já foi sorteado
    assert hub.history("nao-existe") == []


def test_the_history_shows_the_historical_name_a_session_already_had(machine):
    from orb.core import NameBook
    alpha = machine.project("alpha")
    hermes_session(machine, "H-old", alpha, days_ago=30)
    names = NameBook(assigned={"hermes:H-old": "Turing"})
    hub = Hub(machine.observatory(), names=names)
    hub.poll_once()
    assert hub.history("alpha")[0]["name"] == "Turing"
    assert names.assigned == {"hermes:H-old": "Turing"}                         # olhar o histórico nunca sorteia


def test_a_realm_with_only_old_sessions_is_night_and_a_new_session_lights_it(machine):
    alpha, beta = machine.project("alpha"), machine.project("beta")
    hermes_session(machine, "H-old", alpha, days_ago=30)
    hermes_session(machine, "H-new", beta, days_ago=1)
    machine.claude(alpha)                                                       # transcript de 2023: também fora da sala
    hub = Hub(machine.observatory())
    hub.poll_once()
    night = {r["id"]: r["night"] for r in hub.snapshot()["realms"]}
    assert night == {"alpha": True, "beta": False}                              # D-059: realm parado = sala apagada
    hermes_session(machine, "H-wakes", alpha, days_ago=0)
    hub.observatory.refresh_index(force=True)
    hub.poll_once()
    assert {r["id"]: r["night"] for r in hub.snapshot()["realms"]}["alpha"] is False


def test_every_detected_realm_has_a_lot_in_the_city_even_before_the_first_read_and_a_hidden_one_leaves_it_vacant(machine):
    alpha, beta = machine.project("alpha"), machine.project("beta")
    hermes_session(machine, "H-a", alpha, days_ago=1)
    hermes_session(machine, "H-b", beta, days_ago=1)
    hub = Hub(machine.observatory())
    hub.observatory.refresh_index(force=True)                                   # detectado, mas o Hub ainda não leu nada
    snap = hub.snapshot()                                                       # o realm já tem lugar
    assert {r["id"]: r["place"]["district"] for r in snap["realms"]} == {"alpha": "A", "beta": "B"}
    assert {d["letter"] for d in snap["city"]["districts"]} == {"A", "B"}
    places = {r["id"]: r["place"] for r in snap["realms"]}
    hub.world.set_hidden({"alpha"})
    after = hub.snapshot()
    assert [r["id"] for r in after["realms"]] == ["beta"] and after["realms"][0]["place"] == places["beta"]
    assert after["city"] == snap["city"]                                        # o lote do escondido segue vago no traçado


def test_the_content_is_read_only_for_the_room_window_and_it_comes_from_one_value(machine):
    from orb.core import rules
    observatory = machine.observatory()
    assert observatory.recent_seconds == rules.RECENT_SESSION_SECONDS == 10 * DAY
    assert abs((observatory.fresh_after - observatory.since) - (10 * DAY - 30 * 60)) < 5           # replay só dos criados há pouco
    assert all(r.since == observatory.since for r in observatory.readers.values())
    hermes_session(machine, "H-hours", machine.project("beta"), days_ago=0.2)             # ~5 h atrás
    narrow = Hub(machine.observatory(recent_seconds=3600))
    narrow.poll_once()
    assert [h["session"] for h in narrow.history("beta")] == ["H-hours"]       # fora da sala de 1 h: a sala e o Histórico seguem o mesmo valor
    assert not egos_of(narrow, "beta")


def test_the_reading_rhythm_is_250_ms_with_an_active_session_and_2_s_without_one(machine):
    from datetime import UTC, datetime, timedelta

    from orb.protocol import make_event
    start = datetime(2026, 10, 7, 10, 0, 0, tzinfo=UTC)
    now = [start]
    hub = Hub(machine.observatory(), clock=lambda: now[0])
    assert hub.poll_interval(0.25, 2.0) == 2.0                                   # ninguém trabalhando: só a varredura de 2 s
    hub.world.apply(make_event(id="claude:s1:1", ts=start.isoformat(), provider="claude", source="x", realm="r", alter_ego="claude:s1",
                               agent=None, seq=1, kind="x", body={}, signal={"type": "idle"}))
    assert hub.poll_interval(0.25, 2.0) == 0.25                                  # D-087
    now[0] = start + timedelta(minutes=20)
    assert hub.poll_interval(0.25, 2.0) == 2.0                                   # parou: o personagem dormiu


def test_the_world_stream_answers_a_history_request_with_the_sessions_that_left_the_room(machine):
    pytest.importorskip("httpx", reason="TestClient do FastAPI precisa de httpx")
    import json

    from fastapi.testclient import TestClient

    from orb.gateway import GatewayConfig, create_app
    alpha = machine.project("alpha")
    hermes_session(machine, "H-old", alpha, days_ago=30, title="Velha")
    config = GatewayConfig(token="tok", home=machine.home, poll_seconds=0.05, idle_poll_seconds=0.05)
    app = create_app(config, check_installed=False, observatory=machine.observatory())
    with TestClient(app) as client, client.websocket_connect("/world?token=tok", headers={"origin": "http://127.0.0.1"}) as ws:
        ws.receive_json()
        for _ in range(100):                                                    # espera o realm ser detectado
            ws.send_text(json.dumps({"type": "history", "realm": "alpha"}))
            msg = next(m for m in iter(ws.receive_json, None) if m["channel"] == "history")
            if msg["sessions"]:
                break
        assert [(s["session"], s["title"]) for s in msg["sessions"]] == [("H-old", "Velha")]
        ws.send_text(json.dumps({"type": "history", "realm": 7}))                 # pedido malformado: ignorado, sem derrubar
        ws.send_text(json.dumps({"type": "history", "realm": "alpha"}))
        assert next(m for m in iter(ws.receive_json, None) if m["channel"] == "history")["realm"] == "alpha"


def test_the_reading_window_follows_the_room_instead_of_the_hour_the_server_started(machine):
    import time
    observatory = Observatory(home=machine.home, exclusions=machine.exclusions, index_every=0)      # sem `now` fixo: a janela anda
    start = observatory.since
    observatory._wall = lambda: time.time() + 3 * DAY                                               # três dias de servidor aberto
    observatory.refresh_index(force=True)
    assert observatory.since - start > 2.9 * DAY
    assert all(reader.since == observatory.since for reader in observatory.readers.values())


def test_the_history_message_tells_the_total_so_nothing_is_hidden_without_notice(machine, monkeypatch):
    alpha = machine.project("alpha")
    for n in range(5):
        hermes_session(machine, f"H{n}", alpha, days_ago=20 + n)
    monkeypatch.setattr("orb.gateway.app.HISTORY_LIMIT", 3)
    hub = Hub(machine.observatory())
    hub.poll_once()
    assert len(hub.history("alpha")) == 3 and hub.history_total("alpha") == 5
    assert hub.world.snapshot(hub.clock())["mankind"]["alter_egos"] == 0                 # Mankind conta só a sala


# --- preferências e tela de configurações (R3c, R28a, R29, D-022, D-030, D-032) -----------------------------

def hub_with_prefs(machine, folder):
    from orb.registry import PreferencesFile
    return Hub(machine.observatory(), preferences=PreferencesFile(folder))


def test_the_recent_window_can_change_while_the_orb_runs_and_the_room_follows(machine):
    alpha = machine.project("alpha")
    hermes_session(machine, "H-20d", alpha, days_ago=20)
    hub = Hub(machine.observatory())
    hub.poll_once()
    assert not egos_of(hub, "alpha") and [h["session"] for h in hub.history("alpha")] == ["H-20d"]
    hub.observatory.set_recent_seconds(30 * DAY)                       # o Lucas aumentou o prazo para 30 dias
    hub.world.set_recent_seconds(30 * DAY)
    hub.poll_once()
    assert set(egos_of(hub, "alpha")) == {"hermes:H-20d"} and hub.history("alpha") == []
    assert all(r.since == hub.observatory.since for r in hub.observatory.readers.values())


def test_a_hidden_project_leaves_the_city_but_stays_detected_and_listed_in_settings(machine, tmp_path):
    alpha, beta = machine.project("alpha"), machine.project("beta")
    hermes_session(machine, "H1", alpha, days_ago=1)
    hermes_session(machine, "H2", beta, days_ago=1)
    hub = hub_with_prefs(machine, tmp_path / "orb")
    hub.poll_once()
    hub.update_preferences({"hidden_realms": ["alpha"]})
    assert [r["id"] for r in hub.snapshot()["realms"]] == ["beta"]
    settings = hub.settings()
    assert {r["id"]: r["hidden"] for r in settings["realms"]} == {"alpha": True, "beta": False}      # continua detectado e listado
    assert set(hub.observatory.realms) == {"alpha", "beta"}
    hub.update_preferences({"hidden_realms": []})
    assert [r["id"] for r in hub.snapshot()["realms"]] == ["alpha", "beta"]


def test_the_choices_are_saved_in_the_orb_folder_and_survive_a_restart(machine, tmp_path):
    alpha = machine.project("alpha")
    hermes_session(machine, "H1", alpha, days_ago=1)
    hub = hub_with_prefs(machine, tmp_path / "orb")
    hub.poll_once()
    hub.update_preferences({"hidden_realms": ["alpha"], "recent_days": 30})
    assert sorted(p.name for p in (tmp_path / "orb").iterdir()) == ["preferences.json"]
    again = hub_with_prefs(machine, tmp_path / "orb")                  # o Orb reabriu
    again.poll_once()
    assert again.snapshot()["realms"] == [] and again.observatory.recent_seconds == 30 * DAY
    assert again.settings()["preferences"]["recent_days"] == 30


def test_a_change_the_orb_cannot_accept_is_refused_and_nothing_is_saved(machine, tmp_path):
    hub = hub_with_prefs(machine, tmp_path / "orb")
    for bad in ({"recent_days": 0}, {"recent_days": "dez"}, {"hidden_realms": "alpha"}, {"nao_existe": 1}):
        with pytest.raises(ValueError):
            hub.update_preferences(bad)
    assert not (tmp_path / "orb").exists() and hub.preferences.recent_days == 10


def test_an_id_that_is_not_a_known_realm_is_ignored_when_hiding(machine, tmp_path):
    machine.project("alpha")
    hermes_session(machine, "H1", machine.user / "work" / "alpha", days_ago=1)
    hub = hub_with_prefs(machine, tmp_path / "orb")
    hub.poll_once()
    hub.update_preferences({"hidden_realms": ["alpha", "fantasma"]})
    assert hub.settings()["preferences"]["hidden_realms"] == ["alpha"]


def test_the_settings_screen_is_built_from_a_table_of_options_so_new_tickets_only_add_rows(machine, tmp_path):
    options = hub_with_prefs(machine, tmp_path / "orb").settings()["options"]
    assert [(o["key"], o["unit"], o["minimum"], o["maximum"], o["value"]) for o in options] == [("recent_days", "dias", 1, 365, 10)]


def test_without_a_folder_the_choices_apply_but_nothing_is_written(machine):
    hub = Hub(machine.observatory())
    hub.update_preferences({"recent_days": 5})
    assert hub.observatory.recent_seconds == 5 * DAY


def test_the_world_stream_serves_the_settings_and_applies_changes(machine, tmp_path):
    pytest.importorskip("httpx", reason="TestClient do FastAPI precisa de httpx")
    import json

    from fastapi.testclient import TestClient

    from orb.gateway import GatewayConfig, create_app
    hermes_session(machine, "H1", machine.project("alpha"), days_ago=1)
    config = GatewayConfig(token="tok", home=machine.home, poll_seconds=0.05, idle_poll_seconds=0.05, state_dir=tmp_path / "orb")
    app = create_app(config, check_installed=False, observatory=machine.observatory())
    with TestClient(app) as client, client.websocket_connect("/world?token=tok", headers={"origin": "http://127.0.0.1"}) as ws:
        ws.receive_json()

        def ask(message):
            ws.send_text(json.dumps(message))
            return next(m for m in iter(ws.receive_json, None) if m["channel"] == "settings")

        for _ in range(100):                                                    # espera o realm ser detectado
            reply = ask({"type": "settings"})
            if reply["realms"]:
                break
        assert [r["id"] for r in reply["realms"]] == ["alpha"] and reply["preferences"]["recent_days"] == 10
        reply = ask({"type": "preferences", "hidden_realms": ["alpha"], "recent_days": 20})
        assert reply.get("error") is None and reply["realms"][0]["hidden"] and reply["preferences"]["recent_days"] == 20
        bad = ask({"type": "preferences", "recent_days": 9999})
        assert "entre 1 e 365" in bad["error"] and bad["preferences"]["recent_days"] == 20          # recusa e mantém o que valia
        assert ask({"type": "preferences", "hidden_realms": 7})["error"]
        worlds = []
        for _ in range(100):
            message = ws.receive_json()
            if message["channel"] == "world":
                worlds.append(message["world"])
                if worlds[-1]["hidden_realms"] == ["alpha"]:
                    break
        assert worlds and worlds[-1]["realms"] == []                            # a cidade mudou para quem está conectado


def test_what_happens_in_a_hidden_realm_is_not_sent_to_the_clients_and_a_new_hidden_one_never_shows(machine, tmp_path):
    alpha, beta = machine.project("alpha"), machine.project("beta")
    hermes_session(machine, "H1", alpha, days_ago=1)
    hub = hub_with_prefs(machine, tmp_path / "orb")
    hub.poll_once()
    hub.update_preferences({"hidden_realms": ["alpha"]})
    hermes_session(machine, "H2", alpha, days_ago=0)
    hub.observatory.refresh_index(force=True)
    applied, changed = hub.poll_once()
    assert applied == [] and changed is False                                   # nada de um realm escondido é distribuído
    assert "hermes:H2" in {e.id for e in hub.world.realms["alpha"].values()}    # mas o mundo continua sabendo
    hermes_session(machine, "H3", beta, days_ago=0)
    hub.observatory.refresh_index(force=True)
    applied, _ = hub.poll_once()
    assert {e["realm"] for e in applied} == {"beta"}
