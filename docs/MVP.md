# The Orb — MVP

> Escopo do primeiro MVP, critérios de sucesso, riscos e decisões. Visão: [VISION.md](VISION.md) ·
> Resultados dos spikes: [SPIKES.md](SPIKES.md) · Ideias fora do MVP: [IDEAS.md](IDEAS.md).

Última atualização: 2026-10-07

## 1. Objetivo

Provar a tese do Orb pelo menor caminho:

> **Abrir o CLI real de uma IA dentro do Orb, usar normalmente, e ver em tempo real, de forma
> confiável, o que aquela sessão (o Alter Ego) e os subagentes dela estão fazendo, sem alterar em
> nada o comportamento do agente.**

O MVP é a **fundação** que o 3D vai renderizar depois.

## 2. Escopo

### Dentro

1. **Inner World com terminal real:** abrir o `claude` (CLI real) numa pseudo-console, no
   diretório de um realm; digitar, usar `/slash`, redimensionar.
2. **Um realm, um provider (Claude), nível 0:** ler o transcript em tempo real, sem instalar nada.
3. **Protocol 0.2:** evento nativo intacto + sinal de mundo + entrada de Inner World.
4. **Core:** mundo Realm → Alter Ego (sessão) → Subagentes → Atividade.
5. **Mundo 3D** (página web com Three.js e xterm.js; [ADR 0007](adr/0007-cliente-3d-na-web.md)): a
   cidade com os realms, os personagens, o overview do realm, o Inner World e o terminal.

### Já existe, mas fora dos critérios do MVP

Os adapters do **Codex** (rollouts e observador do app-server), do **Hermes** (`state.db`) e do
**opencode** (`opencode.db`) foram escritos e funcionam sobre dados reais desta máquina, e o Gateway já os usa no nível 0. Eles não fazem parte do
critério de aceite do MVP: ficam para a etapa seguinte do roadmap, com validação ao vivo.

### Fora (por enquanto)

Cliente Godot · hooks (nível 1) · Gate, Team visual, Chronicle, Weather, Energy,
Archive · Perfil do Alter Ego · persistência em banco · multiusuário.

## 3. Critérios de sucesso

| # | Critério | Como medir | Status |
|---|---|---|---|
| S1 | A TUI do `claude` roda hospedada: cores, redimensionamento, entrada, `/slash`, sem corromper a tela | Teste manual + captura | ✅ Spike 1 (`/slash` não exercitado) |
| S2 | O CLI hospedado se comporta **igual** a fora do Orb | Nenhum arquivo do projeto/config alterado pelo Orb | ✅ com ressalvas (ambiente limpo, nível 1 só por sessão) |
| S3 | Eventos chegam ao painel em < 1 s | Medir latência | ✅ ~270–470 ms |
| S4 | Subagentes aparecem na Team do Alter Ego certo | Sessão com subagentes | ◐ Hooks ao vivo (Spike 3) e transcripts reais de subagentes lidos pelo adapter; falta ver na TUI hospedada |
| S5 | O que se escreve no terminal aparece na linha do tempo do Inner World | Enviar prompt e verificar | ✅ Spike 1 |
| S6 | Falha de um módulo não derruba os outros | Matar adapter/terminal e observar | ◐ Validação na borda e isolamento da telemetria testados; teste de caos pendente |

## 4. Riscos

| # | Risco | Status |
|---|---|---|
| **R1** | Hospedar a TUI real em pseudo-console no Windows | ✅ Validado (Spike 1) |
| R2 | Telemetria em tempo real pelo transcript | ✅ Validado (Claude, ~270–470 ms) |
| R3 | Terminal no cliente 3D (Godot) | ✅ Validado (Spike 2) |
| R4 | Hooks ao vivo (nível 1) | ✅ Com restrição: um Orb travado atrasa o agente; mitigado |
| R5 | Formatos de Codex, Hermes e opencode | ✅ Codex validado (Spike 4 + rollouts reais); Hermes e opencode lidos nos bancos reais, sem execução ao vivo |
| R6 | Desempenho e legibilidade do 3D em escala | Pendente (cliente 3D) |
| **R7** | Observador do Codex ignorando um pedido de aprovação | **Aberto**, prioridade alta ([adapters/CODEX.md](adapters/CODEX.md) §10) |
| R8 | O modelo "Alter Ego = sessão" não bastar (Perfil) | Aberto ([VISION.md](VISION.md) §7) |

## 5. Decisões tomadas

| # | Decisão | Registro |
|---|---|---|
| D1 | Alter Ego é uma sessão; o Perfil fica em aberto | [ADR 0001](adr/0001-alter-ego-e-uma-sessao.md) |
| D2 | Cada provider aparece como ele é; o mundo usa sinais derivados | [ADR 0002](adr/0002-eventos-nativos-por-provider.md) |
| D3 | Inner World une o terminal e o pensamento (sai "Intrusive Thoughts") | [ADR 0003](adr/0003-inner-world-une-terminal-e-pensamento.md) |
| D4 | Terminal real + CLI chamado dentro dele; um Terminal Host em Python; clientes só exibem | [ADR 0004](adr/0004-terminal-host-unico-em-python.md) |
| D5 | Nível 0 por padrão; nível 1 por sessão (`claude --settings`; app-server próprio do Codex) | [ADR 0005](adr/0005-nivel-zero-de-pegada-por-padrao.md) |
| D6 | O Orb nunca responde diálogos do Lucas nem pedidos do servidor | [ADR 0006](adr/0006-o-orb-nunca-responde-dialogos.md) |
| D7 | O Orb atribui `--session-id` e `-n` ao `claude` hospedado e limpa o ambiente herdado | [SPIKES.md](SPIKES.md) Spike 1 |
| D8 | Segurança do Gateway: loopback, token, `Origin`, lista fixa, linha de comando validada | [ARCHITECTURE.md](ARCHITECTURE.md) §3 |
| D9 | Cliente: mundo 3D na web (Three.js) servido pelo backend Python (FastAPI) | [ADR 0007](adr/0007-cliente-3d-na-web.md) |
| D10 | Um observador por realm acompanha os 4 providers ao mesmo tempo; cada Alter Ego carrega o seu provider | [ARCHITECTURE.md](ARCHITECTURE.md) §3 |

## 6. Próximos passos

**Antes de qualquer implementação (regra P1):**

1. O Lucas revisa [RULES.md](RULES.md) e [VISUAL.md](VISUAL.md).
2. Decidir as pendências. Já decididas em 2026-10-07: cor das janelas = cores do git (R20a), todos
   os projetos já registrados (R3a), sessões fora de projeto ignoradas (R3b), lista para esconder
   realms (R3c), sessões encerradas não excluídas (R28), cenário permitido (R12a). Decididas em
   2026-10-08: paleta do git do VS Code e troca das cores das áreas e do "esperando" (R20a, R20c),
   sessões dos últimos 10 dias na sala (R28a), janela = arquivo com alterações locais (R20b),
   critério de "fora de projeto" (R3b), arquivo de preferências e tela de configurações do Orb (R29),
   projeto inexistente não entra (R3d), Histórico do realm, cores dos providers (R30), janelas por
   percentual com peso = linhas alteradas e x = 5% (R20d), áreas sem cor própria (R20c), janela só
   acesa ou apagada (R20), dormindo após 15 min (R31), subagente sem sinal em cinza (R7), cidade
   retangular com bairros por letra (R32), altura absoluta por classes de faixa de linhas e a
   contagem de linhas (R19), sala cheia (R33), realm de "noite", leitor de diálogos (R34), Gate que
   oferece reabrir (R35), registro local (R36), nome histórico dos Alter Egos (R37), o Orb não
   consome tokens (R38), continuidade da sessão (R39), papel derivado (R40) e forma por classe de
   prédio (R41). O índice das que ainda faltam está em [DECISIONS.md](DECISIONS.md).
3. Criar os tickets por épico (RULES.md, "Do documento aos tickets"), **quando o Lucas pedir** (P5).

Depois, pela ordem dos tickets:

1. **Usar o mundo 3D no dia a dia**
   e usar o `claude` hospedado pelo painel (fecha S1 `/slash`, S4 e S6).
2. **Amadurecer o Alter Ego / Perfil** (retomada, fork, `/clear`, várias sessões por realm).
3. **Testar o risco R7** com o Lucas acompanhando.
4. Codex, Hermes e opencode hospedados e validados ao vivo no mesmo painel; modo Observar.
5. Sala 3D mais rica e desempenho com muitos realms e sessões (R6).
