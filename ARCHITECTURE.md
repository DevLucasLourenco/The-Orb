# Orb IA — ARCHITECTURE

> Como o sistema é dividido, quais contratos existem entre as partes e quais regras de
> engenharia valem. Vocabulário de domínio: ver [CONTEXT.md](CONTEXT.md).
> Este documento é **proposta inicial**; muda conforme o protótipo de risco valida as premissas.

Última atualização: 2026-10-06

---

## 1. Objetivos de engenharia

1. **Modularização:** responsabilidades separadas, fronteiras e contratos explícitos.
2. **Robustez:** entrada externa não é confiável; falhas ficam isoladas e visíveis.
3. **Lógica bem estruturada:** domínio puro, determinístico e testável, separado de I/O.

---

## 2. Módulos e fronteiras

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Adapters    │   │  Probes      │   │  Terminal    │
│ (por provider)│   │ (git/CI/LOC) │   │  Host (PTY)  │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │ eventos          │ fatos            │ bytes
       ▼                  ▼                  │
┌─────────────────────────────────┐          │
│  Protocol (contratos + schemas) │          │
└──────────────┬──────────────────┘          │
               ▼                             │
┌─────────────────────────────────┐          │
│  Core / Domain (puro)           │          │
│  Orb · Realm · AlterEgo · state │          │
└──────────────┬──────────────────┘          │
               ▼                             ▼
┌─────────────────────────────────────────────────┐
│  Gateway (FastAPI: WebSocket + API)             │
└──────────────┬──────────────────────────────────┘
               ▼
┌─────────────────────────────────┐
│  Clients (Godot 3D, painel 2D)  │
└─────────────────────────────────┘
```

| Módulo | Responsabilidade | Conhece | **Não** conhece |
|---|---|---|---|
| **Protocol** | Define eventos, estados universais, `fidelity` e schemas versionados. | nada | todos os outros |
| **Core / Domain** | Regras puras: máquina de estados do Alter Ego, altura do prédio (LOC), XP/stats. Sem I/O. | Protocol | Adapters, Gateway, Godot, disco, rede |
| **Adapters** (um por provider: Claude, Codex, Hermes) | Traduzem hooks e transcripts nativos em eventos do Protocol. | Protocol | Core, Gateway, outros adapters |
| **Probes** (git, GitHub, CI, contagem de LOC) | Coletam fatos do mundo real e os emitem como eventos. Respeitam o `.gitignore`. | Protocol | Core, adapters |
| **Terminal Host** | Abre um terminal real (PowerShell) numa PTY por realm/alter ego, chama o CLI do provider (escolhido pelo modelo, lista fixa) e expõe bytes por stream. Não cria TUI. | Protocol (ids) | Core, adapters |
| **Gateway** | Orquestra: recebe eventos, aplica ao Core, distribui por WebSocket. | todos via interfaces | internals dos adapters |
| **Clients** | Renderizam estado e enviam comandos. | só o contrato do Gateway | Adapters, providers |

### Regras de dependência

- Dependências apontam **para o Protocol e para o Core**, nunca ao contrário.
- Adapters não importam uns aos outros. Adicionar um provider = adicionar um adapter, sem
  alterar Core, Gateway ou Clients.
- O Core não faz I/O. Tempo, disco e rede entram por parâmetros/interfaces injetadas.
- Clients nunca falam com adapters ou providers; só com o Gateway.
- **Diálogos pertencem ao usuário.** Nem o Terminal Host nem os adapters respondem diálogos dos
  CLIs (atualização, confiança, hooks, aprovações). O Terminal Host só transporta o que o usuário
  digita; as únicas escritas automáticas permitidas são as do Gate/`terminal.write` pedidas por
  ele. Um adapter **observador** (ex.: o cliente B do app-server do Codex) **nunca responde** a
  pedidos do servidor.
- **Não interferência (somente leitura).** Adapters, Probes e o leitor do Archive **não
  escrevem** em nada do projeto nem alteram o que molda o agente (`CLAUDE.md`, skills,
  memória, contexto). A única porta de escrita é o Terminal Host (intrusive thoughts). Isso
  é imposto por desenho: esses módulos recebem handles **somente leitura**, e um teste de
  contrato verifica que nenhum deles abre arquivos do projeto para escrita.

---

## 3. Contratos

### Protocol (eventos)

- Todo evento tem: `schema_version`, `event_id`, `timestamp`, `realm`, `alter_ego`,
  `provider`, `type`, `payload`, e `fidelity` quando for `thought`.
- Schemas **versionados**; mudança incompatível = nova versão, com os adapters migrando.
- Eventos são **idempotentes e ordenáveis** (`event_id` + `timestamp` + sequência por sessão),
  para tolerar duplicatas e reentrega.

### Interface de Adapter

Cada adapter implementa o mesmo contrato:

- `detect()` — o provider está instalado/disponível?
- `start_observing(session)` / `stop_observing(session)`
- stream de eventos do Protocol (hooks + leitura de transcript)
- `capabilities()` — o que este provider consegue informar (ex.: thinking `raw`, `summary`,
  nenhum). O resto do sistema se adapta a isso, em vez de assumir.

### Intrusive Thoughts na arquitetura

- O **Terminal Host não interpreta o que é digitado**: só transporta bytes da PTY. Ele não
  sabe o que é um prompt.
- Quem emite `intrusive_thought` é o **Adapter** do provider, a partir do hook de submissão de
  prompt ou do transcript. Isso mantém a regra de que só os adapters conhecem o formato
  nativo.
- No Core, intrusive thoughts e `thought` entram na mesma linha do tempo por alter ego (base
  do Inner World) e alimentam o stat de intervenções humanas.
- `capabilities()` do adapter informa se consegue detectar intrusive thoughts. Se não, o
  Inner World mostra a lacuna, sem inventar.

---

## 4. Robustez

- **Validação na borda.** Todo dado vindo de hook, transcript, webhook ou probe é validado
  contra o schema antes de entrar. Dado inválido é descartado e registrado, nunca propagado.
- **Isolamento de falha.** Um adapter que quebra ou trava não afeta os demais nem o Core.
  Cada adapter roda isolado (processo/tarefa separada) com timeout e supervisão.
- **Degradação explícita.** Sem dados de um provider, o alter ego aparece como "sem sinal"
  e nunca com estado inventado. Nunca preencher lacuna com palpite.
- **Tolerância a formato.** Hooks e transcripts mudam entre versões dos CLIs. Parsers
  ignoram campos desconhecidos, detectam versão e falham com mensagem clara.
- **Reconexão.** Clients e adapters reconectam sozinhos; o Gateway reenvia o estado atual
  (snapshot) ao reconectar, sem exigir replay completo.
- **Sem estado oculto.** O estado do mundo é reconstruível a partir do log de eventos +
  fatos dos probes.
- **Observabilidade interna.** Logs estruturados por módulo e por `event_id`; contadores
  de eventos descartados, erros de parsing e latência de entrega.

---

## 5. Lógica bem estruturada

- **Domínio puro.** Estados do alter ego, altura do prédio, XP e stats são funções
  determinísticas: mesmos eventos de entrada → mesmo resultado.
- **Máquina de estados explícita.** Transições permitidas entre `IDLE`, `CODING`,
  `WAITING` etc. ficam em uma tabela única, não espalhadas em `if`s.
- **Dados antes de código.** Mapeamentos de evento nativo → estado universal são
  declarativos (tabela por adapter), não lógica embutida.
- **Injeção de dependência.** Relógio, sistema de arquivos e transporte são injetados,
  permitindo testar sem disco nem rede.

---

## 6. Estratégia de testes

| Camada | Como testar |
|---|---|
| Core / Domain | Testes unitários puros, incluindo propriedade (ex.: altura monotônica com LOC) |
| Adapters | **Fixtures reais** de hooks/transcripts gravados de cada CLI, versionados (golden files) |
| Protocol | Testes de contrato: todo evento emitido valida contra o schema |
| Gateway | Testes de integração com adapters falsos (fakes) |
| Terminal Host | Teste com processo de eco; teste manual por provider real |
| Clients | Renderizam a partir de um replay de eventos gravado, sem providers reais |

Um **simulador de eventos** (replay de sessões gravadas) permite desenvolver e testar o 3D
sem nenhum agente rodando.

---

## 7. Estrutura de pastas sugerida

```
orb-ia/
├── protocol/        # schemas e tipos dos eventos
├── core/            # domínio puro
├── adapters/
│   ├── claude/
│   ├── codex/
│   └── hermes/
├── probes/          # git, github, ci, loc
├── terminal_host/   # PTY por realm
├── gateway/         # FastAPI + WebSocket
├── clients/
│   ├── godot/       # Orb 3D
│   └── web_panel/   # painel 2D de validação
├── fixtures/        # sessões gravadas por provider/versão
└── docs/
```

### Estado atual: protótipos (spikes), ainda não esta estrutura

O código que existe hoje está em `spikes/` e é **descartável por desenho**: serviu para validar
riscos, não para ser a base final. Mapa de onde cada peça deve ir quando for promovida:

| Hoje (spike) | Vira |
|---|---|
| `spikes/01-terminal-host/terminal_host.py` (PTY, lista fixa de CLIs, limpeza de ambiente) | `terminal_host/` |
| `spikes/01-terminal-host/transcript_tail.py` (tail somente leitura do transcript do Claude) | `adapters/claude/` (nível 0) |
| `spikes/01-terminal-host/server.py` (WebSocket, token, Origin, validação de mensagens) | `gateway/` |
| `spikes/01-terminal-host/static/index.html` (xterm.js + painel de eventos) | `clients/web_panel/` |
| `spikes/02-terminal-godot/` (`bridge.gd`, `monitor3d.gd`) | `clients/godot/` |
| `spikes/03-live-hooks/probe.py` (receptor + `--settings` por sessão) | `adapters/claude/` (nível 1) |
| `spikes/04-codex/drive.py` (cliente JSON-RPC do app-server) | `adapters/codex/` |
| Fixtures geradas por `probe.py` e `drive.py` | `fixtures/` (golden files dos testes de adapter; **não versionadas**, pois contêm caminhos locais e dados da conta; regeneráveis) |

---

## 8. Decisões em aberto

- Como cada adapter é isolado: processo separado, tarefa assíncrona supervisionada, ou ambos.
- Onde vive o log de eventos no MVP (arquivo/SQLite) e quando migra para PostgreSQL/Redis.
- Mecanismo de versionamento dos schemas e política de migração.
- ~~Como embutir o terminal no Godot~~ **Decidido (Spike 2):** godot-xterm como componente de
  exibição; o **Terminal Host continua em Python** e o Godot conecta por WebSocket (opção B em
  [MVP.md](MVP.md) §7). Evita a limitação do ConPTY com stdio redirecionado e mantém um único
  host para web e Godot.
