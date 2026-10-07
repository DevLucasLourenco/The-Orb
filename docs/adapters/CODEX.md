# The Orb — Adapter: Codex

> O que o Codex CLI expõe (app-server, rollouts, hooks), verificado, e como isso vira eventos do
> [PROTOCOL.md](../PROTOCOL.md). Código: `src/orb/adapters/codex/` · Equivalente:
> [CLAUDE.md](CLAUDE.md).

Última atualização: 2026-10-07 · Levantado com Codex `0.149.0` (Spike 4, 2026-10-06) e revisto com
`0.160.1` (esta máquina, 2026-10-07)

## Como isto foi verificado

| Fonte | O que cobre | Confiança |
|---|---|---|
| **Esquema oficial** (`codex app-server generate-json-schema`): 75 notificações em 0.149.0, **83 em 0.160.1**; 10 pedidos do servidor | Métodos, notificações, formas de `ThreadItem`, pedidos | **Alta** (é o contrato) |
| Execução real de uma thread via app-server (cliente A) com um observador (cliente B), Spike 4 | Fluxo de eventos, inscrição de um 2º cliente | **Alta** |
| Rollouts reais em `~/.codex/sessions/` (153 em 2026-10-06; 25 recentes em 2026-10-07, **só estrutura e contagens**) | Formato do arquivo, pensamento, subagentes, ferramentas | **Alta** |
| Adapter de rollout rodado sobre 30 dias de sessões desta máquina (2026-10-07) | 62.520 eventos, 31 sessões, 230 subagentes, **0 inválidos** | **Alta** |
| Docs de hooks (resumo) | Eventos e tipos de hook | **Média** |
| TUI com `--remote` apontando para o app-server do Orb | Só a abertura (diálogos); a conversa completa na TUI **não** foi capturada | Parcial |
| Aprovações ao vivo, hooks ao vivo, subagentes no app-server ao vivo | — | **Não verificado** |

---

## 1. Nível 1: app-server próprio do Orb + observador

```
                     ┌──────────── app-server do Orb (ws://127.0.0.1:PORTA) ────────────┐
TUI nativa do Codex ─┤ cliente A (o Lucas usa:  codex --remote ws://127.0.0.1:PORTA)    │
                     │ cliente B (adapter do Orb): se inscreve nas threads e OBSERVA    │
                     └──────────────────────────────────────────────────────────────────┘
```

- `codex app-server --listen ws://127.0.0.1:PORTA`: em loopback **não exige autenticação**.
- `codex --remote ws://127.0.0.1:PORTA`: a TUI usa esse servidor. **Nada na configuração do Lucas
  muda**; opções por sessão só com `-c chave=valor`.
- Código: `AppServerObserver` (cliente) + `AppServerTranslator` (mapa) + `app_server_command(port)`.

| Pergunta (Spike 4) | Resultado |
|---|---|
| Um 2º cliente recebe eventos da thread de outro? | **Sim, depois de se inscrever** (`thread/resume`). Passivo, só recebe `thread/started` e `thread/status/changed`. Inscrito durante o turno, recebeu **159 de 169** notificações (tudo depois da inscrição) |
| O observador atrapalha? | Não observado: o turno do A terminou normalmente |
| Descobrir threads novas? | `thread/started` chega ao passivo; também `thread/loaded/list` |
| Thread **efêmera**? | Não pode ser observada (`thread/resume` falha: "no rollout found") |
| Latência? | Notificações em ms; o turno inteiro levou ~6,4 s |

Fluxo real de um turno: `thread/status/changed` (active) → `turn/started` → `item/started|completed`
(`userMessage`, `reasoning`, `agentMessage` `commentary`, `commandExecution`, `reasoning`,
`agentMessage` `final_answer`) com `item/agentMessage/delta` e `item/commandExecution/outputDelta` →
`thread/tokenUsage/updated` → `account/rateLimits/updated` → `thread/status/changed` (idle) →
`turn/completed`.

## 2. Mapa do provider (app-server)

`native.kind` = método; para `item/*`, `método:tipo do item`. Formas do esquema 0.160.1.

| Nativo | `inner` | `signal` |
|---|---|---|
| `thread/started` (`thread.parentThreadId` nulo) | — | `session.started` (`cwd`, `model`, `name`) |
| `thread/started` com `parentThreadId` | — | `subagent.started` (`agentRole`/`agentNickname`); o subagente entra na Team da thread raiz |
| `turn/started` | — | `activity: THINKING` |
| `item/started:userMessage` (`content[]` com `{type:"text", text}`) | `prompt` | — |
| `item/completed:agentMessage` (`text`, `phase`) | `narration` | — |
| `item/completed:plan` | `narration` | — |
| `item/completed:reasoning` (`summary[]` de strings) | `thought` · `summary` (só com texto) | `activity: THINKING` |
| `item/started:commandExecution` (`command`, `commandActions[]`) | `tool` | `activity` por `commandActions[].type` (`read`/`listFiles`/`search` → `READING`), senão pelo classificador de comandos |
| `item/completed:commandExecution` (`aggregatedOutput`, `exitCode`) | `result` | — |
| `item/started:fileChange` (`changes[].path`) | `tool` | `activity: CODING` |
| `item/started:webSearch` / `mcpToolCall` | `tool` | `activity: RESEARCHING` |
| `item/started:collabAgentToolCall` | `tool` | `activity: DELEGATING` |
| `item/started:enteredReviewMode` | `tool` | `activity: REVIEWING` |
| `thread/status/changed` `active` + `activeFlags` ∋ `waitingOnApproval`/`waitingOnUserInput` | — | `waiting` (e `waiting.resolved` quando a flag some) |
| ServerRequest `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/permissions/requestApproval`, `item/tool/requestUserInput`, `mcpServer/elicitation/request`, `applyPatchApproval`, `execCommandApproval` | — | `waiting` (**nunca respondido**) |
| `serverRequest/resolved` (`requestId`) | — | `waiting.resolved` |
| `thread/tokenUsage/updated` (`tokenUsage.last`: `inputTokens`, `cachedInputTokens`, `outputTokens`, `reasoningOutputTokens`) | — | `usage` |
| `turn/completed` | — | `idle` |
| `thread/closed` | — | `session.ended` / `subagent.ended` |
| `error` (`error.message`, `willRetry`) | `system` | `error` |
| `*/delta`, `*/outputDelta`, `*/summaryTextDelta`, `*/patchUpdated`… | — | **não vira evento** (desempenho; o item completo traz o texto) |
| Sem `threadId` (ex.: `account/rateLimits/updated`) | — | não pertence a um Alter Ego (fica para a camada Energy) |

## 3. Codex não tem ferramenta "Read"

Ler um arquivo aparece como `commandExecution` de PowerShell (`Get-Content …`), às vezes com
`commandActions[].type` `unknown`. A atividade vem do **classificador de comandos** compartilhado
(`src/orb/adapters/_shared/commands.py`: tabela declarativa, tira o invólucro `powershell -Command`,
padrão seguro `EXECUTING`). O Inner World mostra o comando como o Codex o escreveu.

## 4. Pensamento: melhor que o Claude, ainda parcial

Rollouts (14.278 blocos `reasoning` em 153 sessões, Spike 4): **≈ 42% com texto**, sempre em
`summary`, nunca em `content`; todos com `encrypted_content` (retirado do corpo nativo pelo
adapter). Logo, `fidelity: summary`, nunca `raw`; sem texto, nada de entrada `thought` (o sinal
`THINKING` continua, porque o raciocínio aconteceu). Ao vivo com `gpt-5.6-luna` os `summary`
vieram vazios, mas o `agentMessage` de `commentary` traz narração utilizável.

## 5. Mensagens com papel `user`

Aparecem como `prompt`, do jeito que o Codex grava; o Orb não rastreia quem escreveu
([ADR 0003](../adr/0003-inner-world-une-terminal-e-pensamento.md)). Nos rollouts, mensagens
`role: user` também incluem contexto injetado pelo próprio Codex (`<environment_context>`,
`<external_codex_apps_open_page>`…): elas aparecem igualmente, com o texto que o Codex gravou.

## 6. Princípio de não interferência com o Codex

1. **O observador nunca responde a `ServerRequest`**, nem para recusar
   ([ADR 0006](../adr/0006-o-orb-nunca-responde-dialogos.md)). Coberto por teste
   (`test_observer_never_answers_server_requests`). No `spikes/04-codex/drive.py`, só o cliente A
   (que conduz o teste com `approvalPolicy: never`) recusa; o B é marcado como observador.
2. `thread/resume` é a forma de se inscrever: não altera a thread, mas é uma operação do protocolo.
3. **Diálogos da TUI são do Lucas** (§7).
4. **Hooks do Codex não servem para o nível 1:** só `command`/`mcp_tool` (sem `http`), descobertos
   em `~/.codex/` e `<repo>/.codex/`, **exigem confiança do usuário** e não há injeção por sessão.
5. O `notify` do `config.toml` (usado pelo app Desktop) não é tocado.

## 7. Diálogos da TUI (e o incidente do Spike 4)

| Diálogo | Opções | Padrão |
|---|---|---|
| *Update available!* | 1. **Update now** (roda o instalador) · 2. Skip · 3. Skip until next version | **Update now** |
| *Do you trust the contents of this directory?* | 1. Yes, continue · 2. No, quit | Yes |
| *Hooks need review* | 1. Review hooks · 2. **Trust all and continue** · 3. Continue without trusting · (`t` = trust all) | Review hooks |

**Incidente (2026-10-06, outra máquina):** um script de teste deu Enter às cegas e aceitou "Update
now"; o instalador **falhou sem efeito** (versão intacta; ficou uma pasta de staging vazia). Numa
segunda execução, um prompt foi digitado com a revisão de hooks aberta; a verificação indicou que
nada foi confiado, sem prova de 100%. Regras que ficaram: nenhuma tecla sem a tela verificada; em
testes, só Esc e abortar em diálogo desconhecido; um único marcador de "prompt pronto" não basta (o
compositor aparece desenhado por baixo dos diálogos). `-c check_for_update_on_startup=false` evita o
diálogo de atualização só na sessão, mas **o Orb não o usa por padrão**: ser avisado de atualização
é decisão do Lucas.

## 8. Nível 0: rollouts

`~/.codex/sessions/AAAA/MM/DD/rollout-<data>-<id>.jsonl`, append-only. Cada linha:
`timestamp`, `ordinal`, `type`, `payload` (e às vezes `metadata`). Estrutura observada em 0.160.1:

| `type` / `payload.type` | Uso no adapter |
|---|---|
| `session_meta` (1ª linha): `id`, `cwd`, `cli_version`, `parent_thread_id`, `agent_role`, `agent_nickname`, `forked_from_id`, `source`, `git`… | `session.started` / `subagent.started`; filtro do realm pelo `cwd` |
| `response_item/message` (`role` `user`/`assistant`/`developer`, `phase`, `content[].text`) | Prompt (§5), narração; `developer` é ignorado (instruções) |
| `response_item/reasoning` (`summary[]` de `{type: summary_text, text}`, `encrypted_content`) | `thought` `summary` |
| `response_item/custom_tool_call` (`name: exec`, `input` texto) e `function_call` (`name`, `arguments` JSON: `spawn_agent`, `wait_agent`, `send_message`, `followup_task`, `list_agents`, `request_user_input_async`, `js`, `wait`, `sleep`) | `activity` (`exec` pelo classificador; ferramentas de agentes → `DELEGATING`) |
| `*_call_output` | `result` |
| `event_msg/task_started` · `task_complete` · `turn_aborted` | `THINKING` · `idle` · `idle` |
| `token_usage_record` (`usage`: `input_tokens`, `cached_input_tokens`, `output_tokens`, `reasoning_output_tokens`) | `usage` |
| `event_msg/token_count`, `item_completed`, `turn_context`, `world_state`, `compacted` | Ignorados (redundantes ou sem trabalho visível) |

- **Desempenho:** há rollouts de 145 MB. Arquivo que já existia começa **do fim**; a primeira linha
  (`session_meta`) é lida à parte; a árvore de sessões é varrida no máximo a cada 2 s.
- O Orb não consegue dar o id da thread à TUI hospedada (não há `--session-id`); o vínculo com o
  Alter Ego vem de `thread/started` (nível 1) ou de `cwd` + horário (nível 0).
- **Título da sessão:** `~/.codex/session_index.jsonl` guarda `{id, thread_name, updated_at}` por
  linha (a última vence). O leitor relê o arquivo só quando ele muda e emite `session.updated`.
- O modelo padrão do `config.toml` do Lucas (`gpt-6-luna`, na máquina do Spike 4) não era aceito
  com conta ChatGPT; modelos reais `gpt-5.6-sol`, `terra`, `luna`. O Orb passa `-m <modelo>` quando
  a sessão tem modelo.

## 9. `capabilities()`

| Capacidade | Valor |
|---|---|
| Pensamento | `summary` (~42% dos blocos), nunca `raw` |
| Aprovações | **Pedido + resolução** (melhor que o Claude); o observador não responde |
| Subagentes | Sim (`parentThreadId` / `parent_thread_id`); 230 vistos nos rollouts desta máquina |
| Tempo real | Nível 1 pelo app-server próprio |
| Tokens / limites da conta | Sim (`thread/tokenUsage/updated`, `token_usage_record`, `account/rateLimits/updated`) |

## 10. Pesquisa / não verificado

1. **Assinante passivo que ignora um `ServerRequest` de aprovação:** o servidor bloqueia, repete ou
   reencaminha? **Risco principal**; testar com o Lucas acompanhando.
2. Conversa completa na TUI ligada ao app-server do Orb, depois de o Lucas responder os diálogos.
3. Subagentes ao vivo no app-server (`parentThreadId` em `thread/started`).
4. Se `--remote` mantém todos os recursos da TUI (slash commands, plugins, MCP).
5. `codex resume <id>` para reabrir um Alter Ego: confirmar que mantém o id da thread.
