# Orb IA — CONTEXT

> Glossário canônico e visão do projeto. Fonte da verdade para vocabulário: se um termo
> muda de significado, atualize este arquivo primeiro. Código, API e UI devem usar
> estes termos exatamente como definidos aqui.

Última atualização: 2026-10-06

---

## 1. Visão

**Agent World** (nome de trabalho): um jogo 3D visto de cima (estilo RTS / colony-management,
câmera livre) que representa em tempo real o trabalho **real** de agentes de IA
(Claude Code, Codex, Hermes) nos projetos reais do Lucas.

Os agentes continuam trabalhando de verdade nos repositórios. O mundo 3D apenas **observa
os eventos** e os transforma em comportamento visual. Mais tarde, também **controla**
(mensagem, pausa, aprovação, delegação).

Em uma frase: **projetos reais → agentes reais → telemetria real → mundo virtual.**

**O 3D é o foco do projeto.** Não é um complemento de um dashboard: o mundo 3D é o produto.
Painéis 2D existem para apoiar (e para validar a telemetria na etapa 3 do roadmap), mas a
experiência principal é navegar o Orb.

**O Orb também é o centralizador.** Entrando em um realm, o Lucas usa ali dentro os mesmos
agentes que já usa: para cada modelo que tem CLI (Claude, Codex, Hermes e os que vierem), ele
abre um terminal no próprio Orb com o CLI real daquele agente, no contexto do projeto. Tudo
em um só lugar, com o chat/terminal de cada Alter Ego e o pensamento dele visível.

No fim, o Orb é um **grande centralizador de IAs e de seus agentes e subagentes**: um só lugar
para ver o que cada um faz e para falar com eles, por três portas que desembocam no mesmo
terminal: o **terminal** do Alter Ego (usar o CLI), o **Intrusive Thought** (o que o Lucas
planta nele) e o **Gate** (enviar de um ponto central, sem entrar no realm).

### Hierarquia

```
Orb  (o mundo: uma cidade conceitual)
 └── Realm  (um projeto = um prédio)
      └── Rooftop Room  (o quartinho no teto onde as LLMs trabalham)
           └── Team  (um Alter Ego principal + seus subagentes)
                └── Alter Ego  (a persona de cada LLM; o principal lidera a Team)
                     └── Subagente  (unidade temporária)
```

**Mankind** (a sociedade das IAs) é a população que habita o Orb.

Natureza do projeto: híbrido de RTS + Digital Twin + Agent Orchestration Platform
(um "Agent Control Plane" gamificado).

### Princípios

1. **Telemetria real, nunca animação inventada.** O mundo só mostra o que veio de um evento
   observado. Nada de IA "imaginando" o que talvez esteja acontecendo.
2. **Realidade confirmada por fontes externas.** "Agente disse que terminou" ≠ "terminou".
   Git, GitHub e CI confirmam o que de fato mudou, passou ou quebrou.
3. **Neutro de provider.** O mundo nunca conhece eventos específicos de Claude/Codex/Hermes.
   Adapters traduzem para um protocolo próprio.
4. **Conceito com significado técnico.** Cada conceito deste glossário tem equivalente
   técnico e é usado no código. Nomear só o que o MVP já usa.
5. **Fidelidade explícita.** Tudo que a UI mostra como "pensamento" declara o quão fiel é.
6. **CLI nativo, nada criado do zero.** O Orb **não cria TUI nem terminal próprios**. Ele abre
   um terminal real (PowerShell) e, dentro dele, **chama o CLI original** (`claude`, `codex`
   ou `hermes`), escolhido automaticamente pelo provider/modelo do Alter Ego. O CLI roda com
   todas as funcionalidades dele; quando fecha, o terminal continua aberto. O Orb só observa.
   (O componente que desenha o terminal na tela, como o xterm.js, é um emulador pronto, não uma
   interface criada pelo projeto.)
7. **Modularização.** Cada responsabilidade vive em um módulo com fronteira clara e contrato
   explícito. Módulos se comunicam só por contratos (protocolo de eventos, interfaces), nunca
   por conhecimento interno um do outro. Detalhes em [ARCHITECTURE.md](ARCHITECTURE.md).
8. **Robustez.** Formatos externos (hooks, transcripts, streams) mudam e falham. Entrada
   externa é sempre validada, falha em um provider nunca derruba os outros, e o sistema
   degrada de forma explícita (mostra "sem dados", nunca inventa).
9. **Lógica bem estruturada.** Domínio puro separado de I/O. Regras (estados, altura do
   prédio, XP) são funções determinísticas e testáveis, sem depender de rede, disco ou UI.
10. **Não interferência.** O Orb **não altera em nada** como os modelos funcionam nos
    projetos. Tudo que molda o comportamento do agente (`CLAUDE.md`, skills, arquivos de
    memória, contexto, configurações) é **somente leitura** para o Orb. Hooks do Orb são
    apenas observadores: nunca devolvem decisão nem contexto adicional. A **única porta de
    escrita** é o Intrusive Thought, isto é, o Lucas escrevendo no terminal de um Alter Ego,
    digitando nele ou enviando pelo Gate (que escreve nesse mesmo terminal). Qualquer "controle"
    do painel (enviar mensagem, aprovar, pausar) acontece escrevendo nesse terminal, nunca
    por um canal paralelo. O Orb torna as coisas **visuais**, não as modifica.
    **Decisões do Lucas são dele:** o Orb nunca responde por ele os diálogos dos CLIs
    (atualização, confiança de diretório, confiança de hooks, aprovações de comando). Isso
    inclui automação e testes: nenhuma tecla é enviada a uma TUI sem a tela verificada.

---

## 2. Glossário de conceitos

| Conceito | Significado | Equivalente técnico | Estado |
|---|---|---|---|
| **Orb** | O mundo de onde os realms estão. Uma cidade conceitual que contém todos os projetos. | Cena 3D raiz + coleção de realms | MVP |
| **Mankind** | A sociedade de IAs como um todo: todos os agentes de todos os providers, em todos os realms. | Conjunto global de agentes e sessões | MVP |
| **Realm** | Um projeto do mundo real, representado como um prédio no Orb (TriSafe, CLARA, UTC CONECTA+, SIG Forms). | Projeto / repositório | MVP |
| **Rooftop Room** *(nome provisório)* | O quartinho no teto do prédio onde as LLMs daquele realm trabalham. | Local de presença/atividade dos alter egos de um realm | MVP |
| **Environment** | O ambiente onde os agentes agem dentro de um realm: áreas funcionais, ferramentas, estações e regras. | Workspace, ferramentas, permissões | MVP |
| **Alter Ego** | A persona persistente de um agente (ex.: "Atlas"). É a identidade; o provider é só o corpo. | Entidade `AlterEgo` com identidade, papel, histórico e stats | MVP |
| **Inner World** | O pensamento de cada IA enquanto trabalha, visível ao entrar no alter ego. | Stream de eventos `thought` + plano + contexto | Definido; implementar após telemetria básica |
| **Archive** | A memória do Alter Ego, só para ver: contexto, skills, `CLAUDE.md` e arquivos de memória que moldam o agente. | Leitor somente leitura + evento `archive.snapshot` | Camada viva |
| **Gate** | O portão central do Orb: mostra tudo que espera o Lucas (aprovações pendentes de todos os realms) e permite enviar prompts a qualquer Alter Ego. | Visão derivada de `approval.requested` sem `approval.resolved` + envio por `terminal.write` | Camada viva |
| **Team** | O Alter Ego principal e seus subagentes, vistos como uma equipe. | Agrupamento derivado de `parent` nos eventos | Camada viva |
| **Chronicle** | A história do Orb: replay da cidade no tempo (prédios crescendo, agentes nascendo). | Log de eventos + histórico do git, reproduzíveis | Camada viva |
| **Weather** | O clima de cada realm, refletindo a saúde dele (CI, testes). | Estado derivado de `ci.*` e `test.*` | Camada viva |
| **Energy** | Recursos que o Orb consome: tokens e custo por realm e por Mankind. | Evento `usage.reported` (tokens/custo) | Camada viva |
| **Intrusive Thoughts** | O ato de o Lucas usar um CLI: tudo que ele digita ao agente entra no Inner World do Alter Ego como um pensamento que não nasceu dele. | Evento `intrusive_thought` | MVP |

### Mankind
A sociedade das IAs. É o nível mais alto da hierarquia e o que a visão de "zoom distante"
representa. Estatísticas globais (agentes ativos, tarefas, bloqueios) pertencem a Mankind.

### Orb
O mundo que contém os realms. Visualmente, uma **cidade** (conceitual, não só urbana), vista
de cima com câmera livre. É a cena raiz do 3D e a vista "zoom distante" de Mankind.

### Realm
Cada projeto real é um realm, e no Orb **cada realm é um prédio**. Pode ter aparência
temática própria (ex.: TriSafe como centro operacional/industrial, CLARA como
biblioteca/arquivo, UTC CONECTA+ como estação de comunicação). O objetivo é reconhecer onde
há trabalho só olhando a cidade.

**Altura do prédio = tamanho do código.** O prédio é tão alto quanto a quantidade de linhas
de código (LOC) do projeto. Assim, o skyline do Orb mostra o peso de cada realm.

- **Sempre ignora o que está no `.gitignore`** do projeto (`node_modules`, builds, venvs,
  arquivos gerados etc.). Regra fixa, não configurável.
- Contagem de linhas **filtrável** sobre o que sobra: incluir ou não `.md` (e outros tipos de arquivo).
- A altura reflete a realidade do repositório (princípio 1): é calculada, nunca arbitrada.

### Rooftop Room
No teto de cada prédio fica um quartinho onde as LLMs daquele realm trabalham. Ele contém
todas as áreas funcionais do Environment (ver abaixo), obrigatoriamente. É onde o
Alter Ego "mora" e onde a atividade em tempo real do realm é lida de longe: ao olhar a
cidade de cima, os quartinhos nos tetos são a camada viva do Orb.

### Environment
O que existe *dentro* de um realm e define onde cada ação acontece. As áreas funcionais
abaixo são **obrigatórias e existem em todo Rooftop Room**, sem exceção, mesmo que o realm
nunca use alguma delas. Assim todo quartinho tem a mesma anatomia e qualquer ação de
qualquer agente tem sempre um lugar para acontecer:

| Área | Ação real que a representa |
|---|---|
| Development Center | Write / Edit de código |
| Testing Lab | Execução de testes |
| Research Center | Web search, MCP, leitura de documentação |
| Code Review | Revisão, PR |
| Task Board | Conclusão de tarefas / missões |

### Alter Ego
- Separado do LLM: o mesmo alter ego pode passar de Claude para Codex sem mudar de personagem.
- Campos mínimos: `id`, `name`, `provider`, `model`, `role`, `realm`, `session`, `state`.
- Stats e nível (XP) **só** são calculados com histórico real (testes falhos, PRs aprovados,
  tarefas refeitas, tokens, tempo médio, intervenções humanas). Nunca inventados.
- Subagentes são **unidades temporárias** nascidas de um alter ego pai: recebem missão,
  executam, retornam e são desmobilizadas.

### Inner World
O que cada IA "pensa" enquanto trabalha. Limitação técnica importante: **o raciocínio interno
nem sempre é exposto pelos providers.** O Inner World é uma *reconstrução do que o agente
deixa observável* (plano, narração, ferramentas escolhidas, o que leu, o que decidiu), não
acesso literal ao pensamento.

Verificado no Claude Code: nos transcripts reais, o texto do bloco de thinking vem **vazio em
cerca de 88% dos casos** (só a assinatura é gravada). Então `raw` será raro e o Inner World
precisará se apoiar em narração, plano, ferramentas e intrusive thoughts. Detalhes em
[ADAPTER-CLAUDE.md](ADAPTER-CLAUDE.md).

Por isso todo evento `thought` carrega um campo `fidelity`:

| Fidelity | Significado |
|---|---|
| `raw` | Texto de raciocínio exposto pelo provider, sem alteração |
| `summary` | Resumo de raciocínio fornecido pelo provider |
| `inferred` | Reconstruído por nós a partir de ações/eventos observados |

A UI nunca apresenta `inferred` como pensamento real.

Ideia visual: clicar no alter ego e "mergulhar" nele. O cenário vira o mundo interno
(plano como mapa mental, arquivos lidos como objetos, dúvidas como nós abertos).

### Intrusive Thoughts
Usar um CLI é, no vocabulário do Orb, plantar um **intrusive thought**: o Lucas escreve no
terminal e aquilo entra na cabeça do Alter Ego vindo de fora. É o outro lado do Inner World:
os `thought` são o que o agente pensa; os `intrusive_thought` são o que o humano injeta.

- Inclui: prompts enviados, interrupções e comandos dados ao agente.
- Aprovações e negações de ações (`approval.resolved`) são uma interação relacionada, mas
  ficam como tipo próprio.
- No Inner World aparecem em linha com os pensamentos do agente, marcados como vindos de fora,
  o que mostra o efeito de cada intervenção humana no raciocínio que veio depois.
- No 3D, a ideia é visualizar o pensamento "chegando" ao Rooftop Room (forma visual em aberto).
- Intervenções humanas alimentam stats reais do Alter Ego (ex.: intervenções por tarefa).
- Detecção: o Orb não lê teclas. O evento nasce quando o prompt é submetido, via hook ou
  transcript do CLI (ver [ARCHITECTURE.md](ARCHITECTURE.md)).

### Camadas vivas do Orb

Tudo abaixo é **visualização de dados reais**, somente leitura (princípio 10). Nada disso
altera projeto, modelo ou configuração.

**Andares e janelas acesas (Realm).** Os andares do prédio são os módulos/diretórios de
primeiro nível do repositório (respeitando `.gitignore`); a altura segue as linhas de
código. As janelas acendem onde os agentes editaram recentemente e esmaecem com o tempo:
um mapa de calor vivo de onde o trabalho acontece. Dado: caminho dos arquivos nas edições.

**Weather.** CI passando = céu limpo; CI falhando = tempestade sobre o prédio; testes
falhando = rachaduras/andaimes; realm parado = noite. Dado: probes de git e CI.

**Chronicle.** Linha do tempo do Orb: arrastar para o passado e ver a cidade como era
(prédios mais baixos, agentes que ainda não existiam). Funciona porque o estado do mundo é
reconstruível do log de eventos; o histórico do git permite reconstruir também o passado
anterior ao Orb. Somente leitura sobre o log.

**Energy.** Tokens e custo como recursos: cada realm tem consumo; Mankind tem total e
tendência. Dado real: `usage` e custo dos transcripts. Ajuda a ver qual realm está queimando
mais.

**Gate.** O portão central do Orb, com duas funções:
- **Ver:** todos os pedidos de aprovação pendentes (`WAITING`) de todos os realms, com realm,
  Alter Ego e ação pedida.
- **Enviar prompts:** o Lucas escolhe um Alter Ego e escreve para ele sem entrar no realm.
  É um Intrusive Thought com `channel: gate`.

O Gate **não aprova nem decide nada sozinho** e não cria um canal paralelo ao CLI: tudo que o
Gate envia é escrito **no terminal daquele Alter Ego**, exatamente como se o Lucas tivesse
digitado (princípio 10 continua valendo: a porta de escrita é uma só, o terminal).

**Team.** Um Alter Ego principal e seus subagentes formam uma equipe. No Orb, a Team é
agrupada visualmente (o líder e os subagentes que nasceram dele, com a árvore de quem
delegou o quê) e pode ser vista e endereçada como um todo. Dado: relação `parent` já presente
nos eventos (`agent.spawned`, transcripts de subagentes). Uma Team pode ter subagentes
dentro de subagentes (`spawnDepth`).

**Archive.** A memória de cada Alter Ego, só para ver: o contexto, as skills, o `CLAUDE.md`
e os arquivos de memória que moldam o agente. Regras:
- **Somente leitura.** O Orb abre os arquivos para mostrar, nunca grava, edita ou trava.
- **Privacidade por padrão:** mostrar nomes, tamanhos e datas; o conteúdo só aparece quando
  o Lucas abrir explicitamente (arquivos de memória podem ter dados pessoais).
- Nada do que o Archive lê é reinjetado no agente.

---

## 3. Estados universais

Independentes do provider. Os adapters traduzem eventos nativos para estes estados.

`IDLE` · `THINKING` · `READING` · `RESEARCHING` · `CODING` · `EXECUTING` · `TESTING` ·
`REVIEWING` · `DELEGATING` · `WAITING` · `BLOCKED` · `ERROR` · `COMPLETED`

Exemplo de tradução:

| Evento nativo | Estado |
|---|---|
| Hermes `pre_tool_call` (web_search) | `RESEARCHING` |
| Hermes `pre_tool_call` (terminal) | `EXECUTING` |
| `subagent_start` (qualquer provider) | `DELEGATING` |
| Hermes `kanban_task_blocked` | `BLOCKED` |
| Aguardando aprovação do Lucas | `WAITING` |

---

## 4. Arquitetura (proposta inicial)

```
Claude Hooks ────────► Claude Adapter ──┐
Codex App Server ────► Codex Adapter ───┼─► Agent Event Protocol ─► FastAPI ─► WebSocket ─► Godot 4
Hermes hooks/webhooks ► Hermes Adapter ─┘   (Event Bus + State)       ▲
Git / GitHub / CI ──────────────────────────────────────────────────┘
```

### Terminal nativo + telemetria paralela

Para usar um agente, o Orb abre um **terminal** (pseudo-console; ConPTY no Windows) dentro do
realm e roda o CLI real nele. Quem usa o agente é a TUI original. Em paralelo, o Orb observa
por duas fontes e alimenta o 3D, o Inner World e um chat espelhado:

```
Terminal (PTY) ─► CLI real (claude / codex / hermes) ─┬─► hooks de ciclo de vida ──┐
                                                      └─► arquivos de sessão/transcript ─┤
                                                                                        ▼
                                              Provider Adapter ─► eventos universais ─► 3D + Inner World + chat
```

- Cada **terminal é aberto no contexto de um realm** (pasta do projeto) e vinculado a um
  Alter Ego.
- **Escolha automática do CLI:** o Alter Ego tem `provider` e `model`; o Orb deduz qual CLI
  chamar (ex.: modelo `claude-*`/`opus`/`sonnet` → `claude`; `gpt-*`/`codex` → `codex`;
  `hermes` → `hermes`; ou o provider explícito) e digita o comando no terminal sozinho.
  Provider sem CLI instalado é recusado com mensagem clara. Só executáveis de uma lista fixa.
- Para o Claude, o Orb passa `--session-id` e `-n`, assim sabe qual transcript é daquela sessão.
- O **chat** é uma visão espelhada dos eventos. Enviar mensagem pelo painel significa
  escrever no terminal (mais frágil que digitar na TUI; tratar como recurso secundário).
- O backend Python é dono da PTY e a expõe por WebSocket, independente do cliente (web ou
  Godot). Embutir o terminal no Godot **foi o principal risco técnico e está resolvido**
  (Spike 2, abaixo).
- Dependência de formato: hooks e transcripts são formatos dos CLIs e mudam entre versões;
  ficam isolados dentro dos adapters.
- **Terminal no 3D (validado no Spike 2):** o Godot usa o addon godot-xterm só para **exibir** o
  terminal; o Terminal Host continua em Python e o cliente conecta por WebSocket. O terminal
  pode ser a tela de um **monitor dentro do Rooftop Room** (textura de `SubViewport`), com o
  teclado encaminhado. Detalhes e armadilhas em [MVP.md](MVP.md) §7.

### Observar × Hospedar

O Orb integra com os CLIs de dois modos, e mantém os dois:

| Modo | Como | Uso |
|---|---|---|
| **Hospedar** | O Orb abre o terminal e roda o CLI nele (PTY) | Principal. Sessões iniciadas pelo Orb, em um realm, vinculadas a um Alter Ego |
| **Observar** | O Orb só lê hooks e transcripts de uma sessão que já existe | Sessões iniciadas fora do Orb (ex.: `claude` direto no terminal do Lucas) |

Em ambos, a telemetria é a mesma (adapter → eventos universais). Não há reimplementação do
agente nem do chat: a TUI original é a interface de uso, e o painel de chat é um espelho dos
eventos.

**Níveis de pegada** (quanto o Orb toca no ambiente do Lucas), por provider:

| Nível | Claude Code | Codex |
|---|---|---|
| **0 — zero pegada** (padrão) | Só lê o transcript em `~/.claude/projects/` | Só lê os rollouts em `~/.codex/sessions/` |
| **1 — observação em tempo real** | Hooks injetados **por sessão** com `--settings` (nunca no `settings.json`) | **App-server próprio do Orb** + `codex --remote`; um cliente observador se inscreve nas threads. Hooks do Codex **não servem** (só `command`, exigem confiança do usuário, sem injeção por sessão) |

Detalhes e evidências: [ADAPTER-CLAUDE.md](ADAPTER-CLAUDE.md) §6 e [ADAPTER-CODEX.md](ADAPTER-CODEX.md) §1.

### Documentação do projeto

| Arquivo | Conteúdo |
|---|---|
| [README.md](README.md) | Porta de entrada: o que é o projeto, estado, como rodar os spikes |
| [CONTEXT.md](CONTEXT.md) | Visão, glossário de conceitos, decisões e roadmap (este arquivo) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Módulos, fronteiras, regras de dependência, robustez, testes |
| [PROTOCOL.md](PROTOCOL.md) | Agent Event Protocol: envelope, tipos de evento, estados, fidelity, comandos |
| [ADAPTER-CLAUDE.md](ADAPTER-CLAUDE.md) | Hooks e transcript do Claude Code verificados, mapeamento para o protocolo, lacunas |
| [ADAPTER-CODEX.md](ADAPTER-CODEX.md) | App-server, rollouts e hooks do Codex verificados; observador por app-server; diálogos da TUI |
| [MVP.md](MVP.md) | Escopo do MVP, registro de riscos e resultados dos spikes 1 a 4 |
| [IDEAS.md](IDEAS.md) | Backlog completo de ideias, com status |

- **Backend:** Python + FastAPI; Redis Streams ou NATS; PostgreSQL.
- **Cliente:** Godot 4 (3D, top-down 3/4 de ~40–55°, câmera livre, UI).
- **Protocolo:** próprio. Eventos como `agent.spawned`, `task.started`, `task.completed`,
  `tool.started`, `file.edit`, `test.failed`, `approval.requested`, `thought`, `error`,
  `session.completed`.
- **Câmera:** WASD mover, scroll zoom, Q/E rotacionar, botão direito orbitar, F focar,
  ESC visão geral, 1–9 atalhos de realm, modo FREE CAM. Nível de detalhe muda com o zoom
  (realm → alter egos → card detalhado).

> **Verificação das integrações** (spikes 3 e 4, 2026-10-06):
> - **Claude Code:** hooks e transcript **verificados ao vivo** ([ADAPTER-CLAUDE.md](ADAPTER-CLAUDE.md)).
> - **Codex:** app-server, rollouts e esquema oficial **verificados**; hooks só pelas docs
>   ([ADAPTER-CODEX.md](ADAPTER-CODEX.md)).
> - **Hermes:** **não verificado** (o CLI não está instalado nesta máquina). As referências a
>   hooks e webhooks de saída do Hermes vieram de uma conversa externa; confirmar antes de depender.

---

## 5. Roadmap do MVP

0. ✅ **Protótipos de risco (spikes 1 a 4, concluídos em 2026-10-06):** terminal real hospedado
   em ConPTY (1), terminal dentro do Godot e como monitor 3D (2), hooks do Claude ao vivo (3) e
   observação do Codex pelo app-server (4). Resultados e riscos restantes em [MVP.md](MVP.md).
1. **Collector** capaz de detectar Claude, Codex, Hermes e subagentes em tempo real.
2. **Event Protocol** unificado (eventos + estados universais + fidelity).
3. **Página 2D** Realm → Alter Ego → Subagente → Atividade, para provar que a telemetria
   está correta. *Etapa mais importante: se a árvore em tempo real estiver certa, o 3D
   vira só um renderizador de estados.*
4. **Sala 3D** pequena com personagens no lugar dos cards.
5. **Camadas vivas** (janelas acesas, Weather, Chronicle, Energy, Gate, Team, Archive; ver
   "Camadas vivas do Orb") e **camada de jogo:** mapas, movimentação, XP, quests, conquistas, Inner World, controle
   (mensagem, pausa, aprovar, delegar, terminal, diff).

---

## 6. Decisões em aberto

- Nome oficial do produto (hoje: "Agent World" / pasta "Orb IA").
- Persistência: o que vai para PostgreSQL vs. só em memória no MVP.
- Estilo visual de cada realm.
- **Regra de altura (LOC):**
  - ~~Exclusões~~ **Decidido:** sempre ignorar o `.gitignore`. Em aberto: linhas em branco/comentários contam? Lockfiles versionados (ex.: `package-lock.json`) entram?
  - Escala linear ou comprimida (raiz/log)? Um repo de 500k linhas ao lado de um de 2k pode deixar o skyline ilegível em escala linear.
  - Frequência de recálculo (a cada commit, a cada evento de edição, sob demanda).
  - Como expor o filtro (`.md` sim/não, por extensão) na UI.
- ~~Onde ficam as áreas funcionais?~~ **Decidido:** todas as áreas existem, obrigatoriamente, em todo Rooftop Room.
- **Rooftop Room:** nome definitivo; um quartinho por realm ou um por alter ego; como o layout acomoda as áreas obrigatórias com poucos ou muitos agentes e subagentes (o quartinho cresce? as áreas são fixas?).
- **Inner World por provider** (parcialmente respondido): Claude ≈ 12% dos blocos de thinking com
  texto, Codex ≈ 42% (sempre `summary`). Falta decidir como a UI combina pensamento, narração,
  plano e ferramentas quando o pensamento está ausente. Hermes: não verificado.
- **Intrusive Thoughts** (parcialmente respondido): no Claude, `UserPromptSubmit` + conferência
  de origem no transcript (`origin.kind`); no Codex, `item/started` `userMessage`. Em aberto:
  quais entradas contam além de prompts (slash commands, interrupções) e a origem humana no Codex.
- **Observador do Codex vs. aprovações pendentes (risco principal em aberto):** o que o
  app-server faz com um assinante passivo que ignora um pedido de aprovação. Precisa de teste
  cuidadoso antes de o adapter existir ([ADAPTER-CODEX.md](ADAPTER-CODEX.md) §9).
- **Diálogos das TUIs** (atualização, confiança, hooks): o Orb nunca os responde (princípio 10).
  Em aberto: como a UI avisa que um terminal está parado num diálogo esperando o Lucas.
- **Nível de pegada padrão por provider:** proposta = nível 0 sempre; nível 1 opcional por Alter Ego.
- Representação visual de um intrusive thought no 3D.
- **Sessão visível por Alter Ego (pesquisa futura):** cada IA e seus subagentes aparecerem com a sessão em que trabalham (título da sessão no personagem). Viável no Claude Code; perguntas abertas em [ADAPTER-CLAUDE.md](ADAPTER-CLAUDE.md) §5.
- Quais CLIs entram além de Claude, Codex e Hermes (qualquer modelo com CLI é candidato).

## 7. Origem

Conversa de ideação com ChatGPT ("Pensar projeto agentes IA"):
https://chatgpt.com/share/6ac57860-d8cc-83e9-aa06-19c4c72b6938
