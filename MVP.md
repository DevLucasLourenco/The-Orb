# Orb IA — MVP

> Escopo do primeiro MVP funcional e básico, registro de riscos e plano de validação.
> Visão: [CONTEXT.md](CONTEXT.md) · Ideias fora do MVP: [IDEAS.md](IDEAS.md).

Última atualização: 2026-10-06

## 1. Objetivo do MVP

Provar a tese do Orb com o menor caminho possível:

> **Abrir o CLI real de uma IA dentro do Orb, usar normalmente, e ver em tempo real, de forma
> confiável, o que ela está fazendo, sem alterar em nada o comportamento do agente.**

Fora do MVP (guardado em IDEAS.md): 3D, câmera, camadas vivas, XP, Archive, Gate, Team,
Chronicle etc. O MVP é a **fundação** que o 3D vai renderizar depois.

## 2. Escopo

### Dentro

1. **Terminal Host:** abrir o `claude` (CLI real) em uma pseudo-console, no diretório de um
   realm, exibido em uma janela de terminal; digitar, usar `/slash`, redimensionar.
2. **Telemetria nível 0 (zero pegada):** ler o transcript do Claude Code em tempo real, sem
   instalar hooks nem escrever nada.
3. **Protocol:** eventos universais e estados, conforme PROTOCOL.md (subconjunto).
4. **Painel 2D:** árvore Realm → Alter Ego → Subagente → Atividade, atualizada ao vivo.
5. **Intrusive Thoughts:** detectar prompts enviados (pelo transcript).
6. **Um realm, um provider (Claude).** Segundo provider (Codex) só depois.

### Fora (por enquanto)

3D/Godot · hooks (nível 1) · Codex/Hermes · Gate, Team, Chronicle, Weather, Energy, Archive ·
persistência em banco · multiusuário.

## 3. Critérios de sucesso

| # | Critério | Como medir | Status |
|---|---|---|---|
| S1 | A TUI do `claude` roda hospedada: cores, redimensionamento, entrada, `/slash`, sem corromper a tela | Teste manual + captura | ✅ Spike 1 (`/slash` não exercitado) |
| S2 | O CLI hospedado se comporta **igual** ao rodar fora do Orb | Comparar comportamento; nenhum arquivo do projeto/config alterado pelo Orb | ✅ com ressalvas (§6); hooks do nível 1 só por sessão (§8) |
| S3 | Eventos do transcript chegam ao painel em < 1 s | Medir latência | ✅ ~270–470 ms |
| S4 | Subagentes aparecem como filhos do Alter Ego correto | Sessão com subagentes | ◐ **Via hooks** (Spike 3: `agent_id`/`agent_type`); leitura do transcript de subagente na TUI **não** testada ao vivo |
| S5 | Prompts do Lucas viram `intrusive_thought` | Enviar prompt e verificar | ✅ Spike 1; regra de origem humana em §8 |
| S6 | Falha de um módulo não derruba os outros (robustez) | Matar adapter/terminal e observar | ◐ Validação na borda testada (mensagem inválida, Orb fora do ar/travado); teste de caos completo pendente |

## 4. Registro de riscos (ordenado por criticidade)

| # | Risco | Por que pode inviabilizar | Como validar | Status |
|---|---|---|---|---|
| **R1** | **Hospedar a TUI real do CLI em pseudo-console no Windows** | É a tese do projeto. Se não renderizar ou se comportar bem, a direção muda | **Spike 1** | ✅ **Validado** (ver seção 6) |
| R2 | Telemetria em tempo real por transcript (nível 0) | Se faltar sinal, o painel e o 3D não têm o que mostrar | Spike 1 (tail) + replay dos transcripts reais | ✅ **Validado** para Claude (latência ~270–470 ms) |
| R3 | Embutir o terminal no cliente 3D (Godot) | Se não desse, o 3D como foco ficaria sem terminal | **Spike 2** | ✅ **Validado** (ver seção 7): 2D, 3D e via Python |
| R4 | Hooks ao vivo (nível 1) | Só afeta tempo real e aprovações; nível 0 cobre o básico | Spike 3 | ✅ **Validado, com restrições** (seção 8): funcionam, mas um Orb travado atrasa o agente |
| R5 | Formatos de Codex e Hermes | Afeta o multi-provider, não o MVP | Spike 4 | ✅ **Codex validado, com restrições** (seção 9). Hermes: não instalado, só pesquisa de docs |
| R6 | Desempenho e legibilidade do 3D em escala | Só aparece com o 3D | No cliente 3D | Pendente |

## 5. Plano de spikes

### Spike 1 — Terminal Host (R1 + R2)
Backend Python abre o `claude` em uma pseudo-console (ConPTY), expõe por WebSocket; uma página
com **xterm.js** renderiza. Em paralelo, um leitor do transcript emite eventos.
- **Validar:** S1, S2, S3.
- **Isolado do cliente 3D de propósito:** responde "o CLI roda hospedado?" antes de qualquer
  decisão sobre Godot.
- Código: `spikes/01-terminal-host/`.

- **Status: ✅ concluído** (resultado na seção 6).

### Spike 2 — Terminal no cliente 3D (R3)
Testar `godot-xterm` no Windows (e, se falhasse, webview + xterm.js ou cliente web 3D; a escolha
de Godot é revisável porque o backend é independente do cliente).
- Código: `spikes/02-terminal-godot/`. **Status: ✅ concluído** (seção 7).

### Spike 3 — Hooks ao vivo (R4)
Instalar hooks observadores, disparar cada evento, gravar fixtures e testar o Orb fora do ar e travado.
- Código: `spikes/03-live-hooks/`. **Status: ✅ concluído** (seção 8).

### Spike 4 — Codex e Hermes (R5)
Levantar o que cada CLI expõe, no mesmo formato de ADAPTER-CLAUDE.md.
- Código: `spikes/04-codex/`. **Status: ✅ Codex concluído** (seção 9). **Hermes: pendente** (CLI não
  instalado).

## 6. Resultado do Spike 1 (2026-10-06)

Código: `spikes/01-terminal-host/` (11 testes automatizados passando). Rodado com `claude`
2.1.269 real, no Windows 11, via ConPTY (`pywinpty` 3.0.5) + xterm.js no navegador.

| Critério | Resultado |
|---|---|
| S1 — TUI hospedada funciona | ✅ Logo, cores (truecolor/256), tela alternativa, cursor, barra de modo, redesenho ao redimensionar, entrada de teclado, encerramento com Ctrl+C |
| S2 — Mesmo comportamento que fora do Orb | ✅ com ressalva (abaixo): o Orb não escreveu em nada do projeto; só lê o transcript |
| S3 — Evento chega ao painel em < 1 s | ✅ Latência medida ~270–470 ms (inclui polling de 250 ms) |
| S5 — Prompt vira `intrusive_thought` | ✅ Prompt digitado na TUI apareceu como `intrusive_thought` |
| S6 — Robustez | ✅ parcial: linhas parciais/inválidas do transcript são toleradas (testado); falha de um módulo não derrubar os outros ainda precisa de teste de caos |
| S4 — Subagentes sob o Alter Ego certo | ⏳ Não testado (nenhum subagente nesta sessão); leitura dos transcripts de subagentes está implementada |

Fluxo comprovado: `Terminal (ConPTY) → claude real → transcript → tail somente leitura → eventos
→ painel`, com `Glob`, `Grep`, `Read`, mensagem do agente e prompt aparecendo ao vivo.

### Ajuste de desenho depois do Spike 1: terminal real + CLI chamado dentro dele

O Orb **não executa o CLI direto**. Abre um **PowerShell real** e digita nele o comando do CLI
certo, escolhido automaticamente pelo provider/modelo do Alter Ego. Se o CLI fecha, o terminal
segue aberto. Verificado: 14 testes passando, incluindo "terminal abre e chama o `claude`
sozinho"; rota do servidor com `provider=auto&model=claude-opus-5-5` → `claude`;
`hermes` (não instalado) e modelo desconhecido recusados; token errado e origem externa
bloqueados.

### Achados que mudaram o desenho

1. **O Orb deve atribuir o `--session-id` ao `claude` que hospeda.** Sem isso, o tail
   confundia o transcript da sessão hospedada com outras sessões da mesma pasta (inclusive a
   que estava conversando comigo). Com `--session-id <uuid>` o Orb sabe exatamente qual é o
   transcript. Isso também resolve parte de "sessão visível por Alter Ego".
2. **`-n/--name` dá nome à sessão** (`orb-<id>`), visível na própria TUI.
3. **Marcadores de ambiente herdados mudam o comportamento do CLI.** Iniciado de dentro de uma
   sessão do Claude, o filho herdava `CLAUDE_CODE_CHILD_SESSION` e **não gravava transcript**.
   O Orb remove só esses marcadores e preserva a configuração do usuário (`ANTHROPIC_*` etc.).
4. **Segurança do Terminal Host:** abrir um shell por WebSocket exige token por sessão,
   checagem de `Origin` e lista fixa de comandos. Escuta só em `127.0.0.1`.
5. **Confirmado:** a TUI mostra "Cogitated for 12s", mas o transcript não traz o texto do
   pensamento (bloco `thinking` vazio), como já levantado em ADAPTER-CLAUDE.md §3.

### O que o Spike 1 não provou

- **Codex** hospedado (o `codex` está instalado e permitido no Terminal Host, mas não foi testado).
- **Subagentes** ao vivo, e múltiplos terminais simultâneos.
- **Sessões iniciadas fora do Orb** (modo Observar).
- O terminal **dentro do Godot** (Spike 2): aqui a TUI rodou em xterm.js no navegador.

## 7. Resultado do Spike 2 (2026-10-06): terminal dentro do Godot

Código: `spikes/02-terminal-godot/` (Godot 4.7.2 + godot-xterm 4.0.3). **R3 respondido: sim.**

| Pergunta | Resultado |
|---|---|
| godot-xterm roda no Windows com ConPTY? | ✅ Sim (o "parcial" era só da documentação). PowerShell real, redimensionamento sincronizado PTY↔terminal (99×26 → 79×18) |
| O `claude` real roda dentro do Godot? | ✅ TUI completa, com `-n` e `--session-id` |
| Cores? | ✅ Cor verdadeira, 256 cores, 16 cores, negrito. (Na opção A o `claude` saiu monocromático: faltou o ambiente avisar suporte a cor; na opção B saiu correto) |
| Terminal numa tela **3D** (monitor do Rooftop Room)? | ✅ `SubViewport` projetado num quad inclinado em perspectiva; texto, cursor e `claude` visíveis |
| Teclado em 3D? | ✅ Eventos de teclado da janela encaminhados ao `SubViewport` com `push_input`; comando digitado executou |
| Terminal do Godot exibindo bytes do Terminal Host **em Python**? | ✅ Ciclo completo por WebSocket: digitar no Godot → PTY Python → tela. Funcionou **mesmo com o stdio do Godot redirecionado** |

### Decisão de arquitetura (recomendada)

**Opção B: o Terminal Host continua em Python; o Godot só exibe.** O `Terminal` do godot-xterm
recebe bytes por `write()` e emite `data_sent` com o que o usuário digita; o cliente Godot os
leva ao servidor por WebSocket (mesmo protocolo da página web do spike 1).

| | A — PTY dentro do Godot | **B — PTY no Python (recomendada)** |
|---|---|---|
| Hospedagem do CLI | No Godot (godot-xterm) | Um só Terminal Host (ARCHITECTURE.md) |
| Stdio redirecionado | ❌ quebra (shell sai) | ✅ não importa |
| Sessão/env/telemetria | Dividido entre dois lados | Tudo no mesmo lugar (`--session-id`, limpeza de env, tail do transcript) |
| Outros clientes (painel web) | Outra implementação | Mesmo servidor serve web e Godot |
| Custo extra | — | Latência de WebSocket local (desprezível; a medir) |

A opção A fica como alternativa, mas com a restrição de lançamento acima.

### Armadilhas encontradas (todas documentadas em `spikes/02-terminal-godot/README.md`)

1. ConPTY dentro do Godot **só funciona com stdio não redirecionado** (o filho herda os handles
   do pai). Importa se algo algum dia lançar o Godot com pipes.
2. Caminhos e `cwd` no Windows precisam de **barra invertida**.
3. `JSON.stringify` do Godot não escapa caracteres de controle, então a entrada vai em
   **base64** (`data_b64`).
4. **Bug de robustez no servidor Python, encontrado e corrigido:** uma única mensagem malformada
   do cliente derrubava a sessão inteira. Agora `handle_client_message` valida na borda,
   descarta com motivo e nunca levanta (teste com 10 mensagens ruins; 15 testes passando).
5. Glifos de caixa e bloco (`─ █ ▐`) saem com espaços entre as células. **Cosmético**, medido:
   célula 10,0 px vs glifo 9,6 px, então a causa não é a fonte (testadas JetBrains Mono e
   Cascadia Mono). Possível correção futura: desenhar esses glifos manualmente.
6. Em 3D o teclado **não chega sozinho** ao `SubViewport`: é preciso encaminhar o evento.

### O que o Spike 2 não provou

- **Clique do mouse** no monitor 3D (seleção, foco ao clicar na tela do monitor).
- **Desempenho** com vários monitores 3D ao mesmo tempo (testado em uma GPU modesta, MX110, com um).
- Telemetria (`event`) chegando ao Godot: o canal existe no mesmo WebSocket, mas o teste não
  enviou prompt, então não houve evento para receber.
- Latência de ponta a ponta Godot ↔ Python.

## 8. Resultado do Spike 3 (2026-10-06): hooks ao vivo

Código e fixtures: `spikes/03-live-hooks/`. Detalhes completos, tabelas e correções às docs em
[ADAPTER-CLAUDE.md](ADAPTER-CLAUDE.md) §6. **R4 respondido: os hooks funcionam ao vivo.**

| Pergunta | Resultado |
|---|---|
| Dá para instalar hooks sem mexer na configuração do Lucas? | ✅ `claude --settings <arquivo>` aplica hooks **só àquela sessão**. O `settings.json` dele não é tocado |
| Hooks HTTP chegam ao Orb? | ✅ Com token por header; receptor local responde `{}` (sem decisão, sem contexto) |
| Funcionam na TUI hospedada pelo Orb? | ✅ Eventos chegam e o `session_id` bate com o `--session-id` do Orb |
| Subagentes aparecem? | ✅ `SubagentStart`/`SubagentStop`, e as ações de dentro vêm com `agent_id`/`agent_type` |
| Pedido de aprovação aparece? | ✅ `PermissionRequest` (a decisão continua sem hook) |
| Orb fora do ar atrapalha o agente? | ✅ Não (6,7 s vs 7,5 s) |
| **Orb travado atrasa o agente?** | ❌ **Sim:** 21,5 s vs ~7 s com hook `http` (e `async` não ajuda em `http`). Com `command` async + `curl`: ~10,5 s |

### O que isso muda

1. **Nível 0 (só transcript) continua o padrão.** Hooks são acréscimo opcional.
2. **O nível 1 usa `--settings` por sessão**, nunca o `settings.json` do usuário.
3. **Um Orb travado fere o princípio 10.** Mitigação: receptor mínimo e sempre responsivo que só
   enfileira e responde na hora, e transporte por hook `command` assíncrono com `curl` de
   timeout curto.
4. **`UserPromptSubmit` não é sempre o Lucas.** Prompts do sistema (`<task-notification>`) também
   passam por ele; só o transcript (`origin.kind`) distingue. Regra de `intrusive_thought` ajustada.
5. **`Stop` do agente principal não encerra a Team**: o subagente pode ainda estar rodando.
6. **O resumo das docs tinha erros de campo** (`tool_response`, não `tool_output`; sem
   `is_continuation`/`is_background`). Por isso as fixtures reais são a fonte da verdade.

### O que o Spike 3 não provou

- Eventos não exercitados: `TaskCreated/Completed`, `Notification`, `PostToolUseFailure`,
  `PermissionDenied`, `StopFailure`, `PreCompact/PostCompact`, `CwdChanged`, `InstructionsLoaded`.
- A decisão do usuário num `PermissionRequest` (continua deduzida).
- Hooks em sessões do app Desktop e em sessões iniciadas fora do Orb (modo Observar).
- Sobrecarga contínua do `curl` por evento numa sessão longa e movimentada.

## 9. Resultado do Spike 4 (2026-10-06): Codex

Código e fixtures: `spikes/04-codex/`. Análise completa em [ADAPTER-CODEX.md](ADAPTER-CODEX.md).

| Pergunta | Resultado |
|---|---|
| O Codex expõe eventos estruturados em tempo real? | ✅ Protocolo oficial JSON-RPC por WebSocket (`codex app-server`); 75 tipos de notificação e 10 pedidos do servidor, com esquema gerado pelo próprio CLI |
| Dá para observar **sem tocar na configuração do Lucas**? | ✅ O Orb sobe o **seu próprio app-server** em loopback e a TUI nativa se conecta com `codex --remote`. Opções só por sessão (`-c`) |
| Um 2º cliente (o adapter) observa uma sessão viva? | ✅ Depois de `thread/resume`, recebeu **159 de 169** notificações do cliente que conduzia o turno. Thread **efêmera** não pode ser observada |
| Pensamento? | ◐ `summary` em ~42% dos blocos (6.064 de 14.278), **nunca** `raw`. Melhor que o Claude (~12%) |
| Aprovações? | ✅ Existem como `ServerRequest` e há notificação de resolução (melhor que no Claude) |
| Hooks servem como nível 1? | ❌ Só `command`/`mcp_tool`, sem `http`, **exigem confiança do usuário** e as docs dizem que não há injeção por sessão. Substituído pelo caminho do app-server |
| Subagentes? | ◐ O formato tem (`parent_thread_id`, `agent_nickname`); **não testado ao vivo** |

### O que isso muda

1. **Para o Codex, o "nível 1" é o app-server do Orb com um observador**, e não hooks. Zero
   alteração na configuração do Lucas e fluxo completo (inclui saída de comandos ao vivo).
2. **O Codex não tem ferramenta `Read`**: ler arquivo é um `commandExecution` de PowerShell. O
   adapter precisa de uma tabela declarativa que classifica comandos em categorias.
3. **A tabela `capabilities()` fica diferente por provider**, como o desenho previa: Codex tem
   aprovações melhores e pensamento melhor; Claude tem hooks e `--settings` por sessão.
4. **Modelo de configuração do Lucas:** o padrão do `config.toml` dele (`gpt-6-luna`) **não é
   aceito** com a conta ChatGPT; os modelos reais são `gpt-5.6-sol`, `terra` e `luna`. O Orb
   deve passar o modelo explicitamente ao abrir sessões do Codex (ou mostrar o erro com clareza).

### Incidentes do spike (relatados com transparência)

Ao automatizar a TUI do Codex, **enviei teclas às cegas** duas vezes: na primeira, o Enter aceitou
"Update now" e disparou o instalador oficial, que **falhou sem efeito** (versão intacta; ficou
uma pasta de staging vazia); na segunda, o prompt foi digitado com a revisão de hooks aberta
(indícios fortes de que **nada foi confiado**; ver §6 do ADAPTER-CODEX). O script foi
endurecido (verifica a tela, só envia Esc, aborta em qualquer diálogo desconhecido), e a lição
virou regra: **o Orb nunca responde diálogos do Lucas** (atualização, confiança, hooks).
Também foi criada **1 sessão de teste** no histórico do Codex (`01a11443-9c62-7a23-b900-b05f7dc17dd4`).

### O que o Spike 4 não provou

- A **TUI** do Codex conversando com o app-server do Orb (o observador foi validado com um cliente
  programático; os diálogos de abertura impediram a conversa completa sem a decisão do Lucas).
- Como o servidor trata um **assinante passivo que ignora um pedido de aprovação** (crítico).
- Subagentes ao vivo, hooks ao vivo, eventos de `fileChange`, plano nativo e streaming de
  resumo de raciocínio.
- **Hermes**: o CLI não está instalado nesta máquina.

## 10. Decisões tomadas

Decisões consolidadas dos spikes (a base de cada uma está na seção do spike indicada):

| # | Decisão | Origem |
|---|---|---|
| D1 | **Terminal real + CLI chamado dentro dele**: o Orb abre um PowerShell (ConPTY) e digita o comando do CLI escolhido pelo modelo do Alter Ego. **Nenhuma TUI criada do zero** | §6 |
| D2 | **Terminal Host em Python** (um só, para web e Godot). O Godot só **exibe** os bytes (godot-xterm) por WebSocket | §7 |
| D3 | **Nível de pegada padrão: 0** (só ler transcript/rollout). O nível 1 é opcional por Alter Ego | §8, §9 |
| D4 | **Claude, nível 1:** hooks injetados **por sessão** com `claude --settings`, nunca no `settings.json` do Lucas | §8 |
| D5 | **Codex, nível 1:** app-server **próprio do Orb** + `codex --remote`; um observador se inscreve nas threads. Hooks do Codex descartados | §9 |
| D6 | **O Orb nunca responde diálogos do Lucas** (atualização, confiança de diretório/hooks, aprovações) e nunca envia teclas a uma TUI sem a tela verificada | §9 |
| D7 | O Orb atribui `--session-id` e `-n` ao `claude` que hospeda (vínculo Alter Ego ↔ sessão) e limpa os marcadores de ambiente herdados do Claude | §6 |
| D8 | Segurança do Terminal Host: loopback, token por sessão, checagem de `Origin`, lista fixa de executáveis | §6 |
| D9 | `intrusive_thought` só quando a origem é humana (o transcript distingue prompts do sistema) | §8 |
| D10 | Cliente do MVP: **página web com xterm.js** (painel 2D + terminal); o 3D vem depois. Backend Python (FastAPI) | — |

## 11. Próximos passos

1. **Testar o risco principal que sobrou:** o app-server do Codex com um observador que ignora um
   pedido de aprovação (precisa do acompanhamento do Lucas; ver [ADAPTER-CODEX.md](ADAPTER-CODEX.md) §9).
2. Promover o código dos spikes para os módulos definitivos de [ARCHITECTURE.md](ARCHITECTURE.md):
   Protocol, Core, Adapter Claude, Adapter Codex, Terminal Host, Gateway.
3. Painel 2D Realm → Alter Ego → Subagente → Atividade alimentado pelos dois adapters.
4. Cliente Godot com o terminal como monitor 3D (R6: medir desempenho com vários monitores).
5. Hermes: instalar o CLI e repetir o levantamento (hoje só há referências externas).
