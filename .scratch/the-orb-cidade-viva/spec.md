# Spec: The Orb, a cidade viva

Status: ready-for-agent
Origem: docs/RULES.md (P1 a P5, R1 a R56), docs/DECISIONS.md (D-001 a D-114), docs/VISUAL.md, docs/PROGRESSION.md
Data: 2026-10-09

> Fonte da verdade: os documentos em `docs/`. Esta spec os junta numa só entrega e aponta para eles.
> Se algo aqui divergir de um documento, vale o documento, e a divergência deve ser apontada.
> Vocabulário: [CONTEXT.md](../../CONTEXT.md). Guia de trabalho: [CLAUDE.md](../../CLAUDE.md).

## Problem Statement

O Lucas usa quatro CLIs de IA (Claude Code, Codex, Hermes, opencode) em dezenas de projetos reais, às
vezes vários ao mesmo tempo no mesmo projeto, e cada sessão cria subagentes. Hoje ele não tem um lugar
único para ver o que cada sessão e cada subagente está fazendo, quem está parado esperando por ele, o
que mudou de fato nos projetos, quanto se gastou e se o trabalho está saudável.

A primeira versão do mundo 3D do The Orb prova que a telemetria funciona, mas quebra regras que o
Lucas definiu:

- os projetos (Realms) dependem de caminhos passados na linha de comando, em vez de serem detectados
  pelos próprios providers (viola R3);
- as janelas dos prédios são um padrão aleatório que parece informação e não é (viola R12);
- todos os prédios têm a mesma altura e forma (viola R19 e R41);
- as cores não seguem o orçamento decidido (git nas janelas, provider nos personagens, magenta para
  "esperando"; viola R20a, R20c, R30);
- as sessões encerradas e antigas não têm lugar (R28, R28a), o Alter Ego não tem nome nem papel
  (R37, R40), e as camadas vivas (Gate, Chronicle, Weather, Energy, Archive) não existem;
- as preferências ficam em parâmetros de linha de comando, não dentro do Orb (viola R29).

## Solution

Um mundo 3D navegável que se monta sozinho a partir do que os quatro CLIs já gravam, e que mostra
**só telemetria real**, somente leitura, sem consumir nenhum token:

- **A cidade:** cada projeto que algum CLI já registrou é um prédio (Realm), numa cidade retangular,
  com bairros por letra e posição "aleatória" mas rastreável. A altura vem das linhas de código, em
  seis classes com forma própria (Casa a Arranha-céu). Cada pasta de primeiro nível é um andar, e as
  janelas acendem com as alterações locais do git, na cor do VS Code.
- **O Rooftop Room:** no teto de cada prédio, os Alter Egos (sessões) e os subagentes trabalham nas
  cinco áreas do Environment, conforme a atividade real. Cada Alter Ego tem um nome histórico, um
  papel, a cor do seu provider e ícones neutros para erro, bloqueio, sem sinal e "esperando você".
- **O overview e o Inner World:** o que cada sessão faz agora, a lista de tarefas que o CLI mantém,
  atributos por área, consumo e o terminal real com a linha do tempo da sessão. As sessões antigas
  ficam no Histórico do realm.
- **As camadas vivas, nesta ordem:** janelas → Gate (portão na borda da cidade, com todas as esperas
  e escrita para qualquer Alter Ego) → Chronicle (barra de tempo) → Weather (céu pelo resultado dos
  testes) → Energy (tokens e custo informados) → Archive (o que molda a sessão, só para ver).
- **A progressão:** XP como recibo de trabalho confirmado, níveis em três escalas e conquistas.
- **As preferências do Orb dentro do Orb**, numa tela de configurações e num arquivo próprio, e um
  registro local que guarda o que o Orb derivou.

## User Stories

### A cidade e os realms

1. Como Lucas, quero que os realms sejam detectados a partir das sessões que os quatro CLIs já
   gravam, para nunca precisar informar caminhos de projetos.
2. Como Lucas, quero ver na cidade todo projeto que algum CLI já registrou, não só os recentes, para
   ter o mapa completo do meu trabalho.
3. Como Lucas, quero que sessões abertas na minha pasta de usuário ou em pastas de sistema e
   temporárias (`AppData`, `Temp`, `Downloads`) não virem prédios, para a cidade não se encher de lixo.
4. Como Lucas, quero que um projeto cuja pasta não existe mais no disco não apareça, para a cidade
   refletir o que existe.
5. Como Lucas, quero que worktrees e subpastas de um projeto contem para o projeto principal, para um
   projeto não virar vários prédios.
6. Como Lucas, quero que dois projetos com nomes parecidos (ex.: `trisafe` e `trisafe-enhanced`)
   nunca se misturem, para cada sessão cair no prédio certo.
7. Como Lucas, quero uma lista com todos os realms detectados, cada um com uma marca, para esconder
   da cidade os que não me interessam.
8. Como Lucas, quero que esconder um realm não mude nada nos providers, para o Orb nunca mexer no
   ambiente dos CLIs.
9. Como Lucas, quero uma cidade retangular, com bairros por letra inicial em ordem alfabética, para
   achar um projeto pelo nome.
10. Como Lucas, quero que cada prédio tenha um pequeno deslocamento e giro calculados do nome, para a
    cidade parecer orgânica e ainda assim cada prédio ficar sempre no mesmo lugar.
11. Como Lucas, quero que um projeto novo só reorganize o seu bairro, e que um realm escondido deixe o
    lote vago, para os vizinhos não mudarem de lugar.
12. Como Lucas, quero ver a letra de cada bairro escrita no chão, para me orientar.
13. Como Lucas, quero que a altura de um prédio dependa só das linhas de código dele, para um projeto
    novo nunca encolher os outros.
14. Como Lucas, quero seis classes de prédio (Casa, Sobrado, Prédio, Edifício, Torre, Arranha-céu)
    com saltos de altura entre elas e cintas de luz no topo, para o que é grande se destacar de verdade.
15. Como Lucas, quero que cada classe tenha uma forma arquitetônica própria, para reconhecer o
    tamanho do projeto pela silhueta.
16. Como Lucas, quero que a contagem de linhas ignore o `.gitignore`, os arquivos gerados versionados
    e, por padrão, os `.md`, para a altura refletir código de verdade.
17. Como Lucas, quero ajustar o filtro de tipos e a lista de exclusões nas configurações, por realm ou
    para todos, para contar o que eu considero código.
18. Como Lucas, quero ver no rótulo e no overview o número real de linhas e a classe, para a altura
    nunca ser um mistério.
19. Como Lucas, quero que cada pasta de primeiro nível seja um andar proporcional às suas linhas, com
    os arquivos da raiz no térreo e as pastas pequenas juntas num andar "demais pastas".
20. Como Lucas, quero que as janelas acendam onde há alterações locais do git, na cor do tipo de
    alteração (paleta do VS Code), para ver de longe onde o trabalho está mudando o projeto.
21. Como Lucas, quero que cada janela represente uma parcela de 5% das alterações (configurável), sem
    nunca dividir uma alteração em duas janelas, para a fachada ficar harmônica num projeto com
    centenas de arquivos alterados.
22. Como Lucas, quero que a janela tenha só dois estados, acesa ou apagada, para não confundir idade
    com tipo de alteração.
23. Como Lucas, quero que a fachada não "pisque" a cada leitura, para ela ser estável enquanto nada
    muda.
24. Como Lucas, quero que submódulos do git não acendam janelas no projeto pai, porque são outro
    repositório.
25. Como Lucas, quero que ler o estado do git nunca grave nada no projeto nem no `.git`, para o Orb
    ser só observador.
26. Como Lucas, quero que um realm sem sessão nos últimos 10 dias fique de "noite" (sala apagada),
    para ver de longe o que está parado.
27. Como Lucas, quero que o rótulo do prédio mostre sessões ativas, quem espera por mim e, quando
    houver dado, o Weather e as tarefas abertas, para ler a situação do projeto sem entrar nele.
28. Como Lucas, quero que céu, chão, ruas e estrelas sejam cenário neutro, declarado, para nenhuma
    decoração parecer informação.

### O Rooftop Room, os Alter Egos e os subagentes

29. Como Lucas, quero que cada sessão de qualquer CLI seja um personagem (Alter Ego) no Rooftop Room do
    seu projeto, com o provider identificado sozinho, para ver quem trabalha onde.
30. Como Lucas, quero ver sessões de providers diferentes no mesmo realm ao mesmo tempo, para
    acompanhar Claude e Codex trabalhando juntos.
31. Como Lucas, quero que a cor do personagem mostre o provider (Claude laranja, Codex azul, Hermes
    amarelo, opencode cinza), para reconhecer o CLI de longe.
32. Como Lucas, quero que o personagem fique na área da atividade real (Development Center, Testing
    Lab, Research Center, Code Review, Task Board), para saber o que ele faz sem abrir nada.
33. Como Lucas, quero que as áreas não tenham cor própria e sejam identificadas por ícone, nome e um
    padrão no piso, para as cores servirem só ao git, aos providers e à espera.
34. Como Lucas, quero ver de longe, em magenta pulsante, quando uma sessão espera por mim, para não
    deixar ninguém parado.
35. Como Lucas, quero que cada Alter Ego tenha um nome histórico sorteado de uma sacola de 60 nomes,
    sem repetir até a sacola esvaziar, para distinguir as sessões pelo nome.
36. Como Lucas, quero que o nome fique com a sessão para sempre e que dois personagens visíveis na
    mesma sala nunca tenham o mesmo nome.
37. Como Lucas, quero o rótulo com o nome em destaque e, embaixo, "provider · título da sessão" e a
    última ação, para ler a identidade e o trabalho juntos.
38. Como Lucas, quero ver o papel de cada Alter Ego (ex.: "revisor"), calculado pelo que a sessão mais
    fez, sem nenhuma chamada a modelo.
39. Como Lucas, quero ver barras com a parcela do trabalho de cada sessão em cada área, para entender
    de onde vem o papel.
40. Como Lucas, quero que retomar uma sessão mantenha o mesmo Alter Ego e que bifurcar crie um novo,
    mostrando de quem nasceu.
41. Como Lucas, quero que uma sessão parada há 15 minutos apareça "dormindo", para separar quem
    trabalha de quem parou.
42. Como Lucas, quero que sessões encerradas não sumam: fiquem na sala por 10 dias (configurável) e
    depois no Histórico do realm.
43. Como Lucas, quero que o Rooftop Room não cresça e mostre até 8 personagens por área, com "+N", e
    que o overview liste todos.
44. Como Lucas, quero ver os subagentes de cada sessão como personagens menores da sua Team, na área
    da atividade deles.
45. Como Lucas, quero que um subagente que terminou caminhe até o líder antes de sair de cena, para ver
    a entrega.
46. Como Lucas, quero que um subagente sem sinal de fim fique cinza translúcido, sem halo e com um
    ícone de sinal cortado depois de 5 minutos, em vez de sumir.
47. Como Lucas, quero que erro, bloqueio e "sem sinal" do líder apareçam por ícones neutros sobre a
    cabeça (triângulo com "!", cadeado, sinal cortado), nunca em vermelho.
48. Como Lucas, quero que a Team só fique parada quando nenhum subagente está ativo, para o fim do
    turno do líder não esconder trabalho em andamento.

### Overview, Inner World e terminal

49. Como Lucas, quero selecionar um prédio e ver o overview: o que cada sessão faz agora, quem espera
    por mim, subagentes, consumo e há quanto tempo houve atividade.
50. Como Lucas, quero ver o progresso da tarefa de cada sessão ("7 de 12") a partir da lista que o
    próprio CLI mantém, e nada quando o CLI não grava lista.
51. Como Lucas, quero ver as tarefas concluídas na área Task Board.
52. Como Lucas, quero clicar num personagem e abrir o Inner World: a linha do tempo da sessão, com o
    nome e o texto de cada provider, sem tradução.
53. Como Lucas, quero que todo pensamento mostrado diga se é texto bruto ou resumo do provider, e que
    nada deduzido apareça como pensamento.
54. Como Lucas, quero abrir uma sessão nova de qualquer CLI num realm, num terminal real, e usá-la
    como fora do Orb.
55. Como Lucas, quero reabrir uma sessão antiga num terminal novo, retomando a mesma sessão.
56. Como Lucas, quero que o Orb nunca responda diálogos dos CLIs (atualização, confiança, hooks,
    aprovações) nem envie teclas às cegas.
57. Como Lucas, quero ser avisado quando um terminal aberto pelo Orb está parado num diálogo conhecido
    do CLI, com o personagem marcado como "esperando você".
58. Como Lucas, quero ver no Histórico do realm as sessões antigas, com nome, provider, título e
    datas, e poder reabrir qualquer uma.

### Camadas vivas

59. Como Lucas, quero um Gate, um portão na borda da cidade com a contagem de quem espera por mim em
    todos os realms.
60. Como Lucas, quero clicar no Gate e ver a lista de esperas de todos os realms, e escrever para
    qualquer Alter Ego pelo terminal dele.
61. Como Lucas, quero que, para uma sessão fechada, o Gate ofereça reabrir num terminal novo e espere a
    minha confirmação.
62. Como Lucas, quero uma barra de tempo (Chronicle) no rodapé que mostre a cidade como era em qualquer
    momento desde que o Orb começou a registrar.
63. Como Lucas, quero um céu sobre cada prédio (Weather): limpo quando os últimos testes rodados nas
    sessões passaram, chuva quando falharam, nada quando não há dado.
64. Como Lucas, quero ver tokens e custo só quando o provider informa, por sessão e por realm no
    overview e o total de hoje na barra de cima.
65. Como Lucas, quero um painel de Energy com os limites de uso da conta, quando o provider informa.
66. Como Lucas, quero uma aba Archive no Inner World com o que molda a sessão (instruções, skills,
    memória), mostrando só nome, tamanho e data, e o conteúdo só quando eu abrir.

### Progressão

67. Como Lucas, quero que cada Alter Ego ganhe XP só por trabalho confirmado, com um extrato que mostre
    cada entrada com data, regra e evidência.
68. Como Lucas, quero que gastar tokens, mandar mensagens ou esperar por mim nunca dê XP.
69. Como Lucas, quero que a XP de um commit fique provisória até ele chegar à branch principal, seja
    anulada se for revertido e expire em 30 dias, para o nível refletir o que ficou no projeto.
70. Como Lucas, quero ver o nível de cada Alter Ego ao lado do nome e um anel de luz quando ele sobe de
    nível.
71. Como Lucas, quero ver o nível de cada realm e as barras de XP (confirmada e provisória) no
    overview.
72. Como Lucas, quero ver o nível de Mankind na barra de cima e um painel de Progressão com o extrato,
    as conquistas e o placar por provider.
73. Como Lucas, quero que a XP dos subagentes vá para o líder, que retomar mantenha a XP e que bifurcar
    comece do zero.
74. Como Lucas, quero que os meus commits fora das sessões não deem XP, porque o Orb mede os agentes.
75. Como Lucas, quero que a XP seja calculada também para as sessões antigas, em segundo plano, para a
    cidade já ter níveis no primeiro dia.
76. Como Lucas, quero conquistas de uma vez só (Primeiro verde, Fênix, Maestro, Panteão…), cada uma
    com o seu recibo, e um aviso curto quando uma nova acontece.
77. Como Lucas, quero que a curva de níveis seja calibrada com o meu histórico real antes de valer,
    para a sessão típica ficar entre os níveis 2 e 4.

### Preferências, registro local e câmera

78. Como Lucas, quero uma tela de configurações dentro do Orb (realms escondidos, prazo das sessões
    recentes, x das janelas, filtro de linhas), guardada num arquivo próprio do Orb.
79. Como Lucas, quero que nenhuma preferência dependa de parâmetros de linha de comando.
80. Como Lucas, quero que o Orb guarde localmente o que ele derivou (eventos do mundo, nomes, extrato
    de XP), sem copiar o conteúdo das sessões, que continua nos providers.
81. Como Lucas, quero navegar a cidade com WASD, scroll, Q/E, botão direito, F, Esc, 1–9 e duplo clique
    para seguir um personagem.
82. Como Lucas, quero que o detalhe mude com o zoom: de longe o realm, de perto os personagens e os
    rótulos.

### Garantias para o Lucas e para quem mantém o Orb

83. Como Lucas, quero que o Orb nunca chame modelo de IA, para não gastar nada só para monitorar.
84. Como Lucas, quero que o Orb nunca leia as tabelas de credenciais do opencode nem arquivos de
    autenticação, e que fixtures reais nunca sejam versionadas.
85. Como Lucas, quero que a falha de um provider ou de uma leitura nunca derrube os outros, e que a
    falha apareça na interface.
86. Como Lucas, quero que nenhum elemento do mundo apareça sem uma linha em VISUAL.md dizendo o que ele
    significa e de que dado vem.
87. Como agente que mantém o Orb, quero um `CLAUDE.md` com as fontes da verdade, o processo, os
    invariantes e os pontos de teste, e um `AGENTS.md` apontando para ele, para entregar sem quebrar
    o que foi decidido.
88. Como agente que mantém o Orb, quero incluir um provider novo só escrevendo um adapter, sem mexer no
    mundo, no servidor nem no cliente.
89. Como agente que mantém o Orb, quero testar quase todas as regras por um único ponto (eventos +
    hora → estado do mundo), para os testes não dependerem de detalhes internos.

## Implementation Decisions

### Processo

- O trabalho é dividido em tickets, um por fatia vertical, em `.scratch/the-orb-cidade-viva/issues/`,
  só quando o Lucas pedir (P5). Implementação: **uma branch e um PR por ticket**, citando as regras e
  os critérios de aceite (D-114). Ao terminar, a coluna Situação da regra em RULES.md é revista.
- As decisões **Delegadas** (D-047, D-052, D-101 a D-114) valem até o Lucas revisar.

### Protocolo (versão 0.3)

- O vocabulário de sinais continua fechado; a 0.3 acrescenta (R49):
  - `command.result` (`ok`, `exit_code` opcional, atividade opcional): resultado de um comando. Codex,
    Hermes e opencode informam o código de saída; o Claude só informa erro ou interrupção, então `ok`
    sem código.
  - `realm.metrics` (linhas de código, classe, andares), `realm.changes` (alterações locais: caminho,
    tipo, linhas), `account.limits` (limites da conta por provider) e `tasks.updated` (concluídas,
    total, itens opcionais).
- Eventos de realm e de mundo têm `alter_ego` nulo. O evento nativo continua intacto ao lado do sinal.
  Os campos exatos são fechados no ticket do protocolo.

### Mundo (Core)

- Continua puro: aplica eventos e devolve o estado. **O estado passa a ser pedido com uma hora**
  (`snapshot(now)`), e o mundo deriva sozinho, por uma tabela de limites, tudo o que depende do tempo:
  dormindo (15 min), subagente sem sinal (5 min), sessões recentes (10 dias, configurável), noite (10
  dias), "hoje" da Energy (R47). O cliente deixa de calcular.
- Guarda estado **por realm** (métricas, alterações locais, Weather, tarefas abertas) e **do mundo**
  (limites da conta) (D-085).
- **Calcula, em Python, o que o cliente só desenha** (D-099):
  - o traçado da cidade (bairros por letra, lotes em ordem alfabética, deslocamento e giro pela semente
    do nome, lote vago para realm escondido; VISUAL.md §7);
  - a classe, a altura e os andares de cada prédio (VISUAL.md §8);
  - a fachada: o agrupamento das alterações em janelas por andar e tipo, com x = 5%, sem dividir
    alteração, em ordem estável pelo caminho (VISUAL.md §6).
- Deriva também: papel e atributos por área (contagem das atividades), progresso da tarefa (de
  `tasks.updated`), Weather (último `command.result` de comando de teste por realm), Energy (soma dos
  `usage` por sessão, realm e dia).
- O estado do Alter Ego inclui o nome histórico (vindo do registro local), o papel, os atributos, as
  tarefas, o nível e os estados de erro, bloqueio e sem sinal.

### Progressão

- Módulo de domínio puro, ao lado do mundo: entram eventos e fatos do git; saem entradas do extrato,
  níveis e conquistas. Tabela v1 versionada (PROGRESSION.md §3 a §5); mudar a tabela recalcula tudo a
  partir das fontes.
- Evidência de commit: no Claude, o campo `gitOperation` do resultado da ferramenta (D-090); nos
  outros, o comando `git commit` com `command.result` ok. Confirmação (chegou à branch principal,
  revertido, expirado) vem das leituras do git.
- Curva k·n·(n−1) com k = 50 (Alter Ego), 500 (Realm), 2.500 (Mankind), **calibrada com o histórico
  real antes de valer** (D-107): o ticket da progressão roda o cálculo retroativo, mostra a
  distribuição ao Lucas e registra a versão calibrada da tabela.

### Adapters (um por provider)

- Produzem `command.result` (Codex: `exitCode` do app-server e `item.exit_code` em
  `event_msg/item_completed` do rollout; Hermes: `exit_code` no resultado do `terminal`; opencode:
  `state.metadata.exit` do `bash`; Claude: `is_error`/`interrupted`).
- Produzem `tasks.updated` a partir da lista de tarefas que o CLI mantém (TodoWrite do Claude, plano do
  Codex, `todowrite` do opencode). O formato de cada um é levantado no ticket, **só pela estrutura**.
- Codex: mapear `response_item/agent_message` como narração; avaliar
  `inter_agent_communication_metadata` e `event_msg/thread_settings_applied` (D-089). Produzir
  `account.limits` a partir de `account/rateLimits/updated`.
- Claude: ler `gitOperation` como evidência de commit, push, branch e PR (D-090).
- Hermes: ler os totais de tokens por sessão das colunas de `sessions` (hoje não lidos), para a Energy
  (R43).
- Hermes e opencode: confirmar, só pela estrutura, se o pensamento gravado é texto bruto ou resumo, e
  marcar a fidelidade certa (R14; hoje marcam `raw` sem confirmar).
- Todo leitor passa a alimentar o **índice de metadados** (pasta, datas, título, provider, modelo) de
  todas as sessões, além do conteúdo incremental (R48).

### Detecção de realms e histórico

- O Observatório passa a ler **todas** as sessões de todos os providers, sem filtro por pasta (R3, R3a).
  Pasta → projeto: vence a raiz informada pelo provider (Hermes `git_repo_root`, opencode
  `project.worktree`); senão sobe-se até o repositório git lendo arquivos, sem executar nada; worktrees
  contam para o principal. Ignora pasta do usuário, sistema e temporárias (R3b) e pastas inexistentes
  (R3d). Ids por nome da pasta, com sufixo em caso de nomes iguais.
- **Duas camadas de leitura** (R48): índice barato de todas as sessões (cidade, sala, Histórico do
  realm); conteúdo lido incrementalmente só das sessões da sala; o passado (XP retroativa) numa leitura
  única em segundo plano, com o ponto de parada no registro local.
- Leitura a 250 ms para realms com sessão ativa; varredura de sessões novas a cada 2 s (D-087).
- `--root`, `--realm` e `--lookback` saem (no máximo como opções de depuração).

### Leituras do mundo real (Probes)

- **Git, só leitura** (com `--no-optional-locks` ou lendo os arquivos do `.git`): alterações locais
  (tipo e linhas por arquivo, sem submódulos), commits e se chegaram à branch principal ou foram
  revertidos. Nunca grava no projeto nem no `.git`.
- **Contador de linhas:** linhas não vazias dos arquivos acompanhados pelo git, sem os ignorados, sem a
  lista visível de gerados e, por padrão, sem `.md`; recalcula ao abrir e quando as alterações locais
  mudam, até 1×/min por realm.
- **Archive:** lista os arquivos que moldam cada sessão (`CLAUDE.md`, `AGENTS.md`, skills, memória)
  com nome, tamanho e data; o conteúdo só sob pedido explícito.

### Registro local e preferências

- Registro local em SQLite, na pasta de preferências do Orb (`%LOCALAPPDATA%\the-orb\` no Windows):
  eventos do mundo para o Chronicle, sacola e associação sessão → nome histórico, índice de sessões,
  pontos de parada das leituras, extrato de XP e conquistas com a versão da tabela. Nada do conteúdo
  das sessões (R36).
- Arquivo de preferências próprio do Orb, editado pela tela de configurações: realms escondidos, prazo
  das sessões recentes, x das janelas, filtro e exclusões de linhas (R29).

### Leitor de diálogos

- Módulo separado do terminal: só nas sessões abertas pelo Orb, lê a tela do terminal e reconhece
  diálogos **conhecidos** (tabela por provider). Ao reconhecer, emite espera; nunca envia teclas (R34,
  ADR 0006).

### Servidor (Gateway)

- O canal do mundo envia o estado calculado com a hora do servidor, depois deltas; inclui cidade,
  fachadas, classes, Weather, Energy, tarefas e progressão.
- Gate: lista de esperas de todos os realms; escrita para um Alter Ego pelo terminal dele; reabrir uma
  sessão fechada só com confirmação do Lucas (R35).
- Segurança como hoje: só 127.0.0.1, token por execução, `Origin` local, lista fixa de executáveis,
  linha de comando validada.

### Cliente web (só desenha)

- Cidade retangular, ruas e placas dos bairros; prédios com forma por classe, cintas e antena; andares
  e janelas a partir da fachada recebida; céu do Weather em tons neutros; noite.
- Personagens com as cores R30 (tons exatos com prévia para o Lucas aprovar, V-PEND-7d), magenta
  pulsante para espera, ícones neutros de erro, bloqueio e sem sinal, nível ao lado do nome, anel ao
  subir de nível; subagente que volta ao líder; "+N" por área; áreas sem cor, com ícone, nome e padrão
  no piso (ícones também com prévia).
- Gate como portão na borda da cidade; barra do Chronicle no rodapé; painéis de Energy e de Progressão;
  aba Archive no Inner World; Histórico do realm; lista de realms com marcação; tela de configurações.
- Nenhuma cor fora do orçamento (git nas janelas, provider nos personagens, magenta para espera); o
  resto é cenário neutro.

### Guia dos agentes

- `CLAUDE.md` e `AGENTS.md` já existem (R56). Cada ticket que mudar processo, invariantes ou pontos de
  teste atualiza o `CLAUDE.md`.

## Testing Decisions

- **Um bom teste exercita comportamento externo** pelo ponto de teste mais alto e nunca depende de
  detalhes internos: dados entram pela fronteira, o resultado observável sai. Regras em tabela são
  testadas por tabelas de casos.
- **Ponto principal: o mundo** (D-099). Eventos sintéticos do protocolo + uma hora → estado do mundo.
  Cobre: tempo (dormindo, sem sinal, recentes, noite, hoje), papel e atributos, tarefas, Team e
  subagentes, esperas, Weather, Energy, estado por realm e do mundo, traçado da cidade (estabilidade
  ao incluir e esconder realms), classes e andares, fachada (5%, nada dividido, ordem estável), e a
  progressão (extrato, provisória → confirmada, anulação, expiração, níveis, conquistas, recálculo ao
  trocar a versão da tabela).
- **Leitores dos CLIs:** arquivos e bancos sintéticos com a forma verificada → eventos. Cobre os
  mapeamentos novos (`command.result`, `tasks.updated`, `agent_message`, `gitOperation`,
  `account.limits`), o índice de metadados e a regra de nunca tocar tabelas de credenciais.
- **Leituras do mundo real:** pasta de projeto ou de CLI falsa → eventos. Cobre a detecção de realms
  (raiz do provider, subir até o git, worktrees, nomes parecidos, pastas ignoradas e inexistentes),
  o git só leitura (alterações, submódulos, commits na branch principal, reversão) e o contador de
  linhas (vazias, gerados, `.md`).
- **Prior art:** os testes atuais do mundo (Core), os dos quatro adapters com amostras sintéticas, o
  do classificador de comandos por tabela e os do servidor com terminal falso.
- Sem rede e sem CLI real nos testes; o que depender de `pywinpty` ou de um CLI instalado usa
  `importorskip` dentro da função de teste. Caminhos curtos nos testes (limite de 260 caracteres do
  Windows). Fixtures reais nunca são versionadas.
- O cliente web não tem lógica de domínio e não ganha testes automatizados; cada mudança visual é
  conferida no preview, com o console sem erros e nenhuma cor fora da legenda.

## Out of Scope

- Nível 1 de pegada (hooks por sessão do Claude, app-server próprio do Codex, sidecar do Hermes,
  servidor do opencode), incluindo o teste do observador do Codex diante de um pedido de aprovação.
- CI do GitHub no Weather e XP de PR mesclado (opcionais, depois; D-076).
- Chronicle anterior ao primeiro registro do Orb (reconstrução pelo histórico do git).
- Missões definidas pelo Lucas, "mergulho" no Alter Ego, Inner World num monitor 3D na sala.
- Compartilhar elementos do Perfil entre sessões, aparência que evolui com o nível, tema por realm.
- CLIs além dos quatro, cliente Godot, FREE CAM, minimapa, estradas entre realms, som, multiusuário.
- Kanban do Hermes (pesquisa: falta saber se fica gravado em lugar legível).

## Further Notes

- **Ordem sugerida das fatias:** protocolo 0.3 e mundo com hora → detecção de realms, índice e
  preferências → registro local → cidade, classes e linhas → janelas (git) → Rooftop Room (nomes,
  papel, cores, ícones, tarefas) → Gate e leitor de diálogos → Chronicle → Weather → Energy → Archive
  → progressão (com a calibração). Segue a ordem das camadas vivas (D-081), com as fundações antes.
- **Precisam de aprovação visual do Lucas** antes de valer: os tons exatos dos providers e do magenta e
  os ícones das áreas (V-PEND-7d).
- **Verificações por provider** a fazer nos tickets, só pela estrutura: se retomar mantém o id da
  sessão e o que bifurcar, `/clear` e compactação fazem (R39); o formato da lista de tarefas de cada
  CLI; a fidelidade do pensamento do Hermes e do opencode (R14).
- **Riscos:** custo da leitura retroativa (mitigado pelas duas camadas e pelo ponto de parada); o
  servidor atual lê a cada 500 ms e precisa ir a 250 ms; rollouts do Codex de centenas de MB.
- **Invariantes que todo ticket verifica:** só telemetria real (R12), somente leitura (R16), nunca
  responder diálogos (ADR 0006), nenhum token (R38), privacidade (credenciais, fixtures, LGPD).
