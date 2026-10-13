"""As leituras do mundo real: pastas de CLIs falsas -> realms (R3, R3a, R3b, R3d). Sem rede, sem CLI, sem dados
reais: a 'máquina' é montada em pastas temporárias, com a forma verificada dos arquivos de cada provider."""
import os

import pytest

from orb.gateway import Hub, Observatory
from orb.gateway.projects import Exclusions

from .test_session_index import hermes_db, opencode_db, rollout, transcript


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


def realms(observatory):
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
    found = realms(machine.observatory())
    assert set(found) == {"alpha", "beta", "gamma", "delta"}                  # nada de --root nem --lookback
    assert {r.cwd for r in found.values()} == {str(p) for p in (alpha, beta, gamma, delta)}


def test_the_user_folder_system_folders_and_missing_folders_never_become_realms(machine):
    real = machine.project("real")
    machine.claude(machine.user)                                              # a pasta do usuário em si
    machine.codex(machine.user / "Downloads")
    machine.codex(machine.user / "AppData" / "Local" / "Temp")
    machine.codex(machine.user / "work" / "apagado")                          # não existe mais no disco
    machine.claude(real)
    assert set(realms(machine.observatory())) == {"real"}


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
    found = realms(machine.observatory())
    assert set(found) == {"trisafe-enhanced"} and found["trisafe-enhanced"].cwd == str(main)


def test_a_folder_without_a_repository_is_a_realm_but_its_subfolders_do_not_split_it(machine):
    scripts = machine.project("scripts", git=False)
    (scripts / "sub").mkdir()
    machine.codex(scripts)
    machine.codex(scripts / "sub")
    assert set(realms(machine.observatory())) == {"scripts"}


def test_similar_names_never_mix_and_equal_names_get_a_suffix(machine):
    trisafe, enhanced = machine.project("trisafe"), machine.project("trisafe-enhanced")
    left, right = machine.project("area-a", "app"), machine.project("area-b", "app")
    for folder in (trisafe, enhanced, left, right):
        machine.codex(folder)
    found = realms(machine.observatory())
    assert set(found) == {"trisafe", "trisafe-enhanced", "app", "app-2"}
    assert found["trisafe"].cwd == str(trisafe) and found["trisafe-enhanced"].cwd == str(enhanced)
    assert {found["app"].cwd, found["app-2"].cwd} == {str(left), str(right)}
    assert found["app"].cwd == str(left)                                      # ordem estável: o caminho que vem primeiro


def test_realm_ids_do_not_change_when_a_project_with_the_same_name_appears_later(machine):
    right = machine.project("area-b", "app")
    machine.codex(right)
    observatory = machine.observatory()
    assert set(realms(observatory)) == {"app"}
    left = machine.project("area-a", "app")                                   # vem antes na ordem dos caminhos
    machine.codex(left, day="08")
    found = realms(observatory)
    assert found["app"].cwd == str(right) and found["app-2"].cwd == str(left)  # quem já estava na cidade não muda de id


def test_the_root_the_provider_informs_wins(machine):
    project = machine.project("alpha", git=False)                             # sem .git: só o Hermes sabe a raiz
    pkg = project / "pkg"
    pkg.mkdir()
    conn = hermes_db(machine.home / "hermes")
    conn.execute("INSERT INTO sessions VALUES ('H1', 'cli', 'm', NULL, ?, 't', 1700000000.0, 1700000000.0, ?, NULL)",
                 (str(pkg), str(project)))
    conn.commit()
    found = realms(machine.observatory())
    assert {r.cwd for r in found.values()} == {str(project)}


def test_a_new_project_appears_by_itself_and_live_sessions_land_in_the_right_realm(machine):
    trisafe, enhanced = machine.project("trisafe"), machine.project("trisafe-enhanced")
    observatory = machine.observatory(lookback_minutes=60)
    assert realms(observatory) == {}
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
    assert set(realms(observatory)) == {"alpha"}
    assert "RuntimeError" in observatory.errors["index:hermes"]
