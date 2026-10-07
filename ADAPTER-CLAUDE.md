# Orb IA — ADAPTER: Claude Code

> Levantamento do que o Claude Code expõe via **hooks** e **transcript**, e como isso vira
> eventos do [PROTOCOL.md](PROTOCOL.md). Base do Claude Adapter.
> Contexto: [CONTEXT.md](CONTEXT.md) · Módulos: [ARCHITECTURE.md](ARCHITECTURE.md).

Levantado em: 2026-10-06 · Versão do Claude Code observada: `2.1.x` (entrypoint `claude-desktop`)

## Como isto foi verificado (e o que não foi)

| Fonte | O que cobre | Confiança |
|---|---|---|
| Docs de hooks (`code.claude.com/docs/en/hooks`), lidas via resumo automático | Lista de eventos, campos de entrada, tipos de hook, configuração | **Média.** Resumo, não texto bruto: reconfirmar ao gravar as fixtures |
| Transcripts reais em `~/.claude/projects/` (6 projetos, ~3,3 mil blocos de thinking, subagentes) | Formato real do JSONL, campos, subagentes | **Alta** para o que foi visto |
| Hooks executados ao vivo | — | **Verificado depois, no Spike 3** (ver §6). As seções 1 a 5 foram escritas antes disso e valem como levantamento inicial; **onde divergem de §6, vale §6** |
| Transcripts de sessões do **CLI de terminal** | — | **Não verificado.** Todos os transcripts disponíveis vêm de `claude-desktop`. O formato deve ser o mesmo, mas falta confirmar |

O formato do transcript **não é uma API documentada**: é interno e muda entre versões. Os
hooks são o contrato estável; o transcript complementa o que os hooks não entregam.

---

## 1. Hooks

### 1.1 Conclusões

- Dá para o Orb receber eventos **direto por HTTP**: o hook tipo `http` faz POST do JSON do
  evento para uma URL (ex.: o Gateway local). Não precisa de scripts intermediários.
- Hooks funcionam no terminal, nas extensões de IDE e no app Desktop (segundo as docs).
- Subagentes herdam os hooks do pai. Eventos disparados dentro de um subagente trazem
  `agent_id` e `agent_type` no JSON comum, o que permite atribuir cada ação ao subagente certo.
- Cada evento inclui `transcript_path`: o adapter **não precisa adivinhar** onde está o
  transcript da sessão.
- Configuração em `~/.claude/settings.json` (global), `.claude/settings.json` (projeto) ou
  `.claude/settings.local.json` (projeto, não versionado). Para o Orb, o escopo local ou global
  evita alterar o repositório do realm.

### 1.2 Campos comuns a todo evento

`session_id`, `prompt_id`, `transcript_path`, `cwd`, `permission_mode`, `effort`,
`hook_event_name`; e `agent_id` / `agent_type` quando o evento ocorre dentro de um subagente.

### 1.3 Eventos relevantes e mapeamento para o protocolo

| Hook | Campos específicos | → Evento do protocolo | Observações |
|---|---|---|---|
| `SessionStart` | `source` (startup/resume/clear/compact/fork), `model` | `session.started` | `resume`/`fork` precisam ser distinguidos de sessão nova |
| `SessionEnd` | `reason` | `session.ended` | |
| `UserPromptSubmit` | `prompt`, `permission_mode` (**sem** `is_continuation`/`is_background`: ver §6.2) | **`intrusive_thought`** (`kind: prompt`) **só se a origem for humana** | Também dispara para prompts do sistema (`<task-notification>`); confirmar a origem no transcript (§6.3) |
| `UserPromptExpansion` | (expansão de slash command) | `intrusive_thought` (`kind: command`) | Não exercitado no Spike 3 |
| `PreToolUse` | `tool_name`, `tool_input`, `tool_use_id` | `tool.started` (+ `file.*`, `command.started`, conforme a ferramenta) | `tool_use_id` correlaciona com o fim |
| `PostToolUse` | `tool_name`, `tool_input`, `tool_output`, `tool_use_id` | `tool.completed` | |
| `PostToolUseFailure` | idem | `tool.failed` | |
| `PermissionRequest` | `tool_name`, `tool_input` | `approval.requested` | Ver lacuna 1.4 |
| `SubagentStart` | `agent_type`, `agent_id` | `agent.spawned` (com `parent`) | |
| `SubagentStop` | `agent_type`, `agent_id`, `last_assistant_message` | `agent.retired` | |
| `Stop` | `is_error`, `last_assistant_message` | `agent.idle` | Fim do turno |
| `StopFailure` | — | `error` | Turno terminou por erro de API |
| `TaskCreated` | `task_id`, `task_name`, `task_description` | `task.started` | Só tarefas via ferramenta de tarefas |
| `TaskCompleted` | `task_id`, `completed_by` | `task.completed` | |
| `Notification` | `notification_type`, `message` | dica de `WAITING` (`permission_prompt`, `idle_prompt`) | |
| `MessageDisplay` | `delta`, `final`, `index`, `message_id`, `turn_id` (§6.2) | `agent.message` | Útil para o chat espelhado |
| `PreCompact` / `PostCompact` | — | (sem evento próprio no MVP) | Compactação de contexto |

Tipos de hook suportados: `command`, `http`, `mcp_tool`, `prompt`, `agent`. O Orb só precisa
de `http` (ou `command` como fallback), em modo **observação**.

### 1.4 Lacunas e pegadinhas dos hooks

1. **Não há evento de "decisão de permissão".** `PermissionRequest` avisa que pediu; a
   resposta do usuário não chega como hook próprio. `approval.resolved` precisa ser
   **deduzido**: `PostToolUse` da mesma ferramenta indica aprovação; `PermissionDenied` cobre
   só o modo auto. O adapter deve marcar essa dedução como tal.
2. **`FileChanged` não é um feed geral de edições.** Só dispara para arquivos observados por
   nome. Edições de arquivo vêm de `PostToolUse` das ferramentas `Edit`/`Write`.
3. **Não existe hook de pensamento.** Ver seção 3.
4. **Um hook pode atrapalhar o Claude.** Exit code 2 bloqueia em eventos que permitem
   bloqueio. O hook do Orb deve ser **somente observador**: nunca retornar decisão, usar
   timeout curto e, quando possível, `async`. Resposta não-2xx de um hook HTTP é erro
   **não bloqueante** (segundo as docs), o que ajuda a robustez. Orb fora do ar: **sem efeito**;
   Orb **travado**: **atrasa o agente** (medido no Spike 3, §6.4).
5. **Escopo de eventos pode crescer.** A lista de eventos mudou rápido; o adapter deve
   ignorar hooks desconhecidos e declarar `capabilities()` em vez de assumir.

---

## 2. Transcript

### 2.1 Onde fica

- Sessão: `~/.claude/projects/<cwd-codificado>/<session_id>.jsonl`. O caminho exato chega em
  `transcript_path` de cada hook.
- `<cwd-codificado>` é o diretório de trabalho com separadores trocados por `-`
  (ex.: `C--Users-lucas-...-Orb-IA`).
- Subagentes: `~/.claude/projects/<cwd>/<session_id>/subagents/agent-<agentId>.jsonl`, com um
  `agent-<agentId>.meta.json` ao lado.
- Arquivo é **append-only** (uma linha JSON por entrada) e dá para acompanhar em tempo real
  (tail).

### 2.2 Tipos de entrada (`type`) observados

| `type` | O que é | Útil para o Orb |
|---|---|---|
| `user` | Prompt do usuário **ou** resultado de ferramenta | Sim: `intrusive_thought` / fim de `tool.*` |
| `assistant` | Resposta do modelo (blocos `text`, `thinking`, `tool_use`) | Sim: narração, ferramentas, tokens |
| `system` | Eventos do harness (ex.: `stop_hook_summary`) | Pouco |
| `attachment` | Anexos de contexto (ex.: instruções carregadas) | Pouco |
| `queue-operation` | `enqueue` / `dequeue` de mensagens na fila | Possível: prompts enfileirados enquanto o agente trabalha |
| `file-history-snapshot` / `file-history-delta` | Rastreio de arquivos alterados | Possível para `file.edit` |
| `cost-state` | Tokens, custo, linhas adicionadas/removidas, tempos | **Sim:** stats reais (custo, linhas) |
| `mode`, `custom-title`, `agent-name`, `last-prompt`, `atis-latch` | Metadados de sessão | Título/nome da sessão |

### 2.3 Campos importantes

- **Todas as entradas de conversa:** `uuid`, `parentUuid` (encadeia a conversa), `sessionId`,
  `timestamp`, `cwd`, `gitBranch`, `version`, `entrypoint`, `isSidechain`.
- **`user` (prompt humano):** `message.content` (texto), `promptId`, `origin.kind` (`human`),
  `turnOrigin`, `turnPosition` (`promptIndex`, `turnIndex`), `permissionMode`, `promptSource`.
  `origin`/`turnOrigin` distinguem prompt humano de entrada gerada pelo sistema.
- **`user` (resultado de ferramenta):** `message.content[]` com blocos `tool_result`.
- **`assistant`:** `message.content[]` com blocos `text`, `thinking`, `tool_use`
  (`id`, `name`, `input`); `message.model`; `message.usage` (tokens de entrada, saída e cache);
  `message.stop_reason`; `requestId`; `effort`.
- **Subagentes:** `isSidechain: true`, `agentId`, `parentUuid: null` na primeira linha. O
  `.meta.json` traz `agentType`, `description`, `toolUseId` (liga ao `tool_use` do pai),
  `spawnDepth`, `requestShape` (`foreground`/…).

### 2.4 Utilidades diretas para o Orb

- **Ligar subagente ao pai:** `meta.toolUseId` aponta o `tool_use` que o criou.
- **Estatísticas reais por Alter Ego:** `usage` (tokens), `cost-state` (custo, linhas
  adicionadas/removidas, duração de API e de ferramentas).
- **Reconstrução/replay:** o transcript é um log completo, que serve para **gravar
  fixtures** de teste e para recuperar o estado após reconexão.

---

## 3. Thinking: o achado mais importante

Nos transcripts reais, os blocos `thinking` têm só `type`, `thinking` e `signature`, e o campo
`thinking` (texto) está **vazio na grande maioria**:

| Amostra | Com texto | Vazio |
|---|---|---|
| ~3,3 mil blocos de thinking em 6 projetos | 389 (≈ 12%) | 2.917 (≈ 88%) |
| Nesta sessão (Orb IA) | 0 | 9 |

Nas versões mais recentes observadas, a proporção com texto cai ainda mais. O que fica
gravado costuma ser só a `signature` (assinatura criptográfica), não o raciocínio.

**Consequências para o Inner World:**

1. `thought` com `fidelity: raw` será **raro** no Claude. O adapter deve declarar isso em
   `capabilities()`.
2. O Inner World do Claude precisa se apoiar em outras fontes observáveis:
   - blocos `text` das mensagens do assistente (narração, `fidelity: raw` do que ele disse);
   - o plano (lista de tarefas / `TaskCreated`);
   - a escolha de ferramentas e o que foi lido/editado (`inferred`, rotulado como tal);
   - `MessageDisplay`, quando disponível;
   - os `intrusive_thought` do usuário.
3. Quando houver texto de thinking, ele entra como `thought` `raw`. Quando não houver,
   **não se emite `thought`** (regra do protocolo): a UI mostra que o raciocínio não está
   exposto.
4. Vale reavaliar se há configuração do Claude Code que aumente o que é gravado (a verificar).

---

## 4. Desenho do Claude Adapter

```
Hooks (HTTP POST) ─────────────┐
                               ├─► Claude Adapter ─► eventos do protocolo
Transcript (tail do JSONL) ────┘
```

- **Hooks = tempo real e contrato estável.** Fonte principal de `tool.*`, `agent.*`,
  `intrusive_thought`, `approval.requested`.
- **Transcript = complemento.** Texto das mensagens (narração), thinking quando houver,
  tokens/custo, subagentes e recuperação após falha.
- **Reconciliação:** hook e transcript descrevem o mesmo evento (ex.: uma ferramenta). O
  adapter casa por `tool_use_id` e emite **um** evento, sem duplicar.
- **Isolamento:** parsers tolerantes a campos novos, detecção de `version`, falha com
  mensagem clara quando o formato for desconhecido (ver ARCHITECTURE.md §4).
- **Observação segura:** hooks do Orb nunca retornam decisões nem bloqueiam o agente.

### Níveis de pegada (não interferência)

Instalar hooks altera a configuração do Claude Code, então o Orb oferece dois níveis:

| Nível | O que faz | Pegada |
|---|---|---|
| **0 — Zero pegada** | Só lê (tail) o transcript em `~/.claude/projects/`. Não instala nada. | Nenhuma: não toca configuração nem comportamento |
| **1 — Hooks observadores** | Adiciona hooks HTTP/async que só enviam eventos ao Orb | Mexe em `settings`; deve ser reversível e nunca devolver decisão nem `additionalContext` |

O nível 0 cobre boa parte do necessário (ferramentas, mensagens, subagentes, tokens, prompts
via transcript), mas com menos tempo real e sem eventos como `PermissionRequest`. O nível 1
acrescenta tempo real e aprovações. Regras do nível 1: configuração em escopo local/global
(não no repositório do realm), `async` quando possível, timeout curto, **nunca**
`additionalContext`, `decision` ou exit code 2, e remoção limpa pelo Orb.

### `capabilities()` do Claude Adapter (proposta)

| Capacidade | Valor |
|---|---|
| Eventos de ferramenta | Sim (hooks) |
| Subagentes | Sim (hooks + meta) |
| Detecção de intrusive thoughts | Sim (`UserPromptSubmit`) |
| Aprovações | Parcial (pedido sim, decisão deduzida) |
| Thinking `raw` | **Raro** (na maioria dos blocos o texto vem vazio) |
| Narração (`text` do assistente) | Sim |
| Tokens / custo | Sim (transcript) |

---

## 5. Pesquisa futura: sessão visível por Alter Ego

Objetivo: cada IA, com seus subagentes, aparece no Orb **junto da sessão em que trabalha**
(título da sessão sobre o personagem, subagentes agrupados sob a mesma sessão).

Já verificado como disponível no Claude Code:
- `session_id` em todo hook; `agent_id`/`agent_type` dentro de subagentes.
- Transcript com entradas `custom-title` e `agent-name`; `SessionStart` aceita `sessionTitle`
  e informa `source` (`startup`/`resume`/`clear`/`compact`/`fork`).
- Subagente: pasta `<session_id>/subagents/`, `.meta.json` com `description` e `toolUseId`
  (liga ao pai).

**Verificado no Spike 1 (modo hospedar):** o CLI aceita `--session-id <uuid>` e `-n/--name`.
O Orb gera o id, passa ao `claude` e passa a saber qual é o transcript da sessão, sem
adivinhar por pasta. O nome aparece na TUI. Em modo hospedar, Alter Ego ↔ sessão fica resolvido.

Perguntas a pesquisar:
- Modo **observar**: como vincular sessões iniciadas fora do Orb a um Alter Ego (regra de
  detecção por `cwd`/realm, já que o Orb não escolheu o id)? Em modo hospedar a pergunta está
  respondida (acima).
- Sessão retomada (`resume`) e bifurcada (`fork`): mesma sessão visual ou nova?
- Várias sessões simultâneas no mesmo realm: um Alter Ego por sessão ou um Alter Ego com
  várias sessões?
- `clear` e `compact` mudam o `session_id`? Como não duplicar o personagem?
- Equivalentes em Codex ([ADAPTER-CODEX.md](ADAPTER-CODEX.md): em hospedagem, o id vem de
  `thread/started`) e Hermes (**não verificado**; CLI não instalado).

---

## 6. Hooks verificados ao vivo (Spike 3, 2026-10-06, Claude Code 2.1.269)

Código e fixtures: `spikes/03-live-hooks/` (`probe.py`, `probe_tui.py`, `fixtures/claude-2.1.269/`).
As fixtures e capturas contêm prompts e caminhos locais: não versionar fora da máquina.

### 6.1 Como instalar sem tocar na configuração do usuário

`claude --settings <arquivo>` injeta hooks **só naquela sessão**. O `~/.claude/settings.json` do
Lucas não é alterado (e hoje não tem hooks). É o desenho do nível 1 de pegada: o Orb passa o
arquivo ao hospedar a sessão. Token por header (`"X-Orb-Token": "$ORB_TOKEN"` +
`allowedEnvVars`) funcionou; o receptor responde `{}` (nenhuma decisão, nenhum contexto).
`--bare` desliga hooks: não usar.

### 6.2 Eventos observados (e correções às docs)

Dispararam: `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolBatch`, `MessageDisplay`,
`Stop`, `SessionEnd`, `SubagentStart`, `SubagentStop`, `PermissionRequest`, `SessionStart`
(só com hook `command`, ver 6.4). **Não foram exercitados** (não é o mesmo que "não existem"):
`UserPromptExpansion`, `StopFailure`, `PermissionDenied`, `PostToolUseFailure`, `TaskCreated`,
`TaskCompleted`, `Notification`, `PreCompact`, `PostCompact`, `CwdChanged`,
`InstructionsLoaded`, `ConfigChange`.

Correções ao que o resumo das docs dizia:

| Evento | Campos reais (além de `session_id`, `prompt_id`, `transcript_path`, `cwd`, `hook_event_name`) |
|---|---|
| `UserPromptSubmit` | `prompt`, `permission_mode`. **Sem** `is_continuation` / `is_background` |
| `PreToolUse` | `tool_name`, `tool_input`, `tool_use_id`, `permission_mode` |
| `PostToolUse` | `tool_name`, `tool_input`, **`tool_response`** (não `tool_output`), `duration_ms`, `tool_use_id` |
| `PostToolBatch` | `tool_calls[]` |
| `MessageDisplay` | `delta`, `final`, `index`, `message_id`, `turn_id` |
| `Stop` | `last_assistant_message`, `stop_hook_active`, `background_tasks`, `session_crons` |
| `PermissionRequest` | `tool_name`, `tool_input`, `permission_suggestions` |
| `SubagentStart` | `agent_id`, `agent_type` |
| `SubagentStop` | `agent_id`, `agent_type`, **`agent_transcript_path`**, `last_assistant_message` |
| `SessionEnd` | `reason` (ex.: `prompt_input_exit`) |

### 6.3 Comportamentos que mudam o desenho

1. **Eventos dentro de um subagente trazem `agent_id` e `agent_type`** (`PreToolUse`,
   `PostToolUse`, `PostToolBatch`). Atribuição de ação ao subagente certo: confirmada.
   `SubagentStop` entrega o `agent_transcript_path` do subagente.
2. **`UserPromptSubmit` também dispara para prompts do sistema.** Quando um subagente em segundo
   plano termina, chega um `UserPromptSubmit` com `<task-notification>...`. Tratar todo
   `UserPromptSubmit` como `intrusive_thought` contaria o sistema como se fosse o Lucas.
   O transcript separa os dois: prompt humano **sem** `origin` (ou `origin.kind: human`);
   sistema com `origin.kind: task-notification`. **Regra:** `intrusive_thought` só quando a
   reconciliação com o transcript confirma origem humana (ou, sem transcript, quando o prompt
   não começa com `<task-notification>`).
3. **A ferramenta `Agent` roda de forma assíncrona.** O `Stop` do agente principal chegou aos
   5 s, enquanto o subagente só terminou aos 12 s (`SubagentStop`). Portanto **`Stop` do pai ≠
   Team terminada**: o estado da Team só vira `IDLE` quando não há subagente ativo.
4. **O mesmo `session_id` do `--session-id` do Orb aparece em todos os eventos**, inclusive na
   TUI hospedada: o vínculo Alter Ego ↔ sessão se confirma.
5. Aparece `SubagentStop` mesmo numa sessão em que nenhum subagente foi pedido (provável
   subagente interno do Claude Code). Tratar `agent_type` desconhecido sem quebrar.
6. `PermissionRequest` chega, mas a decisão do usuário continua sem hook próprio
   (`approval.resolved` segue deduzido).

### 6.4 Falhas do Orb não podem atrasar o agente (princípio 10)

Cenário A (ler um arquivo), mesma sessão, variando o receptor:

| Receptor | Hook | Tempo | Efeito |
|---|---|---|---|
| Vivo | `http` | ~7,5 s | referência |
| **Fora do ar** (recusa conexão) | `http` | ~6,7 s | nenhum |
| **Travado** (aceita e não responde) | `http`, timeout 2 s | **21,5 s** | **+14 s** (≈ 7 hooks × 2 s) |
| Travado | `http` + `async: true` | 20,5 s | **`async` não ajuda em hook http** |
| Travado | `command` async + `curl -m 1` | 10,5 s | ~+3 s |
| Vivo | `command` async + `curl` | 8,0 s | ~+0,5 s; eventos chegam |

Conclusões:
- Servidor ausente é inofensivo. **Servidor travado não é** com hook `http` síncrono.
- Mitigação em camadas: (a) o receptor do Orb é um processo mínimo, sempre responsivo, que só
  enfileira e responde `{}` imediatamente; (b) hook `command` assíncrono com `curl` de timeout
  curto como transporte, que não bloqueia o agente; (c) o **nível 0 (só transcript) continua o
  padrão**, e os hooks são um acréscimo opcional.
- `command` assíncrono perde o último evento quando o processo termina antes do `curl`
  (`SessionEnd` no modo `-p`); em sessão interativa a TUI segue viva. `SessionEnd` também pode
  ser deduzido do fim do processo do terminal.
- `SessionStart` só chegou com hook `command`; hook `http` não o recebeu (nem em `-p` nem na
  TUI). Para início de sessão, usar o terminal host (que já sabe quando abre) ou `command`.

---

## 7. Próximos passos de verificação

Concluídos no Spike 3: ✅ disparar eventos ao vivo e gravar fixtures · ✅ servidor fora do ar e
travado · ✅ regra de origem humana em `UserPromptSubmit` (usa `origin.kind` do transcript; os
campos `is_background`/`is_continuation` não existem na 2.1.269).

Pendentes:
1. Gravar um transcript de uma sessão do **CLI de terminal** e comparar com o do Desktop.
2. Descobrir como se comporta `PermissionRequest` → decisão, para melhorar `approval.resolved`.
3. Investigar se há opção para o Claude Code gravar mais texto de thinking.
4. Exercitar os eventos que não foram provocados (`TaskCreated/Completed`, `Notification`,
   `PostToolUseFailure`, `PermissionDenied`, `StopFailure`, `Pre/PostCompact`, `CwdChanged`,
   `InstructionsLoaded`, `ConfigChange`, `UserPromptExpansion`).
5. Hooks em sessões do app Desktop e em sessões iniciadas fora do Orb (modo Observar).
