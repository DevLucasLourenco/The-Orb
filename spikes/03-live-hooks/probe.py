"""Spike 3: hooks ao vivo do Claude Code, injetados POR SESSÃO via --settings (sem tocar no
settings.json do usuário). O receptor só GRAVA: devolve {} (nenhuma decisão, nenhum contexto).

Uso:  python probe.py [A B C D ...]      (sem argumentos roda todos os cenários)
Saída: captures/*.jsonl (tudo que chegou) e fixtures/claude-<versão>/*.json (1 amostra por evento).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "01-terminal-host"))
from terminal_host import clean_env  # noqa: E402  (limpa marcadores herdados do Claude)

PORT = 8770
DEAD_PORT = 8799          # nada escuta aqui: simula o Orb fora do ar
HANG_PORT = 8798          # aceita a conexão e NUNCA responde: simula o Orb travado
TOKEN = uuid.uuid4().hex
PROJECT = str(HERE.parent.parent)   # raiz do projeto Orb IA (cwd das sessões de teste)

# Eventos de hook documentados que interessam ao Orb.
EVENTS = [
    "SessionStart", "SessionEnd", "UserPromptSubmit", "UserPromptExpansion", "Stop", "StopFailure",
    "PreToolUse", "PermissionRequest", "PermissionDenied", "PostToolUse", "PostToolUseFailure",
    "PostToolBatch", "SubagentStart", "SubagentStop", "TaskCreated", "TaskCompleted",
    "Notification", "MessageDisplay", "PreCompact", "PostCompact", "CwdChanged",
    "InstructionsLoaded", "ConfigChange",
]

CAPTURES: list[dict] = []
CURRENT = {"scenario": None}
app = FastAPI()


@app.post("/hook/{event}")
async def hook(event: str, request: Request):
    if request.headers.get("x-orb-token") != TOKEN:
        return Response(status_code=401)
    raw = await request.body()
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        body = {"_unparsable": raw[:200].decode("utf-8", "replace")}
    CAPTURES.append({"scenario": CURRENT["scenario"], "event": event, "t": time.time(), "body": body})
    return {}   # corpo vazio: não decide nada e não injeta contexto no agente


def build_settings(port: int, timeout: int = 2, is_async: bool = False) -> dict:
    hook = {"type": "http", "url": "", "headers": {"X-Orb-Token": "$ORB_TOKEN"},
            "allowedEnvVars": ["ORB_TOKEN"], "timeout": timeout}
    if is_async:
        hook["async"] = True
    hooks = {}
    for ev in EVENTS:
        h = dict(hook, url=f"http://127.0.0.1:{port}/hook/{ev}")
        hooks[ev] = [{"hooks": [h]}]
    return {"hooks": hooks}


def build_settings_curl(port: int) -> dict:
    """Alternativa ao hook http: hook `command` ASSÍNCRONO que só dispara um curl e sai.
    O Claude não espera por ele, então um Orb travado não atrasa o agente."""
    hooks = {}
    for ev in EVENTS:
        cmd = (f'curl -s -m 1 -X POST -H "X-Orb-Token: $ORB_TOKEN" -H "Content-Type: application/json" '
               f'--data-binary @- http://127.0.0.1:{port}/hook/{ev}')
        hooks[ev] = [{"hooks": [{"type": "command", "command": cmd, "async": True, "timeout": 5}]}]
    return {"hooks": hooks}


def write_settings(port: int, name: str, **kw) -> Path:
    path = HERE / name
    path.write_text(json.dumps(build_settings(port, **kw), indent=2), encoding="utf-8")
    return path


def start_blackhole(port: int) -> None:
    """Servidor que aceita conexões e nunca responde (Orb travado)."""
    import socket
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(64)
    held = []

    def loop():
        while True:
            conn, _ = srv.accept()
            held.append(conn)          # segura aberta, sem ler nem responder
    threading.Thread(target=loop, daemon=True).start()


def claude_version() -> str:
    out = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=30).stdout
    return out.split()[0]


def run_claude(prompt: str, settings: Path, extra: list[str] | None = None, timeout: int = 240) -> dict:
    sid = str(uuid.uuid4())
    cmd = [shutil.which("claude") or "claude", "-p", prompt, "--session-id", sid,
           "--settings", str(settings), "--model", "haiku", "--output-format", "json"] + (extra or [])
    env = clean_env()
    env["ORB_TOKEN"] = TOKEN
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=PROJECT, env=env, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=timeout, encoding="utf-8")
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = -1, "", "timeout"
    dur = time.time() - t0
    result = None
    try:
        result = json.loads(out)
    except (json.JSONDecodeError, ValueError):
        pass
    return {"session_id": sid, "returncode": rc, "seconds": round(dur, 1),
            "answer": (result or {}).get("result"), "is_error": (result or {}).get("is_error"),
            "stderr": err[:300]}


SCENARIOS = {
    "A": ("basico: ler um arquivo",
          "Leia o arquivo MVP.md e responda apenas com o título da seção 1, nada mais.", []),
    "B": ("subagente",
          "Use a ferramenta Agent com subagent_type Explore para contar quantos arquivos .md existem "
          "na pasta atual (sem subpastas) e me responda só com o número.", []),
    "C": ("permissao: Bash em modo manual",
          "Rode o comando `git --version` com a ferramenta Bash e me diga só a versão.",
          ["--permission-mode", "manual"]),
}


def summarize(scenario: str) -> dict:
    caps = [c for c in CAPTURES if c["scenario"] == scenario]
    by_event: dict[str, list[dict]] = {}
    for c in caps:
        by_event.setdefault(c["event"], []).append(c["body"])
    return {ev: {"count": len(v), "keys": sorted(v[0].keys())} for ev, v in by_event.items()}


def save_fixtures(version: str) -> Path:
    out = HERE / "fixtures" / f"claude-{version}"
    out.mkdir(parents=True, exist_ok=True)
    seen: set[tuple[str, str]] = set()
    for c in CAPTURES:
        key = (c["scenario"], c["event"])
        if key in seen:
            continue
        seen.add(key)
        (out / f"{c['scenario']}__{c['event']}.json").write_text(
            json.dumps(c["body"], indent=2, ensure_ascii=False), encoding="utf-8")
    (HERE / "captures").mkdir(exist_ok=True)
    with open(HERE / "captures" / f"run-{int(time.time())}.jsonl", "w", encoding="utf-8") as fh:
        for c in CAPTURES:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    return out


def main(selected: list[str]) -> None:
    version = claude_version()
    print(f"claude {version}; receptor em 127.0.0.1:{PORT}; cwd das sessões: {PROJECT}")
    settings_up = write_settings(PORT, "orb-hooks.settings.json")
    settings_down = write_settings(DEAD_PORT, "orb-hooks-dead.settings.json")
    settings_hang = write_settings(HANG_PORT, "orb-hooks-hang.settings.json", timeout=2)
    settings_hang_async = write_settings(HANG_PORT, "orb-hooks-hang-async.settings.json", timeout=2, is_async=True)
    start_blackhole(HANG_PORT)
    settings_curl_hang = HERE / "orb-hooks-curl-hang.settings.json"
    settings_curl_hang.write_text(json.dumps(build_settings_curl(HANG_PORT), indent=2), encoding="utf-8")
    settings_curl_live = HERE / "orb-hooks-curl-live.settings.json"
    settings_curl_live.write_text(json.dumps(build_settings_curl(PORT), indent=2), encoding="utf-8")
    OFFLINE = {"D": ("servidor fora do ar", settings_down), "E": ("servidor TRAVADO, timeout 2s", settings_hang),
               "F": ("servidor TRAVADO, timeout 2s, async", settings_hang_async),
               "G": ("servidor TRAVADO, hook command async + curl", settings_curl_hang)}
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)

    report = {}
    for key in selected:
        if key in OFFLINE:     # Orb ausente/travado: o claude tem que funcionar normalmente
            label, cfg = OFFLINE[key]
            name, prompt, extra = SCENARIOS["A"]
            CURRENT["scenario"] = key
            res = run_claude(prompt, cfg, extra)
            report[key] = {"nome": f"{label} (cenário A)", **res, "events": {}}
        elif key == "H":        # command async + curl, com o receptor VIVO: os eventos chegam?
            name, prompt, extra = SCENARIOS["A"]
            CURRENT["scenario"] = "H"
            res = run_claude(prompt, settings_curl_live, extra)
            time.sleep(3)       # dá tempo aos curls assíncronos terminarem
            report["H"] = {"nome": "hook command async + curl, receptor vivo (cenário A)", **res, "events": summarize("H")}
        else:
            name, prompt, extra = SCENARIOS[key]
            CURRENT["scenario"] = key
            res = run_claude(prompt, settings_up, extra)
            report[key] = {"nome": name, **res, "events": summarize(key)}
        r = report[key]
        print(f"\n=== {key}: {r['nome']}  (rc={r['returncode']}, {r['seconds']}s, erro={r['is_error']})")
        print("  resposta:", (r["answer"] or r["stderr"] or "").strip()[:160].replace("\n", " "))
        for ev, info in r["events"].items():
            print(f"  {ev:20s} x{info['count']}  {info['keys']}")
    fx = save_fixtures(version)
    (HERE / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nfixtures em {fx}")
    server.should_exit = True


if __name__ == "__main__":
    main(sys.argv[1:] or ["A", "B", "C", "D", "E", "F", "G", "H"])
