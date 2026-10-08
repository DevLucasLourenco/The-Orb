# The Orb — Registro de decisões

> **Toda decisão tomada sobre o projeto, em ordem**, com a data, quem decidiu e onde ela se aplica.
> É o índice: o detalhe fica no documento do assunto ([RULES.md](RULES.md), [VISUAL.md](VISUAL.md),
> [ARCHITECTURE.md](ARCHITECTURE.md), [adr/](adr/)…). Decisões difíceis de reverter também têm um ADR.
> Nada é apagado: uma decisão revista fica listada, com a que a substituiu.

Última atualização: 2026-10-08

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

## Pendências que ainda precisam de decisão

Ficam no documento do assunto; aqui só o índice.

| Id | Pergunta | Onde |
|---|---|---|
| V-PEND-1c | ~~A janela também esmaece pela recência?~~ Decidido em D-043: só acesa ou apagada | [VISUAL.md](VISUAL.md) |
| V-PEND-2b | A partir de quanto tempo parada uma sessão recente aparece "dormindo" dentro da sala? | [VISUAL.md](VISUAL.md) |
| V-PEND-7c | ~~As novas cores dos providers colidem~~ Decidido em D-040: áreas sem cor própria | [VISUAL.md](VISUAL.md) |
| V-PEND-7d | Os tons exatos (hex) dos providers e do magenta, e os ícones das 5 áreas | [VISUAL.md](VISUAL.md) §5 |
| V-PEND-8 | ~~Peso de uma alteração~~ Decidido em D-041: linhas alteradas | [VISUAL.md](VISUAL.md) §6 |
| V-PEND-9 | ~~Valor de x~~ Decidido em D-042: 5% | [VISUAL.md](VISUAL.md) §6 |
| V-PEND-3 | Subagente sem sinal de fim no nível 0 | [VISUAL.md](VISUAL.md) |
| V-PEND-5 | Posição dos prédios na cidade | [VISUAL.md](VISUAL.md) |
| V-PEND-6 | Escala da altura | [VISUAL.md](VISUAL.md) |
| V-PEND-7b | ~~As novas cores das áreas e do "esperando o Lucas"~~ decidido em D-036, revisto pela V-PEND-7c | [VISUAL.md](VISUAL.md) |
| D-REALM-3 | Aparência de um realm parado há muito tempo | [ARCHITECTURE.md](ARCHITECTURE.md) |
| R6 | O Perfil do Alter Ego | [VISION.md](VISION.md) §7 |
| — | Questões de [VISION.md](VISION.md) §7 e dos adapters ([CODEX.md](adapters/CODEX.md) §10, risco do observador com aprovações) | — |
