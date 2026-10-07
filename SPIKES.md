# Orb IA — SPIKES

> Resumo executivo dos 4 spikes de validação (2026-10-06): o que cada um perguntou, o que
> descobriu, o que mudou no desenho e o que continua em aberto. É o **índice dos resultados**;
> os detalhes e as evidências de cada um estão nos documentos linkados.
> Plano e riscos: [MVP.md](MVP.md) · Visão: [CONTEXT.md](CONTEXT.md).

Última atualização: 2026-10-07

**Spike** = experimento curto e descartável, feito para responder uma pergunta técnica antes de
investir no produto. O código vive em `spikes/` e **não é a base final** (o mapa de onde cada peça
será promovida está em [ARCHITECTURE.md](ARCHITECTURE.md) §7).

## Veredito

**Todos os riscos que podiam inviabilizar o projeto foram respondidos de forma positiva**, com
restrições que mudaram o desenho em alguns pontos. A tese se sustenta: dá para abrir o CLI real de
uma IA dentro do Orb, usar normalmente e observar o que ela faz em tempo real, sem alterar o
agente.

| Spike | Risco | Resultado | Código | Detalhes |
|---|---|---|---|---|
| **1 — Terminal Host** | R1, R2 | ✅ Validado | `spikes/01-terminal-host/` | [MVP.md](MVP.md) §6 |
| **2 — Terminal no Godot** | R3 | ✅ Validado | `spikes/02-terminal-godot/` | [MVP.md](MVP.md) §7 |
| **3 — Hooks do Claude ao vivo** | R4 | ✅ Validado, com restrição | `spikes/03-live-hooks/` | [MVP.md](MVP.md) §8, [ADAPTER-CLAUDE.md](ADAPTER-CLAUDE.md) §6 |
| **4 — Codex** | R5 | ✅ Validado, com restrições (Hermes pendente) | `spikes/04-codex/` | [MVP.md](MVP.md) §9, [ADAPTER-CODEX.md](ADAPTER-CODEX.md) |

---

## Spike 1 — Terminal Host ✅

**Pergunta:** dá para abrir um terminal real controlado pelo Orb, chamar o CLI do agente dentro
dele e observá-lo, no Windows?

**Resultado**
- A TUI real do `claude` roda hospedada numa pseudo-console (ConPTY): cores, redimensionamento,
  teclado e encerramento.
- Os eventos chegam ao painel em **~270–470 ms** lendo o transcript (nível 0, nada instalado).
- O terminal é um **PowerShell real** e o CLI é chamado dentro dele, **escolhido pelo modelo** do
  Alter Ego (`claude-*` → `claude`, `gpt-*` → `codex`). Nenhuma TUI criada do zero.
- 15 testes automatizados.

**Achados que mudaram o desenho**
1. O Orb atribui `--session-id` e `-n` ao `claude` que hospeda: assim sabe qual transcript é dele
   (sem isso o tail confundia sessões da mesma pasta).
2. Marcadores de ambiente herdados do Claude Code mudam o comportamento do filho (ele deixava de
   gravar transcript). O Orb os remove e preserva a configuração do usuário.
3. Um terminal por WebSocket é um shell exposto: exige loopback, token, checagem de `Origin` e
   lista fixa de executáveis.

---

## Spike 2 — Terminal no Godot ✅

**Pergunta:** o terminal funciona dentro do Godot, inclusive como tela de um monitor 3D?

**Resultado**
- O addon `godot-xterm` roda no Windows (ConPTY) com o PowerShell e o `claude` reais, com cores
  e redimensionamento.
- O terminal funciona como **monitor 3D**: `SubViewport` projetado num quad em perspectiva, com o
  teclado encaminhado e comando digitado executando.
- O Godot exibe os bytes de um **Terminal Host em Python** por WebSocket (ciclo completo
  verificado, mesmo com o stdio do Godot redirecionado).

**Decisão:** o Terminal Host continua em Python e o Godot **só exibe**. Um único host serve a
página web e o Godot, e evita a limitação do ConPTY com stdio redirecionado (o PTY dentro do
Godot só funciona se ele for aberto sem redirecionar stdin/stdout).

**Achados**
- **Bug de robustez no servidor, achado e corrigido:** uma mensagem malformada derrubava a
  sessão inteira. Agora cada mensagem é validada na borda e descartada com o motivo.
- O `JSON.stringify` do Godot não escapa caracteres de controle: a entrada vai em base64.
- Glifos de caixa e bloco (`─ █`) saem com espaços entre as células: cosmético, causa no addon.

**Não provado:** clique do mouse no monitor 3D; desempenho com vários monitores (testado com um,
numa GPU modesta).

---

## Spike 3 — Hooks do Claude ao vivo ✅ (com restrição)

**Pergunta:** os hooks funcionam sem tocar na configuração do Lucas e sem atrapalhar o agente?

**Resultado**
- **Funcionam por sessão** com `claude --settings <arquivo>`: o `settings.json` do Lucas não é
  alterado.
- Chegam também na **TUI hospedada**, e o `session_id` bate com o `--session-id` do Orb.
- **Subagentes:** `SubagentStart`/`SubagentStop` chegam e as ações de dentro vêm com `agent_id` e
  `agent_type`; o `SubagentStop` traz o caminho do transcript do subagente.
- `PermissionRequest` chega (a decisão do usuário continua sem hook; o Orb a deduz).
- Foram gravadas fixtures reais de cada evento.

**Achados que mudaram o desenho**
1. **Os resumos das docs tinham campos errados** (`tool_response`, não `tool_output`; sem
   `is_background`/`is_continuation`). Vale a fixture real, não o resumo.
2. **`UserPromptSubmit` não é sempre o Lucas:** prompts do sistema (`<task-notification>`) também
   passam por ele. O transcript distingue (`origin.kind`); o `intrusive_thought` só nasce quando a
   origem é humana.
3. **`Stop` do agente principal não encerra a Team:** a ferramenta `Agent` roda de forma
   assíncrona e o subagente pode estar rodando.

**A restrição: um Orb travado atrasa o agente** (princípio de não interferência):

| Receptor | Hook | Tempo | Efeito |
|---|---|---|---|
| Vivo | `http` | ~7,5 s | referência |
| Fora do ar | `http` | ~6,7 s | nenhum |
| **Travado** | `http`, timeout 2 s | **21,5 s** | +14 s |
| Travado | `http` + `async` | 20,5 s | `async` não ajuda em `http` |
| Travado | `command` async + `curl` | 10,5 s | ~+3 s |

Mitigação: receptor mínimo e sempre responsivo, transporte por `command` assíncrono, e **nível 0
como padrão** (hooks são um acréscimo opcional).

**Não provado:** vários eventos que não foram provocados (`TaskCreated/Completed`,
`Notification`, `PostToolUseFailure`, `PermissionDenied`, `Pre/PostCompact` e outros); hooks no
app Desktop e em sessões iniciadas fora do Orb.

---

## Spike 4 — Codex ✅ (com restrições)

**Pergunta:** o que o Codex expõe e como o Orb o observa sem tocar na configuração do Lucas?

**Resultado**
- O Codex tem **protocolo oficial em tempo real** (JSON-RPC por WebSocket, `codex app-server`); o
  próprio CLI gerou o esquema: 75 tipos de notificação e 10 pedidos do servidor.
- **Observação sem alterar nada:** o Orb sobe o **seu próprio app-server** em loopback e a TUI
  nativa se conecta com `codex --remote`. Um segundo cliente, depois de `thread/resume`, recebeu
  **159 de 169** notificações de uma sessão viva, e o turno do outro cliente terminou normalmente.
  Thread efêmera não pode ser observada.
- **Pensamento melhor que o Claude:** ~42% dos blocos de raciocínio têm texto (6.064 de 14.278),
  sempre como `summary`, nunca `raw` (Claude: ~12%).
- **Aprovações:** existem como pedidos do servidor e há notificação de resolução (melhor que no
  Claude, onde é deduzido).
- **Hooks do Codex não servem** como nível 1: só `command`/`mcp_tool`, exigem confiança do
  usuário e não há injeção por sessão. O app-server ocupa esse lugar.

**Achados que mudaram o desenho**
1. O Codex **não tem ferramenta `Read`**: ler arquivo é um comando de PowerShell (`Get-Content`).
   O adapter precisa de uma tabela declarativa que classifica comandos.
2. O modelo padrão do `config.toml` do Lucas (`gpt-6-luna`) **não é aceito** com conta ChatGPT; os
   modelos reais são `gpt-5.6-sol`, `terra` e `luna`. O Orb deve passar o modelo explicitamente.
3. A TUI abre com **diálogos cujo padrão tem efeito** (atualizar, confiar no diretório, confiar
   nos hooks). Daí a regra abaixo.

**Não provado:** uma conversa completa na TUI ligada ao app-server do Orb (os diálogos de abertura
são decisão do Lucas); subagentes e hooks ao vivo no Codex; **o que o servidor faz com um
observador que ignora um pedido de aprovação**; o **Hermes** (o CLI não está instalado).

### Incidentes do Spike 4 (registrados com transparência)

Ao automatizar a TUI do Codex, o script **enviou teclas às cegas** duas vezes:

1. O Enter aceitou **"Update now"** e disparou o instalador oficial, que **falhou sem efeito**: a
   versão segue 0.149.0 e `codex doctor` confirma. Ficou só uma pasta de staging vazia
   (`~/.codex/packages/standalone/releases/.staging.0.160.1-…`).
2. Um prompt foi digitado com a **revisão de hooks** aberta ("Press t to trust all"). O
   `config.toml` não mudou e a tela ainda mostrava 0 hooks confiados; tudo indica que **nada foi
   confiado**, mas a TUI foi encerrada à força e não há prova de 100%.
3. Foi criada **1 sessão de teste** no histórico do Codex (`01a11443-9c62-7a23-b900-b05f7dc17dd4`).

**Pendências para o Lucas:** conferir no Codex se a revisão de hooks segue pendente; decidir se
apaga a pasta de staging vazia e a sessão de teste.

---

## Regras que os spikes criaram

| # | Regra | Origem |
|---|---|---|
| 1 | **O Orb nunca responde diálogos do Lucas** (atualização, confiança de diretório/hooks, aprovações) e **nunca envia teclas a uma TUI sem a tela verificada** | Spike 4 |
| 2 | **Nível 0 (só ler transcript/rollout) é o padrão**; o nível 1 é opcional: hooks **por sessão** no Claude, **app-server próprio** no Codex | Spikes 3 e 4 |
| 3 | Um Orb **travado não pode atrasar** o agente: receptor mínimo, sempre responsivo, transporte não bloqueante | Spike 3 |
| 4 | **Um único Terminal Host, em Python**; o cliente (web ou Godot) só exibe | Spike 2 |
| 5 | Toda entrada externa é **validada na borda** e a falha é isolada | Spike 2 |
| 6 | `intrusive_thought` **só com origem humana confirmada** | Spike 3 |
| 7 | Adapters declaram `capabilities()`: Claude e Codex diferem em pensamento, aprovações e hooks | Spikes 3 e 4 |

## O que continua em aberto

| Item | Prioridade |
|---|---|
| **Observador do Codex ignorando um pedido de aprovação** (bloqueia? reenvia? decide?) | **Alta**: toca no princípio de não interferência; precisa de teste cuidadoso e do acompanhamento do Lucas |
| Subagentes ao vivo (Claude na TUI e Codex) e eventos de hook não provocados | Média |
| **Hermes**: instalar o CLI e repetir o levantamento | Média |
| Clique do mouse e desempenho com vários monitores 3D | Média (aparecem com o cliente 3D) |
| Sessões do CLI de terminal do Claude (os transcripts disponíveis vêm do app Desktop) | Baixa |

## Como reproduzir

Cada spike tem um README com os comandos (`spikes/0N-*/README.md`). Eles rodam os **CLIs de
verdade** e **consomem cota** das contas logadas. Os arquivos gerados (capturas, fixtures, logs)
não são versionados porque contêm caminhos locais, prompts e dados da conta; regeneram-se rodando
os spikes. **Nunca envie teclas à TUI do Codex às cegas.**
