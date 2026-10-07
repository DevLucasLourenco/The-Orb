"""Spike 3 (parte TUI): os hooks disparam quando o claude roda INTERATIVO, hospedado numa
pseudo-console como o Orb faz? Usa os hooks por sessão (--settings), sem tocar no settings.json.
"""
from __future__ import annotations

import sys
import threading
import time
import uuid
from pathlib import Path

import uvicorn
from winpty import PtyProcess

import probe
from probe import CAPTURES, CURRENT, HERE, PORT, TOKEN, app, clean_env, write_settings

settings = write_settings(PORT, "orb-hooks.settings.json")
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error"))
threading.Thread(target=server.run, daemon=True).start()
while not server.started:
    time.sleep(0.05)

CURRENT["scenario"] = "TUI"
env = clean_env()
env["ORB_TOKEN"] = TOKEN
sid = str(uuid.uuid4())
proc = PtyProcess.spawn(["powershell.exe", "-NoLogo"], cwd=probe.PROJECT, env=env, dimensions=(32, 120))
chunks: list[str] = []
threading.Thread(target=lambda: [chunks.append(proc.read(65536)) for _ in iter(lambda: proc.isalive(), False)],
                 daemon=True).start()

proc.write(f'claude --session-id {sid} -n orb-hooks-tui --model haiku --settings "{settings}"\r')
time.sleep(12)                                    # TUI sobe
started = {c["event"] for c in CAPTURES if c["scenario"] == "TUI"}
print("depois de subir a TUI (sem prompt):", sorted(started) or "nenhum evento")
proc.write("Leia o arquivo docs/MVP.md e responda só com o título da seção 1.")
time.sleep(0.5)
proc.write("\r")
time.sleep(25)
proc.write("\x03"); time.sleep(0.8); proc.write("\x03"); time.sleep(2)
proc.write("exit\r"); time.sleep(1.5)

events = [c for c in CAPTURES if c["scenario"] == "TUI"]
t0 = events[0]["t"] if events else 0
print("\neventos recebidos na TUI hospedada:")
for c in events:
    b = c["body"]
    extra = {k: str(b[k])[:50] for k in ("tool_name", "prompt", "source", "reason") if k in b}
    print(f"  +{c['t'] - t0:5.1f}s {c['event']:18s} {extra}")
print("\nsession_id bate com o --session-id do Orb:",
      all(c["body"].get("session_id") == sid for c in events) if events else "n/a")
try:
    proc.terminate(force=True)
except Exception:
    pass
server.should_exit = True
