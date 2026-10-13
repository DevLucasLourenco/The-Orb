# The Orb — Adapter: Claude Code

> O que o Claude Code expõe (transcript e hooks), verificado, e como isso vira eventos do
> [PROTOCOL.md](../PROTOCOL.md): o evento nativo intacto + sinal de mundo + entrada de Inner World.
> Código: `src/orb/adapters/claude/` · Vocabulário: [CONTEXT.md](../../CONTEXT.md).

Última atualização: 2026-10-07

## Como isto foi verificado

| Fonte | O que cobre | Confiança |
|---|---|---|
| Transcripts reais em `~/.claude/projects/` (2026-10-06: 6 projetos, ~3,3 mil blocos de thinking; 2026-10-07: 12 sessões recentes, **só estrutura e contagens**, sem ler conteúdo) | Formato do JSONL, origem dos prompts, subagentes, `usage`, `stop_reason` | **Alta** para o que foi visto |
| Hooks ao vivo (Spike 3, `claude` 2.1.269, -p e TUI hospedada) | Campos reais de cada hook, comportamento com o Orb fora do ar e travado | **Alta** |
| Adapter rodado sobre os transcripts desta pasta (2026-10-07, `claude` 2.1.248) | 598 eventos, **0 inválidos** | **Alta** |
| Docs de hooks (`code.claude.com/docs/en/hooks`) | Lista de eventos e tipos de hook | **Média** (lidas por resumo; os campos reais vieram do Spike 3) |
| Transcripts do **CLI de terminal** vs. app Desktop | — | **Não comparado.** O formato observado é o mesmo nas sessões disponíveis |

O transcript **não é uma API documentada**: é interno e muda entre versões. Por isso o adapter
ignora campos desconhecidos e preserva o nativo intacto.

---

## 1. Nível 0: transcript (padrão)

### 1.1 Onde fica

- Sessão: `~/.claude/projects/<cwd codificado>/<session_id>.jsonl`. `<cwd codificado>` = o diretório
  com todo caractere não alfanumérico trocado por `-` (ex.: `C--Users-x-Documents-Sistemas-e-Projetos-The-Orb`).
- Subagentes: `<session_id>/subagents/agent-<agentId>.jsonl`, com `agent-<agentId>.meta.json` ao lado
  (`agentType`, `description`, `toolUseId`, `spawnDepth`, `requestShape`, `requestNonInteractive`).
- Append-only, uma linha JSON por entrada: dá para acompanhar em tempo real.
- **Subpastas e worktrees:** uma sessão aberta numa subpasta do projeto (ex.:
  `<projeto>/.claude/worktrees/<nome>`) tem a sua própria pasta codificada. O leitor do realm
  também acompanha as pastas cujo nome começa com o do projeto, mas só depois de confirmar pelo
  `cwd` gravado no transcript, porque o nome codificado é ambíguo ("trisafe" é prefixo de
  "trisafe-enhanced").
- **Identidade:** o título vem de `custom-title` (`customTitle`) ou `agent-name` (`agentName`), e o
  modelo de `message.model`; na descoberta o leitor lê só o fim do arquivo para achá-los.

### 1.2 Tipos de entrada observados

`assistant`, `user`, `attachment`, `system`, `queue-operation`, `file-history-snapshot`,
`file-history-delta`, `cost-state`, `mode`, `permission-mode`, `custom-title`, `agent-name`,
`last-prompt`, `atis-latch`, `pr-link`. O adapter usa `user` e `assistant`; o resto fica para
camadas futuras (título da sessão, custo).

### 1.3 Campos que o adapter usa

- **Toda entrada de conversa:** `uuid` (vira a chave do `id` do evento), `timestamp`, `sessionId`,
  `isSidechain`.
- **`assistant`:** `message.id`, `message.content[]` (blocos `text`, `thinking`, `tool_use`),
  `message.usage`, `message.stop_reason`.
  - **Uma mensagem aparece em várias linhas** (uma por bloco) com o **mesmo `message.id` e o mesmo
    `usage`**: o adapter conta `usage` uma vez por `message.id`.
  - `stop_reason`: `tool_use` (continua) ou `end_turn` (fim do turno → sinal `idle`).
- **`user`:** `message.content` (texto, ou lista com blocos `tool_result`/`text`/`image`), `origin`,
  `isMeta`, `promptId`.
- **`toolUseResult`** (na entrada `user` que traz o resultado; estrutura vista em 2026-10-09): para
  ferramentas de shell, `stdout`, `stderr`, `interrupted`, `isImage` e, às vezes, `returnCodeInterpretation`
  (texto), `backgroundTaskId`, `timedOutAfterMs` e **`gitOperation`** (`commit`, `push`, `branch`, `pr`).
  **Não há código de saída**: falha = `is_error` no bloco `tool_result` (D-084). `gitOperation` é a
  evidência de commit, push, branch e PR (D-090).

### 1.4 Mensagens com papel `user`

Toda entrada `user` com texto aparece no Inner World como `user/text` (papel `prompt`), do jeito que
o Claude gravou; o corpo nativo mantém `origin`, `isMeta` e `promptId`. O Orb **não classifica quem
escreveu** ([ADR 0003](../adr/0003-inner-world-une-terminal-e-pensamento.md)). Para referência, o
`origin.kind` observado em 2.1.248 distingue `human`, `task-notification` (subagente em segundo
plano terminou) e `peer` (mensagem de outra sessão); entradas `isMeta` são contexto do harness.

### 1.5 Mapa do provider (transcript)

| `native.kind` | `inner` | `signal` |
|---|---|---|
| `user/text` | `prompt` | — |
| `user/tool_result` | `result` | `subagent.ended` quando fecha um subagente *foreground* |
| `assistant/text` | `narration` | — |
| `assistant/thinking` (só com texto) | `thought` · `raw` | `activity: THINKING` |
| `assistant/tool_use` | `tool` (`Nome alvo`) | `activity` pela tabela de ferramentas |
| `assistant/usage` | — | `usage` (uma vez por `message.id`) |
| `assistant/stop` | — | `idle` (`stop_reason: end_turn` do líder) |
| `subagent/meta` | `system` | `subagent.started` (`kind` = `agentType`) |

Ferramenta → atividade: `Read`/`Glob`/`Grep` → `READING`; `Edit`/`Write`/`NotebookEdit` →
`CODING`; `Bash`/`PowerShell` → classificador de comandos (`pytest` → `TESTING`, `git status` →
`READING`, …); `WebFetch`/`WebSearch`/`mcp__*` → `RESEARCHING`; `Agent`/`Task` → `DELEGATING`;
desconhecida → `EXECUTING`.

### 1.6 Subagentes no nível 0

- Nascem quando aparece `agent-<id>.jsonl`; o `.meta.json` dá o tipo e o `toolUseId` do pai.
- **Fim:** o transcript do subagente **não** marca o fim (`stop_reason` vem `null` em ~90% das
  linhas de subagente). O adapter encerra o subagente quando chega o `tool_result` do pai para o
  `toolUseId` dele, **só se `requestShape` for `foreground`**.
- **Lacuna:** subagentes em segundo plano não têm fim observável no nível 0 (o líder aparece
  `DELEGATING`). O nível 1 (`SubagentStop`) resolve; correlacionar o `<task-notification>` é pesquisa.

### 1.7 Thinking: quase sempre vazio

| Amostra | Com texto | Vazio |
|---|---|---|
| ~3,3 mil blocos em 6 projetos (2026-10-06) | 389 (≈ 12%) | 2.917 (≈ 88%) |

O que fica gravado costuma ser só a `signature`. Sem texto, **não há entrada `thought`**; a
`signature` é retirada do corpo nativo (não serve para nada no Orb e ocupa espaço). O Inner World do
Claude se apoia em narração (`text`), ferramentas e prompts. A TUI mostra "Cogitated for 12s", mas
o texto não vai ao transcript.

---

## 2. Nível 1: hooks por sessão (opcional)

### 2.1 Como instalar sem tocar na configuração do Lucas

`claude --settings <arquivo>` injeta hooks **só naquela sessão** ([ADR 0005](../adr/0005-nivel-zero-de-pegada-por-padrao.md)).
O `~/.claude/settings.json` do Lucas não é alterado. Token por variável de ambiente
(`ORB_TOKEN`) no header. `--bare` desliga hooks: não usar. Gerador: `session_settings(port)`.

### 2.2 Campos reais (Spike 3, `claude` 2.1.269)

Comuns: `session_id`, `prompt_id`, `transcript_path`, `cwd`, `hook_event_name`; e `agent_id` /
`agent_type` quando o evento ocorre dentro de um subagente.

| Hook | Campos específicos | → `signal` |
|---|---|---|
| `UserPromptSubmit` | `prompt`, `permission_mode` (**sem** `is_continuation`/`is_background`) | — (entra no Inner World como `prompt`) |
| `PreToolUse` | `tool_name`, `tool_input`, `tool_use_id`, `permission_mode` | `activity` |
| `PostToolUse` | `tool_name`, `tool_input`, **`tool_response`** (não `tool_output`), `duration_ms`, `tool_use_id` | `waiting.resolved` deduzido, se havia pedido |
| `PostToolBatch` | `tool_calls[]` | — |
| `MessageDisplay` | `delta`, `final`, `index`, `message_id`, `turn_id` | — (streaming) |
| `Stop` | `last_assistant_message`, `stop_hook_active`, `background_tasks`, `session_crons` | `idle` |
| `PermissionRequest` | `tool_name`, `tool_input`, `permission_suggestions` | `waiting` |
| `SubagentStart` | `agent_id`, `agent_type` | `subagent.started` |
| `SubagentStop` | `agent_id`, `agent_type`, **`agent_transcript_path`**, `last_assistant_message` | `subagent.ended` |
| `SessionEnd` | `reason` (ex.: `prompt_input_exit`) | `session.ended` |
| `SessionStart` | `source`, `model` (só chegou com hook `command`) | `session.started` |

Não exercitados (não é o mesmo que "não existem"): `UserPromptExpansion`, `StopFailure`,
`PermissionDenied`, `PostToolUseFailure`, `TaskCreated`, `TaskCompleted`, `Notification`,
`PreCompact`, `PostCompact`, `CwdChanged`, `InstructionsLoaded`, `ConfigChange`.

### 2.3 Comportamentos que moldaram o desenho

1. Eventos dentro de um subagente trazem `agent_id`/`agent_type`: atribuição confirmada.
2. **`UserPromptSubmit` também dispara para prompts do sistema** (`<task-notification>`); como o Orb
   não rastreia autoria, isso não muda nada no mundo.
3. **A ferramenta `Agent` é assíncrona:** o `Stop` do líder chegou aos 5 s e o `SubagentStop` aos
   12 s. `Stop` do líder ≠ Team parada (o Core mostra o líder `DELEGATING`). **Exceção (ticket 01,
   R7):** um subagente sem atividade há mais de 5 min e sem aviso de fim vira "sem sinal" e deixa de
   segurar o líder em `DELEGATING`; sem isso, um subagente em segundo plano nunca fecharia e a sessão
   nunca dormiria.
4. O `session_id` dos hooks é o mesmo do `--session-id` dado pelo Orb, também na TUI hospedada.
5. Aparece `SubagentStop` sem subagente pedido (provável subagente interno): `agent_type`
   desconhecido não pode quebrar nada.
6. **A decisão do Lucas num `PermissionRequest` não tem hook.** O adapter deduz: `PostToolUse` da
   mesma ferramenta → `approved`; `PermissionDenied` → `denied`; o sinal leva `deduced: true`.

### 2.4 Um Orb travado não pode atrasar o agente

Cenário: ler um arquivo, mesma sessão, variando o receptor.

| Receptor | Hook | Tempo | Efeito |
|---|---|---|---|
| Vivo | `http` | ~7,5 s | referência |
| Fora do ar | `http` | ~6,7 s | nenhum |
| **Travado** | `http`, timeout 2 s | **21,5 s** | **+14 s** |
| Travado | `http` + `async` | 20,5 s | `async` não ajuda em `http` |
| Travado | `command` async + `curl -m 1` | 10,5 s | ~+3 s |
| Vivo | `command` async + `curl` | 8,0 s | ~+0,5 s |

Por isso o transporte é `command` assíncrono com `curl -m 1` para um receptor mínimo que só
enfileira e responde `{}`. Limitações: `command` assíncrono pode perder o último evento quando o
processo termina antes do `curl` (`SessionEnd` em `-p`); `SessionStart` não chega por hook `http`
(o Terminal Host já sabe quando a sessão abre).

---

## 3. Sessão = Alter Ego

- **Hospedar:** o Orb gera o UUID, chama `claude --session-id <uuid> -n orb-<8>` e sabe qual é o
  transcript sem adivinhar pela pasta (sem isso o leitor confundia sessões da mesma pasta).
- **Reabrir:** `claude --resume <uuid>` num terminal novo. **A verificar:** se a retomada mantém o
  mesmo id (mesmo Alter Ego) e o que `fork`, `/clear` e compactação fazem com o id.
- **Observar:** sessões abertas fora do Orb são descobertas pela pasta do realm
  (`TranscriptReader` sem `session_id`).
- Disponível para o Perfil, quando ele for decidido: entradas `custom-title` e `agent-name` no
  transcript.

## 4. `capabilities()`

| Capacidade | Valor |
|---|---|
| Pensamento | `raw`, raro (~12% dos blocos) |
| Aprovações | Pedido sim (nível 1); decisão deduzida |
| Subagentes | Sim (meta + hooks); fim de subagente em segundo plano só no nível 1 |
| Tempo real | Nível 1 por hooks de sessão |
| Tokens | Sim (`message.usage`) |

## 5. Pendências

1. Retomada/fork/clear/compactação e o id da sessão (ver [VISION.md](../VISION.md) §7).
2. Fim de subagente em segundo plano no nível 0.
3. Exercitar os hooks não provocados (§2.2).
4. Opção que faça o Claude Code gravar mais texto de thinking (a investigar).
5. Receptor mínimo do nível 1 como processo separado e sempre responsivo.
