# The Orb — Progressão: XP, níveis e conquistas

> **Decidido em 2026-10-09 (D-101 a D-111, Delegada: vale até o Lucas revisar).** Regras R53 a
> R55. Nada é implementado antes dos tickets (P1, P5).
> Vocabulário: [CONTEXT.md](../CONTEXT.md) · Regras: [RULES.md](RULES.md) · Visual: [VISUAL.md](VISUAL.md).

Última atualização: 2026-10-09

---

## 1. A ideia central: XP é recibo de trabalho confirmado

Em quase todo jogo, XP premia o esforço. No Orb, isso violaria dois princípios: a telemetria real
(R12) e "o agente disse que terminou ≠ terminou" ([VISION.md](VISION.md) §3, princípio 2). Por isso
a proposta é outra:

1. **Toda XP tem um recibo.** Cada ponto aponta para a evidência que o gerou: o comando de teste e
   o código de saída dele, o hash do commit, o subagente concluído. O **extrato** de um Alter Ego
   lista cada entrada com data, regra e evidência, como um extrato bancário. Sem recibo, sem XP.
2. **O mundo real confirma.** O que depende de confirmação externa (um commit que chega à branch
   principal) entra como **XP provisória** e só vira **XP confirmada** quando o git confirma. O
   nível usa só a confirmada.
3. **Não se ganha XP por gastar.** Tokens, custo, número de mensagens, tempo esperando o Lucas e
   linhas escritas sem commit **não dão XP**. Gastar mais não é mérito, e o que não foi para o
   histórico do projeto pode ser descartado.
4. **Determinística e recalculável.** A XP é uma função pura dos eventos e dos fatos do git,
   declarada numa **tabela versionada** (princípio 11). O extrato guardado no registro local (R36) é
   um cache: se a tabela mudar, tudo é recalculado a partir das fontes, e o mesmo histórico sempre
   dá a mesma XP.
5. **Sem tokens e somente leitura.** Nada chama modelo (R38). O git é lido sem gravar nada
   (`--no-optional-locks`, R16, R20b). Os agentes nunca veem a XP: ela é para o Lucas, não
   interfere no trabalho (princípio 5).
6. **XP nunca é negativa.** Um erro não tira pontos; só deixa de render. Um commit revertido
   **anula** a entrada dele no extrato (com o recibo da reversão), porque o trabalho deixou de
   existir no projeto.

## 2. Três escalas

| Escala | De onde vem | Onde aparece (proposta, §6) |
|---|---|---|
| **Alter Ego** (a sessão) | A XP confirmada da sessão, incluindo a da Team (os subagentes rendem para o líder) | Nível ao lado do nome; barra e extrato no overview |
| **Realm** (o projeto) | A soma da XP confirmada de todos os Alter Egos do realm, das sessões ativas e do Histórico do realm | Nível no overview do realm |
| **Mankind** (todos) | A soma de todos os realms; é o nível do Orb inteiro | Barra de cima, com o **placar por provider** (a XP de Claude, Codex, Hermes e opencode lado a lado) |

Continuidade (segue R39): **retomar** mantém a XP e o nível; **bifurcar** cria um Alter Ego novo, que
começa do zero e mostra de quem nasceu.

## 3. De onde vem a XP (tabela v1)

| Código | Feito | Evidência (recibo) | XP | Limite | Estado |
|---|---|---|---|---|---|
| X-TEST | **Teste passou** | Comando classificado como teste (o classificador já existe) + código de saída 0 | 5 | 1 a cada 10 min por sessão (rodar o mesmo teste em laço não rende) | Confirmada na hora: o código de saída já é o mundo real |
| X-FIX | **Vermelho → verde**: um teste falhou e depois passou, na mesma sessão | As duas execuções | 25 | 1 por falha consertada | Confirmada na hora |
| X-COMMIT | **Commit feito pela sessão** | Commit observado na sessão (no Claude, o campo `gitOperation`, D-090; nos outros, o comando `git commit` com `command.result` ok, D-084) + o commit existe no `git log` do realm | 10, +1 a cada 20 linhas alteradas, teto de 40 por commit | — | **Provisória** até o commit chegar à branch principal (a padrão do remoto, senão `main`/`master`); revertido = anulada; não chegou em 30 dias = expira |
| X-DELEG | **Subagente concluído** | Sinal `subagent.ended` | 3, para o líder | Teto de 30 por sessão por dia | Confirmada na hora |
| X-CRAFT | **Ofício**: tempo em atividade (código, teste, leitura, pesquisa, revisão) | Sinais de atividade | 1 a cada 5 min ativos | Teto de 30 por sessão por dia | Confirmada na hora |
| X-PR | **PR mesclado** *(depois, opcional, junto do CI do Weather)* | `gh`, só leitura | 50 | — | Confirmada pelo GitHub |

Por que **X-CRAFT** existe, e com teto: sem ela, uma sessão só de pesquisa ou de revisão ficaria
sempre no nível 1, embora tenha trabalhado de verdade. O teto impede que o tempo vire a fonte
principal de XP.

**Commits do Lucas fora das sessões não contam:** o Orb mede os agentes. Eles continuam aparecendo
nas janelas e na altura do prédio, que são dados do projeto.

Ordem de grandeza (a calibrar, §4): uma sessão produtiva, com 10 commits, 5 consertos, 20 testes
verdes, 10 subagentes e algumas horas de trabalho, rende cerca de 500 XP.

## 4. Níveis

**Curva:** a XP acumulada para chegar ao nível *n* é **k · n · (n − 1)**: cada nível pede 2k a mais
que o anterior. É simples, cresce sem explodir e cabe numa tabela.

| Nível | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|---|---|---|
| Alter Ego (k = 50) | 100 | 300 | 600 | 1.000 | 1.500 | 2.800 | 4.500 | 10.500 | 19.000 |
| Realm (k = 500) | 1 mil | 3 mil | 6 mil | 10 mil | 15 mil | 28 mil | 45 mil | 105 mil | 190 mil |
| Mankind (k = 2.500) | 5 mil | 15 mil | 30 mil | 50 mil | 75 mil | 140 mil | 225 mil | 525 mil | 950 mil |

**Calibração antes do ticket:** os valores de *k* e da tabela §3 são um ponto de partida. Com o
cálculo retroativo (§7) rodado sobre o histórico real desta máquina, ajusta-se *k* para que a
sessão típica fique entre os níveis 2 e 4 e só sessões excepcionais passem do 8. O ajuste é uma
nova versão da tabela, registrada em [DECISIONS.md](DECISIONS.md).

O nível é função da XP **confirmada**. Se um commit for revertido, a XP dele é anulada e o nível
pode cair; é raro e é a verdade do projeto.

## 5. Conquistas

Medalhas de uma vez só, cada uma com o seu recibo (o evento ou o conjunto de eventos que a
cumpriu). **Não dão XP** (para não contar o mesmo trabalho duas vezes). Lista inicial:

| Id | Conquista | Escala | Condição (sempre de dado observado) |
|---|---|---|---|
| C-01 | **Primeiro verde** | Alter Ego | O primeiro teste que passou na sessão |
| C-02 | **Fênix** | Alter Ego | 3 consertos (vermelho → verde) na mesma sessão |
| C-03 | **Maestro** | Alter Ego | 5 subagentes ativos ao mesmo tempo |
| C-04 | **Polímata** | Alter Ego | Passou pelas 5 áreas do Environment na mesma sessão |
| C-05 | **Cirurgião** | Alter Ego | Um commit confirmado de até 10 linhas que fez um teste vermelho passar |
| C-06 | **Maratonista** | Alter Ego | 6 horas de atividade no mesmo dia |
| C-07 | **Fiel** | Alter Ego | Sessão retomada 5 vezes (R39) |
| C-08 | **Linhagem** | Alter Ego | Uma bifurcação desta sessão teve um commit confirmado |
| C-20 | **Pedra fundamental** | Realm | O primeiro commit confirmado de um Alter Ego no realm |
| C-21 | **Semana de céu limpo** | Realm | 7 dias seguidos em que o último teste do dia passou (a fonte do Weather, R42) |
| C-22 | **Babel** | Realm | Sessões de 3 providers diferentes no realm |
| C-23 | **Obra nova** | Realm | O prédio subiu de classe (ex.: Sobrado → Prédio; R19), a partir do dia em que o Orb registra a contagem |
| C-24 | **Casa arrumada** | Realm | Num dia com commits confirmados, terminou sem alterações locais (todas as janelas apagadas, R20) |
| C-40 | **Os quatro** | Mankind | Claude, Codex, Hermes e opencode ativos no mesmo dia |
| C-41 | **Cidade viva** | Mankind | 10 realms com atividade na mesma semana |
| C-42 | **Panteão** | Mankind | Os 60 nomes históricos já foram usados e a sacola recomeçou (R37) |

## 6. Como aparece no mundo (decidido, D-110; também em VISUAL.md)

Todos os elementos abaixo são **Dado** (vêm do extrato) e não usam cores com significado: a
progressão usa **branco neutro**, fora das paletas do git, dos providers e do magenta "esperando"
(R20c). Dourado ficou de fora de propósito: confundiria com o amarelo do Hermes (R30).

| Id | Elemento | Fonte |
|---|---|---|
| V-EGO-13 | O nível ao lado do nome histórico no rótulo ("Einstein · 7") | Nível do Alter Ego |
| V-EGO-14 | **Subir de nível**: um anel de luz neutra sobe pelo personagem uma vez | O evento real de subir de nível |
| V-HUD-12 | Nível de Mankind e a barra de progresso na barra de cima; clicar abre o painel **Progressão** (extrato, conquistas, placar por provider) | Soma da XP confirmada |
| V-HUD-13 | No overview do realm: o nível do realm e, por Alter Ego, a barra de XP (confirmada cheia, provisória tracejada) | Extrato |
| V-HUD-14 | **Conquista nova**: um aviso curto no HUD com o nome e o recibo | Conquista |

## 7. Retroatividade

Os realms já incluem todo o histórico dos providers (R3a), e os nomes históricos valem para todas as
sessões. A proposta é que a XP também seja **retroativa**: no primeiro uso, o Orb calcula a XP de
todas as sessões antigas **em segundo plano**, com baixa prioridade e um indicador de progresso,
guardando o ponto em que parou em cada fonte. Assim, no primeiro dia a cidade já tem níveis.

**Custo a considerar:** hoje os leitores começam arquivos antigos pelo fim, para não ler rollouts de
centenas de MB ([ARCHITECTURE.md](ARCHITECTURE.md) §5). O cálculo retroativo lê cada sessão antiga
**uma vez**, em segundo plano, e nunca de novo (o registro local guarda o resultado). A alternativa
é começar do zero no dia em que o Orb passa a registrar, como o Chronicle (D-078).

## 8. Onde mora no código

- **`src/orb/progression/`**: domínio puro, como o Core. Entra: eventos do Protocol e fatos do git
  (dos Probes). Sai: entradas do extrato e conquistas. Tabelas em `rules.py` (a tabela v1 da §3, a
  curva e as conquistas), com versão. Sem disco, rede ou relógio; testável por tabela de casos.
- **Probes (git)**: confirmar commits (existe, chegou à branch principal, foi revertido), só leitura.
- **Registro local (R36)**: o extrato e as conquistas, com a versão da tabela que os gerou.
- **Gateway**: envia nível, extrato e conquistas ao cliente, como já faz com o mundo.

## 9. Referências (pesquisadas em 2026-10-09)

- **Visual Studio Achievements** (Microsoft, 2012): conquistas por ações dentro da IDE, com placar.
  Jesper Juul criticou o "problema jogo × ferramenta": o sistema de pontos de outra pessoa entra em
  conflito com os objetivos de quem trabalha. **Lição para o Orb:** pontuar só o que o Lucas já
  considera resultado (testes, commits que ficam), nunca ações por si só.
  [Microsoft (anúncio)](https://blogs.microsoft.com/blog/2012/01/18/visual-studio-achievements-program-brings-gamification-to-development/) ·
  [Juul, "Microsoft Visual Studio as a Game"](https://www.jesperjuul.net/ludologist/2012/01/23/visual-studio-as-a-game/)
- **Badges mudam o comportamento** (Anderson, Huttenlocher, Kleinberg e Leskovec, *Steering User
  Behavior with Badges*, WWW 2013, dados do Stack Overflow): medalhas aumentam a participação e
  **mudam a mistura de atividades** de quem as persegue. **Lição para o Orb:** os agentes nunca veem
  a XP (§1), mas o Lucas vê; por isso as conquistas premiam resultado confirmado, e não volume de
  uma atividade, para não puxar o trabalho numa direção errada.
  [Artigo (PDF)](https://archives.iw3c2.org/www2013/proceedings/p95.pdf)

## 10. Depois (backlog)

- **Missões** (quests) **definidas pelo Lucas** no Orb (ex.: "deixar o TriSafe com testes verdes"),
  cumpridas quando os dados confirmam. Nunca geradas automaticamente.
- XP de **PR mesclado** e de **CI verde**, junto do CI opcional do Weather (D-076).
- Aparência que evolui com o nível (parte do Perfil ainda em aberto).
