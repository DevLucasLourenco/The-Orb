# The Orb — Linguagem visual

> O que **cada elemento** do mundo 3D significa e de que dado real ele vem. Regra R12
> ([RULES.md](RULES.md)): todo elemento que parece dado **é** dado; o resto é **cenário**, declarado
> aqui. Um elemento novo só entra no mundo depois de ter uma linha nesta tabela.

Última atualização: 2026-10-09 · Decisões em ordem: [DECISIONS.md](DECISIONS.md)

Tipo: **Dado** (vem da telemetria) · **Legenda** (código fixo de cores/formas, sempre o mesmo
significado) · **Cenário** (sem significado, só ambiente) · **Heurística** (deduzido pelo Orb;
precisa de decisão) · **Identidade** (o nome do personagem: não é dado e não se apresenta como dado,
§9).
Situação: ✅ como está · ❌ precisa mudar · ❓ precisa de decisão.

## 1. A cidade

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-CITY-1 | Chão da cidade | Cenário | **Decidido (R32): retangular**, com ruas entre os bairros (§7). Hoje: disco flutuante com borda de luz | ❌ Mudar para retangular |
| V-CITY-2 | Grade polar no chão | Cenário | Referência de profundidade para a câmera | ✅ (R12a) |
| V-CITY-3 | Céu em degradê e estrelas | Cenário | Ambiente noturno | ✅ (R12a) |
| V-CITY-4 | Posição de cada prédio | Legenda | **Decidido (R32):** bairros por letra inicial, em ordem alfabética; lotes em ordem alfabética; deslocamento e giro pela semente do nome (§7). Hoje: grade alfabética simples | ❌ Mudar para §7 |
| V-CITY-6 | Placa do bairro (a letra) no chão | Legenda | A letra inicial dos realms daquele bairro (§7) | ⏳ |
| V-CITY-7 | **O Gate**: um portão na borda da cidade, de frente para a câmera inicial, fora dos bairros | Dado | A contagem de quem espera o Lucas em todos os realms; clicar abre a lista e a escrita para qualquer Alter Ego (R46) | ⏳ |
| V-CITY-5 | Barra superior (realms, sessões, ativas, esperando você, subagentes, tokens) | Dado | Soma do snapshot do Core | ✅ |

## 2. O prédio (Realm)

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-REALM-1 | Existir um prédio | Dado | Todo projeto que algum provider já registrou (R3, R3a), menos os escondidos pelo Lucas na lista (R3c) e as sessões fora de projeto (R3b) | ❌ Hoje vem de `--root`/`--realm`, inclusive pastas sem sessão |
| V-REALM-2 | **Altura** | Dado | Linhas de código do projeto, ignorando o `.gitignore` (R19), em **escala absoluta por classes** (Casa a Arranha-céu), com saltos entre as classes (§8). Não depende dos outros prédios | ❌ Altura fixa igual para todos |
| V-REALM-12 | **Altura de cada andar** | Dado | Parcela das linhas do projeto que está naquela pasta de 1º nível; pastas pequenas demais se juntam em "demais pastas" (§8) | ⏳ |
| V-REALM-13 | **Cintas de luz neutra no topo** (e antena no Arranha-céu) | Legenda | A classe do prédio por faixa de linhas: uma cinta a mais por classe (§8) | ⏳ |
| V-REALM-15 | **Forma arquitetônica** do prédio | Legenda | A classe do prédio (Casa a Arranha-céu), cada uma com a sua forma (§8, R41) | ❌ Hoje todos têm a mesma forma |
| V-REALM-16 | **Céu sobre o prédio (Weather)**: limpo, chuva ou nada | Dado | Resultado dos últimos testes rodados nas sessões do realm: passaram = céu limpo; falharam = chuva; sem dado = nada (R42). Cores neutras (cinza, branco), fora do orçamento de cores | ⏳ |
| V-REALM-3 | **Janelas: quais acendem e de que cor** | Dado | **Hoje: padrão aleatório**, sorteado pelo nome do realm, com cores quentes/frias sem significado. **Decidido:** andares = pastas de 1º nível (R20); as janelas mostram as **alterações locais** (R20b); **cada janela acesa = x% das alterações, e nenhuma alteração é dividida** (R20d, §6); **a cor é a do tipo de alteração no git**, paleta do VS Code (R20a, §5). A janela é só **acesa ou apagada**, sem esmaecer (D-043) | ❌ Viola R12 |
| V-REALM-4 | Brilho geral das janelas | Dado | Quantidade de sessões ativas no realm (0 → apagado; 3 ou mais → máximo) | ⚠️ Correto como dado, mas aplicado sobre o padrão aleatório |
| V-REALM-5 | Arestas de luz do Rooftop Room: azul / âmbar | Dado | Âmbar quando alguma sessão do realm espera o Lucas | ⚠️ A cor do "esperando" muda (R20c, V-PEND-7b) |
| V-REALM-6 | Feixe âmbar subindo do prédio, anel âmbar pulsando | Dado | Alguma sessão do realm espera o Lucas (aprovação/pergunta); visível de toda a cidade | ⚠️ A cor do "esperando" muda (R20c, V-PEND-7b) |
| V-REALM-7 | Rótulo: nome, "N sessões · M ativas · K esperando" e, quando houver dado, o **Weather** e as **tarefas abertas** (D-097) | Dado | Snapshot do Core; sem dado, a parte não aparece | ⚠️ Faltam Weather e tarefas |
| V-REALM-17 | **Task Board com as tarefas concluídas** da lista do CLI | Dado | A lista de tarefas que o provider grava (R50, D-093) | ⏳ |
| V-REALM-8 | Cinco áreas no piso | Legenda | **Decidido (R20c):** piso neutro, cada área identificada por **ícone e nome** e um padrão no piso, sem cor própria. Hoje: Azul = Development Center · Verde = Testing Lab · Violeta = Research Center · Amarelo = Code Review · Rosa = Task Board (R21) | ❌ Mudar para R20c; ícones em V-PEND-7d |
| V-REALM-9 | Anel no centro da sala (lobby) | Legenda | Lugar de quem não está numa área: pensando, parado, esperando, delegando | ✅ |
| V-REALM-10 | Fileira na frente da sala | Heurística | Sessões "dormindo" (parada há mais de 15 min, ou encerrada). Encerradas **não são excluídas** (R28). **Na sala só ficam as ativas e as dos últimos 10 dias** (configurável, R28a); as demais vão para o Histórico do realm | ✅ Prazo (R28a) e limite de 15 min (R31) decididos |
| V-REALM-11 | Luz interna da sala, sombras | Cenário | Iluminação | ✅ (R12a) |
| V-REALM-14 | **"Noite"**: sala do teto apagada | Dado | Nenhuma sessão nos últimos 10 dias (o prazo de sessões recentes, R28a); as janelas seguem mostrando as alterações locais; acende quando surge uma sessão (D-059) | ⏳ |

## 3. O personagem (Alter Ego) e os subagentes

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-EGO-1 | **Cor** do corpo e do halo | Legenda | Provider da sessão. **Decidido (R30):** laranja = Claude · azul = Codex · amarelo = Hermes · cinza = opencode. Hoje: laranja-coral, verde-água, violeta, azul | ❌ Mudar para R30; colisões em V-PEND-7c |
| V-EGO-2 | **Posição** (área da sala) | Dado | Atividade atual da sessão → área ([PROTOCOL.md](PROTOCOL.md) §5) | ✅ |
| V-EGO-3 | Caminhar até a área | Dado | Mudança de atividade | ✅ |
| V-EGO-4 | Balanço do corpo, halo girando mais rápido | Dado | A sessão está trabalhando (lendo, editando, executando, testando, revisando, pesquisando) | ✅ |
| V-EGO-5 | Três pontos orbitando a cabeça | Dado | `THINKING` | ✅ |
| V-EGO-6 | Losango âmbar sobre a cabeça | Dado | A sessão espera o Lucas | ⚠️ A cor do "esperando" muda (R20c, V-PEND-7b) |
| V-EGO-7 | Translúcido, cabeça baixa, sem halo | Heurística | "Dormindo": sessão recente parada há mais de 15 min (R31) | ✅ |
| V-EGO-8 | Rótulo: **nome histórico em destaque**; embaixo "provider · título da sessão"; depois atividade · última ação | Dado + Identidade | Título e modelo do próprio CLI; última ferramenta usada, com o texto do provider; o nome vem de §9 (D-066) | ⚠️ Hoje sem o nome |
| V-EGO-11 | **Nome histórico** do personagem (ex.: "Einstein") | Identidade | Sorteado sem reposição quando a sessão aparece, fica com a sessão (R37, §9) | ⏳ |
| V-EGO-12 | Contador **"+N"** numa área | Dado | Personagens além dos 8 visíveis naquela área (R33) | ⏳ |
| V-EGO-9 | Personagem menor, mesma cor | Dado | Subagente da sessão (Team) | ✅ |
| V-EGO-10 | Subagente **cinza ("sem sinal")** | Heurística | **Decidido (R7, D-045, D-050):** depois de **5 min sem atividade** e sem sinal do fim, o subagente fica **cinza translúcido, sem halo, com um ícone de sinal cortado** sobre a cabeça, em vez de sumir. O opencode continua cinza **sólido, com halo**. Hoje: some depois de 5 min | ❌ Mudar |
| V-EGO-15 | **Líder em erro, bloqueado ou sem sinal**: ícone neutro sobre a cabeça (erro = triângulo branco com "!" e corpo apagado; bloqueado = cadeado; sem sinal = o ícone de sinal cortado de V-EGO-10) | Dado | Estados `ERROR`, `BLOCKED`, `NO_SIGNAL` do Core (R52, D-095); sem vermelho | ⏳ |
| V-EGO-16 | **Subagente que termina caminha até o líder** e então sai de cena | Dado | Sinal `subagent.ended` (R51, D-094); sem o sinal, vale V-EGO-10 | ⏳ |

## 4. Painéis

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-HUD-1 | Lista de realms com pontos coloridos | Dado | Um ponto por sessão, na cor do provider; apagado = dormindo | ✅ |
| V-HUD-2 | Overview do realm (cartões das sessões) | Dado | R18: o que faz agora, espera, subagentes, tokens/custo, há quanto tempo | ✅ |
| V-HUD-3 | Inner World: linha do tempo | Dado | Eventos nativos com o texto do provider; rótulo = `native.kind` | ✅ |
| V-HUD-4 | Inner World: terminal | Dado | Terminal real do CLI (só para sessões abertas pelo painel; R9) | ⚠️ |
| V-HUD-5 | **Lista de realms com marcação** | Dado | Todos os realms detectados; desmarcar esconde o prédio da cidade (R3c). A escolha fica guardada pelo Orb | ⏳ |
| V-HUD-6 | **Histórico do realm** | Dado | Sessões encerradas ou paradas há mais que o prazo (10 dias, R28a), no overview do realm; nenhuma some | ⏳ |
| V-HUD-8 | **Papel** do Alter Ego no overview (ex.: "revisor") | Dado | O que a sessão mais fez, por contagem das atividades observadas; sem modelo, sem tokens (R40, R38) | ⏳ |
| V-HUD-7 | **Tela de configurações do Orb** | Dado | Realms escondidos, prazo das sessões recentes e outras preferências, guardadas no arquivo próprio do Orb (R29) | ⏳ |
| V-HUD-9 | **Energy**: tokens e custo por sessão e realm (overview), total de hoje (barra de cima), limites da conta (painel) | Dado | Só o que o provider informa, nunca estimado (R43) | ⚠️ Só por sessão hoje |
| V-HUD-10 | **Chronicle**: barra de tempo no rodapé | Dado | Arrastar mostra a cidade como era, pelo registro local do Orb (R44) | ⏳ |
| V-HUD-11 | **Archive**: aba no Inner World | Dado | Instruções, skills e memória da sessão: nome, tamanho e data; conteúdo só ao abrir (R45) | ⏳ |
| V-HUD-15 | **Progresso da tarefa** no overview: "7 de 12" e uma barra por sessão | Dado | A lista de tarefas que o próprio CLI mantém (R50, D-093); sem lista, nada | ⏳ |
| V-HUD-16 | **Atributos por área** no overview: barras com a parcela do trabalho em cada área | Dado | A mesma contagem do Papel (R40, D-096); não é pontuação | ⏳ |

---

## 5. Paletas

### Git — alterações locais nas janelas (R20a, R20b)

Paleta das decorações de alteração do git no **VS Code** (tema escuro padrão). **Conferida na fonte
em 2026-10-09:** `contributes.colors` da extensão git do VS Code
([extensions/git/package.json](https://github.com/microsoft/vscode/blob/main/extensions/git/package.json)),
ids `gitDecoration.*ResourceForeground`, valores `dark`. Os seis valores abaixo batem exatamente. O
VS Code tem ainda `ignoredResourceForeground` (`#8C8C8C`; arquivos ignorados não têm janela, R19) e
`submoduleResourceForeground` (`#8db9e2`): **submódulos não acendem janela** no projeto pai (D-092, R20e).

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
exatos, saturados para se distinguirem da paleta do git, ficam para a V-PEND-7d. (Antes: Claude
`#E8845C`, Codex `#2FD3A2`, Hermes `#B18CFF`, opencode `#5AA8FF`.)

### Áreas e "esperando o Lucas"

**Decidido (R20c):** as áreas **não têm cor própria**: piso neutro, identificadas por **ícone e
nome** (e um padrão no piso). "Esperando o Lucas" é **magenta pulsante**. Ícones e tons exatos:
V-PEND-7d.

**Orçamento de cores do mundo:** janelas = paleta do git · personagens = cor do provider ·
"esperando o Lucas" = magenta. Nenhuma outra cor carrega significado; o cenário é neutro (R12a).

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
2. Cada alteração tem um **peso = linhas alteradas** (inseridas + removidas; arquivo novo = linhas
   dele; apagado = linhas que tinha; arquivo binário = 1). O total do realm é a soma dos pesos (D-041).
3. **Pacote:** as alterações são agrupadas em janelas **só com outras do mesmo andar e do mesmo
   tipo**, até somar x% do total. Isso garante cor única por janela e o andar certo.
4. **Nada é dividido:** uma alteração que sozinha passa de x% ocupa uma janela inteira, que então
   representa mais que x%. As menores se juntam numa janela sem passar de x%. A ordem de
   agrupamento é estável (pelo caminho do arquivo), para a fachada não "piscar" a cada leitura.
5. **Quantas janelas acendem:** com **x = 5%** (D-042) e muitas alterações pequenas, ~20 janelas no prédio
   inteiro. Com poucas alterações, uma janela para cada (nunca dividida). Cada combinação de andar
   e tipo com alteração tem pelo menos uma janela acesa.
6. **Onde no andar:** as janelas acesas se espalham de forma regular pela fachada do andar, e não
   amontoadas num canto. Arquivos na raiz do projeto ficam no **térreo**.
7. **Janela apagada = sem alteração** ali. É dado ("nada mudou"), não cenário. A janela só tem
   esses dois estados, **acesa ou apagada**; não esmaece com o tempo (D-043).
8. **Andar pequeno com muitos pacotes:** se um andar precisar de mais janelas do que tem, os pacotes
   dele se juntam mais (o x daquele andar sobe) até caber, ainda sem dividir nenhuma alteração.

| Id | Pergunta | Proposta |
|---|---|---|
| V-PEND-8 | ~~**Peso de uma alteração**: linhas alteradas ou um por arquivo?~~ **Decidido (2026-10-08): linhas alteradas (D-041).** | — |
| V-PEND-9 | ~~**Valor de x**~~ **Decidido (2026-10-08): 5%, configurável na tela do Orb (D-042).** | — |

## 7. A cidade: traçado retangular (R32)

**Decidido pelo Lucas (2026-10-08, D-046):** cidade **retangular**; prédios em **ordem alfabética**,
com um ar **"aleatório", mas rastreável**, posicionados por uma **estrutura lógica** no mapa.

**Traçado (definição delegada ao Claude, D-047; vale até o Lucas revisar):**

1. **Bairros por letra.** A cidade é dividida por ruas em **bairros**, um para cada letra inicial
   dos realms (A, B, C…; números e símbolos ficam num bairro "#" no começo). Só existem bairros de
   letras que têm realms: não sobra espaço vazio para letras sem projeto.
2. **Ordem de leitura.** Os bairros seguem a ordem alfabética como um texto: da esquerda para a
   direita, em fileiras, de cima para baixo no mapa. O mapa é mais largo que alto (proporção perto
   de 16:9), como a tela.
3. **Lotes.** Dentro de cada bairro, os prédios ocupam **lotes** em grade, também em ordem
   alfabética. O bairro tem o tamanho que precisa para os seus lotes.
4. **O "aleatório" rastreável.** Cada prédio tem um pequeno deslocamento dentro do lote e um leve
   giro, calculados a partir de uma **semente tirada do nome do realm** (um hash). Parece orgânico,
   mas é **determinístico**: o mesmo realm fica sempre no mesmo lugar e do mesmo jeito, e dá para
   explicar onde ele está ("`trisafe-enhanced`: bairro T, 2º lote").
5. **Estabilidade.** Um projeto novo só reorganiza o seu próprio bairro, nunca a cidade inteira.
   Um realm escondido (R3c) deixa o lote vago, para os vizinhos não andarem.
6. **Placa do bairro.** A letra do bairro fica escrita no chão, na esquina (V-CITY-6).
7. **Ruas** são cenário (R12a): separam os bairros e dão leitura ao mapa; não carregam dado.

## 8. A altura dos prédios (R19)

**Decidido pelo Lucas (2026-10-08):**

- ~~A altura é um percentual do maior realm~~ (D-049, **revisto**): **a altura de um prédio depende só
  das linhas dele**. Um projeto novo, por maior que seja, nunca encolhe os outros (D-051).
- **O que é grande se destaca de verdade**, com uma **delimitação** por faixas de milhares de linhas
  e **algo específico** que mostre a faixa (D-051).

**Escala (definição delegada ao Claude, D-052; vale até o Lucas revisar):**

Referência: o *Software World*, uma das primeiras "cidades de software", usa uma escala absoluta (um
andar a cada 10 linhas), sem comparar um prédio com outro. Aqui a escala também é absoluta, mas em
**classes**, para a diferença entre o pequeno e o grande saltar aos olhos.

**O que as fontes dizem (conferido em 2026-10-09):**

- **CodeCity** (Wettel e Lanza, *Visualizing Software Systems as Cities*, VISSOFT 2007): classe =
  prédio, pacote = bairro; **altura = número de métodos**, **base = número de atributos**. A altura
  cai em **5 categorias** (muito pequeno, pequeno, médio, alto, muito alto), com duas formas de
  escolher os limites: por **boxplot** (relativo ao próprio sistema, "cidades equilibradas", mas que
  **não permite comparar cidades**) ou por **limites fixos** tirados de *Object-Oriented Metrics in
  Practice* (Lanza e Marinescu, 2006), que permite comparar. A forma nasce da proporção entre as
  duas métricas: prédios em forma de antena (muitos métodos, poucos atributos), "estacionamentos"
  (muitos atributos, poucos métodos) e casinhas formando bairros inteiros.
- **Consequência para o Orb:** a decisão do Lucas (D-051, "o maior prédio não define os outros") é
  exatamente o **mapeamento por limites fixos** do CodeCity, e não o por boxplot. As 6 classes da
  tabela abaixo são esse mapeamento aplicado às linhas de código; a quantidade de classes (6 em vez
  de 5) foi **confirmada pelo Lucas (D-091)**.
- **Software World** (Knight e Munro, *Virtual but visible software*, IV 2000): classes Java são
  bairros e **métodos são prédios, com um andar a cada 10 linhas**; portas mostram parâmetros.

Fontes: [Wettel e Lanza, VISSOFT 2007 (PDF)](https://www.si.usi.ch/assets/publications/conf/vissoft/vissoft2007/WettelL07.pdf) ·
[CodeCity — página do autor](https://wettel.github.io/codecity.html) ·
[Software Systems as Cities: A Controlled Experiment, ICSE 2011 (PDF)](https://www.inf.unibz.it/~rrobbes/p/ICSE2011-codecity.pdf) ·
[Software World resumido em levantamento de Jeffery (PDF)](https://dspace5old.zcu.cz/bitstream/11025/35620/1/Jeffery.pdf).

1. **Classes de prédio por faixa de linhas.** A unidade de altura é o **nível** (uma fileira de
   janelas). As faixas crescem cerca de 4 a 5 vezes de uma classe para a próxima:

   | Classe | Linhas de código | Altura | Marca no topo | Forma (aprovada, D-075) |
   |---|---|---|---|---|
   | 1. Casa | até 1 mil | 1 nível | — | Um volume baixo, com a base do tamanho do Rooftop Room |
   | 2. Sobrado | 1 mil a 5 mil | 2 a 3 níveis | 1 cinta | Dois volumes: base um pouco mais larga e um corpo com terraço em volta da sala |
   | 3. Prédio | 5 mil a 20 mil | 5 a 8 níveis | 2 cintas | Bloco retangular, com marquise no térreo |
   | 4. Edifício | 20 mil a 100 mil | 11 a 16 níveis | 3 cintas | Bloco com **um recuo** na parte de cima |
   | 5. Torre | 100 mil a 500 mil | 20 a 28 níveis | 4 cintas | Pódio largo na base e **torre esguia** com dois recuos |
   | 6. Arranha-céu | 500 mil ou mais | 34 níveis ou mais | 5 cintas e uma antena | Torre alta com **recuos escalonados**, coroa no topo e antena |

   **Forma por classe (D-072, R41):** como o CodeCity, que mapeia métricas no **tipo** do prédio,
   cada classe tem a sua arquitetura. As formas são **neutras** (sem cor de significado) e o
   **Rooftop Room tem sempre o mesmo tamanho** no topo; os recuos acontecem abaixo dele, e as
   classes maiores têm a base mais larga. As janelas (§6) acompanham as fachadas de cada forma.

2. **Delimitação visível.** As faixas de altura **não se encostam**: entre uma classe e a próxima há
   um salto (3 → 5, 8 → 11, 16 → 20, 28 → 34 níveis). Dois prédios de classes vizinhas nunca ficam
   com alturas parecidas.
3. **Dentro da classe**, a altura cresce aos poucos com as linhas (escala logarítmica dentro da
   faixa): um projeto de 90 mil linhas é mais alto que um de 21 mil, mas os dois continuam
   "Edifício". No Arranha-céu, o crescimento continua devagar, para um monorepo gigante não sair da
   tela.
4. **A marca específica de cada classe:** **cintas de luz neutra** (branca, sem cor de significado,
   R20c) em volta do topo, logo abaixo do Rooftop Room: uma a mais a cada classe; o Arranha-céu
   ganha também uma antena. Dá para ler a classe de longe, pela silhueta.
5. **No rótulo e no overview:** o número real de linhas e o nome da classe (ex.:
   "`trisafe-enhanced` · 48 mil linhas · Edifício").
6. **Andares (R20) dentro da altura.** Cada pasta de 1º nível é um andar, com altura proporcional à
   sua parcela das linhas do projeto; os arquivos da raiz formam o **térreo**. Cada andar tem pelo
   menos um nível. Se o prédio tiver mais pastas do que níveis (ex.: uma Casa com várias pastas),
   as pastas menores se juntam num andar **"demais pastas"**, e as alterações delas acendem ali (§6).
7. **Contagem (D-053, D-054, D-056):** linhas **não vazias** dos arquivos que o git acompanha
   (comentários contam), ignorando o que o `.gitignore` ignora e uma **lista fixa e visível de
   arquivos gerados** (lockfiles, `*.min.js`, saídas de build versionadas). Padrão: só código, **sem
   `.md`**; o filtro e as exclusões mudam nas configurações do Orb (R29), por realm ou para todos.
   As faixas são fixas (rastreáveis).
8. **Quando recalcular (D-055):** ao abrir o Orb e quando as alterações locais do realm mudam, no
   máximo uma vez por minuto por realm.

## 9. Os nomes dos Alter Egos (R37)

**Decidido pelo Lucas (2026-10-08, D-063):** o primeiro elemento do **Perfil** é um **nome histórico**:
um nome famoso da tecnologia, física, matemática ou filosofia, **sorteado** quando a sessão
aparece. Repetir não é problema, mas o ideal é **consumir todos os nomes antes de um se repetir**
(sorteio sem reposição, como uma sacola).

**Tipo: Identidade.** O nome **não é dado** de telemetria (não diz nada sobre a sessão) e por isso
não fere a regra R12: é o nome do personagem, e assim é apresentado.

**Como funciona (decidido em 2026-10-08, D-064 a D-067):**

1. **Sacola.** Os 60 nomes abaixo entram numa sacola embaralhada. Cada sessão nova tira o próximo.
   Quando a sacola esvazia, ela é embaralhada de novo. Assim um nome só volta depois de todos os
   outros terem saído.
2. **O nome fica com a sessão para sempre**: na sala, no Histórico do realm e ao reabrir a sessão. O
   Orb guarda a associação sessão → nome no seu registro local (R36).
3. **Sem gêmeos na sala:** se o nome sorteado já estiver em uso por um personagem visível na mesma
   sala, tira-se o seguinte.
4. **Subagentes não ganham nome histórico**: ficam com o tipo que o CLI dá a eles (Explore,
   qa-reviewer…), porque são temporários (D-065).
5. **Rótulo:** o nome em destaque; embaixo, "Claude · <título da sessão>" (D-066).
6. Só pessoas históricas **já falecidas**, de áreas e épocas variadas, com mulheres e brasileiros.
   **A lista abaixo está aprovada** (D-067).

| # | Nome no personagem | Pessoa | Área |
|---|---|---|---|
| 1 | Einstein | Albert Einstein | física |
| 2 | Newton | Isaac Newton | física |
| 3 | Galileu | Galileu Galilei | física |
| 4 | Marie Curie | Marie Curie | física |
| 5 | Tesla | Nikola Tesla | física |
| 6 | Oppenheimer | J. Robert Oppenheimer | física |
| 7 | Feynman | Richard Feynman | física |
| 8 | Bohr | Niels Bohr | física |
| 9 | Planck | Max Planck | física |
| 10 | Faraday | Michael Faraday | física |
| 11 | Maxwell | James Clerk Maxwell | física |
| 12 | Schrödinger | Erwin Schrödinger | física |
| 13 | Heisenberg | Werner Heisenberg | física |
| 14 | Dirac | Paul Dirac | física |
| 15 | Fermi | Enrico Fermi | física |
| 16 | Lise Meitner | Lise Meitner | física |
| 17 | Hawking | Stephen Hawking | física |
| 18 | César Lattes | César Lattes | física |
| 19 | Kepler | Johannes Kepler | astronomia |
| 20 | Copérnico | Nicolau Copérnico | astronomia |
| 21 | Euler | Leonhard Euler | matemática |
| 22 | Gauss | Carl Friedrich Gauss | matemática |
| 23 | Emmy Noether | Emmy Noether | matemática |
| 24 | Ramanujan | Srinivasa Ramanujan | matemática |
| 25 | Gödel | Kurt Gödel | matemática |
| 26 | Hilbert | David Hilbert | matemática |
| 27 | Riemann | Bernhard Riemann | matemática |
| 28 | Poincaré | Henri Poincaré | matemática |
| 29 | Galois | Évariste Galois | matemática |
| 30 | Euclides | Euclides | matemática |
| 31 | Pitágoras | Pitágoras | matemática |
| 32 | Arquimedes | Arquimedes | matemática |
| 33 | Al-Khwarizmi | Al-Khwarizmi | matemática |
| 34 | Hipátia | Hipátia de Alexandria | matemática |
| 35 | Ada Lovelace | Ada Lovelace | computação |
| 36 | Turing | Alan Turing | computação |
| 37 | Babbage | Charles Babbage | computação |
| 38 | Boole | George Boole | computação |
| 39 | Shannon | Claude Shannon | computação |
| 40 | Von Neumann | John von Neumann | computação |
| 41 | Grace Hopper | Grace Hopper | computação |
| 42 | Dijkstra | Edsger Dijkstra | computação |
| 43 | Ritchie | Dennis Ritchie | computação |
| 44 | McCarthy | John McCarthy | computação |
| 45 | Katherine Johnson | Katherine Johnson | computação |
| 46 | Hedy Lamarr | Hedy Lamarr | tecnologia |
| 47 | Santos Dumont | Alberto Santos Dumont | tecnologia |
| 48 | Da Vinci | Leonardo da Vinci | tecnologia |
| 49 | Sócrates | Sócrates | filosofia |
| 50 | Platão | Platão | filosofia |
| 51 | Aristóteles | Aristóteles | filosofia |
| 52 | Tales | Tales de Mileto | filosofia |
| 53 | Descartes | René Descartes | filosofia |
| 54 | Pascal | Blaise Pascal | filosofia |
| 55 | Leibniz | Gottfried Leibniz | filosofia |
| 56 | Kant | Immanuel Kant | filosofia |
| 57 | Spinoza | Baruch Spinoza | filosofia |
| 58 | Wittgenstein | Ludwig Wittgenstein | filosofia |
| 59 | Confúcio | Confúcio | filosofia |
| 60 | Simone de Beauvoir | Simone de Beauvoir | filosofia |

## Decisões pendentes

| Id | Pergunta | Proposta inicial |
|---|---|---|
| V-PEND-1 | **Janelas (V-REALM-3).** ~~Que cor significa o quê?~~ **Decidido (2026-10-07): a cor do tipo de alteração no git (R20a).** ~~(a) Qual unidade cada janela representa?~~ **Decidido (2026-10-08): um arquivo (R20b).** ~~(b) De onde vem o tipo de alteração?~~ **Decidido: das alterações locais** (estado do repositório na máquina), lido sem gravar nada no `.git` (R20b, R16). ~~E um prédio com milhares de arquivos?~~ **Decidido: janelas por percentual (R20d, §6).** ~~(c) V-PEND-1c: ela também esmaece pela recência?~~ **Decidido (2026-10-08): não; só acesa ou apagada (D-043).** | — |
| V-PEND-2 | **"Dormindo" e sessões encerradas.** ~~Sessão encerrada some?~~ **Decidido: não é excluída (R28).** ~~Onde ficam as encerradas e as antigas (~450 sessões nesta máquina)?~~ **Decidido (2026-10-08): na sala, as ativas e as dos últimos 10 dias, prazo configurável no Orb; as demais no Histórico do realm (R28a).** ~~V-PEND-2b: a partir de quanto tempo parada uma sessão aparece "dormindo"?~~ **Decidido (2026-10-08): 15 min (R31, D-044).** ~~E o nome da lista?~~ **Decidido: Histórico do realm.** | — |
| V-PEND-3 | ~~**Fim de subagente em segundo plano** sem o sinal no nível 0: esconder, mostrar como "sem sinal" ou exigir o nível 1?~~ **Decidido (2026-10-08): fica cinza (R7, D-045).** | — |
| V-PEND-3b | ~~**Cinza "sem sinal" × cinza do opencode**: como distinguir? Depois de quanto tempo?~~ **Decidido (2026-10-08, D-050): cinza translúcido, sem halo e com ícone de sinal cortado; 5 min sem atividade.** | — |
| V-PEND-4 | ~~Cenário é permitido?~~ **Decidido (2026-10-07): sim, declarado aqui e sem cores da legenda (R12a).** | — |
| V-PEND-5 | ~~**Posição dos prédios**~~ **Decidido (2026-10-08): cidade retangular, ordem alfabética, "aleatório" rastreável (R32, D-046); traçado delegado (D-047, §7).** | — |
| V-PEND-6 | ~~**Escala da altura**~~ **Decidido (2026-10-08): absoluta, por classes de faixa de linhas, com destaque para o grande (R19, D-051); escala delegada (D-052, §8).** ~~Percentual do maior realm (D-049)~~ revisto. | — |
| V-PEND-7 | **Conflito de cores (apontado pela regra P2).** As cores do git (verde = inserção, âmbar/amarelo = modificação, vermelho = remoção) já existem na legenda: verde = Testing Lab (V-REALM-8) e verde-água = Codex (V-EGO-1); amarelo = Code Review (V-REALM-8); âmbar = "esperando o Lucas" (V-REALM-5/6, V-EGO-6). ~~Qual muda? Qual a paleta do git?~~ **Decidido (2026-10-08): as janelas usam a paleta do git do VS Code; as áreas e o "esperando" trocam de cor (R20a, R20c).** | — |
| V-PEND-7b | **As novas cores** das 5 áreas e do "esperando o Lucas", sem colidir com a paleta do git (§5). Atenção também às cores dos **providers**: o laranja do Claude fica perto do vermelho de remoção e do conflito, e o verde-água do Codex perto do verde de "não rastreado". Personagens e janelas são objetos diferentes; basta isso, ou os providers também mudam? | **Decidido (2026-10-08):** áreas em tons frios e neutros; "esperando" em magenta pulsante (R20c). Os providers **mudaram** (R30), o que reabre a escolha: V-PEND-7c. **Revisto em D-040:** áreas sem cor própria |
| V-PEND-7c | **As cores novas dos providers (R30) colidem** (apontado pela regra P2): (a) **Hermes amarelo** × âmbar de "modificado" do git (`#E2C08D`) nas janelas; (b) **Codex azul** e **opencode cinza** × as áreas em tons frios e neutros (azul, cinza-azulado): um personagem azul sobre um piso azul some; (c) **Claude laranja** fica perto do vermelho de "apagado"/"conflito". | **Decidido (2026-10-08, D-040):** áreas sem cor própria (ícone, nome e padrão no piso); providers com as cores escolhidas, em tons saturados. |
| V-PEND-7d | **Os tons exatos** (hex) de cada provider e do magenta, e **os ícones das 5 áreas** (Development Center, Testing Lab, Research Center, Code Review, Task Board). | Escolher junto da implementação, com uma prévia visual para o Lucas aprovar antes de valer |
