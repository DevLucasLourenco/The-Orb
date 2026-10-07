# Orb IA

Um **grande centralizador de IAs e de seus agentes e subagentes**: um mundo 3D visto de cima (o
**Orb**) onde cada projeto real é um prédio (**Realm**), no teto de cada prédio as IAs trabalham
(**Rooftop Room**) e tudo o que se vê é **telemetria real** dos agentes de verdade (Claude Code,
Codex, Hermes), nunca animação inventada. O Lucas usa os CLIs originais dentro do Orb e o Orb só
observa, sem alterar em nada como os modelos funcionam nos projetos.

> Estado: **fase de documentação e protótipos**. Os 4 spikes de validação foram concluídos; ainda
> não há o produto (MVP) nem o 3D final. O código em `spikes/` é descartável por desenho.

## Comece por aqui

| Documento | Para quê |
|---|---|
| [CONTEXT.md](CONTEXT.md) | **Visão, princípios e glossário** (Orb, Realm, Alter Ego, Inner World, Intrusive Thoughts, Gate, Team…) |
| [SPIKES.md](SPIKES.md) | **Resumo dos resultados dos 4 spikes**: o que provaram, o que mudou, o que falta |
| [MVP.md](MVP.md) | Escopo do MVP, riscos, resultados detalhados dos spikes e decisões tomadas |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Módulos, fronteiras, regras de dependência, robustez, testes |
| [PROTOCOL.md](PROTOCOL.md) | Agent Event Protocol: envelope, eventos, estados, `fidelity`, comandos |
| [ADAPTER-CLAUDE.md](ADAPTER-CLAUDE.md) | O que o Claude Code expõe (hooks e transcript), verificado ao vivo |
| [ADAPTER-CODEX.md](ADAPTER-CODEX.md) | O que o Codex expõe (app-server e rollouts), verificado ao vivo |
| [IDEAS.md](IDEAS.md) | Backlog **completo** de ideias, com status (nada é descartado) |

## Princípios (resumo)

1. **Telemetria real**: o mundo só mostra o que foi observado.
2. **CLI nativo, nada criado do zero**: o Orb abre um terminal real e chama `claude`/`codex` nele.
3. **Não interferência**: tudo que molda o agente é somente leitura para o Orb; a única porta de
   escrita é o Lucas usando o terminal. **O Orb nunca responde diálogos dele** (atualização,
   confiança, hooks, aprovações).
4. **Modular, robusto, com lógica bem estruturada**; neutro de provider.

## O que os spikes provaram

| Spike | Pergunta | Resultado |
|---|---|---|
| 1 — `spikes/01-terminal-host/` | Hospedar a TUI real num terminal controlado, no Windows? | ✅ Sim; telemetria ao vivo em ~270–470 ms |
| 2 — `spikes/02-terminal-godot/` | Terminal dentro do Godot e como monitor 3D? | ✅ Sim (godot-xterm); o host continua em Python |
| 3 — `spikes/03-live-hooks/` | Hooks do Claude ao vivo, sem tocar na configuração? | ✅ Sim, por sessão (`--settings`); um Orb travado atrasa o agente |
| 4 — `spikes/04-codex/` | Observar o Codex sem tocar na configuração? | ✅ Sim, por app-server próprio do Orb + `--remote`. Hermes não verificado |

## Rodar os spikes (Windows 11)

Requisitos: Python 3.14 (`fastapi uvicorn websockets pywinpty pytest`), Godot 4.7.2 (spike 2),
`claude` e `codex` instalados e logados. Cada spike tem um README com os comandos.

**Atenção:** os spikes rodam os **CLIs de verdade** e **consomem cota** das contas logadas.
Nunca envie teclas à TUI do Codex às cegas (diálogos de atualização/confiança têm padrão com
efeito): veja [ADAPTER-CODEX.md](ADAPTER-CODEX.md) §6.

Arquivos gerados pelos spikes (capturas, fixtures, logs) **não são versionados** (`.gitignore`):
contêm caminhos locais, prompts e dados da conta. Regeneram-se rodando os spikes. O addon
`godot-xterm` também não é versionado; veja `spikes/02-terminal-godot/README.md`.

## Próximos passos

Ver [MVP.md](MVP.md) §11. O principal risco que sobrou: o comportamento do app-server do Codex
quando um observador ignora um pedido de aprovação.
