import pytest

from orb.adapters._shared import classify_command, realm_id_for


@pytest.mark.parametrize("command, activity", [
    ("Get-Content docs/MVP.md", "READING"),
    ('"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Raw a.py"', "READING"),
    ("bash -lc 'cat a.py | head -n 5'", "READING"),
    ("rg -n foo src", "READING"),
    ("git status", "READING"),
    ("git push origin main", "EXECUTING"),
    ("python -m pytest -q", "TESTING"),
    ("npm run test -- --watch", "TESTING"),
    ("cargo test", "TESTING"),
    ("gh pr view 12", "REVIEWING"),
    ("curl -s https://example.com", "RESEARCHING"),
    ("pip install x", "EXECUTING"),
    ("", "EXECUTING"),
    (None, "EXECUTING"),
])
def test_classify_command(command, activity):
    assert classify_command(command) == activity


def test_realm_id_from_folder():
    assert realm_id_for(r"C:\Users\x\Documents\Sistemas e Projetos\The Orb") == "the-orb"
    assert realm_id_for("/home/x/UTC CONECTA+/") == "utc-conecta"
