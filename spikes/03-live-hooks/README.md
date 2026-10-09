# Spike 3 — Hooks ao vivo do Claude Code (experimento)

Responde: os hooks do Claude Code entregam ao Orb o que as docs dizem, sem tocar na
configuração do usuário e sem atrapalhar o agente? Resultado: [SPIKES.md](../../docs/SPIKES.md) e
[adapters/CLAUDE.md](../../docs/adapters/CLAUDE.md) §2. O formato de settings por sessão escolhido
(hook `command` assíncrono + `curl`) foi promovido para `src/orb/adapters/claude/hooks.py`; este
experimento continua aqui para regenerar as fixtures reais e repetir as medições.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `probe.py` | Sobe um receptor HTTP local (só grava, responde `{}`) e roda cenários pequenos do `claude -p` com hooks injetados por `--settings` |
| `probe_tui.py` | Mesmo teste com o `claude` **interativo**, hospedado numa pseudo-console como o Orb faz |
| `orb-hooks*.settings.json` | Arquivos de settings **gerados** pelo `probe.py` (hook `http`, servidor morto, servidor travado, `command` async + `curl`). Não versionados |
| `fixtures/claude-<versão>/` | **Gerado localmente**, não versionado: 1 amostra real de cada evento por cenário (golden files para os futuros testes do adapter) |
| `captures/`, `report.json` | **Gerados localmente**, não versionados: tudo que chegou em cada execução e o resumo |

## Cenários

`A` ler um arquivo · `B` subagente · `C` permissão (Bash em modo manual) · `D` Orb fora do ar ·
`E` Orb travado (`http`) · `F` Orb travado (`http` + `async`) · `G` Orb travado (`command` async +
`curl`) · `H` `command` async + `curl` com receptor vivo.

```powershell
python probe.py A B C        # escolhe cenários (sem argumentos roda todos)
python probe_tui.py          # TUI hospedada
```

Cada cenário envia um prompt curto ao `claude` (modelo `haiku`) e **consome uma pequena parte da
cota** da conta logada. As fixtures e capturas contêm prompts e caminhos locais.
