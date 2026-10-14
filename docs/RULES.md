# The Orb — Regras do produto

> Tudo o que o Lucas pediu, como **regras numeradas e verificáveis**. É a fonte dos tickets: todo
> ticket cita as regras que cumpre, e uma regra só está "cumprida" quando a implementação a respeita
> e existe forma de verificar. Vocabulário: [CONTEXT.md](../CONTEXT.md) · Visão: [VISION.md](VISION.md)
> · O que cada elemento visual significa: [VISUAL.md](VISUAL.md) · Todas as decisões, em ordem:
> [DECISIONS.md](DECISIONS.md).

Última atualização: 2026-10-14

## Como usar este documento

1. **Uma regra nova nasce aqui** (ou num ADR, se for uma decisão difícil de reverter), antes de
   qualquer código.
2. A coluna **Situação** é a auditoria da implementação atual. Toda regra que não está ✅ vira
   ticket (ver [Do documento aos tickets](#do-documento-aos-tickets)).
3. Ao mudar uma regra, atualize a data e a situação; o que for abandonado continua listado como
   **Revista**, com o motivo (como em [IDEAS.md](IDEAS.md)).

Situação: ✅ cumprida · ⚠️ parcial ou com heurística não decidida · ❌ violada · ⏳ não implementada.

---

## 1. Processo

| # | Regra | Origem | Situação |
|---|---|---|---|
| P1 | **Documentar → criar tickets → implementar**, nessa ordem. Nada é implementado sem a regra escrita e o ticket criado. | Lucas, 2026-10-07 | ❌ O mundo 3D v1, o Observatório e o `--root` foram implementados sem ticket nem especificação visual |
| P2 | Pedido que conflita com uma regra existente é apontado **antes** de implementar, e a decisão fica registrada. | Lucas, 2026-10-07 | ⚠️ Antes: janelas aleatórias contradiziam R12 e R20 sem aviso. Agora em uso: o conflito das cores do git com a legenda foi apontado (VISUAL.md, V-PEND-7) |
| P3 | Nenhuma ideia é apagada; muda de status com motivo. | [IDEAS.md](IDEAS.md) | ✅ |
| P4 | **Toda decisão é registrada** em [DECISIONS.md](DECISIONS.md) (data, quem, onde se aplica) e aplicada no documento do assunto. | Lucas, 2026-10-08 | ✅ |
| P5 | **Fase atual: tickets escritos.** A primeira spec e os 25 tickets estão em `.scratch/the-orb-cidade-viva/` (D-100, D-117). A implementação segue ticket a ticket, pela fronteira (os que não têm bloqueio pendente). | Lucas, 2026-10-08 e 2026-10-09 | ✅ |

## 2. Identidade e domínio

| # | Regra | Origem | Situação |
|---|---|---|---|
| R1 | O projeto se chama **The Orb** (sem "Orb IA", "Orb AI", "Agent World"), inclusive no GitHub. | Lucas | ✅ |
| R2 | **Realm = um projeto = um prédio.** | Visão | ✅ |
| R3 | **Os realms são detectados pelos providers.** Um realm existe porque algum provider tem sessões naquele projeto; o Lucas nunca precisa informar caminhos. Detalhe em [ARCHITECTURE.md](ARCHITECTURE.md) §3 (Detecção de realms). | Lucas, 2026-10-07 | ✅ Detectados pelo índice de sessões dos quatro CLIs, sem informar caminho (ticket 03); `--root` e `--realm` ficam só como opções de depuração |
| R3a | **Todos os projetos que algum CLI já registrou** viram realms, não só os com sessão recente. | Lucas, 2026-10-07 | ✅ Todo projeto do índice vira realm, de qualquer idade; o `--lookback` só limita de quais sessões o conteúdo é lido |
| R3b | **Sessões fora de projeto são ignoradas**: não viram realm. "Fora de projeto" = **a pasta do usuário em si e pastas de sistema ou temporárias** (`AppData`, `Temp`, `Downloads`); qualquer outra pasta é projeto. | Lucas, 2026-10-07 e 2026-10-08 | ✅ Pasta do usuário, `AppData`, `Downloads`, temporárias, de sistema e raiz do disco ficam de fora (ticket 03) |
| R3d | **Projeto cuja pasta não existe mais no disco não entra** na cidade, mesmo que esteja no histórico dos CLIs. | Lucas, 2026-10-08 | ✅ Pasta inexistente não vira realm; um worktree cujo principal sumiu também não (ticket 03) |
| R3c | **O Lucas pode esconder realms**: uma lista com todos os realms detectados, cada um com uma marca; desmarcado = não aparece na cidade. A escolha é do **Orb** (guardada localmente pelo Orb) e nunca altera nada nos providers. | Lucas, 2026-10-07 | ✅ Ticket 07: lista com marca na tela de configurações; desmarcado sai da cidade e continua detectado; a escolha fica em `preferences.json` na pasta do Orb |
| R4 | Um realm pode ter sessões de **vários providers ao mesmo tempo** (ex.: Claude e Codex). | Lucas | ✅ |
| R5 | **Alter Ego = uma sessão.** Carrega e identifica **sozinho** o seu provider, e o título e o modelo vêm do próprio CLI. | Lucas, [ADR 0001](adr/0001-alter-ego-e-uma-sessao.md) | ✅ |
| R6 | O **Perfil** do Alter Ego (identidade além da sessão) está em aberto e **não é implementado** antes de decidido. | Lucas | ✅ (não implementado) |
| R7 | Os **subagentes** de uma sessão aparecem junto dela, como a Team. Quando não há sinal do fim de um subagente (nível 0), ele **fica cinza ("sem sinal") em vez de sumir**. | Lucas; 2026-10-08 (D-045) | ✅ O **mundo** deriva o "sem sinal" e o subagente não some mais; o desenho (cinza translúcido, sem halo, ícone de sinal cortado) foi conferido ao vivo (ticket 01, 2026-10-09). "Sem sinal" = cinza translúcido, sem halo, com ícone de sinal cortado, após 5 min sem atividade (D-050) Subagente antigo já nasce sem sinal, sem parecer "recém-ativo" por 5 min (ticket 03, D-128). |
| R8 | Os 4 CLIs instalados são providers: **claude, codex, hermes, opencode**. | Lucas | ✅ |
| R28 | **Sessões encerradas não são excluídas** do mundo: o Alter Ego continua existindo depois que a sessão termina. | Lucas, 2026-10-07 | ✅ Ticket 06: o Alter Ego continua no mundo depois que a sessão termina (na sala enquanto recente, depois no Histórico do realm) |
| R28a | **Na sala ficam as sessões ativas e as recentes: últimos 10 dias**, prazo **configurável dentro do Orb** (R29). As demais ficam no **Histórico do realm** (a lista de sessões antigas), acessível pelo overview, sem sumir. | Lucas, 2026-10-08 | ✅ Ticket 07: o prazo é uma opção da tela de configurações (1 a 365 dias, padrão 10), vale na hora e fica no arquivo de preferências; sala, Histórico do realm e noite já seguiam o valor único |

## 3. Inner World

| # | Regra | Origem | Situação |
|---|---|---|---|
| R9 | **Inner World = o terminal com o CLI real + a linha do tempo da sessão**, num lugar só. | Lucas, [ADR 0003](adr/0003-inner-world-une-terminal-e-pensamento.md) | ⚠️ O terminal só existe para sessões abertas pelo painel; sessões abertas fora do Orb só têm a linha do tempo |
| R10 | O Inner World é **persistido e reutilizável**: a sessão pode ser reaberta (retomada) num terminal novo. | Lucas | ⏳ `Launch(resume=True)` existe; não há interface nem verificação por provider |
| R11 | O Orb **não rastreia quem escreveu** cada mensagem. | Lucas, 2026-10-07 | ✅ |

## 4. Telemetria e fidelidade

| # | Regra | Origem | Situação |
|---|---|---|---|
| R12 | **Telemetria real, nunca animação inventada.** Todo elemento visual que parece dado **é** dado; o que for só cenário é declarado como cenário em [VISUAL.md](VISUAL.md). | Visão, princípio 1 | ✅ Ticket 11: o padrão aleatório de janelas saiu (V-REALM-3). ~~"Dormindo" e subagente que some são inferências sem decisão~~: decididas em R31 e R7 e derivadas pelo mundo (ticket 01) |
| R12a | **Cenário é permitido** (céu, chão, grade, estrelas, iluminação), desde que **declarado** em VISUAL.md e sem usar cores que tenham significado na legenda. | Lucas, 2026-10-07 | ✅ declarado em VISUAL.md |
| R13 | **Cada provider aparece como ele é** (evento nativo intacto); o mundo usa só sinais derivados. | Lucas, [ADR 0002](adr/0002-eventos-nativos-por-provider.md) | ✅ |
| R14 | **Fidelidade explícita** do pensamento (`raw`/`summary`); nada deduzido aparece como pensamento. | Visão | ⚠️ Codex sempre `summary`; Hermes marca `summary` com o marcador estrutural (`codex_reasoning_items`) e `raw` no resto; opencode `raw`. **Confirmado pela estrutura só no modelo observado** (o mesmo nos dois); as dúvidas por modelo estão em [adapters/HERMES.md](adapters/HERMES.md) §1 e [adapters/OPENCODE.md](adapters/OPENCODE.md) §2 (ticket 02, D-126 e D-127) |
| R15 | **CLI nativo**: o Orb abre um terminal real e chama o CLI original; nenhuma TUI criada. | Visão, ADR 0004 | ✅ |
| R16 | **Não interferência**: tudo do provider é somente leitura; o Orb nunca responde diálogos nem pedidos de servidor. | Visão, ADR 0005, ADR 0006 | ✅ |

## 5. O mundo

| # | Regra | Origem | Situação |
|---|---|---|---|
| R17 | **Mundo 3D navegável**, o produto principal: cidade vista de cima, câmera livre (WASD, scroll, Q/E, botão direito, F, Esc, 1–9, duplo clique para seguir). | Lucas, Visão | ⚠️ Falta "duplo clique segue o personagem" |
| R18 | **Overview por alto** de um realm: o que cada sessão faz agora, quem está esperando o Lucas, subagentes e consumo. | Lucas, 2026-10-07 | ✅ |
| R19 | **Altura do prédio = linhas de código** do projeto, sempre ignorando o `.gitignore`, com filtro (ex.: incluir `.md`). A escala é **absoluta**: a altura depende só das linhas do próprio projeto (nunca do maior prédio), em **classes por faixa de milhares de linhas**, com um salto visível entre classes e uma marca da classe no topo, para o que é grande se destacar de verdade. Escala concreta (delegada): [VISUAL.md](VISUAL.md) §8. **Contagem:** linhas não vazias (comentários contam); sem arquivos gerados versionados (lista visível de exclusões); padrão sem `.md`; recálculo ao abrir e quando as alterações locais mudam, até 1×/min por realm. | Visão (decidido); Lucas, 2026-10-08 (D-051 a D-056) | ⚠️ Ticket 09: contagem de linhas (Probe, só leitura), filtro de tipos e exclusões editáveis (todos os realms ou por realm), recálculo ao abrir e quando algo muda (até 1×/min por realm), classe derivada pelas faixas fixas e mostrada no rótulo e no overview. **Ticket 10:** a altura em níveis (absoluta, com saltos entre as classes) vem do mundo e o prédio é desenhado nela; decisões D-166 a D-171 |
| R20 | **Andares = pastas de primeiro nível; janelas acendem onde há alteração local**, e a janela só tem dois estados: **acesa ou apagada** (~~esmaece com o tempo~~, revisto em D-043). | Visão (camadas vivas); Lucas, 2026-10-08 | ✅ Ticket 11: os andares (térreo, uma pasta por andar, "demais pastas", ticket 10) acendem janelas pelas alterações locais; a janela só tem dois estados e brilho fixo |
| R20a | **A cor de uma janela acesa é a cor do tipo de alteração no git**, com a **paleta de alterações do git do VS Code** (inserção, modificação, remoção, não rastreado, renomeado, conflito). Valores em [VISUAL.md](VISUAL.md) §5. | Lucas, 2026-10-07 e 2026-10-08 | ✅ Ticket 11: a cor da janela é a do tipo de alteração, com os seis valores da VISUAL §5 no código (o tom renderizado, com brilho e *tone mapping*, não foi comparado pixel a pixel) |
| R20b | As janelas mostram as **alterações locais** do projeto (o estado do repositório na máquina: modificado, novo, apagado…). Uma **alteração** é um arquivo com alteração local. Ler esse estado **nunca grava nada** no projeto nem no `.git` (R16). ~~Cada janela é um arquivo~~ (revisto por R20d). | Lucas, 2026-10-08 | ✅ Ticket 11: `git status` e `git diff --numstat` só leitura (`--no-optional-locks`), com tipo e linhas alteradas por arquivo; nada é gravado no projeto nem no `.git` |
| R20d | **Janelas por percentual:** cada janela acesa representa **x% das alterações locais** do realm, com **x = 5%** (configurável no Orb), e **uma alteração nunca fica dividida entre duas janelas**. O peso de uma alteração são as **linhas alteradas**. Como as alterações viram janelas: [VISUAL.md](VISUAL.md) §6. | Lucas, 2026-10-08 (D-038, D-039, D-041, D-042) | ✅ Ticket 11: x = 5% (de 1 a 50, nas configurações), nenhuma alteração dividida, ordem estável pelo caminho, distribuição regular no andar (`core/facade.py`) |
| R20c | **As áreas não têm cor própria**: piso neutro, cada área identificada por **ícone e nome** (e um padrão no piso). O sinal de **"esperando o Lucas"** é **magenta pulsante**. As cores ficam só para janelas (git), personagens (provider) e "esperando". | Lucas, 2026-10-08 (D-036, D-040) | ❌ Hoje as áreas são coloridas (Testing Lab verde, Code Review amarelo…) e "esperando" é âmbar |
| R20e | **Submódulos do git não acendem janela** no projeto pai: são outro repositório. | Lucas, 2026-10-09 (D-092) | ✅ Ticket 11: os submódulos ficam de fora (`--ignore-submodules=all` e o registro de submódulo é descartado) |
| R30 | **Cores dos providers** (corpo e halo do personagem): **Claude laranja · Codex azul · Hermes amarelo · opencode cinza**, em tons saturados. | Lucas, 2026-10-08 (D-037, D-040) | ❌ Hoje Codex é verde-água, Hermes violeta e opencode azul |
| R31 | Uma sessão recente aparece **"dormindo"** na sala depois de **15 min parada**. | Lucas, 2026-10-08 (D-044) | ✅ Derivado pelo mundo (`asleep`, ticket 01); o cliente só desenha |
| R33 | **Sala cheia:** o Rooftop Room não cresce; cada área mostra até **8 personagens** e um contador **"+N"**; o overview lista todos. | Lucas, 2026-10-08 (D-057) | ❌ |
| R34 | **Aviso de diálogo:** nas sessões abertas pelo Orb, um módulo próprio reconhece diálogos conhecidos do CLI pelo texto da tela e marca o personagem como "esperando o Lucas". **Nunca responde** (R16, ADR 0006). | Lucas, 2026-10-08 (D-060) | ⏳ |
| R35 | **O Gate nunca reabre sozinho** uma sessão fechada: oferece reabrir num terminal novo e espera a confirmação do Lucas. | Lucas, 2026-10-08 (D-061) | ⏳ |
| R36 | **Registro local do Orb:** um log próprio (SQLite, na pasta de preferências do Orb) com o que o Orb derivou (eventos do mundo, nomes dos Alter Egos); o conteúdo das sessões continua só nos providers. | Lucas, 2026-10-08 (D-062) | ⚠️ **Ticket 04:** o registro existe (`orb.registry`, `registry.db` na pasta do Orb) e guarda a associação sessão → nome e a sacola de nomes; faltam os eventos do mundo (Chronicle), o índice de sessões, os pontos de parada e o extrato de XP, que entram nos tickets deles |
| R38 | **O Orb não consome tokens.** Só monitora: nenhuma parte do Orb chama modelo de IA (nem para resumir, classificar, nomear ou derivar papel). Tudo vem da telemetria por regras e tabelas. O único consumo é o do Lucas usando o CLI pelo Inner World. | Lucas, 2026-10-08 (D-070) | ✅ Nenhum módulo chama modelo |
| R39 | **Continuidade da sessão:** retomar = o mesmo Alter Ego (mesmo nome); bifurcar = um Alter Ego novo, com nome novo, mostrando de quem nasceu; `/clear` e compactação = o mesmo Alter Ego se o provider liga o id antigo ao novo, senão um novo. | Lucas, 2026-10-08 (D-068) | ⏳ A confirmar por provider |
| R40 | **Papel do Alter Ego** = o que a sessão mais fez (ex.: "revisor"), por contagem das atividades observadas, mostrado no overview. Sem modelo, sem tokens (R38). | Lucas, 2026-10-08 (D-069) | ⏳ |
| R42 | **Weather** = resultado dos testes rodados nas sessões (comando de teste e código de saída), sem rede; céu limpo / chuva / nada. CI do GitHub só depois e opcional, ligado nas configurações, só leitura. | Lucas, 2026-10-09 (D-076) | ⏳ |
| R43 | **Energy** = tokens e custo **só quando o provider informa**, nunca estimados; por sessão, por realm e o total de hoje; limites de uso da conta quando o provider informa. | Lucas, 2026-10-09 (D-077) | ⚠️ Tokens por sessão já aparecem; faltam realm, "hoje" e o painel |
| R44 | **Chronicle** = barra de tempo que mostra a cidade como era, a partir do registro local do Orb (R36). | Lucas, 2026-10-09 (D-078) | ⏳ |
| R45 | **Archive** = aba no Inner World com o que molda a sessão (instruções, skills, memória), só nome, tamanho e data; conteúdo só quando o Lucas abrir; somente leitura. | Lucas, 2026-10-09 (D-079) | ⏳ |
| R46 | **O Gate é um lugar no mundo**: um portão na borda da cidade, fora dos bairros, com a contagem de quem espera o Lucas, a lista de esperas de todos os realms e a escrita para qualquer Alter Ego pelo terminal dele (R35). | Lucas, 2026-10-09 (D-080) | ⏳ Hoje só existem o feixe no prédio e a contagem no topo |
| R50 | **Progresso da tarefa = a lista de tarefas do próprio CLI** (TodoWrite do Claude, plano do Codex, `todowrite` do opencode): "concluídas de total" no overview e as concluídas no Task Board; sem lista gravada pelo provider, nada aparece. | Lucas, 2026-10-09 (D-093) | ⏳ |
| R51 | **Subagente que termina caminha até o líder** antes de se desmobilizar; sem sinal de fim, vale R7. | Lucas, 2026-10-09 (D-094) | ⏳ Hoje ele some depois de 5 min |
| R52 | **Erro, bloqueio e "sem sinal" do líder** aparecem por ícones neutros sobre a cabeça, nunca em vermelho. | Lucas, 2026-10-09 (D-095) | ❌ Hoje esses estados não têm forma própria |
| R57 | **Árvore da Team no overview:** os subagentes aparecem em árvore (quem criou quem), com tipo e estado; no mundo, todos na sala. | Lucas, 2026-10-09 (D-116) | ⏳ Hoje a lista é plana |
| R53 | **XP é recibo de trabalho confirmado:** cada ponto tem evidência no extrato; provisória até o mundo real confirmar (commit na branch principal); nada por tokens, custo, mensagens ou espera; nunca negativa; os agentes nunca a veem. Tabela versionada e recalculável. | Delegada, 2026-10-09 (D-101 a D-103, D-105, D-106) | ⏳ |
| R54 | **Níveis em três escalas** (Alter Ego, Realm, Mankind) pela curva k·n·(n−1), calibrada com o histórico real; o nível usa só a XP confirmada. | Delegada, 2026-10-09 (D-104, D-107) | ⏳ |
| R55 | **Conquistas** de uma vez só, cada uma com recibo, sem XP; lista inicial em PROGRESSION.md §5. | Delegada, 2026-10-09 (D-109) | ⏳ |
| R56 | **Guia dos agentes:** `CLAUDE.md` na raiz é o guia de trabalho; `AGENTS.md` aponta para ele; na implementação, uma branch e um PR por ticket. | Delegada, 2026-10-09 (D-112 a D-114) | ✅ `CLAUDE.md` e `AGENTS.md` existem |
| R41 | **Prédios no mesmo estilo** (sem tema por realm), mas **cada classe de tamanho tem uma forma arquitetônica própria** (Casa a Arranha-céu), como o CodeCity mapeia métricas no tipo do prédio. Um tema por realm, se vier, é cenário escolhido pelo Lucas. | Lucas, 2026-10-08 (D-071, D-072) | ✅ Ticket 10: as 6 formas, neutras, com o Rooftop Room do mesmo tamanho no topo; vistas na tela com dados reais (as seis classes existem nesta máquina) e numa página com métricas sintéticas |
| R37 | **Cada Alter Ego tem um nome histórico** (tecnologia, física, matemática, filosofia), sorteado sem reposição de uma lista de 60 ([VISUAL.md](VISUAL.md) §9), **uma vez, para sempre**, de uma sacola **global**, sem nomes iguais visíveis na mesma sala. **Subagentes não ganham nome** (ficam com o tipo do CLI). O nome é **identidade**, não dado. | Lucas, 2026-10-08 (D-063 a D-067) | ⚠️ Ticket 04: sacola global persistida, nome permanente, subagente sem nome (`orb.core.names`, `orb.registry`); "sem gêmeos na sala" vale no sorteio e pelo **realm inteiro** até a sala de 10 dias (ticket 06), e um nome já guardado nunca muda (D-136) |
| R32 | **A cidade é retangular.** Os prédios ficam em **ordem alfabética**, com um ar **"aleatório", mas rastreável**: a posição vem de uma estrutura lógica e é sempre a mesma para o mesmo realm. Traçado concreto (delegado): [VISUAL.md](VISUAL.md) §7. | Lucas, 2026-10-08 (D-046, D-047) | ⚠️ **Ticket 08:** o mundo calcula bairros por letra, lotes em ordem alfabética e o deslocamento e o giro pela semente do nome (`orb.core.city`); o chão é um retângulo com calçadas, ruas e placas. A estabilidade (projeto novo só mexe no seu bairro, realm escondido deixa o lote vago) e a divisão em fileiras estão em VISUAL §7 e foram confirmadas (D-159 a D-165). Voo da câmera visto na tela (atalho `2`, Esc e a abertura na visão geral; o F não foi testado) |
| R21 | Todo Rooftop Room tem as **5 áreas** do Environment, sempre. | Visão (decidido) | ✅ |
| R22 | O personagem fica na área da **atividade real** da sessão; esperar o Lucas é visível de longe. | Visão | ✅ |

## 6. Engenharia

| # | Regra | Origem | Situação |
|---|---|---|---|
| R23 | **Estrutura sólida por âmbito**: módulos com fronteira e contrato (protocolo, mundo, adapters, terminal, servidor, cliente). | Lucas | ✅ no servidor · ⚠️ no cliente: as regras visuais estão só no código, sem documento (corrigido por VISUAL.md) |
| R24 | **Robustez**: entrada validada na borda, falha isolada, degradação explícita. | Lucas | ✅ |
| R25 | **Desempenho**: leitura incremental, cargas limitadas, nada lido duas vezes, leitores compartilhados. | Lucas | ✅ |
| R26 | **Lógica bem descrita**: regras em tabelas declarativas e documentadas. | Lucas | ⚠️ Mesmo caso da R23 no cliente |
| R47 | **O tempo é derivado num só lugar:** o Core calcula os estados que dependem do tempo (dormindo, sem sinal, noite, "hoje") em `snapshot(now)`, com a hora de quem pede e os limites numa tabela; o Core não lê relógio, e os clientes não calculam. | Lucas, 2026-10-09 (D-086) | ⚠️ Dormindo e sem sinal já vêm do mundo, com a hora do servidor e a tabela de limites (ticket 01); faltam noite e "hoje" (tickets 06 e 20); a abertura de sessão e de subagente do Claude e do Hermes leva a hora da última escrita, não a da leitura (ticket 03, D-128) |
| R48 | **Histórico em duas camadas:** um índice leve de metadados de todas as sessões (cidade, sala, Histórico do realm); o conteúdo é lido incrementalmente só das sessões da sala; o passado é lido uma única vez, em segundo plano, com o ponto de parada no registro local (R36). | Lucas, 2026-10-09 (D-088) | ⚠️ Camada 1 (índice de metadados de todas as sessões) pronta no ticket 03; **Camada 2 pronta no ticket 06** (conteúdo lido só das sessões da sala de 10 dias; as mais antigas só no índice, no Histórico do realm); falta a leitura única do passado em segundo plano (ticket 25) |
| R49 | **Protocolo 0.3:** sinais novos `command.result` (resultado de comando: `ok`, `exit_code?`), `realm.metrics`, `realm.changes` e `account.limits`; o Core guarda estado por realm e do mundo. | Lucas, 2026-10-09 (D-084, D-085; lista de tarefas por D-093) | ⚠️ Ticket 09: protocolo **0.3** com eventos de realm (`alter_ego` nulo), o sinal `realm.metrics` e o estado por realm no Core. **Ticket 11:** `realm.changes` entregue. Faltam `command.result`, `account.limits` e `tasks.updated`, nos tickets deles |
| R29 | **Configurações do Orb ficam dentro do Orb**: uma tela de configurações (realms escondidos, prazo das sessões recentes…) guardada num **arquivo de preferências próprio do Orb**, nunca nos providers e sem parâmetros de linha de comando. | Lucas, 2026-10-08 | ✅ Ticket 07: tela de configurações (⚙) e arquivo próprio `preferences.json` na pasta do Orb; `--root`, `--realm` e `--lookback` seguem só como opções de depuração. As opções dos tickets 09 e 11 entram como linhas da tabela `SETTINGS` (ticket 11: o x das janelas, `window_percent`) |

---

## Do documento aos tickets

**Quando:** só quando o Lucas pedir (P5). Antes, as questões em aberto de VISUAL.md e de
ARCHITECTURE.md §3 (Detecção de realms) precisam estar decididas; o índice está em
[DECISIONS.md](DECISIONS.md).

**Onde:** ~~GitHub Issues do repositório `DevLucasLourenco/The-Orb`~~ **arquivos locais em `.scratch/`, versionados no git** (D-098), com a etiqueta `ready-for-agent`. Nada em issues públicas.

**Organização em épicos** (um por âmbito):

| Épico | Regras principais |
|---|---|
| Processo e documentação | P1, P2 |
| Detecção de realms pelos providers e lista para esconder | R3, R3a, R3b, R3c, R3d |
| Alter Ego e Perfil (nome, papel, continuidade, sessões encerradas e recentes) | R5, R6, R10, R28, R28a, R37, R39, R40 |
| Princípio: o Orb não consome tokens (verificação em todos os épicos) | R38 |
| Protocolo 0.3, estado por realm e do mundo, tempo no Core e histórico em duas camadas | R47, R48, R49 |
| Tarefas da sessão, subagente que volta ao líder, estados de erro do líder, atributos por área | R50, R51, R52, R40 |
| Progressão: XP, níveis e conquistas | R53, R54, R55 |
| Guia dos agentes (`CLAUDE.md`, `AGENTS.md`) | R56 |
| Gate e avisos de diálogo | R34, R35 |
| Registro local do Orb | R36 |
| Configurações do Orb (tela e arquivo de preferências) | R29 |
| Inner World (terminal + linha do tempo, retomada) | R9, R10 |
| Adapters (Claude, Codex, Hermes, opencode) | R7, R8, R13, R14 |
| Mundo 3D: prédios (altura por LOC, forma por classe, andares, janelas por percentual na cor do git) | R12, R12a, R19, R20, R20a, R20b, R20c, R20d, R41 |
| Mundo 3D: cores (providers, áreas, "esperando") | R20c, R30 |
| Mundo 3D: cidade (traçado retangular, bairros, posição dos prédios) | R32 |
| Mundo 3D: personagens dormindo, subagentes sem sinal, sala cheia | R7, R31, R33 |
| Mundo 3D: personagens, áreas, câmera | R17, R21, R22 |
| Overview e camadas vivas, nesta ordem: janelas → Gate → Chronicle → Weather → Energy → Archive (D-081) | R18, R20–R20d, R42–R46 |

**Modelo de ticket:**

```
Título: <verbo> <o quê>                     (ex.: "Detectar realms a partir das sessões dos providers")
Regras: R3, R12                             (as regras que o ticket cumpre)
Contexto: por que, com link para o trecho da documentação
Critérios de aceite: verificáveis, um por linha
Fora do escopo: o que este ticket não faz
Dependências: outros tickets
Pronto quando: critérios cumpridos + testes + documentação atualizada + Situação da regra revista aqui
```
