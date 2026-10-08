# The Orb — Linguagem visual

> O que **cada elemento** do mundo 3D significa e de que dado real ele vem. Regra R12
> ([RULES.md](RULES.md)): todo elemento que parece dado **é** dado; o resto é **cenário**, declarado
> aqui. Um elemento novo só entra no mundo depois de ter uma linha nesta tabela.

Última atualização: 2026-10-08 · Decisões em ordem: [DECISIONS.md](DECISIONS.md)

Tipo: **Dado** (vem da telemetria) · **Legenda** (código fixo de cores/formas, sempre o mesmo
significado) · **Cenário** (sem significado, só ambiente) · **Heurística** (deduzido pelo Orb;
precisa de decisão).
Situação: ✅ como está · ❌ precisa mudar · ❓ precisa de decisão.

## 1. A cidade

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-CITY-1 | Disco flutuante (o Orb), borda de luz | Cenário | O chão da cidade; o raio só acompanha a quantidade de realms | ✅ (R12a) |
| V-CITY-2 | Grade polar no chão | Cenário | Referência de profundidade para a câmera | ✅ (R12a) |
| V-CITY-3 | Céu em degradê e estrelas | Cenário | Ambiente noturno | ✅ (R12a) |
| V-CITY-4 | Posição de cada prédio (grade em ordem alfabética) | Heurística | Ordem arbitrária | ❓ V-PEND-5 |
| V-CITY-5 | Barra superior (realms, sessões, ativas, esperando você, subagentes, tokens) | Dado | Soma do snapshot do Core | ✅ |

## 2. O prédio (Realm)

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-REALM-1 | Existir um prédio | Dado | Todo projeto que algum provider já registrou (R3, R3a), menos os escondidos pelo Lucas na lista (R3c) e as sessões fora de projeto (R3b) | ❌ Hoje vem de `--root`/`--realm`, inclusive pastas sem sessão |
| V-REALM-2 | **Altura** | Dado | Linhas de código do projeto, ignorando o `.gitignore` (R19) | ❌ Altura fixa igual para todos |
| V-REALM-3 | **Janelas: quais acendem e de que cor** | Dado | **Hoje: padrão aleatório**, sorteado pelo nome do realm, com cores quentes/frias sem significado. **Decidido:** andares = pastas de 1º nível (R20); as janelas mostram as **alterações locais** (R20b); **cada janela acesa = x% das alterações, e nenhuma alteração é dividida** (R20d, §6); **a cor é a do tipo de alteração no git**, paleta do VS Code (R20a, §5). Pendente: se também esmaece pela recência (V-PEND-1c) | ❌ Viola R12 |
| V-REALM-4 | Brilho geral das janelas | Dado | Quantidade de sessões ativas no realm (0 → apagado; 3 ou mais → máximo) | ⚠️ Correto como dado, mas aplicado sobre o padrão aleatório |
| V-REALM-5 | Arestas de luz do Rooftop Room: azul / âmbar | Dado | Âmbar quando alguma sessão do realm espera o Lucas | ⚠️ A cor do "esperando" muda (R20c, V-PEND-7b) |
| V-REALM-6 | Feixe âmbar subindo do prédio, anel âmbar pulsando | Dado | Alguma sessão do realm espera o Lucas (aprovação/pergunta); visível de toda a cidade | ⚠️ A cor do "esperando" muda (R20c, V-PEND-7b) |
| V-REALM-7 | Rótulo: nome, "N sessões · M ativas · K esperando" | Dado | Snapshot do Core | ✅ |
| V-REALM-8 | Cinco áreas coloridas no piso | Legenda | Hoje: Azul = Development Center · Verde = Testing Lab · Violeta = Research Center · Amarelo = Code Review · Rosa = Task Board (R21) | ⚠️ Verde e amarelo colidem com o git: as cores das áreas mudam (R20c, V-PEND-7b) |
| V-REALM-9 | Anel no centro da sala (lobby) | Legenda | Lugar de quem não está numa área: pensando, parado, esperando, delegando | ✅ |
| V-REALM-10 | Fileira na frente da sala | Heurística | Sessões "dormindo" (parada há mais de 15 min, ou encerrada). Encerradas **não são excluídas** (R28). **Na sala só ficam as ativas e as dos últimos 10 dias** (configurável, R28a); as demais vão para o Histórico do realm | ⚠️ Prazo decidido; limite de "dormindo" em V-PEND-2b |
| V-REALM-11 | Luz interna da sala, sombras | Cenário | Iluminação | ✅ (R12a) |

## 3. O personagem (Alter Ego) e os subagentes

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-EGO-1 | **Cor** do corpo e do halo | Legenda | Provider da sessão. **Decidido (R30):** laranja = Claude · azul = Codex · amarelo = Hermes · cinza = opencode. Hoje: laranja-coral, verde-água, violeta, azul | ❌ Mudar para R30; colisões em V-PEND-7c |
| V-EGO-2 | **Posição** (área da sala) | Dado | Atividade atual da sessão → área ([PROTOCOL.md](PROTOCOL.md) §5) | ✅ |
| V-EGO-3 | Caminhar até a área | Dado | Mudança de atividade | ✅ |
| V-EGO-4 | Balanço do corpo, halo girando mais rápido | Dado | A sessão está trabalhando (lendo, editando, executando, testando, revisando, pesquisando) | ✅ |
| V-EGO-5 | Três pontos orbitando a cabeça | Dado | `THINKING` | ✅ |
| V-EGO-6 | Losango âmbar sobre a cabeça | Dado | A sessão espera o Lucas | ⚠️ A cor do "esperando" muda (R20c, V-PEND-7b) |
| V-EGO-7 | Translúcido, cabeça baixa, sem halo | Heurística | "Dormindo" (ver V-REALM-10) | ❓ V-PEND-2 |
| V-EGO-8 | Rótulo: provider · título; atividade · última ação | Dado | Título e modelo do próprio CLI; última ferramenta usada, com o texto do provider | ✅ |
| V-EGO-9 | Personagem menor, mesma cor | Dado | Subagente da sessão (Team) | ✅ |
| V-EGO-10 | Subagente some depois de 5 min sem atividade | Heurística | Contorna a falta do sinal de fim de subagente em segundo plano no nível 0 | ❓ V-PEND-3 |

## 4. Painéis

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-HUD-1 | Lista de realms com pontos coloridos | Dado | Um ponto por sessão, na cor do provider; apagado = dormindo | ✅ |
| V-HUD-2 | Overview do realm (cartões das sessões) | Dado | R18: o que faz agora, espera, subagentes, tokens/custo, há quanto tempo | ✅ |
| V-HUD-3 | Inner World: linha do tempo | Dado | Eventos nativos com o texto do provider; rótulo = `native.kind` | ✅ |
| V-HUD-4 | Inner World: terminal | Dado | Terminal real do CLI (só para sessões abertas pelo painel; R9) | ⚠️ |
| V-HUD-5 | **Lista de realms com marcação** | Dado | Todos os realms detectados; desmarcar esconde o prédio da cidade (R3c). A escolha fica guardada pelo Orb | ⏳ |
| V-HUD-6 | **Histórico do realm** | Dado | Sessões encerradas ou paradas há mais que o prazo (10 dias, R28a), no overview do realm; nenhuma some | ⏳ |
| V-HUD-7 | **Tela de configurações do Orb** | Dado | Realms escondidos, prazo das sessões recentes e outras preferências, guardadas no arquivo próprio do Orb (R29) | ⏳ |

---

## 5. Paletas

### Git — alterações locais nas janelas (R20a, R20b)

Paleta das decorações de alteração do git no **VS Code** (tema escuro padrão). Conferir os valores
na implementação.

| Tipo de alteração | Cor | Hex |
|---|---|---|
| Modificado | âmbar | `#E2C08D` |
| Adicionado (no índice) | verde | `#81B88B` |
| Não rastreado (arquivo novo) | verde | `#73C991` |
| Renomeado | verde | `#73C991` |
| Apagado | vermelho | `#C74E39` |
| Em conflito | vermelho-rosado | `#E4676B` |
| Sem alteração local | janela apagada | — |

Arquivos ignorados pelo `.gitignore` não têm janela (R19).

### Providers — personagens (V-EGO-1, R30)

**Decidido:** Claude **laranja** · Codex **azul** · Hermes **amarelo** · opencode **cinza**. Os tons
exatos se escolhem junto da V-PEND-7c. (Antes: Claude `#E8845C`, Codex `#2FD3A2`, Hermes
`#B18CFF`, opencode `#5AA8FF`.)

### Áreas e "esperando o Lucas"

**Decidido (R20c):** áreas em tons frios e neutros; "esperando o Lucas" em **magenta pulsante**.
A forma das áreas está em aberto na V-PEND-7c.

## 6. Fachada: as janelas por percentual (R20, R20a, R20b, R20d)

**Decidido pelo Lucas (2026-10-08):**

- Cada **janela acesa** representa **x% das alterações locais** do realm. Assim a fachada fica
  harmônica: o número de janelas acesas não explode num projeto com centenas de arquivos alterados.
- **Uma alteração nunca fica dividida entre duas janelas.**
- A cor da janela é a cor do **tipo de alteração** no git (§5), e o andar é a **pasta de 1º nível**
  onde a alteração está (R20).

**Como as alterações viram janelas (proposta para validar):**

1. **Alteração** = um arquivo com alteração local, com um único tipo (modificado, adicionado, não
   rastreado, renomeado, apagado, em conflito). Arquivos ignorados pelo `.gitignore` não contam.
2. Cada alteração tem um **peso** (V-PEND-8). O total do realm é a soma dos pesos.
3. **Pacote:** as alterações são agrupadas em janelas **só com outras do mesmo andar e do mesmo
   tipo**, até somar x% do total. Isso garante cor única por janela e o andar certo.
4. **Nada é dividido:** uma alteração que sozinha passa de x% ocupa uma janela inteira, que então
   representa mais que x%. As menores se juntam numa janela sem passar de x%. A ordem de
   agrupamento é estável (pelo caminho do arquivo), para a fachada não "piscar" a cada leitura.
5. **Quantas janelas acendem:** com x = 5% e muitas alterações pequenas, ~20 janelas no prédio
   inteiro. Com poucas alterações, uma janela para cada (nunca dividida). Cada combinação de andar
   e tipo com alteração tem pelo menos uma janela acesa.
6. **Onde no andar:** as janelas acesas se espalham de forma regular pela fachada do andar, e não
   amontoadas num canto. Arquivos na raiz do projeto ficam no **térreo**.
7. **Janela apagada = sem alteração** ali. É dado ("nada mudou"), não cenário.
8. **Andar pequeno com muitos pacotes:** se um andar precisar de mais janelas do que tem, os pacotes
   dele se juntam mais (o x daquele andar sobe) até caber, ainda sem dividir nenhuma alteração.

| Id | Pergunta | Proposta |
|---|---|---|
| V-PEND-8 | **Peso de uma alteração** para os percentuais: linhas alteradas (inseridas + removidas; arquivo novo = linhas dele; apagado = linhas que tinha) ou **um por arquivo**? | Linhas alteradas: um ajuste de 1 linha não pesa o mesmo que reescrever um módulo; arquivo binário pesa 1 |
| V-PEND-9 | **Valor de x** | 5%, configurável na tela do Orb (R29) |

## Decisões pendentes

| Id | Pergunta | Proposta inicial |
|---|---|---|
| V-PEND-1 | **Janelas (V-REALM-3).** ~~Que cor significa o quê?~~ **Decidido (2026-10-07): a cor do tipo de alteração no git (R20a).** ~~(a) Qual unidade cada janela representa?~~ **Decidido (2026-10-08): um arquivo (R20b).** ~~(b) De onde vem o tipo de alteração?~~ **Decidido: das alterações locais** (estado do repositório na máquina), lido sem gravar nada no `.git` (R20b, R16). ~~E um prédio com milhares de arquivos?~~ **Decidido: janelas por percentual (R20d, §6).** (c) **V-PEND-1c, em aberto:** a janela fica acesa enquanto as alterações dela existirem; ela também esmaece pela recência? | (c) Brilho pela recência da alteração mais nova da janela; cor pelo tipo |
| V-PEND-2 | **"Dormindo" e sessões encerradas.** ~~Sessão encerrada some?~~ **Decidido: não é excluída (R28).** ~~Onde ficam as encerradas e as antigas (~450 sessões nesta máquina)?~~ **Decidido (2026-10-08): na sala, as ativas e as dos últimos 10 dias, prazo configurável no Orb; as demais no Histórico do realm (R28a).** **V-PEND-2b, em aberto:** dentro da sala, a partir de quanto tempo parada uma sessão aparece "dormindo"? ~~E o nome da lista?~~ **Decidido: Histórico do realm.** | 2b: dormindo depois de 15 min parada (o atual), também configurável |
| V-PEND-3 | **Fim de subagente em segundo plano** sem o sinal no nível 0: esconder por tempo, mostrar como "sem sinal", ou exigir o nível 1? | Mostrar `NO_SIGNAL` (cinza) em vez de sumir, até haver sinal real |
| V-PEND-4 | ~~Cenário é permitido?~~ **Decidido (2026-10-07): sim, declarado aqui e sem cores da legenda (R12a).** | — |
| V-PEND-5 | **Posição dos prédios:** ordem alfabética, por atividade, por tamanho, ou fixa e escolhida pelo Lucas? | Posição estável (não muda sozinha) para a memória espacial; critério a decidir |
| V-PEND-6 | **Escala da altura** (linear, raiz, log) para um repo de 500 mil linhas não esconder um de 2 mil. | Já listada em [VISION.md](VISION.md) §7 |
| V-PEND-7 | **Conflito de cores (apontado pela regra P2).** As cores do git (verde = inserção, âmbar/amarelo = modificação, vermelho = remoção) já existem na legenda: verde = Testing Lab (V-REALM-8) e verde-água = Codex (V-EGO-1); amarelo = Code Review (V-REALM-8); âmbar = "esperando o Lucas" (V-REALM-5/6, V-EGO-6). ~~Qual muda? Qual a paleta do git?~~ **Decidido (2026-10-08): as janelas usam a paleta do git do VS Code; as áreas e o "esperando" trocam de cor (R20a, R20c).** | — |
| V-PEND-7b | **As novas cores** das 5 áreas e do "esperando o Lucas", sem colidir com a paleta do git (§5). Atenção também às cores dos **providers**: o laranja do Claude fica perto do vermelho de remoção e do conflito, e o verde-água do Codex perto do verde de "não rastreado". Personagens e janelas são objetos diferentes; basta isso, ou os providers também mudam? | **Decidido (2026-10-08):** áreas em tons frios e neutros; "esperando" em magenta pulsante (R20c). Os providers **mudaram** (R30), o que reabre a escolha: V-PEND-7c |
| V-PEND-7c | **As cores novas dos providers (R30) colidem** (apontado pela regra P2): (a) **Hermes amarelo** × âmbar de "modificado" do git (`#E2C08D`) nas janelas; (b) **Codex azul** e **opencode cinza** × as áreas em tons frios e neutros (azul, cinza-azulado): um personagem azul sobre um piso azul some; (c) **Claude laranja** fica perto do vermelho de "apagado"/"conflito". | **Áreas sem cor própria**: piso neutro escuro, cada área identificada por **ícone e nome** (e um padrão no piso), não por cor. Assim as cores ficam só para três coisas: janelas = git, personagens = provider, magenta = esperando. Para (a) e (c): personagens e janelas são objetos diferentes e não ficam lado a lado, então as cores dos providers ficam como o Lucas escolheu, em tons bem saturados para se distinguirem dos tons do git |
