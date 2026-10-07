# The Orb — Arquitetura

> Como o sistema se divide, os contratos entre as partes e as regras de engenharia de cada
> âmbito. Vocabulário: [CONTEXT.md](../CONTEXT.md) · Contrato de eventos: [PROTOCOL.md](PROTOCOL.md)
> · Decisões: [adr/](adr/).

Última atualização: 2026-10-07

---

## 1. Objetivos de engenharia

1. **Modularização.** Um módulo por âmbito, com fronteira e contrato explícitos.
2. **Robustez.** Entrada externa não é confiável; falhas ficam isoladas e visíveis.
3. **Desempenho.** Nada é lido duas vezes, nada cresce sem limite, nada bloqueia o agente.
4. **Lógica bem estruturada.** Domínio puro, determinístico, declarado em tabelas e testável sem
   I/O.

## 2. Módulos e fronteiras

```
 provider (CLI real)                                   mundo real
 ┌───────────────┐  transcript/rollout/hooks/app-server  ┌──────────┐
 │ claude/codex/ │ ─────────────────────┐                │ git / CI │
 │ hermes        │                      ▼                └────┬─────┘
 └──────▲────────┘              ┌──────────────┐              │
        │ bytes (PTY)           │  Adapters    │       ┌──────▼─────┐
 ┌──────┴────────┐              │ (1/provider) │       │  Probes    │ (futuro)
 │ Terminal Host │              └──────┬───────┘       └──────┬─────┘
 └──────▲────────┘                     │ eventos (nativo + sinal + inner)
        │                              ▼                      │
        │                     ┌──────────────────┐            │
        │                     │    Protocol      │◄───────────┘
        │                     └────────┬─────────┘
        │                              ▼
        │                     ┌──────────────────┐
        │                     │  Core (puro)     │  mundo: Realm → Alter Ego → Subagente
        │                     └────────┬─────────┘
        │                              ▼
 ┌──────┴──────────────────────────────────────────┐
 │  Gateway (FastAPI + WebSocket)                  │
 └──────────────────────┬──────────────────────────┘
                        ▼
          ┌──────────────────────────────┐
          │ Clients (web 3D, godot)      │
          └──────────────────────────────┘
```

| Módulo | Pasta | Responsabilidade | Conhece | **Não** conhece |
|---|---|---|---|---|
| **Protocol** | `src/orb/protocol/` | Envelope, vocabulário fechado (atividades, sinais), limites de tamanho, validação | nada | todos os outros |
| **Core** | `src/orb/core/` | O mundo: aplica eventos, deriva a atividade de cada personagem, Teams, pendências, Energy; snapshot | Protocol | Adapters, Gateway, disco, rede, relógio |
| **Adapters** (claude, codex, hermes, opencode) | `src/orb/adapters/<provider>/` | Ler a fonte nativa do provider e produzir eventos (nativo + sinal + inner) pelo Mapa do provider | Protocol | Core, Gateway, outros adapters |
| **Terminal Host** | `src/orb/terminal_host/` | Abrir o terminal real (ConPTY), chamar o CLI (lista fixa), transportar bytes, limpar o ambiente herdado | nada do domínio | Core, adapters |
| **Gateway** | `src/orb/gateway/` | Autenticar, ligar terminal + adapter + Core por sessão, validar mensagens do cliente, distribuir por WebSocket | todos, por interfaces | internals de adapters |
| **Clients** | `clients/` | Renderizar o mundo e o Inner World, enviar teclas | só as mensagens do Gateway | adapters, providers |
| **Probes** *(futuro)* | `src/orb/probes/` | Fatos do mundo real (git, CI, LOC respeitando `.gitignore`) | Protocol | Core, adapters |

### Regras de dependência

- Dependências apontam para **Protocol** e **Core**, nunca o contrário. O Core não importa nada
  além do Protocol.
- **Adapters não importam uns aos outros.** O que eles compartilham é genérico e fica em
  `src/orb/adapters/_shared/` (fábrica de eventos, leitura incremental de JSONL, leitura somente
  leitura de SQLite, classificador de comandos de shell), sem conhecimento de provider.
- **Adicionar um provider = adicionar um adapter** (`mapping.py` + leitores), sem tocar em Core,
  Gateway ou clientes ([ADR 0002](adr/0002-eventos-nativos-por-provider.md)).
- Clientes nunca falam com adapters ou providers; só com o Gateway.
- **Somente leitura por desenho.** Adapters e Probes só abrem arquivos do provider e do projeto
  em modo leitura. A única escrita é o Terminal Host transportando o que o Lucas digita
  ([VISION.md](VISION.md) §3, princípio 5).
- **Diálogos são do Lucas.** Nenhum módulo responde diálogos dos CLIs nem pedidos de servidor
  ([ADR 0006](adr/0006-o-orb-nunca-responde-dialogos.md)). Um observador de protocolo nem recusa:
  ignora e registra.

## 3. Contratos

### Protocol

Ver [PROTOCOL.md](PROTOCOL.md). Implementação: `orb.protocol.events` (envelope `OrbEvent`,
`make_event`, `clip_body`, `validate`) e `orb.protocol.vocab` (atividades e tipos de sinal).

### Interface de adapter

Todo adapter expõe a mesma forma (`orb.adapters._shared.base`):

| Membro | Contrato |
|---|---|
| `PROVIDER` | Nome do provider (`"claude"`, `"codex"`, …) |
| `capabilities()` | O que este provider consegue informar (pensamento `raw`/`summary`, aprovações, subagentes, tempo real, tokens). O resto do sistema se adapta, em vez de assumir |
| Leitor nível 0 | Objeto com `poll() -> list[OrbEvent]`, incremental e somente leitura |
| Leitor nível 1 *(opcional)* | Hooks por sessão (Claude) ou observador de app-server (Codex) |
| `mapping.py` | O Mapa do provider: tabelas declarativas de evento nativo → `signal`/`inner` |

### Core

- `World.apply(event) -> bool` aplica um evento (falso se repetido ou inválido) e
  `World.snapshot() -> dict` devolve o estado para os clientes.
- Puro: tempo vem do `ts` dos eventos; nenhuma chamada a disco, rede ou relógio.
- Regras em tabelas (`orb.core.rules`): atividade → área, sinais → transições, estados que
  sobrepõem outros (`WAITING`, `NO_SIGNAL`).

### Terminal Host

- `resolve_provider(provider, model)` escolhe o CLI (explícito vence; senão pelo prefixo do
  modelo). `launch_line(provider, …)` monta a linha **só com valores controlados pelo Orb**.
- `HostedTerminal` abre o shell numa PTY e chama o CLI dentro dele; o processo de PTY é
  injetável (testes rodam sem ConPTY).
- `clean_env()` remove marcadores que o Claude Code injeta nos filhos e preserva a configuração
  do usuário.

### Gateway

- **Realms observados** (`orb.gateway.realms`): um `RealmObserver` por pasta de projeto roda os
  leitores de nível 0 dos **4 providers ao mesmo tempo**. Qualquer sessão que nasça na pasta (pelo
  Orb ou fora dele) vira um Alter Ego que carrega o seu provider. A falha de um provider não afeta
  os outros (fica em `errors` do realm).
- **`Hub`**: um laço único lê todos os realms (fora do loop, `to_thread`), aplica no Core, guarda as
  últimas linhas de Inner World por sessão (`Feed`) e distribui aos clientes.
- `/world?token=…`: o mundo para o cliente 3D — snapshot, depois `event` (linhas de Inner World),
  `world` (snapshot quando algo muda) e `feed` (histórico de uma sessão, sob pedido).
- `/ws?token=…&realm=…&provider=…&model=…`: abre o terminal real de uma sessão nova num realm e
  devolve `term`, `exit`, `system` (com o `alter_ego` quando o Orb escolhe o id, no Claude).
- Segurança: escuta só em `127.0.0.1`, token por execução, `Origin` local obrigatória, lista fixa
  de executáveis.
- `handle_client_message(term, raw)` valida cada mensagem e **nunca levanta**.

## 4. Robustez

- **Validação na borda.** Todo dado de hook, transcript, rollout, app-server ou cliente é validado
  antes de entrar. Inválido é descartado com motivo; nunca propaga.
- **Isolamento de falha.** Leitores de adapter rodam fora do loop do Gateway (`to_thread`); uma
  exceção de leitura vira mensagem `system`, nunca derruba o terminal. Um provider em falha não
  afeta outro.
- **Degradação explícita.** Sem dados, `NO_SIGNAL`; nunca um estado inventado.
- **Tolerância a formato.** Parsers ignoram campos desconhecidos e linhas parciais/ inválidas;
  formatos de hooks/transcripts mudam entre versões e ficam confinados nos adapters.
- **Idempotência.** Ids determinísticos + janela de deduplicação no Core: reler uma fonte depois
  de reconectar não duplica nada.
- **Um Orb travado não atrasa o agente.** Nível 1 do Claude usa hook `command` assíncrono com
  `curl` de timeout curto para um receptor mínimo ([ADR 0005](adr/0005-nivel-zero-de-pegada-por-padrao.md)).
- **Sem estado oculto.** O mundo é reconstruível do log de eventos.

## 5. Desempenho

| Ponto | Regra |
|---|---|
| Leitura de transcript/rollout | Incremental por offset; só lê bytes novos; linha parcial fica em buffer |
| Bancos SQLite (Hermes, opencode) | `mode=ro`; cursor por id/`time_updated`; lotes de 500; só tabelas permitidas |
| Arquivos grandes (rollouts de 145 MB) | Arquivo que já existia começa **do fim**; nunca se lê o arquivo inteiro |
| Corpo de evento | `native.body` ≤ 16 KiB, strings ≤ 4 KiB, `inner.text` ≤ 4.000 caracteres |
| Deduplicação | Janela limitada por Alter Ego (memória constante) |
| Deltas de streaming (`outputDelta`, `agentMessage/delta`) | Não viram eventos um a um; o item completo (`item/completed`) carrega o texto |
| Envio ao cliente | Snapshot ao conectar, depois deltas; bytes do terminal nunca são descartados |
| Polling (nível 0) | 250 ms por sessão hospedada (medido: ~270–470 ms ponta a ponta) |

## 6. Lógica bem estruturada

- **Domínio puro.** Atividade, Team, pendências e Energy são funções dos eventos aplicados:
  mesmos eventos → mesmo mundo.
- **Tabelas, não `if`s espalhados.** Ferramenta → atividade (por adapter), comando de shell →
  atividade (compartilhado), atividade → área, sinal → transição (Core).
- **Injeção de dependência.** PTY, diretório home e relógio entram por parâmetro.

## 7. Testes

| Camada | Como | Onde |
|---|---|---|
| Protocol | Contrato: todo evento produzido valida; limites e cortes | `tests/test_protocol.py` |
| Core | Unitários puros: atividade, Team, `WAITING`, dedupe, snapshot | `tests/test_core.py` |
| Adapters | Linhas/notificações/bancos com a forma verificada (spikes, esquema oficial do Codex, estrutura dos bancos reais) | `tests/test_adapter_{claude,codex,hermes,opencode}.py` |
| Classificador de comandos | Tabela de casos | `tests/test_commands.py` |
| Terminal Host | PTY falsa (sempre) + terminal real (quando `pywinpty` e o CLI existem) | `tests/test_terminal_host.py` |
| Gateway | Validação de mensagens; app com terminal falso | `tests/test_gateway.py` |

Fixtures **reais** (golden files) são geradas pelos scripts de `spikes/03-live-hooks` e
`spikes/04-codex` e **não são versionadas** (contêm caminhos locais, prompts e dados da conta).
Os testes versionados usam amostras mínimas com a forma verificada, sem dados reais.

Rodar: `python -m pytest -q` na raiz.

## 8. Estrutura de pastas

```
The Orb/
├── README.md · CONTEXT.md · pyproject.toml
├── docs/
│   ├── VISION.md · ARCHITECTURE.md · PROTOCOL.md · MVP.md · SPIKES.md · IDEAS.md
│   ├── adapters/   CLAUDE.md · CODEX.md · HERMES.md · OPENCODE.md
│   └── adr/        decisões numeradas
├── src/orb/
│   ├── protocol/        events.py · vocab.py
│   ├── core/            world.py · rules.py
│   ├── adapters/
│   │   ├── _shared/     base.py · commands.py · jsonl.py · sqlite.py
│   │   ├── claude/      mapping.py · transcript.py · hooks.py
│   │   ├── codex/       mapping.py · app_server.py · rollout.py
│   │   ├── hermes/      mapping.py · state_db.py
│   │   └── opencode/    mapping.py · state_db.py
│   ├── terminal_host/   launch.py · env.py · terminal.py
│   └── gateway/         app.py · messages.py
├── clients/
│   ├── web/             o mundo 3D: index.html, styles.css, js/ (scene, realm3d, avatar, hud, innerworld, net)
│   └── godot/           terminal remoto (alternativa; godot-xterm só exibe)
├── tests/
└── spikes/              experimentos que rodam os CLIs reais (02, 03, 04)
```

### De onde veio cada peça (promoção dos spikes, 2026-10-07)

| Spike | Virou |
|---|---|
| `spikes/01-terminal-host/terminal_host.py` | `src/orb/terminal_host/` (`launch.py`, `env.py`, `terminal.py`) |
| `spikes/01-terminal-host/transcript_tail.py` | `src/orb/adapters/claude/transcript.py` + `mapping.py` |
| `spikes/01-terminal-host/server.py` | `src/orb/gateway/` (`app.py`, `messages.py`) |
| `spikes/01-terminal-host/static/index.html` | `clients/web/` (hoje o mundo 3D; ADR 0007) |
| `spikes/01-terminal-host/test_spike.py` | `tests/` |
| `spikes/02-terminal-godot/bridge.*` | `clients/godot/` |
| `spikes/03-live-hooks/probe.py` (settings por sessão) | `src/orb/adapters/claude/hooks.py` |
| `spikes/04-codex/drive.py` (cliente JSON-RPC) | `src/orb/adapters/codex/app_server.py` (observador que **nunca** responde) |

O que ficou em `spikes/` são experimentos que rodam os CLIs de verdade (e geram as fixtures
reais); eles importam os módulos definitivos em vez de duplicar código.

## 9. Em aberto

- Isolamento de adapters: tarefa supervisionada (hoje) ou processo separado.
- Onde vive o log de eventos (arquivo/SQLite) e quando entra um banco.
- Receptor de hooks do nível 1 como processo separado, sempre responsivo.
- Nível 1 de Hermes (sidecar da TUI) e opencode (servidor próprio).
