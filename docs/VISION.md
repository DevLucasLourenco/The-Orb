# The Orb — Visão

> O que o The Orb é, os princípios que não se negociam, como o mundo se organiza e o que ainda
> está em aberto. Vocabulário: [CONTEXT.md](../CONTEXT.md) · Decisões: [adr/](adr/).

Última atualização: 2026-10-07

---

## 1. O que é

O **The Orb** é um jogo 3D visto de cima (estilo RTS / colony-management, câmera livre) que
representa em tempo real o trabalho **real** de agentes de IA (Claude Code, Codex, Hermes,
opencode e outros CLIs) nos projetos reais do Lucas.

Os agentes continuam trabalhando de verdade nos repositórios, com os CLIs originais. O Orb
**observa** e transforma o que observa em mundo. Em uma frase:
**projeto real → sessão real → telemetria real → mundo virtual.**

**O 3D é o produto.** Painéis 2D existem para apoiar e para validar a telemetria antes do 3D.

**O Orb é o centralizador.** É um só lugar para ver o que cada IA e cada subagente faz e para
falar com eles. Há duas portas, e as duas dão no mesmo terminal:

- o **Inner World** de um Alter Ego (o terminal com o CLI real daquela sessão);
- o **Gate**, que escreve nesse mesmo terminal sem que o Lucas precise entrar no realm.

Natureza: híbrido de RTS, Digital Twin e plataforma de orquestração de agentes (um "Agent
Control Plane" gamificado).

## 2. Hierarquia

```
The Orb  (o mundo: uma cidade conceitual)
 └── Realm  (um projeto = um prédio; altura = linhas de código)
      └── Rooftop Room  (o quartinho no teto, com as 5 áreas do Environment)
           └── Team  (um Alter Ego + os subagentes da sessão dele)
                ├── Alter Ego  (uma sessão de um CLI = um personagem, o líder)
                │    └── Inner World  (o terminal do CLI + a linha do tempo da sessão)
                └── Subagente  (unidade temporária da sessão; pode ter subagentes)
```

**Mankind** é a população inteira: todos os Alter Egos e subagentes de todos os realms.

## 3. Princípios

1. **Telemetria real, nunca animação inventada.** O mundo só mostra o que veio de um evento
   observado. Sem dados, o personagem aparece como `NO_SIGNAL`; nunca com um estado inventado.
2. **Realidade confirmada por fontes externas.** "O agente disse que terminou" ≠ "terminou". Git,
   GitHub e CI confirmam o que de fato mudou, passou ou quebrou.
3. **Cada provider aparece como ele é.** O Orb não traduz o vocabulário do Claude, do Codex ou
   do Hermes e do opencode para um formato comum. Eventos são preservados no formato nativo e mostrados assim.
   O mundo usa só **sinais de mundo** derivados, ao lado do evento nativo
   ([ADR 0002](adr/0002-eventos-nativos-por-provider.md)).
4. **CLI nativo, nada criado do zero.** O Orb não cria TUI nem terminal próprios. Abre um terminal
   real (PowerShell) e chama nele o CLI original, escolhido pelo provider/modelo da sessão. O CLI
   roda com todas as funcionalidades; quando fecha, o terminal continua aberto. (O emulador que
   desenha o terminal na tela, como o xterm.js, é um componente pronto, não uma interface do Orb.)
5. **Não interferência.** O Orb não altera em nada como os agentes trabalham. Tudo o que molda uma
   sessão (`CLAUDE.md`, skills, memória, contexto, configurações) é somente leitura para o Orb.
   Observadores nunca devolvem decisão nem contexto. A **única porta de escrita** é o terminal do
   Inner World (digitado pelo Lucas, ou enviado por ele pelo Gate/painel).
6. **Decisões do Lucas são dele.** O Orb nunca responde diálogos dos CLIs (atualização, confiança
   de diretório, confiança de hooks, aprovações), nem em automação ou testes
   ([ADR 0006](adr/0006-o-orb-nunca-responde-dialogos.md)).
7. **Fidelidade explícita.** Tudo o que se mostra como pensamento declara o quão literal é
   (`raw`, `summary`); o que o Orb deduz (`inferred`) nunca é mostrado como pensamento.
8. **Modularização.** Cada âmbito do projeto é um módulo com fronteira e contrato explícitos.
   Módulos se falam só por contratos. Detalhes em [ARCHITECTURE.md](ARCHITECTURE.md).
9. **Robustez.** Formatos externos mudam e falham. Entrada externa é validada na borda; a falha de
   um provider nunca derruba os outros; a degradação é explícita.
10. **Desempenho por desenho.** Leitura incremental, nada lido duas vezes, cargas limitadas,
    estado em memória com snapshot + deltas. Detalhes em [ARCHITECTURE.md](ARCHITECTURE.md) §5.
11. **Lógica bem estruturada.** Domínio puro separado de I/O. Regras (atividade, altura do prédio,
    XP) são funções determinísticas, declaradas em tabelas, testáveis sem rede, disco ou UI.

## 4. O mundo

### Realm

Cada projeto real é um realm, e cada realm é um prédio. **Os realms são detectados pelos
providers**: a cidade se monta sozinha a partir das sessões que Claude, Codex, Hermes e opencode já
registram; o Lucas não informa caminhos (regra R3; como, em [ARCHITECTURE.md](ARCHITECTURE.md),
Detecção de realms). Entram **todos os projetos que algum CLI já registrou**; sessões fora de
projeto (pasta do usuário, pastas temporárias) são ignoradas; projetos cuja pasta não existe mais
não entram; e o Lucas pode **esconder** realms desmarcando-os numa lista, sem que nada mude nos
providers. As preferências do Lucas ficam numa **tela de configurações do Orb** (regra R29). Pode ter aparência temática própria (ex.:
TriSafe como centro industrial, CLARA como biblioteca, UTC CONECTA+ como estação de comunicação).
O objetivo é reconhecer onde há trabalho só olhando a cidade.

**A cidade é retangular**, com os prédios em ordem alfabética por bairros de letra e uma posição
"aleatória" mas rastreável (regra R32; traçado em [VISUAL.md](VISUAL.md) §7).

**Altura do prédio = linhas de código (LOC)** do repositório, em **escala absoluta por classes**
(Casa, Sobrado, Prédio, Edifício, Torre, Arranha-céu): a altura depende só das linhas do próprio
projeto, e o que é grande se destaca de verdade (escala em [VISUAL.md](VISUAL.md) §8):

- sempre ignora o que o `.gitignore` do projeto ignora (regra fixa, não configurável);
- contagem filtrável sobre o que sobra (incluir ou não `.md` e outros tipos);
- é calculada, nunca arbitrada.

### Rooftop Room e Environment

No teto de cada prédio fica o quartinho onde os Alter Egos daquele realm trabalham. Todo Rooftop
Room tem as cinco áreas do Environment, sem exceção, mesmo que o realm nunca use alguma:

| Área | Atividade que a ocupa |
|---|---|
| Development Center | `CODING`, `EXECUTING` |
| Testing Lab | `TESTING` |
| Research Center | `READING`, `RESEARCHING` |
| Code Review | `REVIEWING` |
| Task Board | `COMPLETED` |

### Alter Ego, Team e subagentes

- **Cada sessão é um Alter Ego** ([ADR 0001](adr/0001-alter-ego-e-uma-sessao.md)): um
  personagem, o líder da sua Team. Duas sessões no mesmo realm são dois personagens no mesmo
  Rooftop Room.
- Os **subagentes** que a sessão cria aparecem como personagens da Team, nascem, cumprem a
  missão e se desmobilizam. Subagentes podem criar subagentes.
- A Team só fica parada quando **nenhum** subagente está ativo: o fim do turno do líder não
  encerra a Team (verificado no Claude: a ferramenta `Agent` é assíncrona).
- O Alter Ego **persiste** depois que o terminal fecha, porque a sessão fica gravada pelo provider.
  Reabri-lo é retomar a sessão num terminal novo. **Sessões encerradas não são excluídas do mundo**
  (regra R28). Na sala ficam as ativas e as dos **últimos 10 dias** (configurável no Orb); as demais
  ficam no **Histórico do realm** (regra R28a).
- Stats e nível (XP), quando existirem, vêm só de histórico real (testes, PRs, retrabalho,
  tokens, tempo). Nunca inventados.

### Inner World

O interior de um Alter Ego ([ADR 0003](adr/0003-inner-world-une-terminal-e-pensamento.md)):

- **O terminal** com o CLI real da sessão. É onde o Lucas usa o agente, exatamente como fora do
  Orb.
- **A linha do tempo** da sessão: mensagens, pensamento, narração, ferramentas, arquivos lidos e
  editados, sempre com o nome e o texto do provider (`PreToolUse · Read` no Claude,
  `commandExecution` no Codex). O Orb não rastreia quem escreveu cada mensagem: quem usa o CLI é o
  Lucas, no próprio terminal ([ADR 0003](adr/0003-inner-world-une-terminal-e-pensamento.md)).

Limitação real: **o raciocínio interno nem sempre é exposto.** No Claude, ~88% dos blocos de
thinking vêm sem texto; no Codex, ~42% dos blocos de reasoning têm `summary` e nunca `raw`. O Inner
World é a reconstrução do que a sessão deixa observável, não acesso literal ao pensamento. Sem
sinal de pensamento, não se mostra pensamento: a ausência fica visível.

Ideia visual: clicar no Alter Ego e "mergulhar" nele; o cenário vira o mundo interno (plano como
mapa mental, arquivos lidos como objetos, dúvidas como nós abertos).

### Hospedar × Observar

| Modo | Como | Uso |
|---|---|---|
| **Hospedar** | O Orb abre o terminal e chama o CLI nele | Principal: a sessão nasce ligada a um Alter Ego |
| **Observar** | O Orb só lê uma sessão iniciada fora dele | Sessões abertas direto no terminal do Lucas |

Nos dois modos a telemetria é a mesma (adapter → eventos nativos + sinais de mundo).

**Níveis de pegada** ([ADR 0005](adr/0005-nivel-zero-de-pegada-por-padrao.md)):

| Nível | Claude Code | Codex | Hermes | opencode |
|---|---|---|---|---|
| **0 — zero pegada** (padrão) | Lê o transcript em `~/.claude/projects/` | Lê os rollouts em `~/.codex/sessions/` | Lê o `state.db` (somente leitura) | Lê o `opencode.db` (só tabelas de sessão) |
| **1 — tempo real** (opcional) | Hooks **por sessão** com `--settings` | **App-server próprio do Orb** + `codex --remote` | Sidecar da TUI (`HERMES_TUI_SIDECAR_URL`), a implementar | Servidor próprio + `--server`, a levantar |

## 5. Camadas vivas

Tudo abaixo é visualização de dados reais, somente leitura (princípio 5).

- **Andares e janelas acesas.** Andares = módulos/diretórios de primeiro nível (respeitando o
  `.gitignore`). As janelas mostram as **alterações locais** do projeto, na **cor do tipo de
  alteração no git** (paleta do VS Code): **cada janela acesa representa x% das alterações**, e
  nenhuma alteração fica dividida entre duas janelas (regras R20a, R20b, R20d; detalhe em
  [VISUAL.md](VISUAL.md) §6).
- **Weather.** CI passando = céu limpo; CI falhando = tempestade; testes falhando =
  rachaduras/andaimes; realm parado = noite.
- **Chronicle.** Arrastar a linha do tempo e ver a cidade como era. Funciona porque o estado do
  mundo é reconstruível do log de eventos; o histórico do git reconstrói o passado anterior ao Orb.
- **Energy.** Tokens e custo como recursos, por Alter Ego, por realm e por Mankind.
- **Gate.** Duas funções: **ver** tudo o que espera o Lucas (aprovações pendentes de todos os
  realms) e **escrever** a qualquer Alter Ego sem entrar no realm. O Gate não aprova nem decide
  sozinho e não cria canal paralelo: escreve no terminal do Inner World daquele Alter Ego, como se
  o Lucas tivesse digitado. Para uma sessão já fechada, o Gate **oferece reabrir** a sessão num
  terminal novo e espera a confirmação do Lucas; nunca reabre sozinho (R35).
- **Team.** O Alter Ego e os seus subagentes, agrupados, com a árvore de quem delegou o quê.
- **Archive.** O que molda cada sessão (instruções, skills, `CLAUDE.md`, memória), só para ver:
  nunca grava nem reinjeta nada; mostra nomes, tamanhos e datas por padrão e o conteúdo só quando
  o Lucas abrir explicitamente (pode haver dados pessoais).

Ordem sugerida: janelas acesas → Gate → Chronicle → Weather → Energy → Archive.

## 6. Roadmap

**Como se avança (regra P1):** documentar a regra ([RULES.md](RULES.md), [VISUAL.md](VISUAL.md), ADR) →
criar o ticket → implementar. Nada entra no código sem passar pelos dois primeiros.

0. ✅ **Spikes 1 a 4** (2026-10-06): terminal real hospedado, terminal no Godot e como monitor 3D,
   hooks do Claude ao vivo, observação do Codex. Ver [SPIKES.md](SPIKES.md).
1. ✅ **Promoção dos spikes** para os módulos definitivos (2026-10-07). Ver
   [ARCHITECTURE.md](ARCHITECTURE.md).
2. ✅ **Primeira versão do mundo 3D** (2026-10-07, [ADR 0007](adr/0007-cliente-3d-na-web.md)): cidade
   navegável em Three.js, vários realms, os 4 providers observados ao mesmo tempo, overview do realm
   (o que cada sessão faz, quem espera o Lucas, subagentes e consumo) e o Inner World com o terminal.
   Substituiu o painel 2D de validação.
3. Codex, Hermes e opencode validados ao vivo no mesmo painel; modo Observar.
4. **Sala 3D mais rica**: o terminal como monitor dentro do Rooftop Room, animações por atividade,
   altura do prédio pela contagem de linhas, andares e janelas acesas.
5. **Camadas vivas** e camada de jogo (mapas, movimentação, XP, quests, conquistas).

Interface 3D prevista: câmera 3/4 de ~40–55°, WASD mover, scroll zoom, Q/E rotacionar, botão
direito orbitar, F focar, ESC visão geral, 1–9 atalhos de realm, modo FREE CAM; o detalhe muda
com o zoom (realm → personagens → card detalhado).

## 7. Questões em aberto

**Alter Ego e Perfil** (a ideia ainda precisa amadurecer):

- O que é o **Perfil** de um Alter Ego? ~~Nome?~~ **Decidido: um nome histórico sorteado (R37,
  [VISUAL.md](VISUAL.md) §9).** Ainda em aberto: papel, aparência, stats; detalhes do nome em
  Q-NAME-1 a 4 ([DECISIONS.md](DECISIONS.md)).
- Duas sessões podem compartilhar um Perfil (ex.: "o Alter Ego de revisão do TriSafe" usado em
  várias sessões)? Se sim, o personagem é a sessão ou o Perfil?
- Retomada (`resume`), bifurcação (`fork`), `/clear` e compactação: mesmo Alter Ego ou um novo?
  Depende de o id da sessão mudar em cada provider (a verificar).
- ~~O que acontece com o personagem quando a sessão termina?~~ **Decidido: não é excluído (R28).**
  ~~Onde ficam as encerradas e as antigas?~~ **Decidido: na sala, as dos últimos 10 dias
  (configurável); as demais no Histórico do realm (R28a).**
- ~~O Gate escrevendo para um Alter Ego cuja sessão está fechada?~~ **Decidido: oferece reabrir,
  com confirmação (R35).**

**Mundo e interface:**

- ~~Escala da altura (linear, raiz, log)?~~ **Decidido: absoluta, por classes de faixa de linhas
  (R19; [VISUAL.md](VISUAL.md) §8).** Ainda em aberto: linhas em branco e comentários
  contam? Lockfiles versionados entram? Frequência de recálculo; como expor o filtro.
- ~~Rooftop Room: nome definitivo; sala cheia?~~ **Decidido: o nome fica; até 8 por área e "+N" (R33).**
- Estilo visual de cada realm; como o Inner World aparece no 3D. Cenário é permitido quando
  declarado (R12a). Decisões visuais pendentes: [VISUAL.md](VISUAL.md).
- ~~Como a UI avisa que um terminal está parado num diálogo?~~ **Decidido: leitor de diálogos
  próprio marca "esperando o Lucas", sem responder (R34).**

**Telemetria:**

- Observador do Codex ignorando um pedido de aprovação: o servidor bloqueia, reenvia ou decide?
  **Risco principal**, ver [adapters/CODEX.md](adapters/CODEX.md) §9.
- Quais CLIs entram além de Claude, Codex, Hermes e opencode (qualquer CLI com sessões legíveis é candidato).
- ~~Persistência?~~ **Decidido: registro local do Orb em SQLite, só com o que o Orb derivou (R36).**

## 8. Origem

Conversa de ideação com ChatGPT ("Pensar projeto agentes IA"):
https://chatgpt.com/share/6ac57860-d8cc-83e9-aa06-19c4c72b6938
