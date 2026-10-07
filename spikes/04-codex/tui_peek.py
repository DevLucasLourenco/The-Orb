"""Abre a TUI do Codex (apontando para o app-server do Orb) e só LÊ a tela. Nenhuma tecla é enviada,
para não aceitar sem querer algum diálogo de atualização/confirmação."""
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from winpty import PtyProcess

from observe import PORT, PROJECT, wait_port

HERE = Path(__file__).parent
args = sys.argv[1:] or ["--remote", f"ws://127.0.0.1:{PORT}"]
server = None
if "--remote" in args:
    server = subprocess.Popen(["codex", "app-server", "--listen", f"ws://127.0.0.1:{PORT}"],
                              stdout=open(HERE / "app-server-peek.log", "wb"), stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL)
    assert wait_port(PORT), "app-server não subiu"

proc = PtyProcess.spawn(["powershell.exe", "-NoLogo"], cwd=PROJECT, dimensions=(40, 120))
chunks: list[str] = []
threading.Thread(target=lambda: [chunks.append(proc.read(65536)) for _ in iter(lambda: proc.isalive(), False)],
                 daemon=True).start()
proc.write("codex " + " ".join(args) + f' -C "{PROJECT}"\r')
time.sleep(28)
text = "".join(chunks)
text = re.sub(r"\x1b\[[0-9;]*[Hf]", "\n", text)           # reposicionar o cursor = nova linha
text = re.sub(r"\x1b\[[0-9;]*[ABCD]", " ", text)          # mover cursor = espaço
clean = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[()][A-Z0-9]", "", text).replace("\r", "")
lines = []
for l in clean.split("\n"):
    l = l.rstrip()
    if l.strip() and l not in lines[-6:]:                  # remove repetições dos redesenhos
        lines.append(l)
print("--- tela da TUI (sem escapes, redesenhos repetidos removidos) ---")
for l in lines[-45:]:
    print(l[:150])
try:
    proc.terminate(force=True)
except Exception:
    pass
if server:
    server.terminate()
