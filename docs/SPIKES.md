# The Orb — Spikes

> Os 4 experimentos de validação (2026-10-06): o que cada um perguntou, o que descobriu, o que
> mudou no desenho e o que continua em aberto. É o registro **completo** dos resultados; as
> evidências por provider estão em [adapters/](adapters/). Escopo e riscos: [MVP.md](MVP.md).

Última atualização: 2026-10-07

**Spike** = experimento curto e descartável, feito para responder uma pergunta técnica antes de
investir no produto. Em 2026-10-07 o código que serviu foi **promovido** para `src/orb/` e
`clients/` (mapa em [ARCHITECTURE.md](ARCHITECTURE.md) §8). Em `spikes/` ficaram só os experimentos
que rodam os CLIs de verdade (02, 03, 04), agora importando os módulos definitivos.

**Ambiente dos spikes:** outra máquina (pasta anterior do projeto), com `claude` 2.1.269,
`codex` 0.149.0, Hermes não instalado. **Esta máquina** (2026-10-07): `claude` 2.1.248, `codex`
0.160.1, `hermes` 0.20.5, `opencode` 2.0.23; Python 3.14; Godot fora do PATH; `pywinpty` 3.0.5
(instalado em 2026-10-07).

## Veredito

**Todos os riscos que podiam inviabilizar o projeto foram respondidos de forma positiva**, com
restrições que mudaram o desenho. A tese se sustenta: dá para abrir o CLI real de uma IA dentro do
Orb, usar normalmente e observar o que ela faz em tempo real, sem alterar o agente.

| Spike | Risco | Resultado | Hoje |
|---|---|---|---|
| **1 — Terminal Host** | R1, R2 | ✅ Validado | Promovido: `src/orb/terminal_host/`, `gateway/`, `adapters/claude/transcript.py`, `clients/web/` |
| **2 — Terminal no Godot** | R3 | ✅ Validado | Opção B promovida para `clients/godot/`; opção A segue em `spikes/02-terminal-godot/` |
| **3 — Hooks do Claude ao vivo** | R4 | ✅ Validado, com restrição | Settings por sessão em `src/orb/adapters/claude/hooks.py`; experimento em `spikes/03-live-hooks/` |
| **4 — Codex** | R5 | ✅ Validado, com restrições | Observador em `src/orb/adapters/codex/`; experimento em `spikes/04-codex/` |

---

## Spike 1 — Terminal Host ✅

**Pergunta:** dá para abrir um terminal real controlado pelo Orb, chamar o CLI do agente dentro dele
e observá-lo, no Windows?

**Resultado** (`claude` 2.1.269 real, ConPTY via `pywinpty` 3.0.5 + xterm.js):

| Critério | Resultado |
|---|---|
| S1 — TUI hospedada funciona | ✅ Logo, cores (truecolor/256), tela alternativa, cursor, redesenho ao redimensionar, teclado, Ctrl+C. `/slash` não exercitado |
| S2 — Mesmo comportamento que fora do Orb | ✅ O Orb não escreveu em nada do projeto; só leu o transcript |
| S3 — Evento chega ao painel em < 1 s | ✅ ~270–470 ms (inclui polling de 250 ms) |
| S5 — Prompt aparece na telemetria | ✅ Apareceu no painel |
| S6 — Robustez | ◐ Linhas parciais/inválidas toleradas; teste de caos pendente |
| S4 — Subagentes | ⏳ Não houve subagente nesta sessão |

O terminal é um **PowerShell real** e o CLI é chamado dentro dele, escolhido pelo modelo
(`claude-*` → `claude`, `gpt-*` → `codex`); quando o CLI fecha, o terminal continua. 15 testes no
spike (hoje cobertos pelos testes de `tests/`).

**Achados que mudaram o desenho**

1. **O Orb atribui `--session-id` e `-n` ao `claude` que hospeda.** Sem isso, o leitor confundia o
   transcript hospedado com outras sessões da mesma pasta. Hoje isso é a identidade do Alter Ego
   ([ADR 0001](adr/0001-alter-ego-e-uma-sessao.md)).
2. **Marcadores de ambiente herdados mudam o CLI.** Iniciado de dentro de uma sessão do Claude, o
   filho herdava `CLAUDE_CODE_CHILD_SESSION` e **não gravava transcript**. O Orb remove só esses
   marcadores e preserva a configuração do usuário.
3. **Segurança:** um terminal por WebSocket é um shell exposto: loopback, token, `Origin` local e
   lista fixa de executáveis. Na promoção, a linha de comando passou também a validar modelo, id e
   nome de sessão (o texto é digitado num shell).
4. A TUI mostra "Cogitated for 12s", mas o texto do thinking não vai ao transcript.

**Não provado:** Codex hospedado; vários terminais simultâneos; modo Observar ao vivo.

---

## Spike 2 — Terminal no Godot ✅

**Pergunta:** o terminal funciona dentro do Godot, inclusive como tela de um monitor 3D?
(Godot 4.7.2 + godot-xterm 4.0.3.)

| Pergunta | Resultado |
|---|---|
| godot-xterm roda no Windows com ConPTY? | ✅ PowerShell real; redimensionamento PTY↔terminal sincronizado |
| O `claude` real roda dentro do Godot? | ✅ TUI completa, com `-n` e `--session-id` |
| Cores? | ✅ Na opção B; na opção A o `claude` saiu monocromático |
| Terminal numa tela **3D**? | ✅ `SubViewport` num quad inclinado em perspectiva |
| Teclado em 3D? | ✅ Eventos encaminhados ao `SubViewport` com `push_input` |
| Godot exibindo bytes do Terminal Host **em Python**? | ✅ Ciclo completo por WebSocket, mesmo com o stdio do Godot redirecionado |

**Decisão:** opção B, um único Terminal Host em Python; o Godot só exibe
([ADR 0004](adr/0004-terminal-host-unico-em-python.md)).

**Achados**

1. ConPTY dentro do Godot **só funciona com stdio não redirecionado**.
2. Caminhos e `cwd` no Windows precisam de **barra invertida**.
3. `JSON.stringify` do Godot não escapa caracteres de controle: entrada em **base64** (`data_b64`).
4. **Bug de robustez corrigido:** uma mensagem malformada derrubava a sessão inteira. Hoje
   `handle_client_message` valida na borda e nunca levanta.
5. Glifos de caixa/bloco (`─ █ ▐`) com espaços entre células: cosmético (célula 10,0 px × glifo
   9,6 px; não é a fonte).
6. Em 3D o teclado não chega sozinho ao `SubViewport`.

**Não provado:** clique do mouse no monitor 3D; desempenho com vários monitores (testado com um,
numa GPU MX110); telemetria chegando ao Godot; latência ponta a ponta Godot ↔ Python.

---

## Spike 3 — Hooks do Claude ao vivo ✅ (com restrição)

**Pergunta:** os hooks funcionam sem tocar na configuração do Lucas e sem atrapalhar o agente?

| Pergunta | Resultado |
|---|---|
| Instalar sem mexer na configuração? | ✅ `claude --settings <arquivo>` aplica hooks **só àquela sessão** |
| Funcionam na TUI hospedada? | ✅ O `session_id` bate com o `--session-id` do Orb |
| Subagentes? | ✅ `SubagentStart`/`SubagentStop`; ações de dentro com `agent_id`/`agent_type` |
| Pedido de aprovação? | ✅ `PermissionRequest` (a decisão continua sem hook) |
| Orb fora do ar atrapalha? | ✅ Não (6,7 s × 7,5 s) |
| **Orb travado atrasa o agente?** | ❌ **Sim:** 21,5 s × ~7 s com hook `http` (e `async` não ajuda). Com `command` async + `curl`: ~10,5 s |

**Achados que mudaram o desenho**

1. **Os resumos das docs tinham campos errados** (`tool_response`, não `tool_output`; sem
   `is_continuation`/`is_background`). Vale a fixture real.
2. **`UserPromptSubmit` não é sempre o Lucas** (`<task-notification>`; o transcript distingue por
   `origin.kind`). Em 2026-10-07 decidiu-se que o Orb não rastreia autoria (ADR 0003), então isso
   ficou só como informação.
3. **`Stop` do líder não encerra a Team:** a ferramenta `Agent` é assíncrona.
4. Mitigação do travamento: receptor mínimo, `command` assíncrono com `curl -m 1`, e **nível 0 como
   padrão** ([ADR 0005](adr/0005-nivel-zero-de-pegada-por-padrao.md)).

**Não provado:** os hooks não provocados (`TaskCreated/Completed`, `Notification`,
`PostToolUseFailure`, `PermissionDenied`, `StopFailure`, `Pre/PostCompact`, `CwdChanged`,
`InstructionsLoaded`, `ConfigChange`, `UserPromptExpansion`); a decisão do usuário num
`PermissionRequest`; hooks no app Desktop e em sessões abertas fora do Orb; custo contínuo do
`curl` por evento numa sessão longa.

---

## Spike 4 — Codex ✅ (com restrições)

**Pergunta:** o que o Codex expõe e como o Orb o observa sem tocar na configuração do Lucas?

| Pergunta | Resultado |
|---|---|
| Eventos estruturados em tempo real? | ✅ JSON-RPC por WebSocket (`codex app-server`), esquema gerado pelo próprio CLI |
| Observar sem tocar na configuração? | ✅ App-server **próprio do Orb** em loopback + `codex --remote` |
| Um 2º cliente observa uma sessão viva? | ✅ Depois de `thread/resume`: **159 de 169** notificações. Thread efêmera não pode ser observada |
| Pensamento? | ◐ `summary` em ~42% dos blocos, nunca `raw` (Claude: ~12%) |
| Aprovações? | ✅ Pedidos do servidor + notificação de resolução |
| Hooks como nível 1? | ❌ Só `command`/`mcp_tool`, exigem confiança, sem injeção por sessão |
| Subagentes? | ◐ No formato (`parent_thread_id`); em 2026-10-07, 230 subagentes lidos dos rollouts desta máquina |

**Achados que mudaram o desenho**

1. Para o Codex, o nível 1 é o **app-server com observador**, não hooks.
2. O Codex **não tem `Read`**: ler é `Get-Content`. Daí o classificador de comandos.
3. `capabilities()` difere por provider, como previsto.
4. O modelo padrão do `config.toml` do Lucas não era aceito com conta ChatGPT: o Orb passa `-m`.
5. A TUI abre com **diálogos cujo padrão tem efeito**. Daí a regra
   [ADR 0006](adr/0006-o-orb-nunca-responde-dialogos.md).

### Incidentes (registrados com transparência)

1. O script deu Enter às cegas e aceitou **"Update now"**; o instalador **falhou sem efeito** (versão
   0.149.0 intacta, `codex doctor` confirmou). Ficou uma pasta de staging vazia
   (`~/.codex/packages/standalone/releases/.staging.0.160.1-…`).
2. Um prompt foi digitado com a **revisão de hooks** aberta. `config.toml` sem mudança e 0 hooks
   confiados na tela; tudo indica que nada foi confiado, sem prova de 100%.
3. Foi criada **1 sessão de teste** no histórico do Codex (`01a11443-9c62-7a23-b900-b05f7dc17dd4`).

Esses três itens ficaram na máquina dos spikes. **Pendências para o Lucas, lá:** conferir se a
revisão de hooks segue pendente; decidir se apaga a pasta de staging e a sessão de teste.

Correção posterior (2026-10-07): o `drive.py` usava a mesma classe para o cliente que conduz e para
o observador, e por isso o observador **recusaria** pedidos do servidor se recebesse algum. Agora o
observador nunca responde, e o adaptador definitivo tem teste para isso.

**Não provado:** conversa completa na TUI ligada ao app-server do Orb; **o que o servidor faz com um
observador que ignora um pedido de aprovação**; subagentes e hooks ao vivo; `fileChange`, plano
nativo e streaming de resumo.

---

## Regras que os spikes criaram

| # | Regra | Origem | Onde está |
|---|---|---|---|
| 1 | O Orb nunca responde diálogos do Lucas e nunca envia teclas sem a tela verificada | Spike 4 | [ADR 0006](adr/0006-o-orb-nunca-responde-dialogos.md) |
| 2 | Nível 0 é o padrão; nível 1 só por sessão | Spikes 3 e 4 | [ADR 0005](adr/0005-nivel-zero-de-pegada-por-padrao.md) |
| 3 | Um Orb travado não pode atrasar o agente | Spike 3 | [ARCHITECTURE.md](ARCHITECTURE.md) §4 |
| 4 | Um único Terminal Host, em Python; o cliente só exibe | Spike 2 | [ADR 0004](adr/0004-terminal-host-unico-em-python.md) |
| 5 | Toda entrada externa é validada na borda e a falha é isolada | Spike 2 | [ARCHITECTURE.md](ARCHITECTURE.md) §4 |
| 6 | ~~Entrada humana só com origem confirmada~~ — revista: o Orb não rastreia autoria | Spike 3 | [ADR 0003](adr/0003-inner-world-une-terminal-e-pensamento.md) |
| 7 | Adapters declaram `capabilities()` | Spikes 3 e 4 | [ARCHITECTURE.md](ARCHITECTURE.md) §3 |

## O que continua em aberto

| Item | Prioridade |
|---|---|
| **Observador do Codex ignorando um pedido de aprovação** (bloqueia? reenvia? decide?) | **Alta**: toca na não interferência; precisa do Lucas acompanhando |
| Hermes ao vivo (instalado nesta máquina; hoje só leitura do código e do `state.db`) | Média |
| Subagentes ao vivo (Claude na TUI e Codex no app-server); hooks não provocados | Média |
| Clique do mouse e desempenho com vários monitores 3D | Média (com o cliente 3D) |

## Como reproduzir

Cada experimento tem um README (`spikes/0N-*/README.md`). Eles rodam os **CLIs de verdade** e
**consomem cota** das contas logadas. Arquivos gerados (capturas, fixtures, logs) não são
versionados (caminhos locais, prompts, dados da conta). **Nunca envie teclas à TUI do Codex às
cegas.**
