# The Orb — Regras do produto

> Tudo o que o Lucas pediu, como **regras numeradas e verificáveis**. É a fonte dos tickets: todo
> ticket cita as regras que cumpre, e uma regra só está "cumprida" quando a implementação a respeita
> e existe forma de verificar. Vocabulário: [CONTEXT.md](../CONTEXT.md) · Visão: [VISION.md](VISION.md)
> · O que cada elemento visual significa: [VISUAL.md](VISUAL.md).

Última atualização: 2026-10-07

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
| P2 | Pedido que conflita com uma regra existente é apontado **antes** de implementar, e a decisão fica registrada. | Lucas, 2026-10-07 | ❌ Ex.: janelas aleatórias contradizem R12 e R20 e não foram apontadas |
| P3 | Nenhuma ideia é apagada; muda de status com motivo. | [IDEAS.md](IDEAS.md) | ✅ |

## 2. Identidade e domínio

| # | Regra | Origem | Situação |
|---|---|---|---|
| R1 | O projeto se chama **The Orb** (sem "Orb IA", "Orb AI", "Agent World"), inclusive no GitHub. | Lucas | ✅ |
| R2 | **Realm = um projeto = um prédio.** | Visão | ✅ |
| R3 | **Os realms são detectados pelos providers.** Um realm existe porque algum provider tem sessões naquele projeto; o Lucas nunca precisa informar caminhos. Detalhe em [ARCHITECTURE.md](ARCHITECTURE.md) §3 (Detecção de realms). | Lucas, 2026-10-07 | ❌ Hoje os realms vêm de `--root`/`--realm`; o `--root` ainda cria prédios para pastas sem nenhuma sessão |
| R4 | Um realm pode ter sessões de **vários providers ao mesmo tempo** (ex.: Claude e Codex). | Lucas | ✅ |
| R5 | **Alter Ego = uma sessão.** Carrega e identifica **sozinho** o seu provider, e o título e o modelo vêm do próprio CLI. | Lucas, [ADR 0001](adr/0001-alter-ego-e-uma-sessao.md) | ✅ |
| R6 | O **Perfil** do Alter Ego (identidade além da sessão) está em aberto e **não é implementado** antes de decidido. | Lucas | ✅ (não implementado) |
| R7 | Os **subagentes** de uma sessão aparecem junto dela, como a Team. | Lucas | ⚠️ No nível 0 o fim de um subagente em segundo plano não é observável; o cliente esconde subagentes sem atividade há 5 min, uma heurística que não foi decidida (ver VISUAL.md, V-PEND-3) |
| R8 | Os 4 CLIs instalados são providers: **claude, codex, hermes, opencode**. | Lucas | ✅ |

## 3. Inner World

| # | Regra | Origem | Situação |
|---|---|---|---|
| R9 | **Inner World = o terminal com o CLI real + a linha do tempo da sessão**, num lugar só. | Lucas, [ADR 0003](adr/0003-inner-world-une-terminal-e-pensamento.md) | ⚠️ O terminal só existe para sessões abertas pelo painel; sessões abertas fora do Orb só têm a linha do tempo |
| R10 | O Inner World é **persistido e reutilizável**: a sessão pode ser reaberta (retomada) num terminal novo. | Lucas | ⏳ `Launch(resume=True)` existe; não há interface nem verificação por provider |
| R11 | O Orb **não rastreia quem escreveu** cada mensagem. | Lucas, 2026-10-07 | ✅ |

## 4. Telemetria e fidelidade

| # | Regra | Origem | Situação |
|---|---|---|---|
| R12 | **Telemetria real, nunca animação inventada.** Todo elemento visual que parece dado **é** dado; o que for só cenário é declarado como cenário em [VISUAL.md](VISUAL.md). | Visão, princípio 1 | ❌ Janelas dos prédios são um padrão aleatório (V-REALM-3); ⚠️ "dormindo" após 15 min e subagente some após 5 min são inferências de apresentação sem decisão |
| R13 | **Cada provider aparece como ele é** (evento nativo intacto); o mundo usa só sinais derivados. | Lucas, [ADR 0002](adr/0002-eventos-nativos-por-provider.md) | ✅ |
| R14 | **Fidelidade explícita** do pensamento (`raw`/`summary`); nada deduzido aparece como pensamento. | Visão | ⚠️ Hermes e opencode marcam `raw` sem confirmar se o modelo entrega texto bruto ou resumo |
| R15 | **CLI nativo**: o Orb abre um terminal real e chama o CLI original; nenhuma TUI criada. | Visão, ADR 0004 | ✅ |
| R16 | **Não interferência**: tudo do provider é somente leitura; o Orb nunca responde diálogos nem pedidos de servidor. | Visão, ADR 0005, ADR 0006 | ✅ |

## 5. O mundo

| # | Regra | Origem | Situação |
|---|---|---|---|
| R17 | **Mundo 3D navegável**, o produto principal: cidade vista de cima, câmera livre (WASD, scroll, Q/E, botão direito, F, Esc, 1–9, duplo clique para seguir). | Lucas, Visão | ⚠️ Falta "duplo clique segue o personagem" |
| R18 | **Overview por alto** de um realm: o que cada sessão faz agora, quem está esperando o Lucas, subagentes e consumo. | Lucas, 2026-10-07 | ✅ |
| R19 | **Altura do prédio = linhas de código** do projeto, sempre ignorando o `.gitignore`, com filtro (ex.: incluir `.md`). | Visão (decidido) | ❌ Todos os prédios têm a mesma altura |
| R20 | **Andares = pastas de primeiro nível; janelas acendem onde houve edição recente** e esmaecem com o tempo. | Visão (camadas vivas) | ❌ As janelas atuais são decoração aleatória e contradizem esta regra |
| R21 | Todo Rooftop Room tem as **5 áreas** do Environment, sempre. | Visão (decidido) | ✅ |
| R22 | O personagem fica na área da **atividade real** da sessão; esperar o Lucas é visível de longe. | Visão | ✅ |

## 6. Engenharia

| # | Regra | Origem | Situação |
|---|---|---|---|
| R23 | **Estrutura sólida por âmbito**: módulos com fronteira e contrato (protocolo, mundo, adapters, terminal, servidor, cliente). | Lucas | ✅ no servidor · ⚠️ no cliente: as regras visuais estão só no código, sem documento (corrigido por VISUAL.md) |
| R24 | **Robustez**: entrada validada na borda, falha isolada, degradação explícita. | Lucas | ✅ |
| R25 | **Desempenho**: leitura incremental, cargas limitadas, nada lido duas vezes, leitores compartilhados. | Lucas | ✅ |
| R26 | **Lógica bem descrita**: regras em tabelas declarativas e documentadas. | Lucas | ⚠️ Mesmo caso da R23 no cliente |

---

## Do documento aos tickets

**Quando:** depois que o Lucas revisar este documento e as questões em aberto de VISUAL.md e de
ARCHITECTURE.md §3 (Detecção de realms) estiverem decididas.

**Onde:** GitHub Issues do repositório `DevLucasLourenco/The-Orb` (a confirmar).

**Organização em épicos** (um por âmbito):

| Épico | Regras principais |
|---|---|
| Processo e documentação | P1, P2 |
| Detecção de realms pelos providers | R3 |
| Alter Ego e Perfil | R5, R6, R10 |
| Inner World (terminal + linha do tempo, retomada) | R9, R10 |
| Adapters (Claude, Codex, Hermes, opencode) | R7, R8, R13, R14 |
| Mundo 3D: prédios (altura por LOC, andares, janelas acesas) | R12, R19, R20 |
| Mundo 3D: personagens, áreas, câmera | R17, R21, R22 |
| Overview e camadas vivas (Gate, Energy, Weather, Chronicle, Archive) | R18 e [IDEAS.md](IDEAS.md) §6 |

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
