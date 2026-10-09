# The Orb — Ideias (backlog completo)

> **Todas** as ideias discutidas, com o status de cada uma. Nada é apagado: o que muda de rumo fica
> listado como `Revisto`, com o motivo. Toda ideia respeita a não interferência ([VISION.md](VISION.md)
> §3, princípio 5): o Orb só visualiza; a única porta de escrita é o terminal do Inner World.
> Escopo do MVP: [MVP.md](MVP.md).

Última atualização: 2026-10-09

**Status:** `Feito` = implementado em `src/` · `MVP` = no escopo do MVP · `Próximo` = logo depois ·
`Backlog` = guardado · `Pesquisa` = investigar antes · `Decidido` = registrado em ADR/visão ·
`Revisto` = substituído por outra decisão (motivo ao lado).

---

## 1. Núcleo (telemetria e hospedagem)

| Ideia | Resumo | Status |
|---|---|---|
| Terminal nativo por CLI | Terminal real com o CLI original (claude, codex, hermes, opencode), escolhido pelo modelo da sessão. **Nada de TUI criada do zero** | **Feito** (`terminal_host`) |
| Linha de comando validada | Modelo, id e nome de sessão validados antes de serem digitados no shell | **Feito** |
| Telemetria paralela | Fonte nativa → adapter → evento nativo + sinal de mundo + Inner World | **Feito** |
| Nível 0 de pegada | Só ler o que o provider já grava | **Feito** (Claude, Codex, Hermes, opencode) |
| Nível 1 de pegada (Claude) | Hooks por sessão via `--settings`, transporte `command` async + `curl` | Próximo (gerador e tradutor feitos; receptor pendente) |
| Receptor de hooks sempre responsivo | Processo mínimo que só enfileira e responde `{}` | Próximo |
| Hooks ainda não exercitados | TaskCreated/Completed, Notification, PostToolUseFailure, PermissionDenied, StopFailure, Pre/PostCompact, CwdChanged | Pesquisa |
| Event Protocol versionado | 0.1: vocabulário universal traduzido | **Revisto** → 0.2 (ADR 0002) |
| Eventos nativos por provider | Cada provider aparece como ele é; o mundo usa sinais derivados | **Decidido** e **Feito** (protocolo 0.2) |
| Painel 2D de validação | Árvore Realm → Alter Ego → Team → Atividade + Inner World | **Revisto**: substituído pelo mundo 3D (ADR 0007) |
| Observador por realm | Os 4 providers observados ao mesmo tempo em cada projeto; sessões de fora do Orb aparecem sozinhas | **Feito** |
| Realms configurados por caminho (`--realm`, `--root`) | O Lucas informa as pastas dos projetos | **Revisto**: viola R3; os realms são detectados pelos providers |
| Detecção de realms pelos providers | A cidade se monta sozinha a partir das sessões que os 4 CLIs registram; entram todos os projetos já registrados | **Decidido** (R3, R3a); pendências D-REALM-2 a 6 decididas; ticket a criar |
| Ignorar sessões fora de projeto | Pasta do usuário, `Temp`, `Downloads` não viram realm | **Decidido** (R3b, critério incluído) |
| Projeto apagado do disco | Pasta que não existe mais, mas está no histórico dos CLIs | **Decidido**: não entra (R3d) |
| Tela de configurações do Orb | Preferências do Lucas (realms escondidos, prazo das sessões recentes) num arquivo próprio do Orb | **Decidido** (R29) |
| Sessões recentes na sala, antigas no Histórico do realm | Na sala, ativas + últimos 10 dias (configurável); as demais no Histórico do realm | **Decidido** (R28a) |
| Cores novas dos providers | Claude laranja, Codex azul, Hermes amarelo, opencode cinza | **Decidido** (R30); colisões resolvidas (D-040) |
| Áreas identificadas por ícone e nome, sem cor | Libera as cores para git (janelas), providers (personagens) e "esperando" | **Decidido** (R20c, D-040); ícones em V-PEND-7d |
| Lista de realms com marcação | O Lucas desmarca um realm para escondê-lo da cidade; preferência guardada pelo Orb | **Decidido** (R3c); ticket a criar |
| Sessões encerradas permanecem | O Alter Ego não é excluído quando a sessão termina | **Decidido** (R28); na sala por 10 dias, depois no Histórico do realm (R28a) |
| Cenário declarado | Céu, chão, grade, estrelas e luz são cenário, declarados em VISUAL.md | **Decidido** (R12a) |
| Linguagem visual documentada | Cada elemento do mundo tem significado declarado (dado, legenda ou cenário) | **Decidido** ([VISUAL.md](VISUAL.md)) |
| Adapter Codex | Rollouts (nível 0) + observador de um app-server próprio do Orb (nível 1) | **Feito** (validação ao vivo pendente) |
| Adapter Hermes | `state.db` somente leitura (nível 0) | **Feito** (validação ao vivo pendente) |
| Hermes nível 1 pelo sidecar da TUI | `HERMES_TUI_SIDECAR_URL` por lançamento, sem mudar configuração (só `--tui`) | Próximo |
| Adapter opencode | `opencode.db` somente leitura, só tabelas de sessão (nível 0) | **Feito** (validação ao vivo pendente) |
| opencode nível 1 | Servidor próprio (`opencode serve`) + TUI com `--server` | Pesquisa |
| Webhooks de saída do Hermes | Receber telemetria por HTTP | **Revisto**: exigem `config.yaml`; o sidecar da TUI ocupa o lugar |
| Verificar assinante passivo vs. aprovações do Codex | O que o servidor faz quando o observador ignora um pedido de aprovação | Pesquisa (**prioridade**) |
| Classificador de comandos | Tabela declarativa: `Get-Content`, `git status` → `READING`; `pytest` → `TESTING`… | **Feito** (compartilhado) |
| Orb passa o modelo explicitamente | `-m`/`--model` quando a sessão tem modelo (o padrão do `config.toml` pode não ser aceito) | **Feito** |
| Sessões grandes do Codex | Leitura incremental começando do fim (rollouts de 145 MB) | **Feito** |
| Diálogos da TUI são do Lucas | Nunca responder; detectar e avisar na UI | **Decidido** (aviso na UI: leitor de diálogos, R34) |
| Adapters para outros CLIs | Gemini CLI, Cursor, agentes próprios (o opencode já entrou) | Backlog |
| Modo Observar | Sessões iniciadas fora do Orb | Próximo (leitores já suportam) |
| Modo Hospedar via stream JSON | Alternativa à TUI | Backlog |
| Chat espelhado | Painel com a conversa a partir dos eventos | **Revisto**: é a linha do tempo do Inner World |
| Fontes de vida real extras | Docker, Jira/Issues além de git, GitHub e CI | Backlog |

## 2. O mundo (Orb, Realm, Environment)

| Ideia | Resumo | Status |
|---|---|---|
| Orb como cidade | Mundo conceitual que contém os realms; o 3D é o produto | **Decidido** |
| Realm = prédio, altura = LOC | Altura calculada, sempre ignorando o `.gitignore`, filtro de `.md` | **Decidido** (probe de LOC: Próximo) |
| Escala comprimida (raiz/log) | Evitar skyline ilegível | **Revisto**: escala absoluta por classes de faixa de linhas, com salto entre classes e cintas no topo (R19, D-051, D-052) |
| Altura relativa ao maior prédio | O maior realm define a altura dos outros | **Revisto**: rejeitado pelo Lucas (D-051) |
| Cidade retangular com bairros por letra | Prédios em ordem alfabética, posição "aleatória" mas rastreável pela semente do nome | **Decidido** (R32, D-046, D-047) |
| Rooftop Room | Quartinho no teto com as 5 áreas obrigatórias | **Decidido** |
| Estilo temático por realm | TriSafe industrial, CLARA biblioteca, UTC CONECTA+ estação de comunicação | **Revisto**: prédios no mesmo estilo (D-071); um tema, se vier, é cenário escolhido pelo Lucas |
| Forma arquitetônica por classe de prédio | Casa a Arranha-céu, cada classe com a sua forma, como o CodeCity mapeia métricas no tipo do prédio | **Decidido** (R41, D-072); formas aprovadas (D-075) |
| O Orb não consome tokens | Só monitora; nada chama modelo de IA | **Decidido** (R38, D-070) |
| Papel do Alter Ego | O que a sessão mais fez, por contagem | **Decidido** (R40, D-069) |
| Mapa/minimap | Visão geral rápida | Backlog |
| Cidade/campus como hub | Tela inicial com todos os realms e contagem de Alter Egos | **Feito** (v1: disco do Orb com os realms em grade); traçado **revisto**: cidade retangular com bairros (R32) |

## 3. Câmera e controles

| Ideia | Resumo | Status |
|---|---|---|
| Câmera 3/4 de cima, livre | ~40–55°, rotação, zoom, foco | **Feito** |
| Controles de câmera | WASD, scroll, Q/E, botão direito orbitar, F focar, duplo clique seguir, ESC, 1–9 realms | **Feito** (menos duplo clique seguir) |
| FREE CAM | Sem limite de inclinação | Backlog |
| Níveis de detalhe por zoom | Longe: realm. Médio: personagens. Perto: card e monitor com o terminal | **Feito** em parte (rótulos de perto; monitor: Próximo) |
| Personagem "Manager" andando | Terceira pessoa (preterido pelo top-down; guardado) | Backlog |

## 4. Alter Ego e Mankind

| Ideia | Resumo | Status |
|---|---|---|
| Alter Ego persistente que troca de provider | Persona separada do provider | **Revisto**: não há sinal real que ligue sessões a uma persona (ADR 0001) |
| Alter Ego = sessão | Cada sessão é um personagem, o líder da sua Team | **Decidido** e **Feito** no Core |
| Perfil do Alter Ego | O que dá identidade além da sessão (nome, papel, aparência, histórico) | Pesquisa (**prioridade**) |
| Reabrir um Alter Ego | Retomar a sessão num terminal novo (`--resume`) | Próximo (`Launch(resume=True)` feito; comportamento do id a verificar) |
| Subagentes como unidades temporárias | Nascem na sessão, cumprem a missão, se desmobilizam | **Feito** no Core |
| Atividades do mundo | THINKING, CODING, TESTING, WAITING, … | **Feito** |
| Personalidade / stats / nível (XP) | Só com histórico real | Personalidade e stats: backlog. **XP, níveis e conquistas: decididos** ([PROGRESSION.md](PROGRESSION.md), D-101 a D-111, Delegada) |
| Nome histórico para cada Alter Ego | Einstein, Ada Lovelace, Tesla…: sorteio sem reposição de 60 nomes, uma vez por sessão, sacola global; subagentes sem nome | **Decidido** (R37, D-063 a D-067) |
| Registro local do Orb (SQLite) | Base do Chronicle e dos nomes; só o que o Orb derivou | **Decidido** (R36) |
| Leitor de diálogos | Avisa que o terminal espera o Lucas num diálogo do CLI, sem responder | **Decidido** (R34) |
| Quests, conquistas, evolução de projeto | Camada de jogo | Conquistas: **decididas** (R55); quests (missões): backlog, só as definidas pelo Lucas (D-111) |
| Quadro de tarefas ligado a issues reais | Task Board alimentado por tickets | Backlog |
| Memorial | Subagentes e sessões encerradas deixam marca; linhagem | Backlog |
| Cerimônias | Commit como entrega, PR merged como celebração | Backlog |

## 5. Inner World

| Ideia | Resumo | Status |
|---|---|---|
| Inner World | Terminal do CLI + linha do tempo da sessão, com `fidelity` no pensamento | **Decidido** (ADR 0003) e **Feito** no protocolo/painel |
| Intrusive Thoughts como conceito próprio | O que o Lucas escreve ao agente | **Revisto**: é parte da linha do tempo do Inner World (ADR 0003) |
| Rastrear quem escreveu cada mensagem | Separar "veio do Lucas" de "veio do sistema" | **Revisto**: desnecessário; quem usa o CLI é o Lucas (ADR 0003) |
| "Mergulhar" no Alter Ego | O cenário vira o mundo interno (plano, arquivos, dúvidas) | Backlog |
| Visual do Inner World no 3D | Mensagens e pensamento "chegando" ao Rooftop Room | Backlog |
| Stat de intervenções humanas | Entradas humanas por tarefa | **Revisto**: o Orb não rastreia autoria |
| Thinking quase vazio no Claude | ~88% sem texto; Inner World usa narração, ferramentas e prompts | **Decidido** |

## 6. Camadas vivas

| Ideia | Resumo | Status |
|---|---|---|
| Janelas acesas e andares | Andares = módulos; janelas mostram as **alterações locais**, **cada janela = x% das alterações, sem dividir nenhuma**, **na cor do tipo de alteração no git** (paleta do VS Code) | Próximo (1ª); decidido (R20, R20a, R20b, R20c, R20d); hoje as janelas são aleatórias e violam R12 (V-REALM-3) |
| Gate | Vê o que espera o Lucas e escreve a qualquer Alter Ego pelo terminal dele; **portão na borda da cidade** | **Decidido** (R35, R46, D-080); 2ª camada (D-081) |
| Team | Alter Ego + subagentes agrupados e endereçáveis | **Feito** em parte (subagentes como personagens menores na sala) |
| Orb como centralizador de IAs | Inner World e Gate: duas portas para o mesmo terminal | **Decidido** |
| Chronicle | Replay da cidade no tempo, pela barra de tempo, a partir do registro local | **Decidido** (R44, D-078); 3ª camada |
| Weather | Testes rodados nas sessões: céu limpo / chuva / nada; CI do GitHub opcional depois | **Decidido** (R42, D-076); 4ª camada |
| Energy | Tokens e custo só quando o provider informa: sessão, realm, hoje, limites da conta | **Decidido** (R43, D-077); 5ª camada |
| Archive | Aba no Inner World, só nome/tamanho/data; conteúdo ao abrir | **Decidido** (R45, D-079); 6ª camada |
| Weather pelo CI do GitHub | Ler o CI pelo `gh`, só leitura, ligado nas configurações | Backlog (D-076) |
| Chronicle anterior ao Orb | Reconstruir o passado pelo histórico do git | Backlog (D-078) |
| Estradas entre realms | Dependências entre projetos | Backlog |
| Ciclo dia/noite ligado à atividade | Cidade acesa onde há trabalho | Backlog |
| Testes como integridade estrutural | Falhas viram rachaduras/andaimes | Backlog |
| Som ambiente | Sound design do trabalho | Backlog |

## 7. Interação e controle (sempre pelo terminal)

| Ideia | Resumo | Status |
|---|---|---|
| Menu de interação com o agente | Falar, prioridade, pausar, criar subagente, ver terminal/diff, aprovar | Backlog (todo "controle" = escrita no terminal) |
| Enviar mensagem pelo painel | `input` no terminal, como se fosse digitado | Próximo |
| Terminal cru como aba | A TUI original no Inner World | **Feito** |

## 8. Clientes

| Ideia | Resumo | Status |
|---|---|---|
| Cliente Godot 4 (3D) | Foco do produto | **Revisto**: alternativa; o mundo 3D é web (ADR 0007) |
| Cliente web (Three.js) | O mundo 3D navegável no navegador | **Decidido** e **Feito** (v1; ADR 0007) |
| Embutir terminal no Godot | godot-xterm exibindo bytes do Terminal Host em Python | **Decidido** (ADR 0004) |
| Monitor 3D no Rooftop Room | O terminal como textura de um monitor (`SubViewport` num quad) | **Decidido** (validado no Spike 2) |
| Clique do mouse no monitor 3D | Foco e seleção de texto | Pesquisa |
| Glifos de caixa/bloco do terminal | Desenhar `─ █ ▐` manualmente | Backlog (cosmético) |
| Vários monitores 3D ao mesmo tempo | Desempenho com um terminal por Alter Ego | Pesquisa |

---

## 9. Da conversa original (lida em 2026-10-09)

A ideação que deu origem ao projeto ([VISION.md](VISION.md) §8) foi relida inteira. Quase tudo já
estava aqui; estas ideias não estavam e entram agora, com status. Propostas na rodada Q-ORIG de
[DECISIONS.md](DECISIONS.md).

| Ideia | Resumo | Status |
|---|---|---|
| Progresso da tarefa da sessão | "7 de 12 subtarefas", barra de progresso sobre o personagem; a lista de tarefas que o próprio CLI mantém (TodoWrite do Claude, plano do Codex, `todowrite` do opencode, Kanban do Hermes) | **Decidido** (D-093) |
| Task Board com as tarefas reais da sessão | A área Task Board mostra as tarefas da lista do CLI, não só quem concluiu | **Decidido** (D-093) |
| Subagente volta ao líder ao terminar | Ao concluir, o subagente caminha até o líder antes de se desmobilizar (ou ficar cinza, R7) | **Decidido** (D-094) |
| Erro, bloqueio e "sem sinal" do líder visíveis | A ideação sugeria "estação vermelha" para erro. Hoje VISUAL.md não define como o líder mostra `ERROR`, `BLOCKED` e `NO_SIGNAL` | **Decidido** (D-095); vermelho não pode (é do git, R20a) |
| Atributos por área ("Backend 92, Tests 84") | Barras por tipo de trabalho, calculadas do histórico real da sessão | **Decidido** (D-096), ligada ao Papel (R40) e à progressão |
| Resumo do realm visto de longe | "8 agentes, 14 tarefas, 2 bloqueados, saudável" no rótulo do prédio | **Decidido** (D-097) |
| Kanban do Hermes | Hooks `kanban_task_claimed/completed/blocked` | Pesquisa: os hooks exigem mudar a configuração (descartados, ver adapters/HERMES.md); falta saber se o Kanban fica gravado em algum lugar legível |
| Personagem com nome próprio ("Atlas") separado do LLM | O personagem trocaria de Claude para Codex | **Revisto**: Alter Ego = sessão (ADR 0001); o nome é o nome histórico (R37) |
| Stack da ideação: React Three Fiber, Redis Streams/NATS, PostgreSQL, webhooks do GitHub | Proposta inicial de tecnologia | **Revisto**: Three.js puro sem build (ADR 0007), SQLite local (R36), sem rede por padrão (R42) |
| Botão do meio + arrastar move o mapa | Controle de câmera | Backlog (hoje: arrastar com o botão esquerdo) |

## Ordem das camadas vivas (decidida, D-081)

Janelas acesas → Gate → Chronicle → Weather → Energy → Archive. As quatro primeiras só dependem de
eventos já previstos; Archive exige o leitor somente leitura e a política de privacidade.

## Regra de ouro deste arquivo

Quando uma ideia é decidida, ela vai para um ADR/visão **e continua listada aqui** com o status
atualizado. Nada é apagado.
