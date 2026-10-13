# The Orb — Adapter: Hermes Agent

> O que o Hermes Agent expõe e como o Orb o observa sem mexer na configuração do Lucas.
> Código: `src/orb/adapters/hermes/` · Equivalentes: [CLAUDE.md](CLAUDE.md), [CODEX.md](CODEX.md).

Última atualização: 2026-10-13 · Hermes Agent `0.20.5` (instalado nesta máquina em
`%LOCALAPPDATA%\hermes`, instalação por git; mesma versão em 2026-10-13)

## Como isto foi verificado

| Fonte | O que cobre | Confiança |
|---|---|---|
| **Código-fonte** do Hermes 0.20.5 (`%LOCALAPPDATA%\hermes\hermes-agent`), lido sem executar o agente | Hooks, servidores, esquema do `state.db`, sessões, subagentes, aprovações, diálogos | **Alta** para o código lido (citações de arquivo:linha abaixo) |
| `hermes --help`, `hermes sessions/serve/acp --help` | Flags | **Alta** |
| Adapter de nível 0 rodado sobre o `state.db` real desta máquina, **só contagens** (2026-10-07) | 1.528 eventos em 20 sessões, **0 inválidos**; `mode=ro` funciona com o banco em WAL no Windows; `finish_reason = "stop"` existe | **Alta** |
| `state.db` real, **só estrutura e contagens** (2026-10-13, ticket 02): colunas de raciocínio, contagens por modelo e relação entre o tamanho do texto e os tokens de saída | Fidelidade do pensamento (§1) | **Alta** para o modelo observado; **dúvida** para os outros |
| Hermes rodando ao vivo com o Orb | — | **Não verificado** |

Não foram lidos `config.yaml`, memórias, nem o conteúdo de sessões (privacidade). Por isso não se
sabe, por exemplo, se o Lucas já tem hooks ou webhooks configurados.

---

## 1. Nível 0: o `state.db` (somente leitura) — implementado

- Banco SQLite em `<HERMES_HOME>\state.db` (padrão no Windows: `%LOCALAPPDATA%\hermes`; `HERMES_HOME`
  sobrepõe), modo WAL (`state.db-wal`, `-shm`). Esquema versão 26 (`hermes_state_common.py:329`).
- **Conexão `file:...state.db?mode=ro`.** Nunca instanciar o `SessionDB()` do Hermes: o construtor
  roda DDL e migrações (`hermes_state.py:3753-3755`).
- `messages.id` é AUTOINCREMENT: o adapter lê `id > último visto`, em lotes de 500, e começa do fim
  (sem `replay`). O assistente grava a chamada de ferramenta **antes** de executá-la, então os dados
  aparecem durante o turno.
- **Reescritas acontecem:** `/retry`, `/undo`, `/compress` e compactação marcam `active = 0` ou
  apagam e reinserem. O adapter ignora linhas inativas.
- As colunas são descobertas com `PRAGMA table_info` (o esquema muda entre versões).

| Tabela | Colunas usadas |
|---|---|
| `sessions` | `id`, `source` (`cli`, `subagent`, …), `model`, `parent_session_id`, `cwd`, `title`, `end_reason`, `model_config` (`_delegate_from`, `_branched_from`) |
| `messages` | `id`, `session_id`, `role` (`user`/`assistant`/`tool`), `content`, `tool_calls` (JSON `{id, function:{name, arguments}}`), `tool_name`, `timestamp`, `finish_reason`, `reasoning`, `active` |

### Mapa do provider

| `native.kind` | `inner` | `signal` |
|---|---|---|
| `messages/user` | `prompt` | — |
| `messages/assistant.reasoning` (`reasoning` com texto) | `thought` · `raw` ou `summary` (ver fidelidade abaixo) | `activity: THINKING` |
| `messages/assistant` (`content`) | `narration` | — |
| `messages/assistant.tool_call` (um por item de `tool_calls`) | `tool` | `activity` por palavra-chave do nome da ferramenta; `terminal` pelo classificador de comandos |
| `messages/tool` | `result` | — |
| `messages/assistant.stop` (`finish_reason = "stop"`, líder) | — | `idle` |

- **Índice (ticket 03):** `StateDbIndex` faz uma consulta à tabela `sessions` (`cwd`, `git_repo_root`, `title`,
  `model`, `started_at`, `last_activity_at`, `source`, `parent_session_id`), sem tocar em `messages`. `git_repo_root`,
  a raiz do projeto que o próprio Hermes informa, vem vazio em todas as sessões desta máquina; quando vier, vence a
  subida até o repositório git. Sessão sem `cwd` fica de fora. A abertura (`session.started`) leva a hora da
  mensagem que revelou a sessão (D-128).
- **Subagente** = sessão com `source = "subagent"` e `parent_session_id` (`tools/delegate_tool.py:1942-1989`).
  `parent_session_id` também é usado por compactação e `/branch`: esses **não** são subagentes.
- A tabela de ferramentas é **heurística por palavra-chave** (`delegate`/`subagent` → `DELEGATING`,
  `web`/`browser`/`mcp` → `RESEARCHING`, `write`/`patch`/`edit` → `CODING`, `read`/`search_files`
  → `READING`), porque a lista completa de ferramentas ainda não foi levantada.
- **Fidelidade do `reasoning` (R14, ticket 02).** O adapter marca `summary` quando a linha traz
  `codex_reasoning_items` com um item `reasoning` (itens da Responses API: resumo mais blob cifrado, o
  mesmo formato dos rollouts do Codex; o blob não vai no evento nativo) e `raw` nos demais casos.
  **Confirmado pela estrutura no `state.db` desta máquina (2026-10-13), num único modelo,
  `nvidia/nemotron-3-ultra-550b-a55b`:** 484 mensagens do assistente, 476 com `reasoning` (19 sessões);
  `reasoning_content` igual a `reasoning` em 476 de 476; `reasoning_details`, `codex_reasoning_items` e
  `codex_message_items` vazios em todas; `sessions.reasoning_tokens` é 0 (o provedor não informa o
  raciocínio à parte). Como não há esse número, a prova vem do total: raciocínio + resposta + argumentos
  das ferramentas dão 4,29 caracteres por token de saída (de 3,46 a 7,2 nas 15 sessões com mais de 1.000
  tokens), faixa de texto comum e sem folga para raciocínio escondido. Logo o texto guardado é a cadeia
  inteira: `raw`.
- **Dúvidas registradas** (não verificáveis aqui; decididas em D-126 e D-127):
  1. `codex_reasoning_items` nunca apareceu nos dados reais: a regra `summary` vem do código do Hermes
     (`agent/codex_responses_adapter.py`) e do formato dos rollouts do Codex (§4 de [CODEX.md](CODEX.md)).
  2. Modelos OpenAI gpt-5.x pelo caminho de chat (ex.: Nous Portal) entregam o resumo em
     `reasoning_content`, sem `codex_reasoning_items` (`agent/reasoning_summaries.py`): o adapter os
     marcaria `raw`, e a estrutura da linha não permite distinguir. Antes de criar uma tabela por modelo,
     observar uma sessão real com esse modelo (tamanho do texto × tokens de saída).
  3. Anthropic (blocos `thinking` em `reasoning_details`, `agent/transports/anthropic.py`): sem marcador
     estrutural; o adapter marca `raw` sem confirmação.
  4. Na Responses API, o texto de mensagens de fase `commentary`/`analysis` também entra em `reasoning`
     (`agent/codex_responses_adapter.py`, por volta da linha 1516) e `item.text` serve de alternativa ao
     resumo (por volta da linha 1328): nesses casos a coluna não é só resumo do raciocínio. A linha com
     `codex_reasoning_items` fica `summary` (o mais próximo), mas pode conter narração.

## 2. Nível 1: eventos em tempo real — ainda não implementado

| Caminho | Como | Avaliação |
|---|---|---|
| **Sidecar da TUI** | `HERMES_TUI_SIDECAR_URL=ws://…` ao lançar `hermes --tui`: a TUI copia cada frame JSON-RPC para esse WebSocket, sem bloquear (`tui_gateway/entry.py:49-65`). Eventos `message.*`, `thinking.delta`, `reasoning.*`, `tool.*`, `approval.request`, `subagent.*`, `session.*`, `error` | **Melhor candidato**: por lançamento, sem mudar configuração. Só funciona com `--tui` (o padrão do CLI é a interface clássica) |
| Hooks de plugin / shell / webhooks de saída | `config.yaml` ou plugins em `HERMES_HOME` | **Descartado**: exigem mudar a configuração; não há flag de injeção por sessão |
| `HERMES_MANAGED_DIR` | Sobreposição administrativa de `config.yaml` | **Descartado**: é semântica de política de TI e substitui listas do Lucas |
| `hermes acp`, servidor de API, dashboard | O Orb teria de ser o cliente que conduz a conversa, ou exige autenticação | Não serve para observar |

Hooks que **mudam o agente** e que um observador nunca pode usar: `pre_tool_call` (bloquear/
modificar), `pre_llm_call` (injeta contexto), `pre_verify`, `transform_*`, `pre_gateway_dispatch`,
`pre_transcription`.

## 3. Sessão = Alter Ego

- **Não há flag para escolher o id** de uma sessão nova (o CLI gera `AAAAMMDD_HHMMSS_<6hex>`).
  Alternativas: `--source <tag>` (vai para `sessions.source`), `-c/--continue <nome>` com
  `--create-if-missing` (cria com título). No modo Hospedar, o vínculo vem de `cwd` + horário, ou de
  um `--source` próprio do Orb (a decidir).
- **Reabrir:** `--resume/-r <id|título|latest>`.
- `/branch` cria uma sessão filha com `_branched_from`.

## 4. Diálogos com efeito (o Orb nunca responde — ADR 0006)

| Diálogo | Padrão | Efeito |
|---|---|---|
| Primeira execução sem provider: "Run setup now? [Y/n]" | **Sim** | Roda o assistente de configuração (grava config) |
| Consentimento de shell hooks "[y/N]" | Não | "yes" grava a allowlist |
| Guarda de custo/política do modelo "[y/N]" | Não | — |
| Aprovação de comando perigoso: `once` / `session` / `always` / `deny` | Nega no timeout (300 s) | `always` grava `command_allowlist` no `config.yaml` |

Observações: o aviso de atualização é só informativo; não há diálogo de confiança de diretório.
Rodar o Hermes por si só já pode gravar `onboarding.seen.*` no `config.yaml`: isso é do Hermes, não
do Orb.

## 5. `capabilities()`

| Capacidade | Valor |
|---|---|
| Pensamento | Coluna `reasoning`: `summary` com `codex_reasoning_items`, `raw` no resto; confirmado só no modelo observado (§1) |
| Aprovações | Não registradas no banco (só o texto do resultado); nível 1 traria `approval.request` |
| Subagentes | Sim (`source = subagent` + `parent_session_id`) |
| Tempo real | Não (nível 1 a implementar pelo sidecar da TUI) |
| Tokens | Totais por sessão nas colunas de `sessions` (ainda não lidos pelo adapter) |

## 6. Pendências

1. Rodar o Hermes hospedado no Orb e confirmar o mapa ao vivo (com o Lucas acompanhando os diálogos).
2. Nível 1 pelo `HERMES_TUI_SIDECAR_URL` (só `--tui`).
3. Lista completa de ferramentas.
4. Vínculo sessão hospedada ↔ Alter Ego sem flag de id (`--source`?).
5. Tokens/custo por sessão (Energy).
6. Fidelidade do pensamento nos modelos ainda não observados (§1, dúvidas 1 a 3).
