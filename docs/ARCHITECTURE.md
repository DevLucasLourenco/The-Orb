# The Orb — Arquitetura

> Como o sistema se divide, os contratos entre as partes e as regras de engenharia de cada
> âmbito. Vocabulário: [CONTEXT.md](../CONTEXT.md) · Contrato de eventos: [PROTOCOL.md](PROTOCOL.md)
> · Decisões: [adr/](adr/).

Última atualização: 2026-10-13

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
| **Core** | `src/orb/core/` | O mundo: aplica eventos, deriva a atividade de cada personagem, Teams, pendências, Energy; snapshot; a sacola e o livro de nomes históricos (`names.py`) | Protocol | Adapters, Gateway, disco, rede, relógio |
| **Adapters** (claude, codex, hermes, opencode) | `src/orb/adapters/<provider>/` | Ler a fonte nativa do provider e produzir eventos (nativo + sinal + inner) pelo Mapa do provider | Protocol | Core, Gateway, outros adapters |
| **Terminal Host** | `src/orb/terminal_host/` | Abrir o terminal real (ConPTY), chamar o CLI (lista fixa), transportar bytes, limpar o ambiente herdado | nada do domínio | Core, adapters |
| **Gateway** | `src/orb/gateway/` | Autenticar, ligar terminal + adapter + Core por sessão, validar mensagens do cliente, distribuir por WebSocket; detectar os realms (`realms.py`) e decidir pasta → projeto (`projects.py`, a borda que conhece o disco) | todos, por interfaces | internals de adapters |
| **Registro local** | `src/orb/registry/` | O arquivo SQLite do próprio Orb (R36): hoje a associação sessão → nome e a sacola de nomes; implementa a interface `NameSource` do Core; a pasta do Orb (`paths.py`) | Core (só a sacola e a interface) | Adapters, Gateway, providers |
| **Clients** | `clients/` | Renderizar o mundo e o Inner World, enviar teclas | só as mensagens do Gateway | adapters, providers |
| **Probes** | `src/orb/probes/` | Fatos do mundo real, só leitura. **Feito (ticket 09):** o contador de linhas (`lines.py`). Depois: git (alterações locais), CI | só o que o chamador passa (o filtro é `orb.core.rules.LineFilter`) | adapters, Gateway |

### Regras de dependência

- Dependências apontam para **Protocol** e **Core**, nunca o contrário. O Core não importa nada
  além do Protocol.
- **Adapters não importam uns aos outros.** O que eles compartilham é genérico e fica em
  `src/orb/adapters/_shared/` (fábrica de eventos, leitura incremental de JSONL, leitura somente
  leitura de SQLite, classificador de comandos de shell, `SessionMeta` do índice de sessões), sem
  conhecimento de provider.
- **Adicionar um provider = adicionar um adapter** (`mapping.py` + leitores), sem tocar em Core,
  Gateway ou clientes ([ADR 0002](adr/0002-eventos-nativos-por-provider.md)).
- Clientes nunca falam com adapters ou providers; só com o Gateway.
- **Somente leitura por desenho.** Adapters e Probes só abrem arquivos do provider e do projeto
  em modo leitura. A única escrita nos arquivos de terceiros é o Terminal Host transportando o que o
  Lucas digita ([VISION.md](VISION.md) §3, princípio 5); o Orb só grava nos **próprios** arquivos: o
  registro local (R36) e, depois, as preferências (R29).
- **Nenhum módulo chama modelo de IA** (R38): o Orb não consome tokens. Papel, nomes,
  classificações e resumos saem de regras e tabelas sobre a telemetria.
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
| Índice de sessões | Objeto com `scan() -> list[SessionMeta]` (`_shared/index.py`): metadados de **todas** as sessões do provider (pasta, raiz do projeto que ele informa, sessão-mãe, datas, título, modelo), sem abrir o conteúdo e somente leitura (R48, camada 1) |
| Leitor nível 1 *(opcional)* | Hooks por sessão (Claude) ou observador de app-server (Codex) |
| `mapping.py` | O Mapa do provider: tabelas declarativas de evento nativo → `signal`/`inner` |

### Core

- `World.apply(event) -> bool` aplica um evento (falso se repetido ou inválido) e
  `World.snapshot(now) -> dict` devolve o estado para os clientes. **Feito (ticket 01, D-086, R47):**
  `now` (com fuso) é a hora de quem pede; com ela o mundo deriva o que depende do tempo e os limites
  ficam numa tabela de `rules.py`: `asleep` no Alter Ego (parado há mais de 15 min, ou encerrado) e
  `no_signal` no subagente (ativo, sem atividade há mais de 5 min; o estado vira `NO_SIGNAL`, a área é
  a do último estado conhecido, e ele deixa de manter o líder em `DELEGATING`) e `active_subagents`
  (os sabidamente ativos). `World.time_key(now)` diz o que só o tempo muda, e o Hub acrescenta
  `generated_at` (a hora do servidor) ao snapshot. Sem `now`, nada que
  dependa do tempo é afirmado. Faltam, para os tickets seguintes, "noite" (06) e "hoje" (20).
- **Decidido (D-085):** o Core guarda também estado **por realm** (métricas, alterações locais,
  Weather) e **do mundo** (limites da conta), vindo de eventos com `alter_ego: null` (protocolo 0.3).
- **Decidido (D-099):** o mundo também calcula, em Python, o **traçado da cidade** (bairros, lotes,
  deslocamento pela semente do nome; VISUAL.md §7), a **classe e os andares** de cada prédio (§8) e a
  **fachada** (as janelas por percentual; §6). O cliente recebe isso pronto no snapshot e só desenha.
- Puro: tempo vem do `ts` dos eventos e do `now` recebido; nenhuma chamada a disco, rede ou relógio.
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

- **Observatório** (`orb.gateway.realms.Observatory`): observa os **4 providers ao mesmo tempo**.
  Qualquer sessão numa pasta de realm **ou subpasta dela** (worktrees), aberta pelo Orb ou fora
  dele, vira um Alter Ego que carrega o seu provider. Os realms são **detectados** pelo índice de sessões
  dos quatro CLIs ([Detecção de realms](#detecção-de-realms-pelos-providers-ticket-03)); `--root` e `--realm`
  só existem para depurar.
  - **Um leitor por provider para a cidade inteira**, que distribui as sessões pelos realms perguntando ao
    Observatório (`realm_of`: projeto da pasta, sem confundir "trisafe" com "trisafe-enhanced"). O Claude
    guarda uma pasta por projeto, e o leitor identifica cada uma pelo `cwd` gravado no transcript.
  - A falha de um leitor ou de um índice não afeta os outros (fica em `errors`).
- **`Hub`**: um laço único lê todos os realms (fora do loop, `to_thread`), aplica no Core, guarda as
  últimas linhas de Inner World por sessão (`Feed`) e distribui aos clientes. É a borda que conhece a
  hora (relógio injetável): pede o mundo ao Core com a hora do servidor e, a cada 15 s, reavalia o que
  só o tempo muda (quem dormiu, quem ficou sem sinal) e avisa os clientes sem esperar um evento novo.
- `/world?token=…`: o mundo para o cliente 3D — snapshot, depois `event` (linhas de Inner World),
  `world` (snapshot quando algo muda), `feed` (linhas de uma sessão, sob pedido) e `history` (Histórico do realm, sob pedido).
- `/ws?token=…&realm=…&provider=…&model=…`: abre o terminal real de uma sessão nova num realm e
  devolve `term`, `exit`, `system` (com o `alter_ego` quando o Orb escolhe o id, no Claude).
- Segurança: escuta só em `127.0.0.1`, token por execução, `Origin` local obrigatória, lista fixa
  de executáveis.
- `handle_client_message(term, raw)` valida cada mensagem e **nunca levanta**.

### Detecção de realms pelos providers (ticket 03)

Regra R3 ([RULES.md](RULES.md)): **o Lucas não informa caminhos.** A cidade se monta sozinha a
partir do que os providers já gravam. Um realm existe porque algum provider tem uma sessão naquele
projeto.

**Como (implementado no ticket 03):**

1. **Índice de sessões (R48, camada 1).** Cada adapter tem uma classe de índice com `scan()` que lista
   **todas** as sessões do provider, sem filtro por pasta e **sem abrir o conteúdo** (`SessionMeta`:
   provider, id, pasta, raiz que o provider informa, sessão-mãe, datas, título, modelo). O Observatório
   varre os quatro a cada 30 s; a falha de um índice fica em `errors` e não derruba os outros.

   | Provider | Onde está a pasta da sessão | Raiz do projeto dada pelo provider | Custo (medido em 2026-10-13) |
   |---|---|---|---|
   | Claude (`TranscriptIndex`) | Campo `cwd` das primeiras linhas de um transcript da pasta; uma pasta por projeto em `~/.claude/projects/` | — | Uma leitura por pasta; datas vêm do arquivo (título e modelo exigem abrir o conteúdo e ficam para as sessões da sala) |
   | Codex (`RolloutIndex`) | `session_meta.cwd` (1ª linha do rollout, lida **uma única vez** por arquivo) | — (`session_meta.git` traz branch, commit e URL, não a pasta) | 428 rollouts: ~5 s na primeira varredura, ~20 ms nas seguintes |
   | Hermes (`StateDbIndex`) | `sessions.cwd` no `state.db` | `sessions.git_repo_root` (vazio em todas as sessões desta máquina) | Uma consulta à tabela `sessions`, sem tocar em `messages` |
   | opencode (`OpencodeDbIndex`) | `session_v2.directory` no `opencode.db` | ~~`project.worktree`~~ (a spec previa lê-la; o Orb não lê a tabela `project`: o banco guarda credenciais e só `session_v2` e `session_message` são lidas; D-129) | Uma consulta, só `session_v2` |

2. **Pasta → projeto** (`gateway/projects.py`, `ProjectResolver`; só lê arquivos, nada é executado nem gravado).
   Vence a raiz que o provider informa, se ela contém a pasta. Senão, sobe da pasta até o repositório git
   (`.git` como pasta é o repositório; como arquivo, `commondir` leva ao repositório **principal**, que é o
   projeto de um worktree; sem `commondir` é um submódulo e a pasta é o projeto). Fora de um repositório, a
   própria pasta da sessão é o projeto, mas uma subpasta de um realm já conhecido entra nele (D-133).
   **Ficam de fora (R3b, R3d):** a pasta do usuário em si (não as subpastas), `AppData` e `Downloads` do
   usuário, as pastas temporárias (`TEMP`, `TMP`, `TMPDIR`, a do Python e `/tmp`), as de sistema (`SystemRoot`,
   `ProgramFiles`, `ProgramFiles(x86)`, `ProgramData`), a raiz do disco e qualquer pasta que não exista mais
   (D-130). A subida para antes de qualquer pasta excluída: um repositório de dotfiles na pasta do usuário
   não engole os projetos abaixo dele. Um worktree cujo repositório principal sumiu também não entra.
3. **Projeto → realm.** O id é o nome da pasta do projeto (`trisafe-enhanced`); a comparação de caminhos
   é por segmento, então "trisafe" nunca captura "trisafe-enhanced". Dois projetos com o mesmo nome em lugares
   diferentes ganham sufixo (`app`, `app-2`): num mesmo lote vale a ordem dos caminhos, e **quem já está na cidade
   nunca muda de id** (D-131). Uma pasta de sessão que já não existe (ex.: worktree apagado) entra no realm
   conhecido que a contém; sem ele, não entra.
4. **Descoberta contínua.** Sessão de um projeto novo cria o prédio na hora (o leitor pergunta ao
   Observatório) ou, no mais tardar, na próxima varredura do índice. O **conteúdo** é lido de forma
   incremental só das sessões da **sala** (R28a, ticket 06): as escritas nos últimos 10 dias
   (`rules.RECENT_SESSION_SECONDS`, um só valor; `--lookback` [depuração] só o estreita). O que já existia antes do Orb abrir é lido só
   do fim (`fresh_after`: só as criadas nos últimos 30 min são lidas desde o começo); o passado fica para a camada de histórico
   (R48, ticket 25). A cidade mostra todos os projetos, e a sala só as sessões da janela. Cada provider tem **um** leitor
   para a cidade inteira; o do Claude identifica cada pasta de `~/.claude/projects/` pelo `cwd` gravado nela.
5. **A sala, o Histórico do realm e a noite (ticket 06, R28a, D-059).** O Core marca cada Alter Ego com `in_room`
   (último evento nos últimos 10 dias, pela hora recebida) e cada realm com `night` (nenhuma sessão na sala; `World.add_realm`
   cria o realm mesmo sem sessão). Cada sessão da sala que o índice lista ganha **um evento de presença** (`session.updated`,
   só identidade: título, modelo, pasta; hora = última atividade): o Hermes e o opencode só falam quando há mensagem nova.
   As sessões mais antigas ficam só no índice: o **Histórico do realm** é pedido pelo cliente no `/world`
   (`{type: "history", realm}` → `{channel: "history", sessions, total}`, até 1000 por pedido com o `total` junto (nada é escondido sem aviso), mais recentes primeiro; o nome histórico
   só aparece se a sessão já ganhou um, `NameSource.name_of`). Nada some.
6. **Hora de abertura (D-128).** Os eventos que abrem uma sessão ou um subagente do Claude levam a hora da
   **última escrita do arquivo** (e os do Hermes, a da mensagem que revelou a sessão), nunca a hora da leitura:
   um subagente antigo nasce já sem sinal, em vez de parecer "recém-ativo" por 5 min (D-132).
7. `--root`, `--realm` e `--lookback` ficam só como **opções de depuração** (o servidor sobe sem nenhum
   argumento); o que for preferência do Lucas vai para a tela de configurações do Orb (R29).

**Limites conhecidos:** um realm cuja pasta é apagada com o Orb aberto só sai da cidade na próxima vez que o servidor
subir; o id de um realm com nome repetido depende da ordem em que os projetos entraram (o registro local, R36, vai
fixá-lo).

**Alterações locais dos arquivos (janelas, R20b).** O estado do repositório (arquivo modificado,
novo, apagado…) é lido **sem gravar nada**: nem no projeto, nem no `.git` (R16). Um `git status`
comum pode atualizar o índice; se o git for usado, só com `--no-optional-locks`. Como ler (rodar o
git só em leitura ou ler os arquivos do `.git`) é decisão de implementação, a registrar quando o
ticket existir.

**Questões em aberto (decidir antes dos tickets):**

| Id | Pergunta |
|---|---|
| D-REALM-1 | ~~Quais realms aparecem?~~ **Decidido (2026-10-07): todos os projetos que algum CLI já registrou (R3a).** Nesta máquina: ~40 pastas (Codex 33, Claude 7, Hermes 7, opencode 2, com sobreposição). Consequência: a descoberta de realms lê os **metadados** de todo o histórico (pasta de cada sessão), não o conteúdo; o conteúdo continua lido de forma incremental. |
| D-REALM-2 | ~~Sessões fora de projeto?~~ **Decidido: ignoradas (R3b).** ~~Critério?~~ **Decidido (2026-10-08): a pasta do usuário em si e pastas de sistema/temporárias (`AppData`, `Temp`, `Downloads`) são ignoradas; qualquer outra pasta é projeto.** |
| D-REALM-3 | **Realm sem sessões há muito tempo:** pela D-REALM-1 ele continua na cidade; o Lucas o esconde pela lista (R3c). ~~Aparência?~~ **Decidido (2026-10-08, D-059): "noite", a sala do teto apagada quando não há sessão nos últimos 10 dias.** |
| D-REALM-4 | ~~Esconder/fixar um realm?~~ **Decidido: uma lista com todos os realms, com marcação; desmarcar esconde (R3c).** Fixar não foi pedido. |
| D-REALM-5 | ~~Persistência local do Orb?~~ **Decidido (2026-10-08): um arquivo de preferências próprio do Orb (R29)**, nunca dos providers, editado pela tela de configurações do Orb: realms escondidos (R3c), prazo das sessões recentes (R28a) e o que vier. Local proposto: `%LOCALAPPDATA%\the-orb\` no Windows (`~/.the-orb/` nos outros). Em aberto: se também guarda a posição dos prédios (V-PEND-5). |
| D-REALM-6 | ~~Pasta de projeto que não existe mais no disco?~~ **Decidido (2026-10-08): não entra (R3d).** |

### Módulos novos decididos (2026-10-08 e 2026-10-09), ainda sem implementação

- **Weather local** (R42, D-076): deriva o resultado dos testes das sessões, a partir dos eventos
  que os adapters já produzem (comando classificado como teste + o sinal `command.result` do
  protocolo 0.3, D-084). A forma de obter o código de saída varia por provider (ex.: `exitCode` no Codex,
  resultado com erro no Claude) e se confirma na implementação. Sem rede; o CI do GitHub é um
  Probe opcional, futuro, só leitura.
- **Energy** (R43, D-077): soma no Core os `usage` que os providers informam, por sessão, realm e
  dia; nunca estima custo.

- **Leitor de diálogos** (R34, D-060): separado do Terminal Host (que só transporta bytes e não
  interpreta o que o CLI imprime). Só nas sessões abertas pelo Orb, lê a tela do terminal e
  reconhece diálogos **conhecidos** (tabela por provider: atualização, confiança de diretório,
  revisão de hooks…). Ao reconhecer, emite um sinal de espera; **nunca envia teclas**
  ([ADR 0006](adr/0006-o-orb-nunca-responde-dialogos.md)).
- **Registro local do Orb** (R36, D-062): SQLite na pasta de preferências do Orb, com o que o Orb
  derivou (eventos do mundo para o Chronicle, associação sessão → nome histórico, preferências).
  Nada do conteúdo das sessões é copiado; ele continua nos providers. **Feito (ticket 04):** pacote
  `orb.registry`; arquivo `registry.db` em `%LOCALAPPDATA%\the-orb\` (`orb_home()`; fora do Windows,
  `$XDG_DATA_HOME` ou `~/.local/share`), com `PRAGMA user_version` para as migrações. Tabelas de hoje:
  `names` (id do Alter Ego → nome) e `bag` (os nomes que restam, na ordem em que saem). Cada sorteio é uma
  transação `BEGIN IMMEDIATE` (dois Orbs abertos não repetem o nome). O Core não conhece o disco: o
  `World(names=...)` recebe um `NameSource` (`name_for(id, avoid)`), e o Gateway entrega o
  `LocalRegistry` (ou, sem pasta do Orb, o `NameBook` em memória). **Falha de disco** (pasta sem
  permissão, arquivo corrompido, banco travado, registro de um Orb mais novo): os nomes vêm de uma cópia em
  memória que segue a mesma sacola; o disco é tentado de novo a cada pedido (uma falha passageira não desliga
  o registro); o arquivo nunca é apagado nem alterado, e `/config` informa o motivo em `registry_error`
  (nenhuma tela mostra isso hoje). Quem sorteia espera o banco por até 5 s, na thread de leitura (`to_thread`).
- **Preferências do Orb** (R29, D-030, D-032; ticket 07): `preferences.json` na pasta do Orb (`orb_home()`), JSON legível com
  `version`, gravado de uma vez (arquivo temporário e troca). Hoje guarda `hidden_realms` (os projetos escondidos, **pelo caminho**
  normalizado: o id pode mudar, o caminho não) e `recent_days` (1 a 365, padrão 10). As opções numéricas ficam na tabela
  `SETTINGS` (`registry/preferences.py`): a tela é montada a partir dela, então os tickets 09 e 11 só acrescentam linhas;
  opções que esta versão não conhece são guardadas como estão. Arquivo ilegível: valem os padrões, `error` diz o motivo e o arquivo é copiado
  para `.bad` antes de ser reescrito. No `/world`: `{type: "settings"}` devolve `{channel: "settings", realms, options, preferences, error}`
  e `{type: "preferences", hidden_realms?, recent_days?}` valida, grava (fora do loop), aplica na hora (`Hub.update_preferences`) e
  republica `settings` e a cidade para **todos** os clientes; valor inválido volta como `error` só a quem pediu e nada é gravado.
  Eventos e linhas de Inner World de um realm escondido não são distribuídos; os caminhos escondidos de projetos que o Orb não detecta
  agora são mantidos no arquivo; sem pasta do Orb a tela avisa que as mudanças valem só até fechar. Realm escondido (`World.set_hidden`)
  sai do snapshot (cidade e Mankind) e continua detectado e lido.
- **Contador de linhas** (R19, D-053 a D-056; ticket 09): faz parte dos Probes; conta linhas não vazias dos
  arquivos acompanhados pelo git, sem os ignorados e sem os gerados da lista de exclusões, e
  recalcula ao abrir e quando as alterações locais mudam (até 1×/min por realm). Somente leitura. **Como funciona:** a lista
  vem do `git ls-files` (com `--no-optional-locks`, nunca grava no `.git`); link, pasta (submódulo), binário (UTF-16 com BOM conta como texto) e arquivo de mais de 2 MB
  ficam de fora; o git roda sem as variáveis `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE`, com `core.fsmonitor=false` e sem entrada; sem repositório ou sem git, o realm fica **sem número** (nunca um zero) e a tela de configurações diz o motivo (`lines_note`). O Probe separa listar (barato), identificar
  mudança (`fingerprint`: arquivos que contam, tamanho, data e filtro) e contar (lê os arquivos). `gateway/probes.py` (`LineScheduler`)
  roda numa **thread própria, um realm por vez**, e devolve um evento `realm.metrics` que o Hub aplica no mundo (mudou o filtro: o realm
  afetado é contado já, na frente dos outros). O Core guarda o estado por realm (`World.metrics`) e deriva a classe (`rules.building_class`).
  O filtro (`include_markdown`, `exclude`) fica nas preferências, geral e por realm, e a tela de configurações o edita.

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
| Polling (nível 0) | **250 ms** para realms com sessão ativa (medido: ~270–470 ms ponta a ponta); varredura de sessões novas a cada **2 s** (D-087). **Feito (ticket 06):** `POLL_SECONDS` = 250 ms quando alguma sessão da sala está ativa (`World.any_active`); sem nenhuma, `IDLE_POLL_SECONDS` = 2 s (granularidade do mundo todo, não por realm: D-142) |
| Histórico (R48, D-088) | **Duas camadas:** índice de metadados de todas as sessões (pasta, datas, título, provider), barato; conteúdo lido incrementalmente só das sessões da sala; o passado lido uma vez em segundo plano, com o ponto de parada no registro local |

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
| Core | Unitários puros: atividade, Team, `WAITING`, dedupe, snapshot, nome do Alter Ego | `tests/test_core.py` |
| Adapters | Linhas/notificações/bancos com a forma verificada (spikes, esquema oficial do Codex, estrutura dos bancos reais) | `tests/test_adapter_{claude,codex,hermes,opencode}.py` |
| Classificador de comandos | Tabela de casos | `tests/test_commands.py` |
| Terminal Host | PTY falsa (sempre) + terminal real (quando `pywinpty` e o CLI existem) | `tests/test_terminal_host.py` |
| Gateway | Validação de mensagens; app com terminal falso | `tests/test_gateway.py` |
| Probes e estado por realm | Pasta de projeto falsa → linhas (arquivos, filtro, binário, link, git real quando instalado); quando contar (relógio falso); realm.metrics → classe no mundo | `tests/test_probes.py`, `tests/test_line_scheduler.py`, `tests/test_realm_metrics.py` |
| Preferências | Arquivo numa pasta temporária (grava, relê, opção desconhecida, arquivo ilegível); realm escondido no mundo e no Hub; tela pelo `/world` | `tests/test_preferences.py`, `tests/test_realms.py` |
| Nomes e registro local | Sacola e livro de nomes sem disco; registro numa pasta temporária (reabrir, falhas de disco) | `tests/test_names.py`, `tests/test_registry.py` |
| Detecção de realms (as leituras do mundo real) | Pastas de CLIs e de projetos falsas → realms; regras de pasta → projeto; índice de sessões | `tests/test_realms.py`, `tests/test_projects.py`, `tests/test_session_index.py` (arquivos falsos em `tests/fakes.py`) |

**Pontos de teste (D-099).** O principal é o mundo: eventos sintéticos + uma hora → estado do mundo
(inclui tempo, papel, tarefas, Weather, Energy, XP, cidade, fachada e classes). Os outros dois são os
leitores dos CLIs (arquivos e bancos sintéticos → eventos) e as leituras do mundo real (pasta de
projeto ou de CLI falsa → eventos: git, linhas de código, detecção de realms). O cliente web não tem
lógica de domínio para testar.

Fixtures **reais** (golden files) são geradas pelos scripts de `spikes/03-live-hooks` e
`spikes/04-codex` e **não são versionadas** (contêm caminhos locais, prompts e dados da conta).
Os testes versionados usam amostras mínimas com a forma verificada, sem dados reais.

Rodar: `python -m pytest -q` na raiz.

## 8. Estrutura de pastas

```
The Orb/
├── README.md · CONTEXT.md · CLAUDE.md · pyproject.toml
├── docs/
│   ├── RULES.md · VISUAL.md · DECISIONS.md · PROGRESSION.md
│   ├── VISION.md · ARCHITECTURE.md · PROTOCOL.md · MVP.md · SPIKES.md · IDEAS.md
│   ├── adapters/   CLAUDE.md · CODEX.md · HERMES.md · OPENCODE.md
│   └── adr/        decisões numeradas
├── src/orb/
│   ├── protocol/        events.py · vocab.py
│   ├── core/            world.py · rules.py · names.py
│   ├── registry/        store.py · preferences.py · paths.py
│   ├── probes/          lines.py
│   ├── adapters/
│   │   ├── _shared/     base.py · commands.py · index.py · jsonl.py · sqlite.py
│   │   ├── claude/      mapping.py · transcript.py · index.py · hooks.py
│   │   ├── codex/       mapping.py · app_server.py · rollout.py · index.py
│   │   ├── hermes/      mapping.py · state_db.py · index.py
│   │   └── opencode/    mapping.py · state_db.py · index.py
│   ├── terminal_host/   launch.py · env.py · terminal.py
│   └── gateway/         app.py · messages.py · realms.py · projects.py
├── clients/
│   ├── web/             o mundo 3D: index.html, styles.css, js/ (scene, realm3d, avatar, hud, innerworld, net)
│   └── godot/           terminal remoto (alternativa; godot-xterm só exibe)
├── tests/               (tests/governance/: testes das skills de acompanhamento)
├── tools/governance/    hook opcional de fechamento das entregas (skill delivery-summary)
├── .claude/skills/      delivery-summary e phase-overview (acompanhamento; não fazem parte do produto)
├── .scratch/            spec e tickets (rastreador local, D-098)
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
- ~~Onde vive o log de eventos (arquivo/SQLite) e quando entra um banco.~~ Decidido: registro local
  do Orb em SQLite (R36).
- Receptor de hooks do nível 1 como processo separado, sempre responsivo.
- Nível 1 de Hermes (sidecar da TUI) e opencode (servidor próprio).
