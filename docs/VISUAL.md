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
| V-REALM-3 | **Janelas: quais acendem e de que cor** | Dado | **Hoje: padrão aleatório**, sorteado pelo nome do realm, com cores quentes/frias sem significado. **Decidido:** andares = pastas de 1º nível (R20); **cada janela é um arquivo**, acesa quando o arquivo tem **alteração local** (R20b); **a cor é a do tipo de alteração no git**, paleta do VS Code (R20a, §5). Pendente: se também esmaece pela recência, e prédios com milhares de arquivos (V-PEND-1c) | ❌ Viola R12 |
| V-REALM-4 | Brilho geral das janelas | Dado | Quantidade de sessões ativas no realm (0 → apagado; 3 ou mais → máximo) | ⚠️ Correto como dado, mas aplicado sobre o padrão aleatório |
| V-REALM-5 | Arestas de luz do Rooftop Room: azul / âmbar | Dado | Âmbar quando alguma sessão do realm espera o Lucas | ⚠️ A cor do "esperando" muda (R20c, V-PEND-7b) |
| V-REALM-6 | Feixe âmbar subindo do prédio, anel âmbar pulsando | Dado | Alguma sessão do realm espera o Lucas (aprovação/pergunta); visível de toda a cidade | ⚠️ A cor do "esperando" muda (R20c, V-PEND-7b) |
| V-REALM-7 | Rótulo: nome, "N sessões · M ativas · K esperando" | Dado | Snapshot do Core | ✅ |
| V-REALM-8 | Cinco áreas coloridas no piso | Legenda | Hoje: Azul = Development Center · Verde = Testing Lab · Violeta = Research Center · Amarelo = Code Review · Rosa = Task Board (R21) | ⚠️ Verde e amarelo colidem com o git: as cores das áreas mudam (R20c, V-PEND-7b) |
| V-REALM-9 | Anel no centro da sala (lobby) | Legenda | Lugar de quem não está numa área: pensando, parado, esperando, delegando | ✅ |
| V-REALM-10 | Fileira na frente da sala | Heurística | Sessões "dormindo" (parada há mais de 15 min, ou encerrada). Encerradas **não são excluídas** (R28). **Na sala só ficam as ativas e as dos últimos 10 dias** (configurável, R28a); as demais vão para a lista de sessões antigas do realm | ⚠️ Prazo decidido; limite de "dormindo" em V-PEND-2b |
| V-REALM-11 | Luz interna da sala, sombras | Cenário | Iluminação | ✅ (R12a) |

## 3. O personagem (Alter Ego) e os subagentes

| Id | Elemento | Tipo | Significado / fonte | Situação |
|---|---|---|---|---|
| V-EGO-1 | **Cor** do corpo e do halo | Legenda | Provider da sessão: laranja = Claude · verde-água = Codex · violeta = Hermes · azul = opencode | ✅ |
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
| V-HUD-6 | **Lista de sessões antigas do realm** | Dado | Sessões encerradas ou paradas há mais que o prazo (10 dias, R28a), no overview do realm; nenhuma some | ⏳ Nome a decidir |
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

### Providers — personagens (V-EGO-1)

Claude `#E8845C` · Codex `#2FD3A2` · Hermes `#B18CFF` · opencode `#5AA8FF`.

### Áreas e "esperando o Lucas"

Mudam (R20c); as novas cores estão em V-PEND-7b.

## Decisões pendentes

| Id | Pergunta | Proposta inicial |
|---|---|---|
| V-PEND-1 | **Janelas (V-REALM-3).** ~~Que cor significa o quê?~~ **Decidido (2026-10-07): a cor do tipo de alteração no git (R20a).** ~~(a) Qual unidade cada janela representa?~~ **Decidido (2026-10-08): um arquivo (R20b).** ~~(b) De onde vem o tipo de alteração?~~ **Decidido: das alterações locais** (estado do repositório na máquina), lido sem gravar nada no `.git` (R20b, R16). (c) **V-PEND-1c, em aberto:** a janela fica acesa enquanto a alteração local existir; ela também esmaece pela recência? E um prédio com milhares de arquivos: uma janela para cada? | (c) Brilho pela recência da alteração, cor pelo tipo; muitos arquivos: janelas proporcionais por andar, com as alteradas sempre visíveis |
| V-PEND-2 | **"Dormindo" e sessões encerradas.** ~~Sessão encerrada some?~~ **Decidido: não é excluída (R28).** ~~Onde ficam as encerradas e as antigas (~450 sessões nesta máquina)?~~ **Decidido (2026-10-08): na sala, as ativas e as dos últimos 10 dias, prazo configurável no Orb; as demais numa lista de sessões antigas do realm (R28a).** **V-PEND-2b, em aberto:** dentro da sala, a partir de quanto tempo parada uma sessão aparece "dormindo"? E o nome da lista ("arquivo" colide com o termo Archive do glossário)? | 2b: dormindo depois de 15 min parada (o atual), também configurável; nome: "Histórico do realm" |
| V-PEND-3 | **Fim de subagente em segundo plano** sem o sinal no nível 0: esconder por tempo, mostrar como "sem sinal", ou exigir o nível 1? | Mostrar `NO_SIGNAL` (cinza) em vez de sumir, até haver sinal real |
| V-PEND-4 | ~~Cenário é permitido?~~ **Decidido (2026-10-07): sim, declarado aqui e sem cores da legenda (R12a).** | — |
| V-PEND-5 | **Posição dos prédios:** ordem alfabética, por atividade, por tamanho, ou fixa e escolhida pelo Lucas? | Posição estável (não muda sozinha) para a memória espacial; critério a decidir |
| V-PEND-6 | **Escala da altura** (linear, raiz, log) para um repo de 500 mil linhas não esconder um de 2 mil. | Já listada em [VISION.md](VISION.md) §7 |
| V-PEND-7 | **Conflito de cores (apontado pela regra P2).** As cores do git (verde = inserção, âmbar/amarelo = modificação, vermelho = remoção) já existem na legenda: verde = Testing Lab (V-REALM-8) e verde-água = Codex (V-EGO-1); amarelo = Code Review (V-REALM-8); âmbar = "esperando o Lucas" (V-REALM-5/6, V-EGO-6). ~~Qual muda? Qual a paleta do git?~~ **Decidido (2026-10-08): as janelas usam a paleta do git do VS Code; as áreas e o "esperando" trocam de cor (R20a, R20c).** | — |
| V-PEND-7b | **As novas cores** das 5 áreas e do "esperando o Lucas", sem colidir com a paleta do git (§5). Atenção também às cores dos **providers**: o laranja do Claude fica perto do vermelho de remoção e do conflito, e o verde-água do Codex perto do verde de "não rastreado". Personagens e janelas são objetos diferentes; basta isso, ou os providers também mudam? | Áreas em tons frios e neutros (azul, índigo, ciano, lilás, cinza-azulado); "esperando" em magenta pulsante; providers mantidos (estão em personagens, não em janelas) |
