# Orb IA — AGENT EVENT PROTOCOL

> Contrato único entre Adapters/Probes (quem produz) e Core/Gateway/Clients (quem consome).
> Nada acima dos adapters conhece eventos nativos de Claude, Codex ou Hermes.
> Vocabulário: [CONTEXT.md](CONTEXT.md) · Módulos e fronteiras: [ARCHITECTURE.md](ARCHITECTURE.md).

Versão do protocolo: `0.1` (rascunho) · Última atualização: 2026-10-06

> ⚠️ Rascunho. Os mapeamentos de **Claude Code** e **Codex** (seção 7) foram verificados ao vivo
> e com fixtures reais: ver [ADAPTER-CLAUDE.md](ADAPTER-CLAUDE.md) e
> [ADAPTER-CODEX.md](ADAPTER-CODEX.md). O de **Hermes** veio de uma conversa externa e **não foi
> verificado** (o CLI não está instalado). O protocolo em si é provider-neutro e não depende deles.

---

## 1. Princípios do protocolo

1. **Provider-neutro.** Descreve o que aconteceu no mundo do Orb, não como o provider chama.
2. **Só fatos observados.** Um evento representa algo que foi de fato observado (hook,
   transcript, probe). O que for reconstruído é marcado como `inferred`.
3. **Versionado.** Todo evento declara `schema_version`. Mudança incompatível = nova versão.
4. **Tolerante.** Consumidores ignoram campos desconhecidos; produtores nunca removem campos
   dentro de uma mesma versão maior.
5. **Idempotente e ordenável.** Reentrega e duplicatas não corrompem o estado.

---

## 2. Envelope

Todo evento tem este envelope. `payload` varia por `type`.

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `schema_version` | string | sim | Ex.: `"0.1"` |
| `event_id` | string (UUID/ULID) | sim | Único. Chave de deduplicação |
| `type` | string | sim | Um dos tipos da seção 4 |
| `timestamp` | string (ISO 8601 com fuso) | sim | Momento em que **ocorreu** (não o de recebimento) |
| `received_at` | string (ISO 8601) | não | Preenchido pelo Gateway ao receber |
| `source` | objeto | sim | Quem produziu o evento (seção 3) |
| `realm` | string | sim | Id do realm (projeto) |
| `alter_ego` | string \| null | sim | Id do Alter Ego; `null` para eventos de realm/mundo |
| `session` | string \| null | sim | Id da sessão do provider |
| `parent` | string \| null | não | `alter_ego` pai, quando for subagente |
| `seq` | inteiro | sim | Sequência crescente **por sessão**, definida pelo produtor |
| `payload` | objeto | sim | Dados específicos do tipo |
| `fidelity` | enum | só em `thought` | `raw` \| `summary` \| `inferred` |

### Exemplo

```json
{
  "schema_version": "0.1",
  "event_id": "01J9ZK3T8Q6V0W4R2M7N5B1C9D",
  "type": "tool.started",
  "timestamp": "2026-10-06T18:12:43-03:00",
  "source": { "kind": "adapter", "name": "claude", "version": "0.1.0" },
  "realm": "trisafe",
  "alter_ego": "atlas",
  "session": "ses_92f1",
  "parent": null,
  "seq": 128,
  "payload": {
    "tool": "edit",
    "category": "write",
    "target": "backend/services/uwb.py"
  }
}
```

---

## 3. `source`

| Campo | Valores |
|---|---|
| `kind` | `adapter` (provider) · `probe` (git/CI/LOC) · `terminal` (terminal host) · `system` |
| `name` | `claude` · `codex` · `hermes` · `git` · `github` · `ci` · `loc` · … |
| `version` | Versão do produtor (adapter/probe), não do CLI |
| `provider_version` | *(opcional)* Versão do CLI observado, para depurar mudanças de formato |

---

## 4. Tipos de evento

Convenção de nome: `domínio.ação` em minúsculas.

### 4.1 Ciclo de vida do Alter Ego

| Tipo | Quando | `payload` principal |
|---|---|---|
| `agent.spawned` | Alter ego/subagente passa a existir | `role`, `provider`, `model?`, `mission?` |
| `agent.state_changed` | Estado universal mudou | `state`, `previous_state?`, `reason?` |
| `agent.idle` | Sem atividade | — |
| `agent.retired` | Subagente concluiu e foi desmobilizado | `outcome` (`completed`\|`failed`\|`cancelled`) |
| `session.started` / `session.ended` | Sessão do provider | `cwd?`, `reason?` |

### 4.2 Trabalho

| Tipo | Quando | `payload` principal |
|---|---|---|
| `task.started` / `task.completed` / `task.blocked` / `task.failed` | Tarefa/missão | `task_id`, `title?`, `reason?` |
| `tool.started` / `tool.completed` / `tool.failed` | Uso de ferramenta | `tool`, `category`, `target?`, `duration_ms?`, `error?` |
| `file.read` / `file.edit` / `file.created` / `file.deleted` | Arquivo | `path` |
| `command.started` / `command.completed` | Comando de shell | `command`, `exit_code?` |
| `test.started` / `test.passed` / `test.failed` | Testes | `suite?`, `passed?`, `failed?` |
| `research.started` / `research.completed` | Busca/pesquisa | `query?`, `source?` |
| `review.started` / `review.completed` | Revisão | `scope?`, `verdict?` |

`category` (de `tool.*`) é a classificação universal, usada para decidir a área do Environment:
`read` · `write` · `execute` · `test` · `research` · `review` · `delegate` · `other`.

### 4.3 Inner World

| Tipo | Quando | `payload` principal |
|---|---|---|
| `thought` | Raciocínio/narração observável | `text`, `kind` (`reasoning`\|`plan`\|`narration`\|`decision`) |
| `plan.updated` | Plano ou lista de passos mudou | `steps[]` (`text`, `status`) |

`thought` exige `fidelity`. Ver seção 6.

### 4.4 Interação

| Tipo | Quando | `payload` principal |
|---|---|---|
| `approval.requested` | Agente aguarda decisão humana | `request_id`, `action`, `target?` |
| `approval.resolved` | Decisão tomada | `request_id`, `decision` (`approved`\|`denied`\|`expired`) |
| `intrusive_thought` | O Lucas plantou um pensamento no alter ego (prompt, interrupção, comando) | `text`, `kind` (`prompt`\|`interrupt`\|`command`), `channel` (`terminal`\|`panel`\|`gate`) |
| `agent.message` | Mensagem do agente ao usuário | `text` |
| `error` | Erro observado | `code`, `message`, `recoverable` |

`intrusive_thought` é o evento do vocabulário "usar um CLI" (ver CONTEXT.md). Regras:
- É emitido quando o prompt é **submetido** (via hook ou transcript), não a cada tecla.
- **Só quando a origem é humana.** O hook `UserPromptSubmit` do Claude também dispara para
  prompts do sistema (ex.: `<task-notification>` quando um subagente termina). O adapter só
  emite `intrusive_thought` se o transcript confirma origem humana (sem `origin`, ou
  `origin.kind: human`); prompts do sistema não viram intrusive thought (verificado no Spike 3).
- `channel` diz por onde entrou: `terminal` (digitado na TUI), `panel` (enviado pelo painel
  do realm) ou `gate` (enviado do Gate). `panel` e `gate` usam `terminal.write`: nunca há
  canal paralelo ao CLI.
- Não carrega `fidelity`: é texto do humano, fato observado, não reconstrução.
- No Inner World é exibido na mesma linha do tempo dos `thought`, marcado como externo.

### 4.5 Fatos do mundo real (Probes)

| Tipo | Quando | `payload` principal |
|---|---|---|
| `git.commit` | Commit criado | `sha`, `message`, `files_changed` |
| `git.branch_changed` | Branch mudou | `from`, `to` |
| `pr.opened` / `pr.merged` / `pr.reviewed` | Pull request | `number`, `url`, `state` |
| `ci.started` / `ci.passed` / `ci.failed` | Pipeline | `run_id`, `url`, `failed_jobs?` |
| `realm.metrics_updated` | LOC recalculado | ver 4.6 |

Probes têm `alter_ego: null` salvo quando atribuíveis a um agente.

### 4.6 `realm.metrics_updated`

Alimenta a altura do prédio.

```json
{
  "type": "realm.metrics_updated",
  "payload": {
    "loc": 48213,
    "by_extension": { ".py": 31200, ".gd": 9100, ".md": 7913 },
    "ignored_by": "gitignore",
    "filters": { "include_md": false },
    "computed_over_ref": "a1b2c3d"
  }
}
```

`.gitignore` é sempre aplicado. O Core decide a altura a partir de `loc` e dos filtros ativos.

### 4.6b Camadas vivas

Eventos que alimentam as camadas visuais. Todos são **observação**: nenhum altera projeto ou modelo.

| Tipo | Quando | `payload` principal |
|---|---|---|
| `usage.reported` | Consumo de tokens/custo observado (Energy) | `input_tokens`, `output_tokens`, `cache_read_tokens?`, `cost_usd?`, `model?` |
| `realm.structure_updated` | Estrutura de módulos mudou (andares) | `modules[]` (`name`, `path`, `loc`) |
| `archive.snapshot` | Foto do que molda o agente (Archive) | `sources[]` (`kind`: `instructions`\|`memory`\|`skill`\|`context`, `path`, `size`, `modified_at`) |

Notas:
- `archive.snapshot` carrega **metadados**, não conteúdo (privacidade por padrão).
- **Janelas acesas:** derivadas de `file.edit`/`file.created` por módulo, sem evento próprio.
- **Weather:** derivado de `ci.*` e `test.*`.
- **Gate:** visão derivada de `approval.requested` sem `approval.resolved`; o envio de prompts
  usa `terminal.write` e vira `intrusive_thought` com `channel: gate`.
- **Team:** agrupamento derivado do campo `parent` do envelope; sem evento próprio.
- **Chronicle:** o próprio log de eventos, reproduzido; sem evento próprio.

### 4.7 Saúde do sistema

| Tipo | Quando | `payload` principal |
|---|---|---|
| `adapter.connected` / `adapter.disconnected` | Estado de um adapter | `name`, `reason?` |
| `adapter.degraded` | Adapter operando com limitações | `name`, `missing[]` |
| `signal.lost` / `signal.restored` | Sem dados de um alter ego | `since?` |

`signal.lost` faz o alter ego aparecer como **"sem sinal"**, nunca com estado inventado.

---

## 5. Estados universais

Valores permitidos em `agent.state_changed.payload.state`:

`IDLE` · `THINKING` · `READING` · `RESEARCHING` · `CODING` · `EXECUTING` · `TESTING` ·
`REVIEWING` · `DELEGATING` · `WAITING` · `BLOCKED` · `ERROR` · `COMPLETED`

Mais um estado **derivado pelo Core** (não emitido por adapters): `NO_SIGNAL`, resultado de
`signal.lost`.

### Categoria → estado → área do Environment

| `tool.category` | Estado | Área (Rooftop Room) |
|---|---|---|
| `read` | `READING` | Research Center |
| `write` | `CODING` | Development Center |
| `execute` | `EXECUTING` | Development Center |
| `test` | `TESTING` | Testing Lab |
| `research` | `RESEARCHING` | Research Center |
| `review` | `REVIEWING` | Code Review |
| `delegate` | `DELEGATING` | origem do subagente |
| conclusão de `task.*` | `COMPLETED` | Task Board |

Esta tabela é **dado**, mantida em um único lugar no Core. Mudar a regra não toca adapters.
Pendências (`approval.requested` sem `resolved`) sobrepõem o estado como `WAITING`.

---

## 6. Fidelity do pensamento

| Valor | Significado | Pode ser mostrado como pensamento? |
|---|---|---|
| `raw` | Texto de raciocínio exposto pelo provider, sem alteração | Sim |
| `summary` | Resumo de raciocínio fornecido pelo provider | Sim, indicado como resumo |
| `inferred` | Reconstruído pelo Orb a partir de ações observadas | **Não** como pensamento real; rotulado como inferência |

Regras:
- O adapter declara, em `capabilities()`, o melhor `fidelity` que consegue entregar.
- O adapter **nunca promove** um `fidelity` (não rotula `inferred` como `summary`).
- Sem sinal de pensamento, **não se emite `thought`**. Ausência é válida e visível na UI.

---

## 7. Mapeamento de eventos nativos (Claude e Codex verificados; Hermes não)

Cada adapter mantém sua própria tabela declarativa; o protocolo só exige o resultado.
Exemplos **ilustrativos**, ainda não confirmados contra as docs:

| Origem | Evento nativo | Evento do protocolo |
|---|---|---|
| Claude | `PreToolUse` | `tool.started` |
| Claude | `PostToolUse` | `tool.completed` |
| Claude | `SubagentStart` | `agent.spawned` (com `parent`) |
| Claude | `SubagentStop` | `agent.retired` (traz `agent_transcript_path`; verificado) |
| Claude | `PermissionRequest` | `approval.requested` (`approval.resolved` é deduzido, sem hook próprio) |
| Claude | `UserPromptSubmit` | `intrusive_thought` |
| Claude | `Stop` | `agent.idle` |
| Hermes | `pre_tool_call` / `post_tool_call` | `tool.started` / `tool.completed` |
| Hermes | `subagent_start` / `subagent_stop` | `agent.spawned` / `agent.retired` |
| Hermes | `kanban_task_blocked` | `task.blocked` |
| Codex | `thread/started` | `session.started` |
| Codex | `item/started` `commandExecution` | `tool.started` (`category` deduzida do comando; ver ADAPTER-CODEX.md §3) |
| Codex | `item/completed` `commandExecution` | `tool.completed` |
| Codex | `item/started` `userMessage` | `intrusive_thought` |
| Codex | `item/*` `agentMessage` (`phase`: `commentary` / `final_answer`) | `agent.message` |
| Codex | `item/*` `reasoning` com `summary` não vazio | `thought` com `fidelity: summary` |
| Codex | `thread/tokenUsage/updated` | `usage.reported` |
| Codex | ServerRequest `item/*/requestApproval` | `approval.requested` |
| Codex | `serverRequest/resolved` | `approval.resolved` |
| Codex | `turn/completed` / `thread/status/changed` `idle` | `agent.idle` |

Os mapeamentos reais virão de **fixtures gravadas** de cada CLI (ver ARCHITECTURE.md §6).

---

## 8. Ordenação, idempotência e consistência

- **Deduplicação:** o consumidor descarta eventos com `event_id` já visto.
- **Ordem:** dentro de uma sessão, `seq` define a ordem; entre sessões, vale `timestamp`.
- **Lacunas:** salto em `seq` gera `adapter.degraded` com `missing`, sem travar o fluxo.
- **Reconstrução:** o estado do mundo deve ser reproduzível aplicando o log de eventos na
  ordem, mais os fatos dos probes.
- **Snapshot:** ao conectar, o Gateway envia o estado atual por alter ego, e depois só deltas.

---

## 9. Validação e erros

- Evento que não valida contra o schema é **descartado** e registrado
  (`code`, `source`, motivo), sem entrar no Core.
- Campos desconhecidos são ignorados; tipos desconhecidos são registrados e ignorados.
- Versão maior desconhecida é rejeitada com erro claro.

---

## 10. Comandos (cliente → Orb)

Fluxo inverso, separado dos eventos. Rascunho para a camada de controle:

| Comando | Efeito |
|---|---|
| `terminal.open` | Abre um terminal no realm para um alter ego/provider |
| `terminal.write` | Escreve no terminal (base do "enviar mensagem pelo painel"); resulta em `intrusive_thought` com `channel: panel` quando o prompt é submetido |
| `terminal.close` | Encerra o terminal |
| `approval.resolve` | Responde a um `approval.requested`. **Implementado apenas como `terminal.write` no terminal do Alter Ego** (princípio 10: único canal de escrita); sem canal paralelo ao CLI |
| `realm.set_filters` | Altera filtros de LOC (ex.: incluir `.md`) |

Detalhes (autenticação, confirmação, auditoria) ficam em aberto.

---

## 11. Versionamento

- `0.x`: rascunho, pode mudar sem aviso. A partir de `1.0`, mudança incompatível exige
  incremento de versão maior, e adapters declaram as versões que suportam.
- Adicionar tipo de evento ou campo opcional não quebra compatibilidade.

---

## 12. Decisões em aberto

- Modelo de **sessão**: título, retomada (`resume`), bifurcação (`fork`) e sessões simultâneas
  por Alter Ego. Hoje o envelope só carrega `session` como id; falta um evento/atributo para
  título e relação entre sessões (ver ADAPTER-CLAUDE.md §5).
- Formato de `event_id` (UUIDv7 vs ULID).
- Granularidade de `thought` (por bloco, por parágrafo, por delta de streaming).
- Representação de `plan.updated` entre providers com formatos de plano muito diferentes.
- Formato do canal de comandos e política de autorização.
- Schema formal (JSON Schema vs Pydantic como fonte única, gerando o outro).
