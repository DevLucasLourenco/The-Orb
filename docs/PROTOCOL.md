# The Orb — Event Protocol

> O contrato entre quem produz eventos (Adapters, Probes, Terminal Host) e quem os consome
> (Core, Gateway, clientes). Vocabulário: [CONTEXT.md](../CONTEXT.md) · Módulos:
> [ARCHITECTURE.md](ARCHITECTURE.md) · Por que é assim: [ADR 0002](adr/0002-eventos-nativos-por-provider.md).

Versão do protocolo: `0.2` (rascunho) · Última atualização: 2026-10-09 · Implementação:
`src/orb/protocol/`

> **Mudança desde a 0.1:** o protocolo deixou de traduzir eventos para um vocabulário universal.
> Cada evento agora carrega o **evento nativo** do provider, intacto, e ao lado dele um **sinal de
> mundo** e uma **entrada de Inner World** opcionais. O evento `intrusive_thought` deixou de
> existir: o que o Lucas escreve é uma mensagem da sessão como outra qualquer (ADR 0003).

---

## 1. Princípios

1. **Nativo primeiro.** O evento nativo (nome e corpo) é preservado como o provider o emitiu. O
   Orb não renomeia nem reescreve.
2. **Sinais derivados, pequenos e fechados.** O mundo só consome sinais de mundo (§5), um
   vocabulário pequeno e estável. Um sinal acompanha o evento nativo; nunca o substitui.
3. **Só fatos observados.** Nada é emitido sem um evento nativo que o sustente. Sem sinal, não há
   evento: a ausência é visível.
4. **Idempotente.** O `id` é determinístico: reler a mesma fonte gera os mesmos ids, e o Core
   descarta repetidos. Reconectar e reler nunca duplica.
5. **Limitado.** Corpos e textos têm tamanho máximo (§3); o que passa é cortado e marcado.
6. **Tolerante.** Consumidores ignoram campos desconhecidos; produtores não removem campos dentro
   da mesma versão maior.

## 2. Envelope

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `v` | string | sim | Versão do protocolo: `"0.2"` |
| `id` | string | sim | Determinístico: `<alter_ego>:<chave nativa>` (ex.: uuid da linha do transcript + índice do bloco). Chave de deduplicação |
| `ts` | string | sim | ISO 8601 com fuso: quando **ocorreu** (vem do evento nativo) |
| `provider` | string \| null | sim | `claude` · `codex` · `hermes` · … ; `null` em eventos de probe/sistema |
| `source` | string | sim | Canal que produziu: `claude/transcript`, `claude/hooks`, `codex/app-server`, `codex/rollout`, `terminal`, `system`, `probe/git`… |
| `realm` | string | sim | Id do realm |
| `alter_ego` | string \| null | sim | `<provider>:<id da sessão>`; `null` em eventos de realm/mundo |
| `agent` | string \| null | sim | Id do subagente dentro da sessão; `null` = o próprio Alter Ego (líder) |
| `seq` | inteiro | sim | Ordem de produção por `alter_ego`, crescente, definida pelo adapter |
| `native` | objeto | sim | O evento nativo (§3) |
| `inner` | objeto \| null | não | Entrada de Inner World (§4) |
| `signal` | objeto \| null | não | Sinal de mundo (§5) |

### Exemplo (Claude, transcript)

```json
{
  "v": "0.2",
  "id": "claude:5f0c…:a91e…#0",
  "ts": "2026-10-07T14:12:43.120Z",
  "provider": "claude",
  "source": "claude/transcript",
  "realm": "trisafe",
  "alter_ego": "claude:5f0c…",
  "agent": null,
  "seq": 128,
  "native": {
    "kind": "assistant/tool_use",
    "body": {"name": "Read", "id": "toolu_01…", "input": {"file_path": "backend/uwb.py"}},
    "truncated": false
  },
  "inner": {"role": "tool", "text": "Read backend/uwb.py"},
  "signal": {"type": "activity", "activity": "READING", "target": "backend/uwb.py"}
}
```

O mesmo momento no Codex chegaria com `native.kind = "item/started:commandExecution"`, o corpo do
item como o Codex o envia e `inner.text = "Get-Content backend/uwb.py"`: o mesmo sinal de mundo, o
vocabulário de cada um.

## 3. `native`

| Campo | Tipo | Descrição |
|---|---|---|
| `kind` | string | Nome nativo, como o provider o chama. Convenção por fonte em §7 |
| `body` | objeto | Corpo nativo, sem renomear campos |
| `truncated` | booleano | `true` se o corpo foi cortado |

Limites: `body` serializado ≤ **16 KiB**; strings dentro dele ≤ **4 KiB** cada. Ao cortar, o
adapter preserva a estrutura (corta valores, não chaves) e marca `truncated`. O conteúdo completo
continua na fonte do provider (transcript/rollout) e pode ser lido sob demanda.

## 4. `inner` — entrada de Inner World

| Campo | Tipo | Descrição |
|---|---|---|
| `role` | `thought` \| `narration` \| `tool` \| `result` \| `prompt` \| `system` | Para o cliente estilizar a linha; o rótulo mostrado é sempre `native.kind` |
| `text` | string | **Texto do provider, sem reescrita** (≤ 4.000 caracteres; cortado com `…`) |
| `fidelity` | `raw` \| `summary` | Só quando `role = thought` |

Regras:

- O Orb **não rastreia quem escreveu**: mensagens com papel de usuário são `prompt`, como o provider as grava.
- Sem texto de pensamento, **não há entrada `thought`**. O adapter nunca preenche lacuna.
- `fidelity: inferred` não existe em `inner`: o que o Orb deduz vai só em `signal`.

## 5. `signal` — sinais de mundo

Vocabulário **fechado**. Um tipo novo exige nova versão do protocolo.

| `type` | Campos | Efeito no mundo |
|---|---|---|
| `session.started` | `cwd?`, `model?`, `title?` | O Alter Ego aparece no Rooftop Room |
| `session.ended` | `reason?` | A sessão terminou; o Alter Ego **não é excluído**: fica na sala enquanto for recente e depois no Histórico do realm (R28) |
| `session.updated` | `title?`, `model?`, `cwd?` | A identidade da sessão mudou (título, modelo); o estado não muda |
| `activity` | `activity`, `target?` | O personagem vai para a área da atividade |
| `idle` | — | Fim do turno; a Team só fica `IDLE` sem subagentes ativos |
| `subagent.started` | `kind?`, `parent?` | Um subagente entra na Team (`agent` do envelope é o id dele) |
| `subagent.ended` | `outcome?` | O subagente se desmobiliza |
| `waiting` | `request`, `action?` | O personagem espera o Lucas (`WAITING`); entra no Gate |
| `waiting.resolved` | `request`, `decision?` | A espera terminou (`approved`, `denied`, `unknown`) |
| `usage` | `input_tokens`, `output_tokens`, `cache_read_tokens?`, `reasoning_tokens?`, `cost_usd?` | Energy |
| `error` | `message`, `recoverable` | O personagem vai a `ERROR` |
| `signal.lost` / `signal.restored` | `since?` | `NO_SIGNAL` (emitido pelo sistema, nunca por adapter) |

### Atividades

`activity` aceita: `THINKING` · `READING` · `RESEARCHING` · `CODING` · `EXECUTING` · `TESTING` ·
`REVIEWING` · `DELEGATING` · `BLOCKED` · `COMPLETED`.

O Core deriva os demais estados: `IDLE` (de `idle`/`session.started`), `WAITING` (pendência
aberta, que **sobrepõe** a atividade), `ERROR` (de `error`) e `NO_SIGNAL` (de `signal.lost`).

| Atividade | Área do Environment |
|---|---|
| `CODING`, `EXECUTING` | Development Center |
| `TESTING` | Testing Lab |
| `READING`, `RESEARCHING` | Research Center |
| `REVIEWING` | Code Review |
| `COMPLETED` | Task Board |
| `DELEGATING` | onde o subagente nasce |

Esta tabela vive **em um só lugar** (`src/orb/core/rules.py`). Mudá-la não toca adapters.

## 6. Ordenação, idempotência e consistência

- **Deduplicação:** o Core descarta eventos cujo `id` já viu (janela limitada por Alter Ego).
- **Ordem:** dentro de um Alter Ego vale `seq`; entre Alter Egos, `ts`.
- **Lacunas:** um salto em `seq` é registrado como degradação, sem travar o fluxo.
- **Reconstrução:** o estado do mundo é reproduzível aplicando o log de eventos na ordem.
- **Snapshot:** ao conectar, o cliente recebe o estado atual do mundo e depois só deltas.

## 7. Fontes nativas por provider

Cada adapter mantém o seu **Mapa do provider** (tabela declarativa em `src/orb/adapters/<p>/mapping.py`).
Resumo; o detalhe e as evidências ficam no documento de cada adapter.

### 7.1 Claude Code ([adapters/CLAUDE.md](adapters/CLAUDE.md))

| Fonte | `native.kind` | `inner` | `signal` |
|---|---|---|---|
| transcript | `user/text` | `prompt` | — |
| transcript | `assistant/text` | `narration` | — |
| transcript | `assistant/thinking` (só com texto) | `thought` · `raw` | `activity: THINKING` |
| transcript | `assistant/tool_use` | `tool` | `activity` pela ferramenta; `Agent`/`Task` → `DELEGATING` |
| transcript | `user/tool_result` | `result` | — |
| transcript | `assistant/usage` | — | `usage` |
| transcript (subagente) | primeira linha de `subagents/agent-<id>.jsonl` | — | `subagent.started` |
| hooks (nível 1) | `PreToolUse`, `PostToolUse`, `PermissionRequest`, `SubagentStart`, `SubagentStop`, `Stop`, `SessionEnd`, `UserPromptSubmit` | conforme o caso | `activity`, `waiting`, `subagent.*`, `idle`, `session.ended` |

### 7.2 Codex ([adapters/CODEX.md](adapters/CODEX.md))

Esquema oficial gerado por `codex app-server generate-json-schema` (0.160.1: 83 notificações, 10
pedidos do servidor). `native.kind` = método, com `:<tipo do item>` para `item/*`.

| `native.kind` | `inner` | `signal` |
|---|---|---|
| `thread/started` | — | `session.started` (ou `subagent.started` se `thread.parentThreadId`) |
| `item/started:userMessage` | `prompt` | — |
| `item/completed:agentMessage` (`phase: commentary`) | `narration` | — |
| `item/completed:agentMessage` (`phase: final_answer`) | `narration` | — |
| `item/completed:reasoning` (`summary` não vazio) | `thought` · `summary` | `activity: THINKING` |
| `item/started:commandExecution` | `tool` | `activity` por `commandActions` ou pela tabela de comandos |
| `item/started:fileChange` | `tool` | `activity: CODING` |
| `item/started:webSearch`, `item/started:mcpToolCall` | `tool` | `activity: RESEARCHING` |
| `item/started:collabAgentToolCall` | `tool` | `activity: DELEGATING` |
| `thread/status/changed` (`active` com `waitingOnApproval`) | — | `waiting` |
| `serverRequest/resolved` | — | `waiting.resolved` |
| `thread/tokenUsage/updated` | — | `usage` |
| `turn/completed` | — | `idle` |
| `error` | `system` | `error` |

Os pedidos do servidor (`item/commandExecution/requestApproval` etc.) são registrados como evento
nativo com `signal: waiting`, e **nunca respondidos** pelo Orb ([ADR 0006](adr/0006-o-orb-nunca-responde-dialogos.md)).

### 7.3 Hermes ([adapters/HERMES.md](adapters/HERMES.md))

Nível 0 pelo `state.db` (SQLite, somente leitura). `native.kind` = `messages/<role>` (`user`,
`assistant`, `assistant.reasoning`, `assistant.tool_call`, `assistant.stop`, `tool`). Subagente =
sessão com `source = subagent`. Sem execução ao vivo ainda.

### 7.4 opencode ([adapters/OPENCODE.md](adapters/OPENCODE.md))

Nível 0 pelo `opencode.db` (SQLite, somente leitura, **só** `session_v2` e `session_message`; o banco
também guarda credenciais). `native.kind` = `session_message/<type>` (`user`, `synthetic`, `system`,
`idle`, `assistant:tool`, `assistant:tool_result`, `assistant:text`, `assistant:reasoning`,
`assistant:usage`). Subagente =
sessão com `parent_id`.

## 8. Validação e erros

- Todo evento é validado na borda (`orb.protocol.validate`). Evento inválido é descartado com
  motivo registrado; nunca entra no Core.
- Campos desconhecidos são ignorados; `signal.type` desconhecido é descartado (o evento nativo
  segue para o Inner World).
- Versão maior desconhecida é rejeitada com erro claro.

## 9. Comandos (cliente → Gateway)

Fluxo inverso, separado dos eventos. Mensagens por WebSocket, validadas na borda
(`orb.gateway.messages`):

| Mensagem | Efeito |
|---|---|
| `{"type":"input","data":"…"}` ou `{"type":"input","data_b64":"…"}` | Escreve no terminal do Inner World (bytes do teclado, ou texto enviado pelo painel/Gate) |
| `{"type":"resize","cols":N,"rows":N}` | Redimensiona o terminal |

Abrir o terminal é a própria conexão (`/ws?realm=…&provider=…&model=…`). **Não existe comando de
aprovação**: aprovar é o Lucas escrevendo no terminal. Futuro: `realm.set_filters` (filtros de LOC).

No canal do mundo (`/world`), o cliente pode pedir o histórico de uma sessão:
`{"type":"feed","alter_ego":"<id>"}`.

## 10. Mensagens (Gateway → cliente)

| `channel` | Conteúdo |
|---|---|
| `term` | Bytes do terminal (texto) |
| `event` | Um evento do protocolo (§2) |
| `world` | Snapshot do mundo (Core) depois de aplicar eventos, com todos os realms observados |
| `feed` | Histórico de linhas de Inner World de uma sessão (`alter_ego`, `events`) |
| `exit` | O processo do terminal terminou |
| `system` | Informação ou erro do Gateway |

## 11. Versionamento

- `0.x`: rascunho, pode mudar sem aviso. A partir de `1.0`, mudança incompatível exige nova versão
  maior e adapters declaram as versões suportadas.
- Adicionar campo opcional não quebra compatibilidade; adicionar `signal.type` quebra (vocabulário
  fechado).

## 12. Em aberto

- Probes (git, CI, LOC): sinais `realm.metrics`, `ci.status`, `git.commit` ainda não definidos.
- Granularidade de `inner` para streaming (deltas de texto agrupados por item ou por intervalo).
- Formato e autorização do canal de comandos além do terminal.
- ~~Sessão retomada/bifurcada: mesmo `alter_ego` ou novo?~~ Decidido (D-068, R39): retomar = o mesmo;
  bifurcar = um novo. Falta confirmar, por provider, como o id muda.
