# The Orb

Um **grande centralizador de IAs, das suas sessões e dos seus subagentes**: um mundo 3D visto de
cima onde cada projeto real é um prédio (**Realm**), cada sessão de um CLI de IA é um personagem
(**Alter Ego**) trabalhando no teto do prédio (**Rooftop Room**), e tudo o que se vê é **telemetria
real** dos agentes de verdade (Claude Code, Codex, Hermes), nunca animação inventada.

O Lucas usa os CLIs originais dentro do Orb, no **Inner World** de cada Alter Ego (o terminal real
da sessão + a linha do tempo do que ela pensa e faz). O Orb só observa: não altera em nada como os
agentes trabalham.

> Estado: **fundação promovida** (2026-10-07). Os 4 spikes validaram a tese; o código útil virou os
> módulos definitivos em `src/orb/` (protocolo, mundo, adapters, terminal, gateway), cobertos por testes automatizados.
> Ainda não há o 3D final.

## Comece por aqui

| Documento | Para quê |
|---|---|
| [CONTEXT.md](CONTEXT.md) | **Glossário** canônico (Orb, Realm, Alter Ego, Inner World, Team, Gate…) |
| [docs/VISION.md](docs/VISION.md) | Visão, princípios, como o mundo se organiza, roadmap e questões em aberto |
| [docs/adr/](docs/adr/) | Decisões difíceis de reverter, e por quê |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Módulos por âmbito, contratos, robustez, desempenho, testes, pastas |
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | Event Protocol 0.2: evento nativo + sinal de mundo + Inner World |
| [docs/adapters/](docs/adapters/) | O que [Claude Code](docs/adapters/CLAUDE.md), [Codex](docs/adapters/CODEX.md) e [Hermes](docs/adapters/HERMES.md) expõem, verificado |
| [docs/MVP.md](docs/MVP.md) | Escopo do MVP, critérios, riscos, decisões e próximos passos |
| [docs/SPIKES.md](docs/SPIKES.md) | Resultados completos dos 4 spikes |
| [docs/IDEAS.md](docs/IDEAS.md) | Backlog **completo** de ideias, com status (nada é apagado) |

## Princípios (resumo)

1. **Telemetria real**: o mundo só mostra o que foi observado.
2. **Cada provider aparece como ele é**: o vocabulário nativo de cada CLI é preservado; o mundo usa
   só sinais derivados.
3. **CLI nativo, nada criado do zero**: o Orb abre um terminal real e chama `claude`/`codex`/`hermes` nele.
4. **Não interferência**: tudo que molda o agente é somente leitura; a única porta de escrita é o
   terminal do Inner World. **O Orb nunca responde diálogos** dos CLIs.
5. **Modular, robusto, com desempenho e lógica bem estruturada.**

## Estrutura

```
src/orb/        protocol · core · adapters (claude, codex, hermes) · terminal_host · gateway
clients/        web_panel (xterm.js + mundo + Inner World) · godot (terminal remoto)
tests/          testes automatizados (python -m pytest -q)
spikes/         experimentos que rodam os CLIs reais (02 Godot, 03 hooks, 04 Codex)
docs/           visão, arquitetura, protocolo, adapters, ADRs, MVP, spikes, ideias
```

## Rodar (Windows 11)

Requisitos: Python 3.12+ e os CLIs que for usar, instalados e logados.

```powershell
pip install -e ".[dev]"          # fastapi, uvicorn, websockets, pywinpty, pytest
python -m pytest -q
the-orb --cwd "C:\caminho\do\projeto"     # imprime a URL com o token
```

**Atenção:** o terminal hospedado roda o **CLI de verdade** e **consome cota** da conta logada. O
Gateway abre um shell: escuta só em `127.0.0.1`, exige token e `Origin` local. Nunca envie teclas a
uma TUI às cegas (diálogos de atualização/confiança têm padrão com efeito): ver
[docs/adr/0006](docs/adr/0006-o-orb-nunca-responde-dialogos.md).

Arquivos gerados pelos experimentos (capturas, fixtures, logs) **não são versionados**: contêm
caminhos locais, prompts e dados da conta.

## Próximos passos

Ver [docs/MVP.md](docs/MVP.md) §6. Os pontos em aberto mais importantes: o **Perfil** do Alter Ego e
o comportamento do app-server do Codex quando um observador ignora um pedido de aprovação.
