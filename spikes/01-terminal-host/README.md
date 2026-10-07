# Spike 1 — Terminal Host

Responde: dá para abrir um terminal real controlado pelo Orb, chamar o CLI do agente dentro dele
(`claude`, `codex`, `hermes`) e observar o que ele faz em tempo real, sem alterar o agente?
Resultado: [MVP.md](../../MVP.md) §6.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `terminal_host.py` | Abre um **PowerShell real** em ConPTY (`pywinpty`) e digita nele o comando do CLI. O provider é escolhido pelo modelo (`resolve_provider`). Lista **fixa** de executáveis. Limpa do ambiente os marcadores que o Claude Code injeta nos filhos |
| `transcript_tail.py` | **Nível 0**: lê (tail, somente leitura) o transcript do Claude Code e traduz para eventos do protocolo. Com `session_id` só segue o transcript daquela sessão |
| `server.py` | FastAPI/WebSocket em `127.0.0.1`: token por sessão, checagem de `Origin`, `handle_client_message` valida cada mensagem sem nunca levantar |
| `static/index.html` | Página com xterm.js (terminal) e painel de eventos do protocolo |
| `test_spike.py` | 15 testes (`python -m pytest -q`) |

## Rodar

```powershell
pip install fastapi uvicorn websockets pywinpty pytest
python server.py --cwd "C:\caminho\do\projeto" --port 8765   # imprime a URL com o token
python -m pytest -q
```

Abra a URL impressa. O seletor escolhe `auto` (pelo modelo), `shell` ou um provider; `claude` e
`codex` precisam estar instalados.

## Cuidados

- O servidor abre um shell: **só escuta em loopback**, exige o token e valida a `Origin`.
- Cada prompt enviado ao `claude` hospedado consome cota da conta logada.
- É um protótipo: o código vai para os módulos definitivos listados em
  [ARCHITECTURE.md](../../ARCHITECTURE.md) §7.
