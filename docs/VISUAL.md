# The Orb — Linguagem visual

> O que **cada elemento** do mundo 3D significa e de que dado real ele vem. Regra R12
> ([RULES.md](RULES.md)): todo elemento que parece dado **é** dado; o resto é **cenário**, declarado
> aqui. Um elemento novo só entra no mundo depois de ter uma linha nesta tabela.

Última atualização: 2026-10-07

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
| V-REALM-3 | **Janelas: quais acendem e de que cor** | Dado | **Hoje: padrão aleatório**, sorteado pelo nome do realm, com cores quentes/frias sem significado. **Decidido:** andares = pastas de 1º nível; janela acesa = alteração recente naquele trecho, esmaecendo com o tempo (R20); **a cor é a do tipo de alteração no git** (R20a): inserção, modificação, remoção… Pendente: unidade da janela, fonte da alteração e paleta exata (V-PEND-1, V-PEND-7) | ❌ Viola R12 |
| V-REALM-4 | Brilho geral das janelas | Dado | Quantidade de sessões ativas no realm (0 → apagado; 3 ou mais → máximo) | ⚠️ Correto como dado, mas aplicado sobre o padrão aleatório |
| V-REALM-5 | Arestas de luz do Rooftop Room: azul / âmbar | Dado | Âmbar quando alguma sessão do realm espera o Lucas | ✅ |
| V-REALM-6 | Feixe âmbar subindo do prédio, anel âmbar pulsando | Dado | Alguma sessão do realm espera o Lucas (aprovação/pergunta); visível de toda a cidade | ✅ |
| V-REALM-7 | Rótulo: nome, "N sessões · M ativas · K esperando" | Dado | Snapshot do Core | ✅ |
| V-REALM-8 | Cinco áreas coloridas no piso | Legenda | Azul = Development Center · Verde = Testing Lab · Violeta = Research Center · Amarelo = Code Review · Rosa = Task Board (R21) | ✅ (legenda documentada aqui) |
| V-REALM-9 | Anel no centro da sala (lobby) | Legenda | Lugar de quem não está numa área: pensando, parado, esperando, delegando | ✅ |
| V-REALM-10 | Fileira na frente da sala | Heurística | Sessões "dormindo" (parada há mais de 15 min, ou encerrada). Encerradas **não são excluídas** (R28) | ❓ V-PEND-2 |
| V-REALM-11 | Luz interna da sala, sombras | Cenário | Iluminação | ✅ (R12a) |

## 3. O personagem (Alter Ego) e os subagentes

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-EGO-1 | **Cor** do corpo e do halo | Legenda | Provider da sessão: laranja = Claude · verde-água = Codex · violeta = Hermes · azul = opencode | ✅ |
| V-EGO-2 | **Posição** (área da sala) | Dado | Atividade atual da sessão → área ([PROTOCOL.md](PROTOCOL.md) §5) | ✅ |
| V-EGO-3 | Caminhar até a área | Dado | Mudança de atividade | ✅ |
| V-EGO-4 | Balanço do corpo, halo girando mais rápido | Dado | A sessão está trabalhando (lendo, editando, executando, testando, revisando, pesquisando) | ✅ |
| V-EGO-5 | Três pontos orbitando a cabeça | Dado | `THINKING` | ✅ |
| V-EGO-6 | Losango âmbar sobre a cabeça | Dado | A sessão espera o Lucas | ✅ |
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

---

## Decisões pendentes

| Id | Pergunta | Proposta inicial |
|---|---|---|
| V-PEND-1 | **Janelas (V-REALM-3).** ~~Que cor significa o quê?~~ **Decidido (2026-10-07): a cor do tipo de alteração no git (R20a).** Ainda em aberto: (a) qual unidade cada janela representa (um arquivo? um trecho da pasta?); (b) **de onde vem o tipo de alteração**: das edições que os agentes fizeram (eventos dos providers: criar arquivo = inserção, editar = modificação, apagar = remoção) ou do estado do repositório (`git status`, que precisa rodar sem gravar nada no `.git`: `--no-optional-locks`)? (c) por quanto tempo a janela fica acesa? | Andar = pasta de 1º nível, proporcional às linhas dela; fonte = eventos dos providers (já são observados e sabem o tipo); esmaece em ~30 min |
| V-PEND-2 | **"Dormindo" e sessões encerradas.** ~~Sessão encerrada some?~~ **Decidido: não é excluída (R28).** Ainda em aberto: com ~450 sessões registradas nesta máquina (Claude 31, Codex 397, Hermes 20, opencode 2), mostrar todas como personagens lotaria as salas. Onde ficam as encerradas e as antigas: dormindo na sala, num memorial/arquivo do realm, ou só no overview? Qual o limite de tempo para "dormir"? | Na sala: só as ativas e as recentes (limite a decidir); as demais ficam acessíveis num "arquivo" do realm (lista no overview), sem sumir |
| V-PEND-3 | **Fim de subagente em segundo plano** sem o sinal no nível 0: esconder por tempo, mostrar como "sem sinal", ou exigir o nível 1? | Mostrar `NO_SIGNAL` (cinza) em vez de sumir, até haver sinal real |
| V-PEND-4 | ~~Cenário é permitido?~~ **Decidido (2026-10-07): sim, declarado aqui e sem cores da legenda (R12a).** | — |
| V-PEND-5 | **Posição dos prédios:** ordem alfabética, por atividade, por tamanho, ou fixa e escolhida pelo Lucas? | Posição estável (não muda sozinha) para a memória espacial; critério a decidir |
| V-PEND-6 | **Escala da altura** (linear, raiz, log) para um repo de 500 mil linhas não esconder um de 2 mil. | Já listada em [VISION.md](VISION.md) §7 |
| V-PEND-7 | **Conflito de cores (apontado pela regra P2).** As cores do git (verde = inserção, âmbar/amarelo = modificação, vermelho = remoção) já existem na legenda: verde = Testing Lab (V-REALM-8) e verde-água = Codex (V-EGO-1); amarelo = Code Review (V-REALM-8); âmbar = "esperando o Lucas" (V-REALM-5/6, V-EGO-6). Qual muda? E qual a paleta exata do git? | Manter as cores do git nas janelas (é o pedido); trocar as cores das **áreas** por tons que não colidam e trocar o "esperando" para outra cor de alerta; paleta do git = a das decorações de alteração do VS Code (a confirmar com o Lucas) |
