# The Orb — Registro de decisões

> **Toda decisão tomada sobre o projeto, em ordem**, com a data, quem decidiu e onde ela se aplica.
> É o índice: o detalhe fica no documento do assunto ([RULES.md](RULES.md), [VISUAL.md](VISUAL.md),
> [ARCHITECTURE.md](ARCHITECTURE.md), [adr/](adr/)…). Decisões difíceis de reverter também têm um ADR.
> Nada é apagado: uma decisão revista fica listada, com a que a substituiu.

Última atualização: 2026-10-09

Quem: **Lucas** = decidido por ele · **Delegada** = o Lucas deixou a definição com o Claude; vale até
ele revisar, e a proposta está escrita no documento do assunto.

**Fase atual:** levantamento de ideias e decisões. **Ainda não há tickets** (decisão D-034); a
implementação só volta depois deles (regra P1).

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
| Q-XP-1 | **O princípio:** o que é XP no Orb? | **Recibo de trabalho confirmado**: cada ponto aponta para a evidência (teste, commit, subagente) num **extrato**; nada por tokens, custo, mensagens ou tempo esperando; nunca negativa; os agentes nunca a veem (§1) |
| Q-XP-2 | **Fontes e pesos** (tabela v1) | Teste verde 5 (1 a cada 10 min); vermelho → verde 25; commit 10 + 1/20 linhas (teto 40); subagente concluído 3 para o líder (teto 30/dia); **ofício** 1 a cada 5 min ativos (teto 30/dia, para sessões de pesquisa e revisão não ficarem no nível 1); PR mesclado 50 depois, opcional (§3) |
| Q-XP-3 | **Provisória → confirmada** | XP de commit é **provisória** até o commit chegar à branch principal; revertido = **anulada**; 30 dias sem chegar = expira. O nível usa só a confirmada e **pode cair** se um commit for revertido (§3, §4) |
| Q-XP-4 | **Três escalas** | **Alter Ego**, **Realm** (soma dos seus Alter Egos) e **Mankind** (o Orb inteiro), com um **placar por provider** (§2) |
| Q-XP-5 | **Team e continuidade** | A XP dos subagentes vai para o líder; retomar mantém a XP; bifurcar começa do zero e mostra de quem nasceu (R39) |
| Q-XP-6 | **Commits do Lucas** fora das sessões | **Não contam**: o Orb mede os agentes. Continuam nas janelas e na altura do prédio |
| Q-XP-7 | **Curva de níveis** | XP para o nível *n* = k · n · (n − 1), com k = 50 (Alter Ego), 500 (Realm), 2.500 (Mankind); **calibrada com o histórico real** antes do ticket, para a sessão típica ficar entre os níveis 2 e 4 (§4) |
| Q-XP-8 | **Retroativa?** | **Sim**: no primeiro uso, o Orb calcula a XP de todas as sessões antigas em segundo plano, lendo cada uma uma única vez. Alternativa: começar do zero, como o Chronicle (§7) |
| Q-XP-9 | **Conquistas** | 16 medalhas iniciais (Primeiro verde, Fênix, Maestro, Polímata, Cirurgião, …, Panteão), cada uma com recibo e **sem XP**, para não contar o trabalho duas vezes (§5) |
| Q-XP-10 | **Onde aparece** | Nível ao lado do nome; anel de luz ao subir de nível; nível de Mankind na barra de cima com o painel Progressão; nível do realm e barras de XP no overview; aviso de conquista nova. Tudo em **branco neutro**, fora das cores com significado (§6) |
| Q-XP-11 | **Missões** (quests) | **Backlog**: só missões definidas pelo Lucas, cumpridas quando os dados confirmam; nunca geradas automaticamente (§9) |

### Próxima rodada: guia dos agentes (aberta em 2026-10-09)

| Id | Pergunta | Proposta |
|---|---|---|
| Q-DEV-1 | **O conteúdo do [CLAUDE.md](../CLAUDE.md)** está bom? | Fontes da verdade, processo e formato das rodadas, 11 invariantes, regras de dependência e padrões de código, testes, git e como falar com o Lucas. Ele aponta para os documentos em vez de copiá-los, para não divergir |
| Q-DEV-2 | **Os outros providers** também trabalham neste repositório? | Um `AGENTS.md` curto, lido por Codex e opencode (a confirmar o do Hermes), que manda seguir o `CLAUDE.md`, para o guia ser um só |
| Q-DEV-3 | **Branches na implementação** | Documentação continua direto na `main` local. Na implementação, **uma branch e um PR por ticket**, com o PR citando as regras e os critérios de aceite do ticket |

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

