# Spike 4 — Codex

Responde: o que o Codex expõe e como o Orb o observa sem tocar na configuração do Lucas?
Resultado: [MVP.md](../../MVP.md) §9 e [ADAPTER-CODEX.md](../../ADAPTER-CODEX.md).

## Arquivos

| Arquivo | O que faz |
|---|---|
| `drive.py` | **O teste que vale.** Sobe um app-server **efêmero** do Orb (porta 8781), um cliente A conduz uma thread e um cliente B observa (`--persist` grava a thread para o B poder se inscrever). Grava `fixtures/codex-<versão>/` |
| `observe.py` | Abre a TUI nativa com `codex --remote` contra o app-server do Orb. **Endurecido**: verifica a tela, só envia Esc, aborta em qualquer diálogo |
| `tui_peek.py` | Só **lê** a tela da TUI. Não envia nenhuma tecla |
| `fixtures/codex-0.149.0/` | **Gerado localmente**, não versionado (contém dados da conta, como o plano): 1 amostra real de cada notificação |
| `captures/`, `*.log` | **Gerados localmente**, não versionados: capturas completas e logs dos app-servers |

```powershell
python drive.py --models      # lista modelos, sem rodar nada
python drive.py               # turno real; thread efêmera (não grava no histórico)
python drive.py --persist     # thread persistida: grava UMA sessão no histórico do Codex
```

## Cuidados (aprendidos no spike)

- **Nunca envie teclas à TUI do Codex às cegas.** Ela abre diálogos modais cujo padrão tem efeito
  (*Update now*, *Trust*, *Trust all hooks*). Detalhes e o incidente em ADAPTER-CODEX.md §6.
- O padrão `model` do `config.toml` do Lucas não é aceito com conta ChatGPT: passe o modelo.
- `--persist` cria uma sessão real no histórico (`~/.codex/sessions`); `drive.py` sem a flag não.
- Cada execução com modelo consome uma pequena parte da cota da conta ChatGPT.
