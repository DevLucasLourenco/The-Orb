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
| V-CITY-1 | Disco flutuante (o Orb), borda de luz | Cenário | O chão da cidade; o raio só acompanha a quantidade de realms | ❓ V-PEND-4 |
| V-CITY-2 | Grade polar no chão | Cenário | Referência de profundidade para a câmera | ❓ V-PEND-4 |
| V-CITY-3 | Céu em degradê e estrelas | Cenário | Ambiente noturno | ❓ V-PEND-4 |
| V-CITY-4 | Posição de cada prédio (grade em ordem alfabética) | Heurística | Ordem arbitrária | ❓ V-PEND-5 |
| V-CITY-5 | Barra superior (realms, sessões, ativas, esperando você, subagentes, tokens) | Dado | Soma do snapshot do Core | ✅ |

## 2. O prédio (Realm)

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-REALM-1 | Existir um prédio | Dado | Um projeto onde algum provider tem sessões (R3) | ❌ Hoje vem de `--root`/`--realm`, inclusive pastas sem sessão |
| V-REALM-2 | **Altura** | Dado | Linhas de código do projeto, ignorando o `.gitignore` (R19) | ❌ Altura fixa igual para todos |
| V-REALM-3 | **Janelas: quais acendem e de que cor** | — | **Hoje: padrão aleatório**, sorteado pelo nome do realm, com cores quentes/frias sem significado. Deveria ser: andares = pastas de 1º nível; janela acesa = edição recente naquele trecho, esmaecendo com o tempo (R20) | ❌ Viola R12 |
| V-REALM-4 | Brilho geral das janelas | Dado | Quantidade de sessões ativas no realm (0 → apagado; 3 ou mais → máximo) | ⚠️ Correto como dado, mas aplicado sobre o padrão aleatório |
| V-REALM-5 | Arestas de luz do Rooftop Room: azul / âmbar | Dado | Âmbar quando alguma sessão do realm espera o Lucas | ✅ |
| V-REALM-6 | Feixe âmbar subindo do prédio, anel âmbar pulsando | Dado | Alguma sessão do realm espera o Lucas (aprovação/pergunta); visível de toda a cidade | ✅ |
| V-REALM-7 | Rótulo: nome, "N sessões · M ativas · K esperando" | Dado | Snapshot do Core | ✅ |
| V-REALM-8 | Cinco áreas coloridas no piso | Legenda | Azul = Development Center · Verde = Testing Lab · Violeta = Research Center · Amarelo = Code Review · Rosa = Task Board (R21) | ✅ (legenda documentada aqui) |
| V-REALM-9 | Anel no centro da sala (lobby) | Legenda | Lugar de quem não está numa área: pensando, parado, esperando, delegando | ✅ |
| V-REALM-10 | Fileira na frente da sala | Heurística | Sessões "dormindo" (parada há mais de 15 min, ou encerrada) | ❓ V-PEND-2 |
| V-REALM-11 | Luz interna da sala, sombras | Cenário | Iluminação | ❓ V-PEND-4 |

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

---

## Decisões pendentes

| Id | Pergunta | Proposta inicial |
|---|---|---|
| V-PEND-1 | **Janelas (V-REALM-3):** qual unidade cada janela representa? Uma janela por arquivo? Por pasta? Que cor significa o quê (ex.: provider que editou; ou só aceso/apagado)? Por quanto tempo uma edição mantém a janela acesa? | Andar = pasta de 1º nível, proporcional às linhas dela; janela acende na cor do provider que editou e esmaece em ~30 min; sem edição = apagada |
| V-PEND-2 | **"Dormindo":** existe esse estado no mundo? Com que limite de tempo? Sessão encerrada some, dorme ou vai para um memorial? | Liga-se ao Perfil (R6) e à retomada (R10); decidir junto |
| V-PEND-3 | **Fim de subagente em segundo plano** sem o sinal no nível 0: esconder por tempo, mostrar como "sem sinal", ou exigir o nível 1? | Mostrar `NO_SIGNAL` (cinza) em vez de sumir, até haver sinal real |
| V-PEND-4 | **Cenário é permitido?** Chão, grade, céu, estrelas e luz não representam dado. Ficam como cenário declarado ou saem? | Permitir cenário neutro e sem cor de dado; nunca usar as cores da legenda no cenário |
| V-PEND-5 | **Posição dos prédios:** ordem alfabética, por atividade, por tamanho, ou fixa e escolhida pelo Lucas? | Posição estável (não muda sozinha) para a memória espacial; critério a decidir |
| V-PEND-6 | **Escala da altura** (linear, raiz, log) para um repo de 500 mil linhas não esconder um de 2 mil. | Já listada em [VISION.md](VISION.md) §7 |
