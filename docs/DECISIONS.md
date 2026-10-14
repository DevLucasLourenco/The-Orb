# The Orb — Registro de decisões

> **Toda decisão tomada sobre o projeto, em ordem**, com a data, quem decidiu e onde ela se aplica.
> É o índice: o detalhe fica no documento do assunto ([RULES.md](RULES.md), [VISUAL.md](VISUAL.md),
> [ARCHITECTURE.md](ARCHITECTURE.md), [adr/](adr/)…). Decisões difíceis de reverter também têm um ADR.
> Nada é apagado: uma decisão revista fica listada, com a que a substituiu.

Última atualização: 2026-10-14

Quem: **Lucas** = decidido por ele · **Delegada** = o Lucas deixou a definição com o Claude; vale até
ele revisar, e a proposta está escrita no documento do assunto.

**Fase atual:** levantamento concluído; **a spec e os 25 tickets estão em
`.scratch/the-orb-cidade-viva/`** (D-100, D-117). A implementação segue ticket a ticket (regra P1).

| Id | Data | Decisão | Quem | Onde se aplica |
|---|---|---|---|---|
| D-001 | 2026-10-06 | O Orb abre um **terminal real** e chama o **CLI original** dentro dele; nenhuma TUI criada | Spike 1 | [ADR 0004](adr/0004-terminal-host-unico-em-python.md), R15 |
| D-002 | 2026-10-06 | **Um único Terminal Host, em Python**; os clientes só exibem | Spike 2 | [ADR 0004](adr/0004-terminal-host-unico-em-python.md) |
| D-003 | 2026-10-06 | **Nível 0 de pegada por padrão**; nível 1 só por sessão (Claude `--settings`, app-server próprio do Codex) | Spikes 3 e 4 | [ADR 0005](adr/0005-nivel-zero-de-pegada-por-padrao.md) |
| D-004 | 2026-10-06 | **O Orb nunca responde diálogos** dos CLIs nem pedidos de servidor | Spike 4 | [ADR 0006](adr/0006-o-orb-nunca-responde-dialogos.md), R16 |
| D-005 | 2026-10-06 | O Orb dá `--session-id` e `-n` ao `claude` hospedado e limpa o ambiente herdado | Spike 1 | [MVP.md](MVP.md) §5 (D7) |
| D-006 | 2026-10-06 | Servidor só em loopback, com token, `Origin` local e lista fixa de executáveis | Spike 1 | [ARCHITECTURE.md](ARCHITECTURE.md) §3 |
| D-007 | 2026-10-06 | **Altura do prédio = linhas de código**, sempre ignorando o `.gitignore`, com filtro | Lucas | R19 |
| D-008 | 2026-10-06 | **As 5 áreas existem em todo Rooftop Room** | Lucas | R21 |
| D-009 | 2026-10-07 | O nome é **The Orb** (fora "Orb IA", "Agent World"), inclusive no GitHub | Lucas | R1 |
| D-010 | 2026-10-07 | **Alter Ego = uma sessão**, que carrega e identifica sozinho o seu provider; o **Perfil** fica em aberto | Lucas | [ADR 0001](adr/0001-alter-ego-e-uma-sessao.md), R5, R6 |
| D-011 | 2026-10-07 | **Inner World** une o terminal do CLI e a linha do tempo; "Intrusive Thoughts" sai do vocabulário | Lucas | [ADR 0003](adr/0003-inner-world-une-terminal-e-pensamento.md), R9 |
| D-012 | 2026-10-07 | **Cada provider aparece como ele é** (evento nativo); o mundo usa só sinais derivados | Lucas | [ADR 0002](adr/0002-eventos-nativos-por-provider.md), R13 |
| D-013 | 2026-10-07 | Os spikes viram a estrutura definitiva por âmbito (protocolo, mundo, adapters, terminal, servidor) | Lucas | [ARCHITECTURE.md](ARCHITECTURE.md) |
| D-014 | 2026-10-07 | Os 4 CLIs da máquina são providers: **claude, codex, hermes, opencode** | Lucas | R8 |
| D-015 | 2026-10-07 | O Orb **não rastreia quem escreveu** cada mensagem | Lucas | R11, ADR 0003 (revista) |
| D-016 | 2026-10-07 | O mundo 3D é **web, com Three.js** (no lugar do Godot) | Lucas | [ADR 0007](adr/0007-cliente-3d-na-web.md) |
| D-017 | 2026-10-07 | O **overview** de um realm mostra: o que cada sessão faz agora, quem espera o Lucas, subagentes e consumo | Lucas | R18 |
| D-018 | 2026-10-07 | **Os realms são detectados pelos providers**; o Lucas nunca informa caminhos | Lucas | R3, [ARCHITECTURE.md](ARCHITECTURE.md) (Detecção de realms) |
| D-019 | 2026-10-07 | **Processo: documentar → tickets → implementar** | Lucas | P1 |
| D-020 | 2026-10-07 | A cor de uma janela acesa é a **cor do tipo de alteração no git** | Lucas | R20a, V-REALM-3 |
| D-021 | 2026-10-07 | Entram **todos os projetos que algum CLI já registrou** | Lucas | R3a, D-REALM-1 |
| D-022 | 2026-10-07 | O Lucas **esconde realms** desmarcando-os numa lista | Lucas | R3c, D-REALM-4, V-HUD-5 |
| D-023 | 2026-10-07 | **Sessões fora de projeto são ignoradas** | Lucas | R3b |
| D-024 | 2026-10-07 | **Sessões encerradas não são excluídas** do mundo | Lucas | R28 |
| D-025 | 2026-10-07 | **Cenário é permitido**, quando declarado e sem cores da legenda | Lucas | R12a, V-PEND-4 |
| D-026 | 2026-10-08 | **Cores:** as janelas usam a **paleta de alterações do git do VS Code**; as **áreas** e o sinal de **"esperando o Lucas"** trocam de cor para não colidir | Lucas | V-PEND-7, VISUAL.md §5 |
| D-027 | 2026-10-08 | **Na sala ficam as sessões ativas e as recentes (últimos 10 dias)**; o prazo é **configurável dentro do Orb**; as demais ficam no **arquivo do realm**, sem sumir | Lucas | R28a, V-PEND-2 |
| D-028 | 2026-10-08 | **Cada janela é um arquivo**, e o que ela mostra são as **alterações locais** dele (o estado do repositório na máquina) | Lucas | R20b, V-PEND-1 |
| D-029 | 2026-10-08 | **"Fora de projeto"** = a pasta do usuário em si e pastas de sistema ou temporárias (`AppData`, `Temp`, `Downloads`); todo o resto é projeto | Lucas | R3b, D-REALM-2 |
| D-030 | 2026-10-08 | O Orb tem um **arquivo de preferências próprio** (realms escondidos, prazo das sessões recentes…), nunca nos providers | Lucas | R29, D-REALM-5 |
| D-031 | 2026-10-08 | **Projeto que não existe mais no disco não entra** na cidade | Lucas | R3d, D-REALM-6 |
| D-032 | 2026-10-08 | As **configurações do Orb ficam dentro do Orb** (uma tela de configurações), não em parâmetros de linha de comando | Lucas | R29 |
| D-033 | 2026-10-08 | Toda decisão fica registrada **neste documento** e aplicada no documento do assunto | Lucas | este arquivo, P1 |
| D-034 | 2026-10-08 | **Os tickets ainda não serão escritos**: a fase é de levantamento de ideias e decisões | Lucas | P1, [RULES.md](RULES.md) (Do documento aos tickets) |
| D-035 | 2026-10-08 | A lista de sessões antigas de um realm se chama **Histórico do realm** | Lucas | R28a, glossário (o **Chronicle** deixa de evitar a palavra "histórico") |
| D-036 | 2026-10-08 | **Áreas em tons frios e neutros**, e **"esperando o Lucas" em magenta pulsante** | Lucas | R20c, V-PEND-7b (revisto por V-PEND-7c) |
| D-037 | 2026-10-08 | **Cores dos providers:** Claude **laranja**, Codex **azul**, Hermes **amarelo**, opencode **cinza** | Lucas | R30, V-EGO-1 |
| D-038 | 2026-10-08 | **Janelas por percentual:** cada janela acesa representa **x% das alterações locais** do realm, para a fachada ficar harmônica | Lucas | R20d, VISUAL.md §6 |
| D-039 | 2026-10-08 | **Uma alteração nunca fica dividida entre duas janelas** | Lucas | R20d, VISUAL.md §6 |
| D-040 | 2026-10-08 | **Áreas sem cor própria:** piso neutro, cada área identificada por **ícone e nome** (e um padrão no piso). As cores ficam só para janelas (git), personagens (provider) e "esperando" (magenta). Os providers mantêm as cores escolhidas, em tons saturados | Lucas | R20c, V-PEND-7c, V-REALM-8 |
| D-041 | 2026-10-08 | **Peso de uma alteração = linhas alteradas** (inseridas + removidas; arquivo novo = linhas dele; apagado = linhas que tinha; arquivo binário = 1) | Lucas | R20d, V-PEND-8, VISUAL.md §6 |
| D-042 | 2026-10-08 | **x = 5%** (configurável na tela do Orb, R29) | Lucas | R20d, V-PEND-9 |
| D-043 | 2026-10-08 | **A janela só tem dois estados: acesa ou apagada.** Não esmaece com o tempo | Lucas | R20, V-PEND-1c |
| D-044 | 2026-10-08 | Uma sessão recente aparece **"dormindo" na sala depois de 15 min parada** | Lucas | R31, V-PEND-2b, V-REALM-10, V-EGO-7 |
| D-045 | 2026-10-08 | **Subagente sem sinal fica cinza**, em vez de sumir | Lucas | R7, V-PEND-3, V-EGO-10 |
| D-046 | 2026-10-08 | **Cidade retangular**; os prédios aparecem em **ordem alfabética** e com um ar **"aleatório", mas rastreável**, posicionados por uma **estrutura lógica** no mapa | Lucas | R32, V-PEND-5, V-CITY-1, V-CITY-4 |
| D-047 | 2026-10-08 | O traçado concreto da cidade (bairros por letra, lotes, semente pelo nome) | **Delegada** | R32, VISUAL.md §7 |
| D-048 | 2026-10-08 | **Altura por percentual:** projeto com poucas linhas = prédio pequeno; com muitas = prédio grande. *Revista em parte por D-051: nada de percentual do maior prédio* | Lucas | R19, V-PEND-6 |
| D-049 | 2026-10-08 | ~~A escala concreta (percentual do maior realm, altura mínima, andares proporcionais às pastas)~~ **Revista por D-051** | **Delegada** | — |
| D-050 | 2026-10-08 | Subagente **"sem sinal"** = **cinza translúcido, sem halo, com ícone de sinal cortado**, depois de **5 min sem atividade**; o opencode segue cinza sólido com halo | Lucas | R7, V-PEND-3b, V-EGO-10 |
| D-051 | 2026-10-08 | **A altura não depende do maior prédio.** Cada prédio tem a altura das suas próprias linhas; **o que é grande se destaca de verdade**, com **delimitação por faixas de milhares de linhas** e algo específico que mostre a faixa | Lucas | R19, V-PEND-6 |
| D-052 | 2026-10-08 | A escala concreta: **6 classes** (Casa, Sobrado, Prédio, Edifício, Torre, Arranha-céu) por faixa de linhas, **saltos de altura** entre classes, crescimento logarítmico dentro da classe, **cintas de luz neutra** no topo (uma por classe) e antena no Arranha-céu; andares por pasta dentro da altura, com "demais pastas" | **Delegada** | R19, VISUAL.md §8 |
| D-053 | 2026-10-08 | Para a altura, **contam as linhas não vazias**; comentários contam | Lucas | R19, VISUAL.md §8 |
| D-054 | 2026-10-08 | **Arquivos gerados versionados** (lockfiles, `*.min.js`, saídas de build) **não contam**: lista fixa e visível de exclusões, além do `.gitignore`, ajustável nas configurações | Lucas | R19, R29 |
| D-055 | 2026-10-08 | **Recalcular** linhas e classe ao abrir o Orb e quando as alterações locais mudam, no máximo 1 vez por minuto por realm | Lucas | R19 |
| D-056 | 2026-10-08 | **Filtro de tipos:** padrão só código, **sem `.md`**; muda-se nas configurações, por realm ou para todos | Lucas | R19, R29 |
| D-057 | 2026-10-08 | **Sala cheia:** o Rooftop Room não cresce; cada área mostra até **8 personagens** e um contador **"+N"**; o overview lista todos | Lucas | R33 |
| D-058 | 2026-10-08 | O nome **Rooftop Room** é definitivo | Lucas | glossário |
| D-059 | 2026-10-08 | **Realm parado** (nenhuma sessão nos últimos 10 dias) fica de **"noite"**: a sala do teto apagada; as janelas seguem mostrando as alterações locais; acende quando surge uma sessão | Lucas | D-REALM-3, V-REALM-14 |
| D-060 | 2026-10-08 | **Aviso de diálogo:** nas sessões abertas pelo Orb, um módulo próprio (não o Terminal Host) reconhece diálogos conhecidos do CLI pelo texto da tela e marca o personagem como "esperando o Lucas"; nunca responde | Lucas | R34, ADR 0006 |
| D-061 | 2026-10-08 | **Gate para sessão fechada:** oferece **reabrir** a sessão num terminal novo, com confirmação do Lucas; nunca reabre sozinho | Lucas | R35 |
| D-062 | 2026-10-08 | **Registro local do Orb:** um log próprio (SQLite, na pasta de preferências do Orb), só com o que o Orb derivou (base do Chronicle e dos nomes); o conteúdo das sessões continua nos providers | Lucas | R36 |
| D-063 | 2026-10-08 | **Perfil, primeiro elemento: um nome histórico** (tecnologia, física, matemática, filosofia), sorteado quando a sessão aparece, de uma lista de 50+; pode repetir, mas o ideal é **consumir todos antes de repetir** | Lucas | R37, R6, VISUAL.md §9 |
| D-064 | 2026-10-08 | O nome histórico é **sorteado uma vez e fica com a sessão para sempre** (sala, Histórico do realm, ao reabrir); a sacola é **global** (todos os realms); **nunca dois nomes iguais visíveis na mesma sala** | Lucas | R37, VISUAL.md §9 |
| D-065 | 2026-10-08 | **Subagentes não ganham nome histórico**: ficam com o tipo dado pelo CLI (Explore, qa-reviewer…) | Lucas | R37, VISUAL.md §9 |
| D-066 | 2026-10-08 | **Rótulo do personagem:** o nome em destaque ("Einstein"); embaixo, "Claude · <título da sessão>"; a cor mostra o provider | Lucas | V-EGO-8, V-EGO-11 |
| D-067 | 2026-10-08 | **A lista dos 60 nomes** de VISUAL.md §9 está aprovada | Lucas | VISUAL.md §9 |
| D-068 | 2026-10-08 | **Retomar** uma sessão = o mesmo Alter Ego; **bifurcar** = um Alter Ego novo, com nome novo, mostrando de quem nasceu; **`/clear` e compactação** = o mesmo Alter Ego quando o provider registra a ligação entre o id antigo e o novo, senão um novo (a confirmar por provider) | Lucas | R39, R10 |
| D-069 | 2026-10-08 | **Papel** do Alter Ego derivado do que a sessão mais fez (ex.: mais revisão = "revisor"), por **contagem da telemetria**, sem nenhuma chamada a modelo; mostrado no overview. **Aparência** = só a cor do provider por enquanto; **stats/XP** no backlog | Lucas | R40, R6 |
| D-070 | 2026-10-08 | **O Orb não consome tokens.** Ele só monitora: nada no Orb chama modelo de IA, nem para resumir, classificar ou nomear. O único consumo é o do Lucas usando o CLI pelo Inner World | Lucas | R38, princípio 12 (VISION.md) |
| D-071 | 2026-10-08 | **Prédios sem tema por realm**: todos no mesmo estilo, diferindo pelos dados; um tema, se vier, é cenário escolhido pelo Lucas nas configurações | Lucas | Q-WORLD-1, R41 |
| D-072 | 2026-10-08 | **Quanto maior o prédio, outro design**: cada classe da tabela de altura (Casa a Arranha-céu) tem uma **forma arquitetônica própria**, como o CodeCity faz ao mapear métricas no **tipo** do prédio | Lucas | R41, VISUAL.md §8 |
| D-073 | 2026-10-08 | **Inner World no 3D:** agora o painel de baixo (linha do tempo e terminal); depois o personagem a um **monitor** na sua área com o terminal na tela; o "mergulho" fica no backlog | Lucas | R9, Q-WORLD-2 |
| D-074 | 2026-10-08 | **Nenhum CLI além dos 4** por agora; o contrato de adapter já permite incluir outro | Lucas | R8, Q-PROV-1 |
| D-075 | 2026-10-08 | **As formas de cada classe de prédio** (VISUAL.md §8) estão aprovadas | Lucas | R41, Q-WORLD-3 |
| D-076 | 2026-10-09 | **Weather:** agora só local, pelo resultado dos testes que as sessões rodaram (comando de teste observado e código de saída), sem rede; o CI do GitHub fica opcional para depois, ligado nas configurações. No mundo: céu limpo (últimos testes passaram), chuva (falharam), nada (sem dado) | Lucas | R42, V-REALM-16 |
| D-077 | 2026-10-09 | **Energy:** tokens e custo só quando o provider informa (nunca estimados); por sessão e por realm no overview; total de **hoje** na barra de cima; limites de uso da conta (Codex) num painel de Energy | Lucas | R43, V-HUD-9 |
| D-078 | 2026-10-09 | **Chronicle:** barra de tempo no rodapé; arrastar mostra a cidade como era; fonte = registro local do Orb (R36), a partir do dia em que ele passa a registrar; o passado anterior pelo histórico do git fica para depois | Lucas | R44, V-HUD-10 |
| D-079 | 2026-10-09 | **Archive:** aba no Inner World com `CLAUDE.md`, `AGENTS.md`, skills e memória de cada provider; só nome, tamanho e data; conteúdo só quando o Lucas abrir; somente leitura, nada reinjetado | Lucas | R45, V-HUD-11 |
| D-080 | 2026-10-09 | **Gate no mundo:** um portão na borda da cidade, de frente para a câmera inicial e fora dos bairros, com a contagem de quem espera o Lucas; clicar abre a lista de esperas de todos os realms e permite escrever para qualquer Alter Ego pelo terminal dele | Lucas | R46, V-CITY-7 |
| D-081 | 2026-10-09 | **Ordem das camadas vivas:** janelas acesas → Gate → Chronicle → Weather → Energy → Archive | Lucas | VISION.md §5 |
| D-082 | 2026-10-09 | **`CLAUDE.md` na raiz**: guia para os agentes que trabalham no repositório (fontes da verdade, processo, invariantes, arquitetura, testes, git). Conteúdo em revisão (Q-DEV-1) | Lucas | [CLAUDE.md](../CLAUDE.md) |
| D-083 | 2026-10-09 | **Progressão (pontos, níveis, conquistas)** sai do backlog e entra no levantamento, com proposta própria | Lucas | [PROGRESSION.md](PROGRESSION.md), rodada Q-XP |
| D-084 | 2026-10-09 | **Resultado de comando no protocolo 0.3:** sinal `command.result` (`ok`, `exit_code?`). Codex, Hermes e opencode informam o código de saída; o Claude só `is_error`/`interrupted` (então `ok` sem código) | Lucas | Q-TEC-1, PROTOCOL.md, R42, R49 |
| D-085 | 2026-10-09 | **Estado por realm e do mundo no Core**, com sinais novos no protocolo 0.3 (`realm.metrics`, `realm.changes`, `account.limits`), produzidos pelos Probes e pelos adapters | Lucas | Q-TEC-2, ARCHITECTURE.md §3, R49 |
| D-086 | 2026-10-09 | **O tempo fica no Core, sem relógio próprio:** `snapshot(now)` recebe a hora de quem pede; os limites (dormindo 15 min, sem sinal 5 min, noite 10 dias, "hoje") numa tabela em `core/rules.py`. O cliente deixa de calcular | Lucas | Q-TEC-3, R47 |
| D-087 | 2026-10-09 | **Intervalo de leitura:** 250 ms para realms com sessão ativa; varredura de sessões novas a cada 2 s | Lucas | Q-TEC-4, ARCHITECTURE.md §5 |
| D-088 | 2026-10-09 | **Histórico em duas camadas:** índice de metadados de todas as sessões; conteúdo lido incrementalmente só das sessões da sala; passado (XP retroativa) numa leitura única em segundo plano, com o ponto de parada no registro local | Lucas | Q-TEC-5, R48 |
| D-089 | 2026-10-09 | **Codex:** mapear `response_item/agent_message` como narração e avaliar `inter_agent_communication_metadata` e `event_msg/thread_settings_applied` | Lucas | Q-TEC-6, [adapters/CODEX.md](adapters/CODEX.md) |
| D-090 | 2026-10-09 | **Claude:** o campo `gitOperation` do resultado das ferramentas é a evidência de commit (e de push, branch, PR) | Lucas | Q-TEC-7, [PROGRESSION.md](PROGRESSION.md) X-COMMIT |
| D-091 | 2026-10-09 | **6 classes de prédio** (não as 5 do CodeCity): linhas de código variam muito mais que métodos, e a 6ª classe é o destaque pedido em D-051 | Lucas | Q-REF-1, VISUAL.md §8 |
| D-092 | 2026-10-09 | **Submódulos do git não acendem janela** no projeto pai (são outro repositório); evita também um azul confundível com o Codex | Lucas | Q-REF-2, R20e |
| D-093 | 2026-10-09 | **Progresso da tarefa e Task Board:** mostrar a lista de tarefas que o próprio CLI mantém ("7 de 12" no overview; concluídas na área Task Board), só quando o provider grava a lista, nunca estimada. Consequência: um sinal de lista de tarefas no protocolo 0.3 | Lucas | Q-ORIG-1, R50, R49, V-HUD-15, V-REALM-17 |
| D-094 | 2026-10-09 | **Subagente que termina caminha até o líder** e só então se desmobiliza; sem sinal de fim, segue R7 (cinza no lugar) | Lucas | Q-ORIG-2, R51, V-EGO-16 |
| D-095 | 2026-10-09 | **Erro, bloqueio e "sem sinal" do líder** com ícones neutros sobre a cabeça: erro = triângulo branco com "!" e corpo apagado; bloqueado = cadeado; sem sinal = o ícone de sinal cortado do subagente. Sem vermelho (é do git) | Lucas | Q-ORIG-3, R52, V-EGO-15 |
| D-096 | 2026-10-09 | **Atributos por área:** barras com a parcela do trabalho da sessão em cada área, pela mesma contagem do Papel; dado real, não pontuação | Lucas | Q-ORIG-4, R40, V-HUD-16 |
| D-097 | 2026-10-09 | **Resumo do realm de longe:** o rótulo do prédio mostra sessões ativas, esperando você e, quando houver dado, o Weather e as tarefas abertas; sem dado, nada | Lucas | Q-ORIG-5, V-REALM-7 |
| D-098 | 2026-10-09 | **Rastreador de specs e tickets: arquivos locais em `.scratch/`, versionados no git**; nada em issues públicas do GitHub. Etiqueta de triagem: `ready-for-agent` | Lucas | RULES.md (Do documento aos tickets), [CLAUDE.md](../CLAUDE.md) |
| D-099 | 2026-10-09 | **Pontos de teste:** um principal, o mundo (Core: eventos + hora → estado do mundo); a **cidade (bairros e lotes), a fachada (janelas) e a classe dos prédios passam a ser calculadas no mundo, em Python**, e o cliente só desenha. Dois pontos a mais: os leitores dos CLIs sobre arquivos sintéticos e as leituras do mundo real (pasta falsa → eventos) | Lucas | ARCHITECTURE.md §3 e §7 |
| D-100 | 2026-10-09 | **Escopo da primeira spec:** tudo o que está decidido, **incluindo a progressão (XP) e o guia dos agentes**; as definições de XP e do guia ficam com o Claude | Lucas | `.scratch/` |
| D-101 | 2026-10-09 | **XP = recibo de trabalho confirmado**, com extrato; nada por tokens, custo, mensagens ou espera; nunca negativa; os agentes nunca a veem | **Delegada** | Q-XP-1, R53, PROGRESSION.md §1 |
| D-102 | 2026-10-09 | **Fontes e pesos da tabela v1** (teste verde, vermelho → verde, commit, subagente concluído, ofício com teto; PR mesclado depois) | **Delegada** | Q-XP-2, PROGRESSION.md §3 |
| D-103 | 2026-10-09 | **XP provisória → confirmada:** commit só conta ao chegar à branch principal; revertido = anulada; 30 dias = expira; o nível usa só a confirmada e pode cair | **Delegada** | Q-XP-3, R53 |
| D-104 | 2026-10-09 | **Três escalas** (Alter Ego, Realm, Mankind) e o placar por provider | **Delegada** | Q-XP-4, R54 |
| D-105 | 2026-10-09 | **XP dos subagentes vai para o líder**; retomar mantém; bifurcar começa do zero | **Delegada** | Q-XP-5 |
| D-106 | 2026-10-09 | **Commits do Lucas fora das sessões não dão XP** | **Delegada** | Q-XP-6 |
| D-107 | 2026-10-09 | **Curva k·n·(n−1)** (k = 50, 500, 2.500), calibrada com o histórico real antes do ticket da progressão | **Delegada** | Q-XP-7, R54 |
| D-108 | 2026-10-09 | **XP retroativa**, lida uma vez em segundo plano (camada 2 de R48) | **Delegada** | Q-XP-8, R48 |
| D-109 | 2026-10-09 | **16 conquistas iniciais**, cada uma com recibo e sem XP | **Delegada** | Q-XP-9, R55 |
| D-110 | 2026-10-09 | **Onde aparece:** nível ao lado do nome, anel ao subir de nível, painel Progressão, nível do realm e barras de XP no overview, aviso de conquista; tudo em branco neutro | **Delegada** | Q-XP-10, V-EGO-13, V-EGO-14, V-HUD-12 a 14 |
| D-111 | 2026-10-09 | **Missões no backlog**, só as definidas pelo Lucas | **Delegada** | Q-XP-11 |
| D-112 | 2026-10-09 | **O conteúdo do `CLAUDE.md` vale**, atualizado com o rastreador local, os pontos de teste e a fase atual | **Delegada** | Q-DEV-1, [CLAUDE.md](../CLAUDE.md) |
| D-113 | 2026-10-09 | **`AGENTS.md` curto** na raiz, mandando seguir o `CLAUDE.md` (lido por Codex e opencode; Hermes a confirmar) | **Delegada** | Q-DEV-2, [AGENTS.md](../AGENTS.md) |
| D-114 | 2026-10-09 | **Na implementação, uma branch e um PR por ticket**, citando as regras e os critérios de aceite; documentação segue direto na `main` | **Delegada** | Q-DEV-3, [CLAUDE.md](../CLAUDE.md) |
| D-115 | 2026-10-09 | **Sem brilho geral das janelas por atividade:** a janela acesa tem brilho fixo; a atividade aparece na sala e no rótulo | Lucas | Q-REV-1, V-REALM-4 |
| D-116 | 2026-10-09 | **Árvore da Team no overview:** subagentes em árvore (quem criou quem), com tipo e estado; no mundo nada muda | Lucas | Q-REV-2, R57, V-HUD-17 |
| D-117 | 2026-10-09 | **Divisão em 25 tickets aprovada**, gravados em `.scratch/the-orb-cidade-viva/issues/` | Lucas | P5 |
| D-118 | 2026-10-09 | **Tickets 05 e 25 ficam `ready-for-agent`**, com um ponto de parada explícito para a aprovação do Lucas (prévia de cores; curva de XP) | Lucas | `.scratch/the-orb-cidade-viva/issues/` 05 e 25 |
| D-119 | 2026-10-09 | **Um subagente "sem sinal" não segura o líder em `DELEGATING`**: sem isso, um subagente em segundo plano que nunca avisa o fim mantinha a sessão "delegando" para sempre e ela nunca dormia | Lucas | Q-T01-1, R7, R31, ticket 01 |
| D-120 | 2026-10-09 | **Atividade de um subagente = qualquer evento dele** (resultado, narração, ferramenta), não só os que trazem sinal | Lucas | Q-T01-2, ticket 01 |
| D-121 | 2026-10-09 | **Os totais de subagentes ativos não contam os "sem sinal"**; eles seguem listados no overview, em cinza | Lucas | Q-T01-3, ticket 01 |
| D-122 | 2026-10-09 | **Líder dormindo não esconde a Team**: só uma sessão encerrada a esconde; os "sem sinal" ficam cinza no lugar (R7); o limite por área é do ticket 13 | Lucas | Q-T01-4, ticket 01, ticket 13 |
| D-123 | 2026-10-09 | **Só dorme quem está parado (`IDLE`)**: sessão presa em atividade (CLI morto) não dorme; "esperando você" nunca dorme | Lucas | Q-T01-5, R31 |
| D-124 | 2026-10-13 | **Codex: `inter_agent_communication_metadata` e `event_msg/thread_settings_applied` ficam ignorados.** O primeiro só traz `trigger_turn`; o segundo repete o modelo que já vem de `turn_context` e carrega `developer_instructions`. Mostrar esforço de raciocínio ou política de aprovação exige antes um sinal novo no PROTOCOL.md | Lucas | Q-T02-1, D-089, [adapters/CODEX.md](adapters/CODEX.md) §8 |
| D-125 | 2026-10-13 | **`agent_message` do Codex aparece como narração simples**, sem prefixo de quem fala e **sem deduplicar** entre a thread raiz e as de subagente (a mesma fala pode aparecer duas vezes na Team); autor e destinatário ficam no corpo nativo | Lucas | Q-T02-2, D-089, [adapters/CODEX.md](adapters/CODEX.md) §8 |
| D-126 | 2026-10-13 | **Fidelidade do pensamento sem confirmação estrutural é `raw`**; `summary` só com marcador estrutural (Hermes: `codex_reasoning_items`, regra provisória, nunca vista em dado real) | Lucas | Q-T02-3, R14, [adapters/HERMES.md](adapters/HERMES.md) §1 |
| D-127 | 2026-10-13 | **Sem tabela de modelos para a fidelidade do Hermes:** modelos gpt-5.x pelo caminho de chat ficariam `raw`; a dúvida fica registrada até haver uma sessão real que a comprove | Lucas | Q-T02-4, R14, [adapters/HERMES.md](adapters/HERMES.md) §1 |
| D-128 | 2026-10-13 | **A hora de abertura de sessão e de subagente do Claude e do Hermes** (hoje a hora da leitura, o que deixa 117 de 120 subagentes "sem sinal") **é tratada no ticket 03**, ~~com as datas de início do índice de sessões~~ (ajustado pelo D-132: com a hora da última escrita) | Lucas | achado do ticket 01, ticket 03, R7, R47 |
| D-129 | 2026-10-13 | **O Orb não lê a tabela `project` do opencode** (`worktree`): o invariante 11 fica como está e o adapter continua só em `session_v2` e `session_message`; a pasta (`directory`) sobe até o repositório git no Observatório. Custo aceito: projeto do opencode sem `.git` cujo `worktree` seja uma pasta acima da sessão vira um prédio por subpasta | Lucas | Q-T03-1, R3, invariante 11, [adapters/OPENCODE.md](adapters/OPENCODE.md) |
| D-130 | 2026-10-13 | **Lista de pastas excluídas da detecção mantida** (R3b): a pasta do usuário em si, `AppData` e `Downloads` do usuário, as temporárias (`TEMP`, `TMP`, `TMPDIR`, a do Python, `/tmp`), as de sistema (`SystemRoot`, `ProgramFiles`, `ProgramFiles(x86)`, `ProgramData`) e a raiz do disco; tudo dentro delas também. Limites aceitos: `Temp` fora do ambiente (ex.: `C:\Temp`) e `Downloads` redirecionado não são excluídos | Lucas | Q-T03-2, D-029, R3b |
| D-131 | 2026-10-13 | **Dois projetos com o mesmo nome ganham sufixo numérico pela ordem dos caminhos** (`app`, `app-2`, `app-3`) num mesmo lote; quem já está na cidade nunca muda de id. O id de um nome repetido pode variar entre execuções até o registro local (R36) fixá-lo | Lucas | Q-T03-3, R3, R36 |
| D-132 | 2026-10-13 | **A abertura de sessão e de subagente leva a hora da última escrita** do arquivo (Claude) ou da mensagem que revelou a sessão (Hermes), **não a data de início**: ajusta o D-128 para que um subagente ainda ativo não pisque "sem sinal". O índice guarda `started_at` e `updated_at` | Lucas | Q-T03-4, D-128, R7, R47 |
| D-133 | 2026-10-13 | **Pasta sem repositório git: a pasta da sessão é o projeto, e uma subpasta de um realm já conhecido entra no realm da pasta mãe** (no mesmo lote, a pasta mais curta vem primeiro). Custo aceito: subpasta vista antes da pasta mãe nasce como prédio separado | Lucas | Q-T03-5, D-031, R3a |
| D-134 | 2026-10-13 | **Casos de borda das regras de pasta confirmados:** submódulo (`.git` arquivo sem `commondir`) é projeto próprio; worktree cujo repositório principal sumiu não entra (R3d); a raiz que o provider informa só vale se contém a pasta da sessão (senão sobe até o git); repositório git na pasta do usuário (dotfiles) não engole os projetos abaixo dele; `--cwd` segue como apelido de `--realm` (depuração). Custo aceito: worktree órfão com sessão antiga não aparece na cidade | Lucas | Q-T03-6, D-029, D-031, R3b, R3d |
| D-135 | 2026-10-13 | **O registro local vive no pacote próprio `orb.registry`** (borda de I/O; o Core só conhece a interface `NameSource`), no arquivo `registry.db` em `%LOCALAPPDATA%\the-orb\` (fora do Windows, `$XDG_DATA_HOME` ou `~/.local/share`), com o esquema versionado por `PRAGMA user_version`. Hoje só as tabelas `names` e `bag`; o Chronicle, o XP e os pontos de parada entram nos tickets deles | Lucas | Q-T04-1, R36, D-062 |
| D-136 | 2026-10-13 | **"Sem gêmeos na sala" age no sorteio e o nome guardado nunca muda:** hoje "visível" é todo personagem do mesmo realm que o mundo conhece (a sala de 10 dias é o ticket 06); o nome em uso é pulado e continua na sacola; se só restarem nomes em uso, sai um de fora da sacola. Se uma sessão antiga volta e coincide com outra, os dois ficam iguais (só depois de mais de 60 sorteios) | Lucas | Q-T04-2, R37, D-064 |
| D-137 | 2026-10-13 | **Falha do registro degrada sem derrubar:** enquanto o disco falha (pasta sem permissão, arquivo corrompido, banco travado, registro de um Orb mais novo) os nomes vêm de uma cópia em memória que segue a mesma sacola; o disco é tentado de novo a cada pedido; o arquivo nunca é apagado nem alterado; `/config` informa o motivo em `registry_error`. Custo aceito: nomes sorteados durante a falha se perdem ao reiniciar | Lucas | Q-T04-3, R36 |
| D-138 | 2026-10-13 | **Invariante 3 reescrito:** a única escrita nos arquivos de **terceiros** é o Terminal Host levando ao CLI o que o Lucas digitou; o Orb grava só nos **próprios** arquivos (registro local, R36, e preferências, R29). Providers e projetos continuam só leitura (CLAUDE.md §4 e ARCHITECTURE §2) | Lucas | Q-T04-4, R16, R36 |
| D-139 | 2026-10-13 | **O nome histórico aparece em três lugares**, sempre em texto neutro: no rótulo do personagem (V-EGO-8, V-EGO-11), no cartão da sessão do overview (V-HUD-2) e na dica dos pontos da lista de realms | Lucas | Q-T04-5, R37, VISUAL.md §4 |
| D-140 | 2026-10-13 | **A presença das sessões da sala vem do índice:** cada sessão dos últimos 10 dias que o índice lista ganha um evento `session.updated` (título, modelo, pasta; hora = última atividade), uma vez, para os 4 providers. Não muda o estado do personagem. É assim que o Hermes e o opencode, que só falam com mensagem nova, aparecem na sala | Lucas | Q-T06-1, R28a, R48 |
| D-141 | 2026-10-13 | **Sala = Alter Egos com o último evento nos últimos 10 dias** (o mundo marca `in_room`); **o Histórico do realm é o que o índice lista como mais antigo**, pedido sob demanda no `/world` (até 1000 por pedido, com o total sempre junto; sessão sem data legível conta como antiga). Mostra nome, provider, título e datas; **o nome só aparece se a sessão já ganhou um** (D-064: o nome nasce quando a sessão aparece; não se sorteia nome para o passado) | Lucas | Q-T06-2, R28a, D-035, D-064 |
| D-142 | 2026-10-13 | **O ritmo de leitura vale para o mundo todo:** 250 ms enquanto alguma sessão da sala estiver ativa; senão 2 s; a varredura de sessões novas segue a cada 2 s (ajusta a D-087, que falava em realms). Custo aceito: um realm parado é lido a 250 ms se outro estiver ativo | Lucas | Q-T06-3, D-087 |
| D-143 | 2026-10-13 | **Sessão da sala criada antes de o Orb abrir é lida só do fim:** nada é relido; só as criadas nos últimos 30 min antes de abrir são lidas desde o começo. O passado é da camada de histórico (R48, ticket 25) | Lucas | Q-T06-4, R48 |
| D-144 | 2026-10-13 | **As sessões da sala gastam nomes da sacola ao subir** (hoje ~34 nesta máquina); com mais de 60 na sala os nomes repetem entre salas diferentes (D-136) | Lucas | Q-T06-5, D-064, D-136 |
| D-145 | 2026-10-13 | **`--lookback` continua como opção de depuração** que só estreita a leitura do conteúdo; a sala e o Histórico seguem o valor único `rules.RECENT_SESSION_SECONDS` | Lucas | Q-T06-6, R3, R28a |
| D-146 | 2026-10-13 | **O arquivo de preferências é `preferences.json`, JSON legível com `version`, na pasta do Orb ao lado do `registry.db`**, gravado de uma vez (arquivo temporário e troca). Opções desconhecidas são preservadas; arquivo ilegível ou com valor inválido volta aos padrões, avisa na tela e é copiado para `.bad` antes de ser reescrito | Lucas | Q-T07-1, R29, D-030, D-032 |
| D-147 | 2026-10-13 | **Realm escondido é guardado pelo caminho do projeto** (o id pode ganhar sufixo): sai da cidade e do Mankind, **continua detectado e lido**; eventos e linhas de Inner World dele não são distribuídos. Uma sessão esperando o Lucas num realm escondido **não acende nada** (sem feixe de espera) | Lucas | Q-T07-2, R3c, D-022 |
| D-148 | 2026-10-13 | **O prazo das sessões recentes vai de 1 a 365 dias** (padrão 10) e vale **na hora, sem reiniciar**: aumentar traz sessões para a sala, diminuir manda para o Histórico do realm | Lucas | Q-T07-3, R28a, D-027 |
| D-149 | 2026-10-13 | **A tela de configurações é uma janela aberta pelo ⚙ da barra de cima**, com a lista de realms (caixa por realm) e as opções numéricas montadas de uma tabela do servidor (`SETTINGS`); **as mudanças valem na hora, sem botão Salvar**. Os tickets 09 e 11 só acrescentam linhas à tabela | Lucas | Q-T07-4, R29, V-HUD-5, V-HUD-7 |
| D-150 | 2026-10-13 | **Qualquer cliente autorizado do `/world` (token por execução e `Origin` local) pode mudar as preferências**, e a mudança vale para todos os conectados. Dois cliques simultâneos em clientes diferentes podem se sobrepor | Lucas | Q-T07-5, R29 |
| D-151 | 2026-10-14 | **Fronteiras das classes de prédio:** cada faixa **começa** no número da tabela (`rules.BUILDING_CLASSES`): 1.000 já é Sobrado, 5.000 Prédio, 20.000 Edifício, 100.000 Torre e 500.000 Arranha-céu. O texto da VISUAL §8 ("até 1 mil", "1 mil a 5 mil") incluía a fronteira nos dois lados; esta regra desfaz o conflito | Lucas | Q-T09-1, R19, D-052, D-091 |
| D-152 | 2026-10-14 | **Arquivo rastreado que o `.gitignore` também ignora não conta**; arquivo que o git ainda não acompanha também não | Lucas | Q-T09-2, R19, D-053 |
| D-153 | 2026-10-14 | **O Probe lê o git executando só `git ls-files`** (`--no-optional-locks`, sem as variáveis que redirecionam o git, `core.fsmonitor=false`, sem entrada, máximo de 30 s): lista nomes, nada grava e nada do projeto roda. Sem git ou sem repositório, o realm fica **sem número** (nunca um zero) e a tela de configurações diz o motivo | Lucas | Q-T09-3, invariante 3, R16 |
| D-154 | 2026-10-14 | **Ficam de fora da contagem:** link, pasta (submódulo), binário (byte nulo no começo; UTF-16 com BOM conta como texto) e arquivo de mais de 2 MB. Contam as linhas que não são só espaço; comentário conta | Lucas | Q-T09-4, R19, D-053 |
| D-155 | 2026-10-14 | **"Quando as alterações locais mudam" = uma impressão digital por minuto por realm** (arquivos que contam, tamanho, data e filtro): só conta de novo se mudou; um realm por vez, numa thread própria. O gatilho real fica para o Probe do git (ticket 11) | Lucas | Q-T09-5, D-055 |
| D-156 | 2026-10-14 | **A lista visível de arquivos gerados:** lockfiles (npm, yarn, pnpm, poetry, pipenv, uv, cargo, gem, composer, `go.sum`), `*.min.js`, `*.min.css`, `*.map`, `dist/*` e `build/*`; padrão sem `/` vale para o nome em qualquer pasta, com `/` para o caminho. Editável na tela de configurações | Lucas | Q-T09-6, D-054 |
| D-157 | 2026-10-14 | **O filtro de linhas se edita na tela de configurações** em duas camadas: o de todos os realms (caixa `.md`, lista de padrões, "Restaurar a lista padrão") e, por realm, usar o de todos ou um próprio que muda só o que precisa. O realm que o Lucas mexe é contado na hora e na frente | Lucas | Q-T09-7, D-056, R29 |
| D-158 | 2026-10-14 | **`realm.metrics` tem `loc` (inteiro ≥ 0) e `files?`**; a classe não vai no evento, **o mundo a deriva** (R47); o protocolo passa a **0.3** (parcial: os outros sinais chegam nos tickets deles) e `floors?` fica para o ticket 10 | Lucas | Q-T09-8, R49, D-085, D-099 |

## Decisões revistas

| Id | Decisão original | Substituída por |
|---|---|---|
| D-010 (parte) | "O Alter Ego é uma persona persistente que pode trocar de Claude para Codex" | D-010: o Alter Ego é uma sessão |
| D-011 (parte) | "Intrusive Thoughts" como conceito próprio | D-011 e D-015 |
| — | Painel 2D de validação como cliente do MVP | D-016 (mundo 3D) |
| — | Godot 4 como cliente 3D | D-016 (web, Three.js); `clients/godot/` fica como alternativa |
| — | Realms informados por caminho (`--realm`, `--root`) | D-018 (detectados pelos providers) |
| — | Janelas "esmaecem com o tempo" após uma edição (visão original) | D-028 e D-043: a janela mostra a alteração local enquanto ela existir, só acesa ou apagada |
| D-020 (parte) | Cor da janela = cor do provider que editou (proposta) | D-020 e D-026: cores do git |
| D-028 (parte) | "Cada janela é um arquivo" | D-038 e D-039: cada janela é uma parcela de x% das alterações locais; um arquivo alterado nunca é dividido |
| D-037 | Cores anteriores dos providers (Claude laranja-coral, Codex verde-água, Hermes violeta, opencode azul) | D-037 |
| D-036 (parte) | Áreas em tons frios e neutros | D-040: áreas sem cor própria (ícone e nome) |
| — | Janela "esmaece com o tempo" (visão original) | D-043: só acesa ou apagada |
| — | Subagente some depois de 5 min sem atividade (heurística da v1 do cliente) | D-045: fica cinza |
| — | Cidade num disco flutuante, prédios em anel e depois em grade alfabética simples (v1 do cliente) | D-046 e D-047: cidade retangular com bairros por letra |
| D-049 | Altura = percentual do maior realm (o maior prédio define o tamanho dos outros) | D-051 e D-052: escala absoluta por classes |
| D-048 (parte) | "Altura por percentual" | D-051: a altura depende só das linhas do próprio projeto |

## Pendências que ainda precisam de decisão

Ficam no documento do assunto; aqui só o índice.

| Id | Pergunta | Onde |
|---|---|---|
| V-PEND-1c | ~~A janela também esmaece pela recência?~~ Decidido em D-043: só acesa ou apagada | [VISUAL.md](VISUAL.md) |
| V-PEND-2b | ~~Quando aparece "dormindo"?~~ Decidido em D-044: 15 min parada | [VISUAL.md](VISUAL.md) |
| V-PEND-7c | ~~As novas cores dos providers colidem~~ Decidido em D-040: áreas sem cor própria | [VISUAL.md](VISUAL.md) |
| V-PEND-7d | Os tons exatos (hex) dos providers e do magenta, e os ícones das 5 áreas | [VISUAL.md](VISUAL.md) §5 |
| V-PEND-8 | ~~Peso de uma alteração~~ Decidido em D-041: linhas alteradas | [VISUAL.md](VISUAL.md) §6 |
| V-PEND-9 | ~~Valor de x~~ Decidido em D-042: 5% | [VISUAL.md](VISUAL.md) §6 |
| V-PEND-3 | ~~Subagente sem sinal de fim no nível 0~~ Decidido em D-045: fica cinza | [VISUAL.md](VISUAL.md) |
| V-PEND-3b | ~~Cinza de "sem sinal" × cinza do opencode~~ Decidido em D-050 | [VISUAL.md](VISUAL.md) |
| V-PEND-5 | ~~Posição dos prédios na cidade~~ Decidido em D-046; traçado delegado (D-047) | [VISUAL.md](VISUAL.md) §7 |
| V-PEND-6 | ~~Escala da altura~~ Decidido em D-051; escala delegada (D-052) | [VISUAL.md](VISUAL.md) §8 |
| V-PEND-7b | ~~As novas cores das áreas e do "esperando o Lucas"~~ decidido em D-036, revisto pela V-PEND-7c | [VISUAL.md](VISUAL.md) |
| D-REALM-3 | ~~Aparência de um realm parado há muito tempo~~ Decidido em D-059: "noite" | [ARCHITECTURE.md](ARCHITECTURE.md) |
| R6 | O Perfil do Alter Ego: nome (D-063) e papel (D-069) decididos; aparência e o que se compartilha entre sessões seguem em aberto; XP em proposta (Q-XP) | [VISION.md](VISION.md) §7 |
| — | Questões de [VISION.md](VISION.md) §7 e dos adapters ([CODEX.md](adapters/CODEX.md) §10, risco do observador com aprovações) | — |

### Próxima rodada (aberta em 2026-10-08)

Perguntas levantadas a partir de [VISION.md](VISION.md) §7 e das decisões já tomadas, cada uma com
uma proposta. Ao decidir, a resposta vira um D-NNN acima e a linha fica riscada.

| Id | Pergunta | Proposta |
|---|---|---|
| ~~Q-LOC-1~~ D-053 | **O que conta como linha** para a altura (R19): linhas em branco e comentários contam? | Contam as linhas **não vazias**; comentários contam (separá-los exigiria entender cada linguagem) |
| ~~Q-LOC-2~~ D-054 | **Arquivos gerados que estão no git** (lockfiles como `package-lock.json`, `*.min.js`, saídas de build versionadas) entram? | Não: uma lista fixa e visível de exclusões conhecidas, além do `.gitignore`, ajustável nas configurações (R29) |
| ~~Q-LOC-3~~ D-055 | **Quando recalcular** as linhas e a classe do prédio? | Ao abrir o Orb e quando as alterações locais do realm mudam, no máximo uma vez por minuto por realm |
| ~~Q-LOC-4~~ D-056 | **Filtro de tipos** (ex.: `.md`): qual o padrão e onde se muda? | Padrão: só código, sem `.md`; muda-se na tela de configurações (R29), por realm ou para todos |
| ~~Q-ROOM-1~~ D-057 | **Sala cheia:** o Rooftop Room tem tamanho fixo. Com muitos Alter Egos e subagentes numa área, o que acontece? | A sala não cresce; cada área mostra até 8 personagens e um contador "+N"; o overview lista todos |
| ~~Q-ROOM-2~~ D-058 | **Nome definitivo** do Rooftop Room (era provisório) | Manter "Rooftop Room" |
| ~~D-REALM-3~~ D-059 | **Realm parado há muito tempo** (nenhuma sessão nos últimos 10 dias): como aparece? | "Noite": a sala do teto apagada (sem personagens), as janelas continuam mostrando as alterações locais; volta a acender quando surge uma sessão |
| ~~Q-UI-1~~ D-060 | **Terminal parado num diálogo** do CLI (atualização, confiança…): como o Orb avisa, sem nunca responder (R16)? | Só nas sessões abertas pelo Orb: um módulo próprio (não o Terminal Host, que não interpreta bytes) reconhece os diálogos conhecidos pelo texto da tela e marca o personagem como "esperando o Lucas" (magenta) |
| ~~Q-GATE-1~~ D-061 | **Gate para uma sessão fechada:** escrever para um Alter Ego cuja sessão terminou | O Gate oferece **reabrir** (retomar) a sessão num terminal novo, com confirmação do Lucas; nunca reabre sozinho |
| ~~Q-DATA-1~~ D-062 | **Persistência:** o Orb guarda o próprio log de eventos (base do Chronicle) ou só lê os providers a cada início? | Um log local do Orb (SQLite, na pasta de preferências do Orb), só com o que o Orb derivou; o conteúdo continua nos providers |
| R6 | **Perfil do Alter Ego** | ~~Precisa da sua visão~~ **D-063: nome histórico sorteado.** O resto do Perfil segue em aberto |
| ~~Q-NAME-1~~ D-064 | **O nome fica com a sessão para sempre** (sala, Histórico do realm, ao reabrir), ou é sorteado de novo a cada abertura? A sacola é **global** (todos os realms)? **Sem gêmeos** na mesma sala? | Fica para sempre; sacola global; sem gêmeos visíveis na mesma sala ([VISUAL.md](VISUAL.md) §9) |
| ~~Q-NAME-2~~ D-065 | **Subagentes** também ganham nome histórico? | Não: são temporários; ficam com o tipo dado pelo CLI (Explore, qa-reviewer…) |
| ~~Q-NAME-3~~ D-066 | **Rótulo do personagem:** como combinar nome, provider e título da sessão? | Nome em destaque ("Einstein"); embaixo, "Claude · <título da sessão>"; a cor já mostra o provider |
| ~~Q-NAME-4~~ D-067 | **A lista dos 60 nomes** ([VISUAL.md](VISUAL.md) §9) está boa? Tira ou põe alguém? | Lista proposta: só pessoas já falecidas, áreas e épocas variadas, com mulheres e brasileiros |

### Próxima rodada (aberta em 2026-10-08, depois dos nomes)

| Id | Pergunta | Proposta |
|---|---|---|
| ~~Q-EGO-1~~ D-068 | **Retomar, bifurcar, limpar, compactar** uma sessão: é o mesmo Alter Ego (mesmo nome) ou um novo? | **Retomar** (`resume`) = o mesmo Alter Ego. **Bifurcar** (`fork`) = um Alter Ego novo, com nome novo, mostrando de quem nasceu. **`/clear` e compactação**: o mesmo Alter Ego quando o provider registra a ligação entre o id antigo e o novo; sem essa ligação, um novo. A confirmar por provider na implementação |
| ~~Q-EGO-2~~ D-069 | **O resto do Perfil** além do nome: papel, aparência, stats | **Papel** derivado do que a sessão mais fez (ex.: mais revisão = "revisor"), mostrado no overview, porque é dado real; **aparência** = só a cor do provider por enquanto; **stats/XP** continuam no backlog |
| ~~Q-WORLD-1~~ D-071, D-072 | **Estilo temático por realm** (a ideia original: TriSafe industrial, CLARA biblioteca…) | Por enquanto **todos os prédios iguais**, diferindo só pelos dados (altura, janelas, sala). Um tema por realm, se vier, é **cenário** escolhido pelo Lucas nas configurações, nunca automático |
| ~~Q-WORLD-2~~ D-073 | **Como o Inner World aparece no 3D** | Agora: o painel de baixo (linha do tempo e terminal), como na v1. Depois: o personagem senta a um **monitor** na sua área com o terminal na tela (já validado no Spike 2). O "mergulho" no personagem fica no backlog |
| ~~Q-PROV-1~~ D-074 | **Outros CLIs** além dos 4 | Nenhum agora. O contrato de adapter já permite incluir um provider novo sem mexer no resto |

### Próxima rodada (aberta em 2026-10-08, depois do design por classe)

| Id | Pergunta | Proposta |
|---|---|---|
| ~~Q-WORLD-3~~ D-075 | **As formas de cada classe** de prédio ([VISUAL.md](VISUAL.md) §8, tabela "Forma"): estão boas? | Proposta na tabela: da Casa (um volume baixo) ao Arranha-céu (torre esguia com recuos escalonados, coroa e antena); todas neutras, sem cor de significado, e o Rooftop Room sempre do mesmo tamanho no topo |

**Fica para a fase de implementação** (não precisa de decisão agora): os tons exatos e os ícones
das áreas (V-PEND-7d, com prévia visual para o Lucas aprovar) e o **teste do observador do Codex
com pedidos de aprovação** (risco principal; com o Lucas acompanhando).

### Próxima rodada: camadas vivas (aberta em 2026-10-08)

As camadas vivas estão descritas em [VISION.md](VISION.md) §5 só como ideia. Antes de virarem
tickets, cada uma precisa de fonte de dado, forma no mundo e limites. Todas respeitam R12
(telemetria real), R16 (somente leitura) e R38 (sem tokens).

| Id | Pergunta | Proposta |
|---|---|---|
| ~~Q-LIVE-1~~ D-076 | **Weather (saúde do realm):** de onde vem o dado? | **Agora, só local:** o resultado dos testes que as sessões rodaram (comando de teste observado e o código de saída dele), sem rede. **Depois, opcional:** o CI do GitHub (pelo `gh`, com a conta do Lucas, só leitura), ligado nas configurações. No mundo: céu limpo sobre o prédio quando os últimos testes passaram, chuva quando falharam, nada quando não há dado |
| ~~Q-LIVE-2~~ D-077 | **Energy (tokens e custo):** o que mostrar e onde? | Tokens e custo **só quando o provider informa** (nunca estimados): por sessão e por realm no overview, e o total de **hoje** na barra de cima. Os limites de uso da conta (o Codex informa) aparecem num painel de Energy |
| ~~Q-LIVE-3~~ D-078 | **Chronicle (a cidade no tempo):** como e desde quando? | Uma **barra de tempo** no rodapé: arrastar mostra a cidade como era (prédios, personagens, janelas). Fonte: o registro local do Orb (R36), então começa no dia em que o Orb passa a registrar. Reconstruir o passado anterior pelo histórico do git fica para depois |
| ~~Q-LIVE-4~~ D-079 | **Archive (o que molda cada sessão):** o que e onde? | Uma aba **Archive** no Inner World: `CLAUDE.md`, `AGENTS.md`, skills e arquivos de memória de cada provider, só **nome, tamanho e data**; o conteúdo só quando o Lucas abrir um arquivo. Somente leitura, nada é reinjetado (já decidido em VISION.md §5) |
| ~~Q-LIVE-5~~ D-080 | **Gate:** onde fica no mundo? | Um **portão na borda da cidade**, de frente para a câmera inicial, fora dos bairros, com a contagem de quem espera o Lucas; clicar abre a lista de esperas de todos os realms e permite escrever para qualquer Alter Ego (pelo terminal dele, R35) |
| ~~Q-LIVE-6~~ D-081 | **Ordem das camadas vivas** | A de VISION.md §5: janelas acesas → Gate → Chronicle → Weather → Energy → Archive |

### Próxima rodada: progressão (aberta em 2026-10-09)

Proposta completa em [PROGRESSION.md](PROGRESSION.md). Tudo respeita R12 (telemetria real), R16
(somente leitura) e R38 (sem tokens).

| Id | Pergunta | Proposta |
|---|---|---|
| ~~Q-XP-1~~ D-101 | **O princípio:** o que é XP no Orb? | **Recibo de trabalho confirmado**: cada ponto aponta para a evidência (teste, commit, subagente) num **extrato**; nada por tokens, custo, mensagens ou tempo esperando; nunca negativa; os agentes nunca a veem (§1) |
| ~~Q-XP-2~~ D-102 | **Fontes e pesos** (tabela v1) | Teste verde 5 (1 a cada 10 min); vermelho → verde 25; commit 10 + 1/20 linhas (teto 40); subagente concluído 3 para o líder (teto 30/dia); **ofício** 1 a cada 5 min ativos (teto 30/dia, para sessões de pesquisa e revisão não ficarem no nível 1); PR mesclado 50 depois, opcional (§3) |
| ~~Q-XP-3~~ D-103 | **Provisória → confirmada** | XP de commit é **provisória** até o commit chegar à branch principal; revertido = **anulada**; 30 dias sem chegar = expira. O nível usa só a confirmada e **pode cair** se um commit for revertido (§3, §4) |
| ~~Q-XP-4~~ D-104 | **Três escalas** | **Alter Ego**, **Realm** (soma dos seus Alter Egos) e **Mankind** (o Orb inteiro), com um **placar por provider** (§2) |
| ~~Q-XP-5~~ D-105 | **Team e continuidade** | A XP dos subagentes vai para o líder; retomar mantém a XP; bifurcar começa do zero e mostra de quem nasceu (R39) |
| ~~Q-XP-6~~ D-106 | **Commits do Lucas** fora das sessões | **Não contam**: o Orb mede os agentes. Continuam nas janelas e na altura do prédio |
| ~~Q-XP-7~~ D-107 | **Curva de níveis** | XP para o nível *n* = k · n · (n − 1), com k = 50 (Alter Ego), 500 (Realm), 2.500 (Mankind); **calibrada com o histórico real** antes do ticket, para a sessão típica ficar entre os níveis 2 e 4 (§4) |
| ~~Q-XP-8~~ D-108 | **Retroativa?** | **Sim**: no primeiro uso, o Orb calcula a XP de todas as sessões antigas em segundo plano, lendo cada uma uma única vez. Alternativa: começar do zero, como o Chronicle (§7) |
| ~~Q-XP-9~~ D-109 | **Conquistas** | 16 medalhas iniciais (Primeiro verde, Fênix, Maestro, Polímata, Cirurgião, …, Panteão), cada uma com recibo e **sem XP**, para não contar o trabalho duas vezes (§5) |
| ~~Q-XP-10~~ D-110 | **Onde aparece** | Nível ao lado do nome; anel de luz ao subir de nível; nível de Mankind na barra de cima com o painel Progressão; nível do realm e barras de XP no overview; aviso de conquista nova. Tudo em **branco neutro**, fora das cores com significado (§6) |
| ~~Q-XP-11~~ D-111 | **Missões** (quests) | **Backlog**: só missões definidas pelo Lucas, cumpridas quando os dados confirmam; nunca geradas automaticamente (§9) |

### Próxima rodada: guia dos agentes (aberta em 2026-10-09)

| Id | Pergunta | Proposta |
|---|---|---|
| ~~Q-DEV-1~~ D-112 | **O conteúdo do [CLAUDE.md](../CLAUDE.md)** está bom? | Fontes da verdade, processo e formato das rodadas, 11 invariantes, regras de dependência e padrões de código, testes, git e como falar com o Lucas. Ele aponta para os documentos em vez de copiá-los, para não divergir |
| ~~Q-DEV-2~~ D-113 | **Os outros providers** também trabalham neste repositório? | Um `AGENTS.md` curto, lido por Codex e opencode (a confirmar o do Hermes), que manda seguir o `CLAUDE.md`, para o guia ser um só |
| ~~Q-DEV-3~~ D-114 | **Branches na implementação** | Documentação continua direto na `main` local. Na implementação, **uma branch e um PR por ticket**, com o PR citando as regras e os critérios de aceite do ticket |

### Próxima rodada: lacunas técnicas (aberta em 2026-10-09)

Encontradas na leitura completa do projeto e conferidas nos dados desta máquina **só pela estrutura**
(nomes de campos e contagens, sem ler conteúdo de sessões). Precisam de decisão antes dos tickets.

| Id | Pergunta | Proposta |
|---|---|---|
| ~~Q-TEC-1~~ D-084 | **Resultado de um comando** (passou/falhou): o Weather (R42) e a XP dependem dele, e o protocolo 0.2 não tem esse sinal | Um sinal novo, `command.result` (`ok`, `exit_code?`), no **protocolo 0.3** (o vocabulário é fechado, então muda a versão). Fonte por provider, conferida: **Codex** `exitCode` no app-server e `item.exit_code` em `event_msg/item_completed` do rollout (2.287 ocorrências; hoje o adapter ignora essa linha); **Hermes** `exit_code` no JSON do resultado do `terminal` (262 de 262); **opencode** `state.metadata.exit` do `bash` (44 de 44); **Claude** **não grava o código**: só `is_error` e `interrupted` no resultado, então `ok` sem `exit_code` |
| ~~Q-TEC-2~~ D-085 | **Eventos que não são de uma sessão** (linhas de código, alterações locais, limites da conta, CI): o Core hoje os ignora | O Core passa a guardar estado **por realm** (métricas, alterações locais, Weather) e **do mundo** (limites da conta), com sinais novos no protocolo 0.3 (`realm.metrics`, `realm.changes`, `account.limits`), produzidos pelos Probes e pelos adapters (ex.: `account/rateLimits/updated` do Codex) |
| ~~Q-TEC-3~~ D-086 | **Onde fica o tempo** ("dormindo" 15 min, "sem sinal" 5 min, "noite" 10 dias, "hoje" da Energy) | **No Core, sem relógio próprio:** `snapshot(now)` recebe a hora de quem pede, e os limites ficam numa tabela em `core/rules.py`. Continua puro e testável, todos os clientes veem o mesmo, e o registro local (R36) guarda o resultado para o Chronicle. O cliente deixa de calcular |
| ~~Q-TEC-4~~ D-087 | **Intervalo de leitura:** a arquitetura diz 250 ms (medido no Spike 1); o servidor usa 500 ms | **250 ms** para realms com sessão ativa (o que foi medido e documentado); varredura de sessões novas a cada 2 s (como o Codex já faz) |
| ~~Q-TEC-5~~ D-088 | **Ler o histórico inteiro** (todos os projetos já registrados, sessões dos últimos 10 dias, XP retroativa) sem perder desempenho | **Duas camadas:** (1) um **índice de metadados** de todas as sessões (pasta, datas, título, provider), barato, para a cidade, a sala e o Histórico do realm; (2) o **conteúdo** lido incrementalmente só das sessões da sala; o passado (XP retroativa) numa leitura única em segundo plano, com o ponto de parada guardado no registro local |
| ~~Q-TEC-6~~ D-089 | **Linhas novas do Codex** que o adapter não conhece: `response_item/agent_message` (139 nos últimos 10 rollouts), `inter_agent_communication_metadata` (134), `event_msg/thread_settings_applied` (126) | Mapear `agent_message` como narração (hoje essa fala do Codex não aparece no Inner World) e avaliar as outras duas; atualizar [adapters/CODEX.md](adapters/CODEX.md) com a versão em que surgiram |
| ~~Q-TEC-7~~ D-090 | **Commits feitos pelo Claude** | O resultado das ferramentas do Claude tem um campo `gitOperation` (`commit`, `push`, `branch`, `pr`) quando a ferramenta mexe no git. Usar como evidência de commit (X-COMMIT em [PROGRESSION.md](PROGRESSION.md)) no lugar de interpretar o comando |

### Próxima rodada: referências (aberta em 2026-10-09)

| Id | Pergunta | Proposta |
|---|---|---|
| ~~Q-REF-1~~ D-091 | **6 classes de prédio ou 5, como o CodeCity?** O CodeCity usa 5 categorias de altura; a D-052 propôs 6 | **Manter 6**: linhas de código vão de centenas a milhões, mais que o número de métodos de uma classe, e a 6ª classe (Arranha-céu) é o destaque que o Lucas pediu (D-051). Fonte em [VISUAL.md](VISUAL.md) §8 |
| ~~Q-REF-2~~ D-092 | **Submódulos do git** nas janelas | O VS Code tem uma cor própria para submódulo (`#8db9e2`, azul). Proposta: **sem janela própria**; a alteração dentro de um submódulo não acende janela do projeto pai (é outro repositório). Evita também um azul que se confundiria com o Codex |

**Correção registrada:** em 2026-10-08 o Claude disse ao Lucas que não havia uma tabela de tipos de
prédio no CodeCity. Há: as 5 categorias de altura por limites, descritas acima e em VISUAL.md §8.

### Próxima rodada: ideias da conversa original (aberta em 2026-10-09)

A conversa de ideação no ChatGPT foi relida inteira a pedido do Lucas. O que não estava nos
documentos entrou em [IDEAS.md](IDEAS.md) §9. Tudo abaixo respeita R12 (só dado real), R38 (sem
tokens) e o orçamento de cores (R20c).

| Id | Pergunta | Proposta |
|---|---|---|
| ~~Q-ORIG-1~~ D-093 | **Progresso da tarefa e Task Board** | Mostrar a **lista de tarefas que o próprio CLI mantém** (TodoWrite do Claude, plano do Codex, `todowrite` do opencode): no overview, "7 de 12" e uma barra na sessão; na área **Task Board**, as tarefas concluídas. Só quando o provider grava a lista; sem lista, nada (nunca estimado). Formato de cada provider a levantar só pela estrutura |
| ~~Q-ORIG-2~~ D-094 | **Subagente que termina** | Ao receber o fim (`subagent.ended`), ele **caminha até o líder** e só então se desmobiliza. Sem sinal de fim, continua a regra R7 (fica cinza no lugar) |
| ~~Q-ORIG-3~~ D-095 | **Erro, bloqueio e "sem sinal" do líder** (hoje sem entrada em VISUAL.md) | Ícones neutros sobre a cabeça, sem cor de significado: **erro** = triângulo branco com "!" e corpo apagado; **bloqueado** = cadeado; **sem sinal** = o mesmo ícone de sinal cortado do subagente (V-EGO-10). Vermelho fica de fora (é do git) |
| ~~Q-ORIG-4~~ D-096 | **Atributos por área** | No overview de cada Alter Ego, **barras da parcela do trabalho em cada área** (Development, Testing, Research, Review), calculadas da mesma contagem do Papel (R40). É dado real e explica o Papel; não vira pontuação |
| ~~Q-ORIG-5~~ D-097 | **Resumo do realm visto de longe** | O rótulo do prédio ganha: sessões ativas, esperando você e, quando houver dado, o **Weather** e as **tarefas abertas** (de Q-ORIG-1). Nada de "saudável" inventado: sem dado, não aparece |

### Próxima rodada: revisão antes dos tickets (aberta em 2026-10-09)

Na revisão de todas as regras e elementos visuais contra a divisão em tickets, apareceram dois pontos
que **nunca foram decididos**:

| Id | Pergunta | Proposta |
|---|---|---|
| ~~Q-REV-1~~ D-115 | **Brilho geral das janelas** (V-REALM-4: mais sessões ativas = janelas mais fortes). Com as janelas mostrando o git (R20) e só acesas ou apagadas (D-043), esse brilho ainda faz sentido? | **Retirar:** a janela acesa tem brilho fixo; a atividade já aparece na sala (personagens trabalhando) e no rótulo. Evita misturar dois dados na mesma janela |
| ~~Q-REV-2~~ D-116 | **Árvore da Team** (VISION.md §5: "a árvore de quem delegou o quê"). Subagentes podem ter subagentes; hoje o overview lista todos no mesmo nível | **No overview**, os subagentes aparecem em árvore (quem criou quem), com o tipo e o estado de cada um; **no mundo**, nada muda (todos na sala, menores) |

### Rodada: o que a implementação do ticket 01 decidiu por conta própria (aberta em 2026-10-09)

Ao implementar o ticket 01 ([.scratch/the-orb-cidade-viva/issues/01-mundo-calcula-o-tempo.md](../.scratch/the-orb-cidade-viva/issues/01-mundo-calcula-o-tempo.md)),
cinco comportamentos **não estavam escritos** e foram escolhidos de forma provisória (regra P2).
**O Lucas confirmou as cinco em 2026-10-09 (D-119 a D-123).** Todos estão cobertos por teste no mundo.

| Id | Pergunta | Proposta (já aplicada, provisória) |
|---|---|---|
| ~~Q-T01-1~~ D-119 | Um subagente **"sem sinal"** (sem atividade há 5 min e sem aviso de fim) ainda segura o líder em `DELEGATING`? | **Não.** Sem isso, um subagente em segundo plano que nunca avisa o fim mantinha a sessão "delegando" para sempre e ela nunca dormia. Custo: um subagente legítimo, mas calado por mais de 5 min, faz o líder voltar a `IDLE` (e, 15 min depois, a dormir) |
| ~~Q-T01-2~~ D-120 | O que conta como **atividade** de um subagente? | **Qualquer evento dele** (resultado, narração, ferramenta), não só os que trazem sinal |
| ~~Q-T01-3~~ D-121 | Os totais de **subagentes ativos** (barra de cima, Mankind) contam os "sem sinal"? | **Não:** não se sabe que ainda trabalham. Eles continuam listados no overview, em cinza |
| ~~Q-T01-4~~ D-122 | Um líder **dormindo** esconde a Team? | **Não** (só uma sessão **encerrada** esconde): os subagentes "sem sinal" ficam cinza no lugar onde estavam, como pede R7. Com muitos, o ticket 13 limita a 8 por área e mostra "+N" |
| ~~Q-T01-5~~ D-123 | Só dorme quem está `IDLE`? Uma sessão presa em `READING`/`CODING` há horas (CLI morto) nunca dorme | **Manter:** é o comportamento que o cliente já tinha, e "esperando você" nunca deve dormir. Alternativa a estudar: sem nenhum evento há mais de X min, qualquer estado de trabalho vira `NO_SIGNAL` |

### Rodada: o que a implementação do ticket 02 decidiu por conta própria (aberta em 2026-10-13)

Ao implementar o ticket 02 ([.scratch/the-orb-cidade-viva/issues/02-ajustes-dos-adapters.md](../.scratch/the-orb-cidade-viva/issues/02-ajustes-dos-adapters.md)),
o que a estrutura dos dados reais mostrou deixou quatro pontos **sem decisão escrita**; foram escolhidos de
forma provisória (regra P2). Todos estão cobertos por teste nos leitores dos CLIs.
**O Lucas confirmou as quatro em 2026-10-13 (D-124 a D-127).**

| Id | Pergunta | Proposta (já aplicada, provisória) |
|---|---|---|
| ~~Q-T02-1~~ D-124 | `inter_agent_communication_metadata` e `event_msg/thread_settings_applied` do Codex: **mapear ou ignorar**? (D-089 deixou os dois "a avaliar") | **Ignorar os dois.** O primeiro só traz `trigger_turn` e vem sempre antes de um `agent_message`; o segundo repete o modelo que já vem de `turn_context` (125 de 125; em threads de subagente o modelo não é lido por ninguém, e o vocabulário não tem modelo do subagente) e carrega `developer_instructions`. Custo: se um dia o Orb quiser mostrar esforço de raciocínio ou política de aprovação, falta o sinal no vocabulário (PROTOCOL.md primeiro) |
| ~~Q-T02-2~~ D-125 | O `agent_message` é **fala entre agentes** (`/root` ↔ `/root/<nome>`), não a fala do Codex ao Lucas que o D-089 supunha. Ele aparece como narração simples ou deve **mostrar quem fala**? | **Narração simples**, como o D-089 decidiu; autor e destinatário ficam no corpo nativo. Na thread raiz aparece o relato do subagente com o mesmo visual da narração do líder, e **a mesma fala pode aparecer duas vezes** na Team (6 de 124 textos distintos estavam gravados na raiz e num subagente; ver CODEX.md §8). Nada é deduplicado. Alternativas: prefixar o texto com "`/root/<nome>` →" (custo: texto fabricado pelo Orb na linha); ou mostrar só o lado de quem recebe, sem repetir (custo: regra de deduplicação entre threads e escolha de qual lado vale) |
| ~~Q-T02-3~~ D-126 | **Fidelidade quando a estrutura não confirma:** `raw` ou `summary`? Confirmado só um modelo (nemotron) no Hermes e no opencode | **`raw` por padrão**; `summary` só com marcador estrutural (Hermes: `codex_reasoning_items`). A regra do marcador `codex_reasoning_items` também é provisória: nunca apareceu em dado real, vem do código do Hermes. Alternativa: marcar `summary` quando não confirmado (afirma menos, mas o rótulo `summary` passaria a significar "não confirmado como bruto") |
| ~~Q-T02-4~~ D-127 | Modelos gpt-5.x no Hermes pelo caminho de chat entregam **resumo sem marcador** e ficariam `raw`. Aceitar até observar uma sessão real ou já criar uma tabela de modelos? | **Aceitar e registrar a dúvida** (HERMES.md §1): nenhuma sessão assim existe nesta máquina para comprovar; a tabela por modelo seria regra sem evidência local |

### Rodada: o que a implementação do ticket 03 decidiu por conta própria (aberta em 2026-10-13)

Ao implementar o ticket 03 ([.scratch/the-orb-cidade-viva/issues/03-realms-detectados-pelos-providers.md](../.scratch/the-orb-cidade-viva/issues/03-realms-detectados-pelos-providers.md)),
seis pontos **não estavam escritos** e foram escolhidos de forma provisória (regra P2). Todos estão cobertos por
teste (as leituras do mundo real e os leitores dos CLIs).
**O Lucas confirmou as seis em 2026-10-13 (D-129 a D-134).**

| Id | Pergunta | Proposta (já aplicada, provisória) |
|---|---|---|
| ~~Q-T03-1~~ D-129 | A spec manda usar a raiz `project.worktree` do opencode, mas o invariante 11 do CLAUDE.md limita o adapter às tabelas `session_v2` e `session_message` (o banco guarda credenciais). Ler também a tabela `project`? | **Não ler.** Mantém o invariante; a pasta (`directory`) sobe até o repositório git, que dá o mesmo projeto na maioria dos casos. Custo: um projeto do opencode sem `.git` cujo `worktree` seja uma pasta acima da sessão vira um prédio por subpasta. Alternativa: liberar a leitura só da tabela `project` e só da coluna `worktree` (ajusta o invariante 11 e `ALLOWED_TABLES`) |
| ~~Q-T03-2~~ D-130 | Quais são as "pastas de sistema ou temporárias" do D-029, além de `AppData`, `Temp` e `Downloads`? | A pasta do usuário **em si** (só ela, não as subpastas); dentro do perfil, `AppData` e `Downloads`; as temporárias (`TEMP`, `TMP`, `TMPDIR`, a do Python, `/tmp`); as de sistema do Windows (`SystemRoot`, `ProgramFiles`, `ProgramFiles(x86)`, `ProgramData`); a raiz do disco. Tudo dentro delas também fica de fora. Limites: uma pasta chamada `Temp` fora do ambiente (ex.: `C:\Temp`) e um `Downloads` redirecionado para outro lugar **não** são excluídos |
| ~~Q-T03-3~~ D-131 | Dois projetos com o mesmo nome em lugares diferentes: qual ganha o sufixo? | Num mesmo lote, a ordem dos caminhos (o primeiro fica com o nome simples, os outros `-2`, `-3`); **quem já está na cidade nunca muda de id**. O id de um nome repetido pode variar entre execuções se a ordem de chegada mudar, até o registro local (R36) fixá-lo. Alternativa: sufixo derivado do caminho (ex.: pasta pai), estável mas menos legível |
| ~~Q-T03-4~~ D-132 | O D-128 fala em "data de início" para a abertura de sessão e de subagente. Um subagente que **ainda trabalha** mas começou há horas piscaria "sem sinal" até o primeiro evento novo | A abertura leva a hora da **última escrita** do arquivo (Claude) ou da mensagem que revelou a sessão (Hermes): um subagente parado há 20 min já nasce sem sinal, e um ativo nasce ativo. O índice guarda as duas datas (`started_at` e `updated_at`) |
| ~~Q-T03-5~~ D-133 | Pasta **sem repositório git**: a própria pasta da sessão é o projeto. E uma subpasta dela? | Uma subpasta de um realm já conhecido entra nele (senão `scripts/a` e `scripts/b` virariam dois prédios); no mesmo lote, a pasta mais curta vem primeiro. Custo: se a subpasta for vista antes da pasta mãe, nasce um prédio separado |
| ~~Q-T03-6~~ D-134 | Casos de borda das regras de pasta que o D-029 e o D-031 não cobrem | **Submódulo** (`.git` arquivo sem `commondir`) é um projeto próprio; **worktree cujo repositório principal sumiu** não entra (R3d); a **raiz que o provider informa só vale se contém a pasta** da sessão (senão sobe até o git); um **repositório git na pasta do usuário** (dotfiles) não engole os projetos abaixo dele; `--cwd` segue como apelido de `--realm` (depuração) |

### Rodada: o que a implementação do ticket 04 decidiu por conta própria (aberta em 2026-10-13)

Ao implementar o ticket 04 ([.scratch/the-orb-cidade-viva/issues/04-registro-local-e-nome-historico.md](../.scratch/the-orb-cidade-viva/issues/04-registro-local-e-nome-historico.md)),
cinco pontos **não estavam escritos** e foram escolhidos de forma provisória (regra P2). Todos estão cobertos por
teste (o mundo e o registro local numa pasta temporária).
**O Lucas confirmou as cinco em 2026-10-13 (D-135 a D-139).**

| Id | Pergunta | Proposta (já aplicada, provisória) |
|---|---|---|
| ~~Q-T04-1~~ D-135 | Onde vive o registro local e como é o arquivo? | Pacote próprio `orb.registry` (borda de I/O; o Core só conhece a interface `NameSource`), arquivo `registry.db` em `%LOCALAPPDATA%\the-orb\` (fora do Windows, `$XDG_DATA_HOME` ou `~/.local/share`), esquema versionado por `PRAGMA user_version`. Hoje só as tabelas `names` e `bag`; o Chronicle, o XP e os pontos de parada entram nos tickets deles |
| ~~Q-T04-2~~ D-136 | "Nunca dois nomes iguais **visíveis na mesma sala**": o que é "visível" hoje, e se um nome já guardado coincide com outro na sala? | Hoje (a sala de 10 dias é o ticket 06) vale **todo personagem do mesmo realm que o mundo conhece**. A regra age **no sorteio**: o nome em uso é pulado e continua na sacola; se **todos** os que restam estão em uso, sai um nome de fora da sacola, que não é descartada (não ter gêmeos vale mais que esgotar a sacola). O nome já guardado **nunca muda** (é identidade): se uma sessão antiga volta e coincide com outra na sala, os dois ficam iguais (só possível depois de mais de 60 sorteios). Quando a sacola esvazia, a nova pode começar pelo último nome da anterior. Alternativa: renomear a sessão mais nova (fere o "para sempre") |
| ~~Q-T04-3~~ D-137 | O que fazer quando o disco falha (pasta sem permissão, arquivo corrompido, registro de um Orb mais novo)? | **Degradar sem derrubar:** enquanto o disco falha, os nomes vêm de uma cópia em memória que segue a mesma sacola; o disco é tentado de novo a cada pedido; o arquivo **nunca é apagado nem alterado**, e `/config` informa o motivo em `registry_error` (nenhuma tela mostra hoje; a tela de configurações do ticket 07 pode mostrar). Custo: nomes sorteados durante a falha se perdem ao reiniciar. Alternativa: parar o servidor |
| ~~Q-T04-4~~ D-138 | O invariante 3 do CLAUDE.md e a regra de ARCHITECTURE §2 diziam "a única escrita é o Terminal Host". O registro local grava | Reescritos como: a única escrita nos arquivos de **terceiros** é o Terminal Host; o Orb grava só nos **próprios** arquivos (registro local R36 e preferências R29). Nada muda para providers e projetos, que continuam só leitura |
| ~~Q-T04-5~~ D-139 | Além do rótulo do personagem, o nome aparece no **cartão da sessão** do overview e na dica dos pontos da lista de realms? | **Sim**, em texto neutro (sem cor nova; V-HUD-2). Sem isso o Lucas não ligaria o cartão ao personagem. Alternativa: só no rótulo |

### Rodada: o que a implementação do ticket 06 decidiu por conta própria (aberta em 2026-10-13)

Ao implementar o ticket 06 ([.scratch/the-orb-cidade-viva/issues/06-sala-recentes-e-historico-do-realm.md](../.scratch/the-orb-cidade-viva/issues/06-sala-recentes-e-historico-do-realm.md)),
seis pontos **não estavam escritos** e foram escolhidos de forma provisória (regra P2). Todos estão cobertos por teste (o
mundo, os leitores dos CLIs e as leituras do mundo real). **O Lucas confirmou as seis em 2026-10-13 (D-140 a D-145).**

| Id | Pergunta | Proposta (já aplicada, provisória) |
|---|---|---|
| ~~Q-T06-1~~ D-140 | Hermes e opencode só emitem evento quando há mensagem nova: como uma sessão deles dos últimos 10 dias entra na sala? | O **índice** (camada 1) dá a presença: cada sessão da sala ganha um evento `session.updated` (título, modelo, pasta; hora = última atividade), uma vez. Vale para os 4 providers e não muda o estado do personagem. Alternativa: cada leitor anunciar as sessões da janela (mais código por provider) |
| ~~Q-T06-2~~ D-141 | O que é a sala e o que vai ao Histórico do realm? | Sala = Alter Egos cujo **último evento** é dos últimos 10 dias; o mundo marca `in_room`. O Histórico é o que o **índice** lista como mais antigo (até 1000 por pedido, com o total sempre junto; sessão sem data legível no índice conta como antiga), pedido sob demanda no `/world` (fora do snapshot, que sai várias vezes por segundo). Mostra nome, provider, título e datas; o **nome só aparece se a sessão já ganhou um** (D-064: o nome é sorteado quando a sessão aparece; sortear 80 nomes para o passado esvaziaria a sacola). Alternativa: sortear nome para todas |
| ~~Q-T06-3~~ D-142 | "250 ms nos realms com sessão ativa" e "2 s nos novos": por realm ou no mundo todo? | **No mundo todo:** 250 ms enquanto **alguma** sessão da sala estiver ativa (não dorme); senão 2 s. Cada leitor já espaça a descoberta de sessões novas a cada 2 s. Ritmo por realm exigiria um leitor por realm (hoje há um por provider, por desempenho). Custo: um realm parado é lido a 250 ms se outro estiver ativo |
| ~~Q-T06-4~~ D-143 | Sessão da sala criada antes de o Orb abrir: ler o conteúdo desde o começo? | **Não:** só do fim (nada é relido; o passado é a camada de histórico, R48/ticket 25). Só as criadas nos últimos 30 min antes de abrir são lidas desde o começo (como já era). Consequência: a linha do tempo de uma sessão de ontem começa vazia |
| ~~Q-T06-5~~ D-144 | As sessões que entram na sala ao subir gastam nomes da sacola de 60 | Aceito: nesta máquina são ~34 sessões. Com mais de 60 sessões na sala os nomes passam a repetir entre salas diferentes (D-136) |
| ~~Q-T06-6~~ D-145 | O que `--lookback` faz agora? | Opção de depuração que só **estreita a leitura do conteúdo**; o padrão é a sala inteira (10 dias). A sala e o Histórico seguem o valor único de `rules.RECENT_SESSION_SECONDS` |

### Rodada: o que a implementação do ticket 07 decidiu por conta própria (aberta em 2026-10-13)

Ao implementar o ticket 07 ([.scratch/the-orb-cidade-viva/issues/07-preferencias-e-configuracoes.md](../.scratch/the-orb-cidade-viva/issues/07-preferencias-e-configuracoes.md)),
cinco pontos **não estavam escritos** e foram escolhidos de forma provisória (regra P2). Todos estão cobertos por teste (o
mundo e as leituras do mundo real, com o arquivo numa pasta temporária). **O Lucas confirmou as cinco em 2026-10-13 (D-146 a D-150).**

| Id | Pergunta | Proposta (já aplicada, provisória) |
|---|---|---|
| ~~Q-T07-1~~ D-146 | Formato e lugar do arquivo de preferências | `preferences.json` na pasta do Orb, ao lado do `registry.db`, em JSON legível com `version`, gravado de uma vez. Separado do SQLite: o Lucas pode abrir e entender. Opções desconhecidas são preservadas; arquivo ilegível vira padrões e é copiado para `.bad` antes de ser reescrito. Alternativa: uma tabela no `registry.db` |
| ~~Q-T07-2~~ D-147 | Como guardar "este realm está escondido"? | **Pelo caminho do projeto** (normalizado), não pelo id: o id pode ganhar sufixo (`app-2`) conforme a ordem de chegada. Escondido sai da cidade e do Mankind, mas **continua detectado e lido**; consequência: uma sessão esperando o Lucas num realm escondido **não acende nada**. Alternativa: manter o feixe "esperando" mesmo escondido |
| ~~Q-T07-3~~ D-148 | Faixa e efeito do prazo das sessões recentes | **1 a 365 dias** (padrão 10), vale **na hora, sem reiniciar**: aumentar traz para a sala as sessões que já estavam no índice; diminuir manda para o Histórico. Não há opção para desligar a sala |
| ~~Q-T07-4~~ D-149 | Como é a tela | Janela aberta pelo **⚙** da barra de cima; lista de realms com caixa + as opções numéricas, **montada de uma tabela do servidor** (os tickets 09 e 11 só acrescentam linhas). As mudanças **valem na hora**, sem botão Salvar; erro de validação aparece na própria janela. Fecha com Esc, ✕ ou clicando fora |
| ~~Q-T07-5~~ D-150 | Quem pode mudar as preferências | Qualquer cliente conectado ao `/world` (já protegido por token por execução e `Origin` local, como o terminal); a mudança vale para **todos** os conectados (a janela e a cidade se atualizam em cada um). Quem manda a lista inteira de realms escondidos usa o estado que viu por último: dois cliques simultâneos em clientes diferentes podem se sobrepor |

### Rodada: o que a implementação do ticket 09 decidiu por conta própria (aberta em 2026-10-14)

Ao implementar o ticket 09 ([.scratch/the-orb-cidade-viva/issues/09-protocolo-0-3-e-linhas-de-codigo.md](../.scratch/the-orb-cidade-viva/issues/09-protocolo-0-3-e-linhas-de-codigo.md)),
oito pontos **não estavam escritos** e foram escolhidos de forma provisória (regra P2). Todos estão cobertos por teste (o
mundo, as leituras do mundo real e o contador, com pastas de projeto falsas e um repositório git real). **O Lucas confirmou as oito em 2026-10-14 (D-151 a D-158).**

| Id | Pergunta | Proposta (já aplicada, provisória) |
|---|---|---|
| ~~Q-T09-1~~ D-151 | **Conflito no texto (P2):** a VISUAL §8 diz Casa "até 1 mil" e Sobrado "1 mil a 5 mil" (os dois incluem 1.000), e Torre "100 mil a 500 mil" e Arranha-céu "500 mil ou mais" (os dois incluem 500.000). Em que classe caem 1.000 e 500.000? | Cada faixa **começa** no número da tabela, o que segue o "500 mil ou mais" e põe 1.000 em Sobrado (a leitura literal de "até 1 mil" o poria em Casa): 1.000 já é Sobrado, 5.000 Prédio, 20.000 Edifício, 100.000 Torre, **500.000 Arranha-céu** (tabela `rules.BUILDING_CLASSES`) |
| ~~Q-T09-2~~ D-152 | "Arquivos acompanhados pelo git, sem os ignorados": e um arquivo rastreado que o `.gitignore` também ignora? | **Não conta** (`git ls-files -ci --exclude-standard` sai da lista). Arquivo novo que o git ainda não acompanha também não conta |
| ~~Q-T09-3~~ D-153 | Como o Probe lê o git sem violar o invariante 3? | Executa **só `git ls-files`** (com `--no-optional-locks`, `GIT_OPTIONAL_LOCKS=0`, tempo máximo de 30 s): lista nomes, não grava nada e não roda nada do projeto. Sem git instalado ou sem repositório, o realm fica **sem número** (nunca um zero). Alternativa: ler o `.git/index` direto, sem executar o git |
| ~~Q-T09-4~~ D-154 | Quais arquivos de código ficam de fora mesmo rastreados? | Link, pasta (submódulo), arquivo **binário** (byte nulo no começo) e arquivo de **mais de 2 MB**. Contam as linhas que não são só espaço; comentários contam |
| ~~Q-T09-5~~ D-155 | "Recalcula quando as alterações locais mudam": como saber, se o Probe do git (alterações locais) é o ticket 11? | A cada minuto por realm o Probe lista os arquivos e compara uma **impressão digital** (arquivos que contam, tamanho, data e filtro): só conta de novo se mudou. Um realm por vez, numa thread própria, para não atrasar a leitura dos providers. Custo: um `git ls-files` e um `stat` por arquivo, por minuto, por realm visível. Na primeira subida desta máquina os 19 repositórios levaram alguns minutos para ficarem todos contados |
| ~~Q-T09-6~~ D-156 | A lista visível de arquivos gerados (D-054): quais? | Lockfiles (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `npm-shrinkwrap.json`, `poetry.lock`, `Pipfile.lock`, `uv.lock`, `Cargo.lock`, `Gemfile.lock`, `composer.lock`, `go.sum`), `*.min.js`, `*.min.css`, `*.map`, `dist/*` e `build/*`. Padrão sem `/` vale para o nome em qualquer pasta; com `/`, para o caminho. Aparece na tela de configurações e o Lucas edita |
| ~~Q-T09-7~~ D-157 | Como se edita o filtro "por realm ou para todos"? | Na tela de configurações: **todos os realms** (caixa ".md" + lista de padrões, um por linha, com "Restaurar a lista padrão") e **por realm** (escolhe o realm; "usa o filtro de todos" ou um filtro próprio que muda só o que ele precisa). O realm que o Lucas mexe é contado **na hora e na frente**; mudar o filtro de todos reconta todos, um por vez |
| ~~Q-T09-8~~ D-158 | Que campos tem `realm.metrics`? | `loc` (obrigatório, inteiro ≥ 0) e `files?`. A **classe não vai no evento**: o mundo a deriva (R47). A versão passa a **0.3** (parcial: os outros sinais da 0.3 chegam nos tickets deles). `floors?` fica para o ticket 10 |


### Rodada: o que a implementação do ticket 08 decidiu por conta própria (aberta em 2026-10-14)

Ao implementar o ticket 08 ([.scratch/the-orb-cidade-viva/issues/08-cidade-retangular.md](../.scratch/the-orb-cidade-viva/issues/08-cidade-retangular.md)),
sete pontos **não estavam escritos** (o traçado foi delegado na D-047) e foram escolhidos de forma provisória (regra P2). Todos estão cobertos
por teste (o mundo e o Hub, com realms sintéticos). O Lucas responde por número.

| Id | Pergunta | Proposta (já aplicada, provisória) |
|---|---|---|
| Q-T08-1 | O que "projeto novo só reorganiza o seu bairro" garante, se os bairros se leem como um texto? | Os **lotes** (qual prédio fica em qual lote, o deslocamento e o giro) só mudam dentro do bairro do realm novo. Se um bairro cresce ou nasce uma letra, os bairros inteiros se **reposicionam como blocos**, sem mexer no que há dentro deles (e a divisão em fileiras pode mudar). Estabilidade total das posições exigiria bairros de tamanho fixo ou letras reservadas, o que a regra "só existem bairros de letras com realm" proíbe. Alternativa: reservar sempre a mesma área para cada bairro |
| Q-T08-2 | "Semente tirada do nome": qual nome? | O **id do realm** (o nome da pasta em minúsculas, com hífens: `The Orb` é `the-orb`), porque é o que o mundo conhece e não muda. A ordem alfabética, a letra do bairro e a semente (um resumo `blake2b`, igual em qualquer máquina) saem dele. Id que não começa com letra de A a Z vai para "#". Limite: o id já vem sem acento (`Ágil` vira `gil`), então a pasta entra no bairro da letra seguinte, não no "#" |
| Q-T08-3 | Medidas do traçado (a VISUAL §7 não as define) | Lote de 46, calçada de 14, rua de 18, deslocamento de até ±6 e giro de até ±7° (tabela `rules.CITY_*`). A base do prédio (24) nunca encosta no vizinho, mesmo no pior deslocamento e giro (coberto por teste) |
| Q-T08-4 | A proporção 16:9 é exata? | Não: entre as quebras de fileira possíveis, vale a que deixa a cidade **mais perto de 16:9**. Com poucos bairros grandes a proporção pode ficar entre 1,4 e 2,4 (numa simulação com nomes sintéticos e a distribuição de bairros desta máquina, 10 bairros, ficou em 2,25; o teste cobre essa faixa) |
| Q-T08-5 | Um bairro cujos realms estão todos escondidos some? | **Não**: o bairro, a placa e os lotes vagos ficam onde estão, para os outros não andarem (R3c). Alternativa: tirar o bairro vazio e reposicionar os seguintes |
| Q-T08-6 | O que substitui a grade polar do chão (V-CITY-2)? | Nada: as calçadas dos bairros e as ruas entre eles dão a referência de profundidade. O chão usa os tons que já existiam (laje escura, borda de luz, calçada um pouco mais clara) e a placa é a letra em azul-acinzentado: **nenhuma cor nova** e nada que pareça dado |
| Q-T08-7 | Qual a vista da câmera ao abrir o Orb com vários realms? | A **visão geral** da cidade inteira (o mesmo voo do Esc). Com um realm só, ele já abre selecionado, como antes. Os atalhos 1–9, o F, o Esc e o voo continuam |
