# The Orb — Adapter: opencode

> O que o opencode expõe e como o Orb o observa sem mexer na configuração do Lucas.
> Código: `src/orb/adapters/opencode/` · Equivalentes: [CLAUDE.md](CLAUDE.md), [CODEX.md](CODEX.md),
> [HERMES.md](HERMES.md).

Última atualização: 2026-10-07 · opencode `2.0.23` (instalado nesta máquina via npm)

## Como isto foi verificado

| Fonte | O que cobre | Confiança |
|---|---|---|
| `opencode --help`, `opencode <sub> --help`, `opencode debug paths` | Flags, subcomandos, pastas | **Alta** |
| Estrutura do `opencode.db` desta máquina: tabelas, colunas, **chaves** dos JSON e contagens (sem ler conteúdo) | Esquema, tipos de mensagem, blocos, ferramentas | **Alta** |
| Adapter rodado sobre o banco real (2026-10-07, só contagens) | 730 eventos, 2 sessões, 20 entradas humanas, **0 inválidos** | **Alta** |
| opencode hospedado ao vivo no Orb; servidor `opencode serve` | — | **Não verificado** |

## 1. Onde fica

`opencode debug paths`: dados em `~/.local/share/opencode` (também no Windows; `XDG_DATA_HOME`
sobrepõe), banco **SQLite `opencode.db`** em modo WAL, logs em `log/`, configuração em
`~/.config/opencode`.

**O banco também guarda credenciais** (`credential`, `account`, `control_account`; e há um
`auth.json` na mesma pasta). O adapter só pode consultar `session_v2` e `session_message`
(`ALLOWED_TABLES`); qualquer outra tabela levanta erro, e há teste verificando que nenhuma consulta
toca credenciais.

## 2. Nível 0: o `opencode.db` (somente leitura) — implementado

| Tabela | Colunas usadas |
|---|---|
| `session_v2` | `id` (`ses_…`), `parent_id` (subagente), `directory` (filtro do realm), `title`, `model`, `agent`, `fork_session_id` |
| `session_message` | `id` (`msg_…`), `session_id`, `type`, `seq`, `time_created`, `time_updated` (ms), `data` (JSON) |

`session_message.type` observado: `user`, `assistant`, `synthetic`, `system`, `idle`. O formato
antigo (`message` + `part`) continua no banco, mas o adapter usa o novo.

**As linhas são reescritas durante o streaming** (194 de 196 linhas tinham `time_updated` depois da
criação): o cursor é `(time_updated, id)` e cada bloco é emitido **uma vez**, quando está pronto:

- ferramenta: ao aparecer (atividade) e de novo quando `state.status` vira `completed`/`error` (resultado);
- texto e raciocínio: só quando a mensagem tem `time.completed` (texto final, não parcial);
- `tokens`/`cost`: uma vez, com a mensagem completa.

### Mapa do provider

| `native.kind` | `inner` | `signal` |
|---|---|---|
| `session_v2` (1ª vez que a sessão aparece) | — | `session.started` (`directory`, `title`) ou `subagent.started` (`agent`) |
| `session_message/user` | `human` · `prompt` (**origem confirmada**) | `human.input` |
| `session_message/synthetic`, `session_message/system` | `agent` · `system` | — |
| `session_message/assistant:tool` (`name`, `state.input`) | `agent` · `tool` | `activity` pela ferramenta |
| `session_message/assistant:tool_result` (`state.content`) | `agent` · `result` | — |
| `session_message/assistant:text` | `agent` · `narration` | — |
| `session_message/assistant:reasoning` | `agent` · `thought` · `raw` | `activity: THINKING` |
| `session_message/assistant:usage` (`tokens.input/output/reasoning/cache.read`, `cost`) | — | `usage` |
| `session_message/idle` (`outcome`) | — | `idle` |

Ferramentas observadas: `read`, `glob`, `grep` → `READING`; `edit`, `write` → `CODING`; `bash` →
classificador de comandos; `todowrite` → `THINKING`; `webfetch`/`websearch` → `RESEARCHING` e
`task` → `DELEGATING` (nomes previstos, ainda não vistos nesta máquina).

**Origem humana confirmada:** diferente do Codex e do Hermes, o próprio opencode separa o que o
Lucas digita (`user`) do que ele injeta (`synthetic`, `system`).

## 3. Sessão = Alter Ego

- `opencode --session <id>` (`-s`): "Session ID to continue, **or to create if it does not
  exist**". Serve para **reabrir** um Alter Ego (`Launch(provider="opencode", session_id="ses_…")`).
  **A verificar:** se aceita um id escolhido pelo Orb para criar uma sessão nova, como o
  `--session-id` do Claude (o formato `ses_…` sugere ids gerados pelo opencode).
- A TUI **não tem flag de modelo** (só `opencode run -m provider/model`); o modelo vem da
  configuração dele. O Orb não passa modelo para o opencode hospedado.
- Hoje o vínculo da sessão hospedada com o Alter Ego vem da pasta (`directory`) + horário.
- `--fork` (em `run`) bifurca; `session_v2.fork_session_id` registra a origem.

## 4. Nível 1: servidor próprio — candidato, não implementado

O opencode 2 roda um **servidor de fundo** (`opencode service`) e a TUI aceita `--server <url>` /
`--standalone`; `opencode serve --port` sobe a API v2 com OpenAPI (`opencode api <operação>`). O
caminho análogo ao do Codex seria: o Orb sobe o **seu próprio** `opencode serve` em loopback, a TUI
hospedada conecta com `--server`, e um observador assina os eventos da API. Falta levantar o canal
de eventos e confirmar que nada muda na configuração do Lucas.

## 5. Diálogos e cuidados

- `--auto` aprova permissões automaticamente: **o Orb nunca usa** ([ADR 0006](../adr/0006-o-orb-nunca-responde-dialogos.md)).
- `opencode upgrade`, `uninstall`, `auth`, `service set`: alteram o ambiente; o Orb nunca os chama.
- Diálogos da TUI na abertura: ainda não levantados (não foi aberta ao vivo).

## 6. `capabilities()`

| Capacidade | Valor |
|---|---|
| Pensamento | Blocos `reasoning` (5 em 2 sessões); `raw` ou resumo conforme o modelo (a confirmar) |
| Aprovações | Tabela `permission` existe, vazia nesta máquina; não mapeada |
| Subagentes | Sim (`session_v2.parent_id`); nenhum observado ainda |
| Origem humana | **Confirmada** (`user` × `synthetic`/`system`) |
| Tempo real | Não (nível 1 a implementar) |
| Tokens / custo | Sim (`tokens`, `cost` por mensagem) |

## 7. Pendências

1. Hospedar o opencode ao vivo no Orb e confirmar o mapa (com o Lucas acompanhando os diálogos).
2. `--session` com id escolhido pelo Orb (vínculo exato sessão ↔ Alter Ego).
3. Nível 1 pelo servidor próprio + `--server`.
4. Aprovações (`permission`) e subagentes ao vivo.
