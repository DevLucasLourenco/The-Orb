# Orb IA — ADAPTER: Codex

> Levantamento do que o Codex CLI expõe (app-server, rollouts, hooks) e como isso vira eventos do
> [PROTOCOL.md](PROTOCOL.md). Base do Codex Adapter. Equivalente a [ADAPTER-CLAUDE.md](ADAPTER-CLAUDE.md).
> Contexto: [CONTEXT.md](CONTEXT.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [MVP.md](MVP.md) §9.

Levantado em: 2026-10-06 · Codex CLI `0.149.0` (Windows 11, login ChatGPT)
Código e fixtures: `spikes/04-codex/` (`drive.py`, `observe.py`, `tui_peek.py`, `fixtures/codex-0.149.0/`).

## Como isto foi verificado (e o que não foi)

| Fonte | O que cobre | Confiança |
|---|---|---|
| **Esquema oficial** gerado pelo próprio CLI (`codex app-server generate-json-schema`) | Todos os métodos, notificações e pedidos do protocolo | **Alta** (é o contrato) |
| **Execução real** de uma thread via app-server (cliente A) com um observador (cliente B) | Fluxo de eventos, inscrição de um 2º cliente, formato das notificações | **Alta** |
| 153 rollouts reais em `~/.codex/sessions/` (só estrutura, sem ler conteúdo) | Formato do arquivo de sessão, presença de texto de raciocínio | **Alta** |
| Docs de hooks (`developers.openai.com/codex/hooks` → `learn.chatgpt.com/docs/hooks`), lidas por resumo | Eventos e tipos de hook, configuração | **Média** (resumo; não disparei hooks) |
| TUI do Codex com `--remote` apontando para o app-server do Orb | Só a abertura (diálogos); **o fluxo de uma conversa na TUI não foi capturado** (ver §6) | Parcial |
| Subagentes, aprovações (ServerRequest) e hooks ao vivo | — | **Não verificado** |

---

## 1. O caminho principal: app-server com mais de um cliente

O Codex tem um protocolo oficial, **JSON-RPC por WebSocket**, e a TUI sabe falar com um servidor
remoto. O desenho:

```
                     ┌──────────── app-server do Orb (ws://127.0.0.1:PORTA) ────────────┐
TUI nativa do Codex ─┤ cliente A (o Lucas usa:  codex --remote ws://127.0.0.1:PORTA)    │
                     │ cliente B (Orb Adapter): se inscreve nas threads e OBSERVA       │
                     └──────────────────────────────────────────────────────────────────┘
```

- `codex app-server --listen ws://127.0.0.1:PORTA` — em loopback **não exige autenticação**.
- `codex --remote ws://127.0.0.1:PORTA` — a TUI usa esse servidor como backend.
- **Nada na configuração do Lucas muda.** Opções por sessão via `-c chave=valor`.

### Verificado ao vivo

| Pergunta | Resultado |
|---|---|
| Um 2º cliente recebe eventos de uma thread de outro cliente? | **Sim, depois de se inscrever.** Passivo, só recebe `thread/started` e `thread/status/changed`. Com `thread/resume` durante o turno, o observador B recebeu **159 de 169** notificações do cliente A (tudo, exceto o que veio antes da inscrição) |
| O observador atrapalha a conversa? | Não observado: o turno do A terminou normalmente com a resposta correta |
| Descobrir threads novas? | `thread/started` chega ao cliente passivo; também `thread/loaded/list` |
| Thread **efêmera** pode ser observada? | **Não.** `thread/resume` falha com "no rollout found". Só threads persistidas |
| Latência? | Notificações em ms: o turno inteiro (leitura de arquivo) levou ~6,4 s |

### Eventos reais de um turno (cliente A, `gpt-5.6-luna`)

`thread/status/changed` (active) → `turn/started` → `item/started|completed` (`userMessage`,
`reasoning`, `agentMessage` fase `commentary`, `commandExecution`, `reasoning`, `agentMessage`
fase `final_answer`) com `item/agentMessage/delta` e `item/commandExecution/outputDelta`
(saída do comando em tempo real) → `thread/tokenUsage/updated` → `account/rateLimits/updated`
→ `thread/status/changed` (idle) → `turn/completed`.

---

## 2. Mapeamento para o protocolo do Orb

Base: esquema oficial (75 notificações, 10 pedidos do servidor) e fixtures reais.

| Codex (notificação) | → Protocolo do Orb | Observações |
|---|---|---|
| `thread/started` | `session.started` | `thread.id` = session; `parentThreadId` indica subagente (não testado) |
| `thread/status/changed` `active` / `idle` | `agent.state_changed` (`THINKING`…) / `agent.idle` | |
| `turn/started` / `turn/completed` | início/fim de trabalho; `turn/completed` → `agent.idle` | |
| `item/started` `userMessage` | **`intrusive_thought`** | Já vem **só com mensagens de usuário**; ver §5 sobre origem humana |
| `item/*` `agentMessage`, `phase: commentary` | `agent.message` / `thought` (narração) | `fidelity` **`raw`** do que o agente disse |
| `item/*` `agentMessage`, `phase: final_answer` | `agent.message` | resposta final |
| `item/*` `reasoning` (`summary[]`) | `thought` com `fidelity: summary` | Texto **só quando o `summary` não está vazio** (§4) |
| `item/*` `commandExecution` | `tool.started` / `tool.completed` (`category` deduzida do comando) | Ver §3 |
| `item/commandExecution/outputDelta` | (saída ao vivo; opcional) | 120 deltas num comando curto: agrupar |
| `item/fileChange/*` (`patchUpdated`, `outputDelta`) | `file.edit` | Nome do esquema; não exercitado |
| `item/mcpToolCall/*` | `tool.*` (`research`) | Não exercitado |
| `turn/plan/updated`, `item/plan/delta` | `plan.updated` | Plano nativo; não exercitado |
| `turn/diff/updated` | `file.edit` agregado | Não exercitado |
| `thread/tokenUsage/updated` | `usage.reported` | `inputTokens`, `cachedInputTokens`, `outputTokens`, **`reasoningOutputTokens`** |
| `account/rateLimits/updated` | (Energy: limites de uso da conta) | Dado extra, útil para a camada Energy |
| `hook/started`, `hook/completed` | (telemetria de hooks) | Existem no protocolo |
| `error`, `warning` | `error` / aviso | Ex.: modelo não suportado |
| **ServerRequest** `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/permissions/requestApproval`, `item/tool/requestUserInput`, `mcpServer/elicitation/request` | `approval.requested` | Ver §5: o observador **nunca responde** |
| `serverRequest/resolved` | `approval.resolved` | Existe notificação de resolução (melhor que no Claude, onde é deduzido) |

---

## 3. Codex não tem ferramenta "Read": é preciso classificar comandos

Ler um arquivo apareceu como `commandExecution` de **PowerShell** (`Get-Content …`), e
`commandActions[].type` veio `unknown`. Para `tool.category`/estado/área do Rooftop Room, o
adapter precisa **classificar o comando** (`Get-Content`/`cat`/`type` → `read`; `git`, `npm`,
`pytest` → `execute`/`test`; edições chegam como `fileChange`). Regra declarativa por tabela de
padrões (dado, não lógica espalhada), com `other` como padrão seguro. Quando `commandActions`
trouxer tipos conhecidos, usá-los primeiro.

---

## 4. Pensamento: melhor que o Claude, ainda parcial

Rollouts reais (14.278 blocos `reasoning` em 153 sessões): **6.064 (≈ 42%) com texto legível**,
8.214 sem texto; texto aparece **sempre em `summary`**, nunca em `content`. Todos têm
`encrypted_content`. Logo:

- Pensamento do Codex é `fidelity: summary` (resumo dado pelo provider), nunca `raw`.
- Em ~58% dos blocos não há texto: **não se emite `thought`** (regra do protocolo).
- Na execução ao vivo com `gpt-5.6-luna`, os blocos de `reasoning` vieram com `summary` vazio,
  mas o `agentMessage` de `commentary` ("Vou ler o arquivo…") traz narração utilizável.
- Há notificações de streaming de resumo: `item/reasoning/summaryTextDelta`,
  `summaryPartAdded`, `textDelta` (não exercitadas).

---

## 5. Princípio 10: o que o Orb nunca faz com o Codex

1. **O observador nunca responde a `ServerRequest`** (aprovações, perguntas ao usuário). Quem
   decide é o Lucas, na TUI. **Risco em aberto:** não testei o que o servidor faz com um
   assinante passivo que ignora um pedido de aprovação (se bloqueia, se reencaminha). O
   `drive.py` recusava pedidos por padrão, só porque o teste usava `approvalPolicy: never`
   (nenhum pedido ocorreu). **Isso precisa ser verificado antes de o adapter existir.**
2. **`thread/resume` é um ato de inscrição do Orb**: não altera a thread, mas é uma operação
   do protocolo, a registrar. Nenhum efeito visível na conversa foi observado.
3. **Diálogos da TUI são do Lucas** (ver §6). O Orb nunca os responde.
4. **Hooks do Codex não servem para o nível 1 do Orb:** só `command`/`mcp_tool` (sem `http`), são
   descobertos em `~/.codex/` e `<repo>/.codex/` e **exigem confiança do usuário**; as docs dizem
   que não há injeção por sessão. Instalar hooks mudaria a configuração dele. **Para o Codex, o
   equivalente do nível 1 é o app-server com observador**, que não toca em nada.
5. O `notify` do `config.toml` (usado pelo app Desktop) não é tocado.

---

## 6. Diálogos da TUI do Codex (e um incidente do spike)

A TUI do Codex abre com **diálogos modais cujo padrão é uma ação com efeito**:

| Diálogo | Opções | Padrão |
|---|---|---|
| *Update available! 0.149.0 → 0.160.1* | 1. **Update now** (roda `irm …/install.ps1 \| iex`) · 2. Skip · 3. Skip until next version | **Update now** |
| *Do you trust the contents of this directory?* (diretório não listado no `config.toml`) | 1. Yes, continue · 2. No, quit | Yes |
| *Hooks need review: N hooks are new or changed* | 1. Review hooks · 2. **Trust all and continue** · 3. Continue without trusting · (`t` = trust all, `esc` fecha) | Review hooks |

**Incidente:** no primeiro teste, o meu script digitou um prompt e deu Enter às cegas depois de
14 s. O Enter caiu no diálogo de atualização e aceitou "Update now": o instalador oficial rodou
**e falhou** ("package archive did not contain the expected package layout"). Efeito real:
**nenhum** (versão segue 0.149.0, `current` aponta para 0.149.0, `codex doctor` confirma, o
`config.toml` não mudou); ficou só uma pasta de staging **vazia**
(`~/.codex/packages/standalone/releases/.staging.0.160.1-…`).

**Segundo deslize, na execução seguinte** (já com a atualização desligada por `-c`): a TUI abriu
a revisão de hooks (*"Press t to trust all…"*), o script não a reconheceu como diálogo, **digitou
o prompt com ela aberta** (o texto continha a letra `t`, atalho de "trust all") e deu Enter.
Verificação posterior: `config.toml` sem alteração (mtime inalterado), nenhum `hooks.json`
criado, e a tabela de hooks no fim da tela ainda mostrava **0 confiados**. Tudo indica que
**nada foi confiado**, mas a TUI foi encerrada à força, então não há como provar 100%; vale o
Lucas abrir o Codex uma vez e conferir se a revisão de hooks ainda aparece como pendente.

Regras que decorrem disso (valem para o Orb inteiro, não só para o Codex):
- **O Orb nunca envia teclas a uma TUI sem a tela estar verificada**, e **nunca responde
  diálogos de atualização, confiança ou hooks**: são decisões do Lucas, no terminal dele.
- Em automação de teste, só se envia a tecla mais conservadora (Esc) e **abortam-se** diálogos
  desconhecidos; o `observe.py` ficou assim.
- Um único marcador de "prompt pronto" não basta: o compositor ("Ask Codex…") aparece
  desenhado **por baixo** dos diálogos.
- Opções por sessão que ajudam a não chegar a esses diálogos **sem tocar no `config.toml`**:
  `-c check_for_update_on_startup=false` (validado com `--strict-config`). Não existe opção
  equivalente que eu tenha validado para trust/hooks, e **o Orb não deve contorná-los**.

---

## 7. Nível 0 para o Codex: rollouts (sessões iniciadas fora do Orb)

`~/.codex/sessions/AAAA/MM/DD/rollout-<data>-<id>.jsonl`, append-only, uma linha JSON por entrada.
Chaves: `timestamp`, `ordinal`, `type`, `payload`.

| `type` | Conteúdo útil |
|---|---|
| `session_meta` | `id`, `cwd`, `cli_version`, `git`, `parent_thread_id`, `agent_nickname`, `agent_path`, `multi_agent_version`, `forked_from_id`, `source`, `model_provider` |
| `turn_context` | contexto do turno |
| `event_msg` (`task_started`, `task_complete`, `item_completed`, `token_count`, `thread_settings_applied`) | ciclo do turno e uso |
| `response_item` (`message`, `reasoning`, `custom_tool_call(_output)`, `function_call(_output)`, `agent_message`) | mensagens, pensamento (`summary`), ferramentas |
| `token_usage_record`, `world_state`, `compacted`, `inter_agent_communication_metadata` | tokens, estado, compactação, **comunicação entre agentes** |

- `session_meta.parent_thread_id`/`agent_nickname`: **suporte a subagentes** no formato (ligar
  ao pai). Não testado ao vivo.
- Sessões muito grandes existem (um rollout de 145 MB): o tail deve ler **a partir do fim** e
  incrementalmente, nunca o arquivo inteiro.
- Não há como o Orb atribuir o id da thread à TUI hospedada (diferente do `--session-id` do
  Claude); o vínculo com o Alter Ego vem de `thread/started` (app-server) ou de `cwd` + horário.

---

## 8. `capabilities()` do Codex Adapter (proposta)

| Capacidade | Valor |
|---|---|
| Eventos de ferramenta/comando | Sim (`item/*`), com **classificação de comando** necessária |
| Subagentes | Provável (`parent_thread_id`, `multi_agent`); **não verificado** |
| Detecção de intrusive thoughts | Sim (`userMessage`); ver dúvida de origem humana |
| Aprovações | **Sim, melhor que o Claude** (`ServerRequest` + `serverRequest/resolved`); observador não responde |
| Pensamento | `summary` em ~42% dos blocos; nunca `raw` |
| Narração (`commentary`) | Sim |
| Tokens / custo / limites da conta | Sim (`thread/tokenUsage/updated`, `account/rateLimits/updated`) |
| Observação sem tocar na configuração | **Sim** (app-server do Orb + `--remote`) |

---

## 9. Pesquisa futura / não verificado

1. **Assinante passivo que ignora um `ServerRequest` de aprovação**: o servidor bloqueia, repete
   ou reencaminha? Crítico para o princípio 10.
2. **Conversa completa na TUI** conectada ao app-server do Orb, com o observador recebendo tudo,
   depois de o Lucas responder os diálogos. O spike só validou o observador com um cliente
   programático.
3. **Subagentes** ao vivo (`parentThreadId` em `thread/started`).
4. Se `--remote` mantém todos os recursos da TUI (slash commands, plugins, MCP do `config.toml`).
5. Hooks do Codex ao vivo (provavelmente fora do plano, ver §5).
6. Origem humana em `userMessage` (equivalente ao `origin.kind` do Claude).
7. Hermes (CLI não instalado nesta máquina): só pesquisa de documentação.
