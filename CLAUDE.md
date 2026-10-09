# The Orb — guia para agentes

Este arquivo é lido por todo agente que trabalha neste repositório. O produto está descrito nos
documentos; aqui está **como trabalhar** com eles e quais limites nunca se cruzam. Na dúvida entre
este arquivo e um documento de `docs/`, vale o documento, e a diferença deve ser apontada.

## 1. O projeto

O **The Orb** é um mundo 3D (cidade vista de cima) que mostra, com **telemetria real**, o trabalho
dos CLIs de IA (Claude Code, Codex, Hermes, opencode) nos projetos do Lucas. Cada projeto é um
prédio (**Realm**); cada sessão de um CLI é um personagem (**Alter Ego**) no **Rooftop Room** do
prédio; o **Inner World** é o terminal real da sessão mais a linha do tempo dela. O Orb **só
observa**: não altera como os agentes trabalham e não consome tokens.

O dono das decisões é o **Lucas**. Ele escreve em português do Brasil e espera respostas, documentos
e mensagens de commit em pt-BR.

## 2. Fontes da verdade

Leia antes de mexer no assunto. Use os termos exatamente como no glossário.

| Documento | Use para |
|---|---|
| [CONTEXT.md](CONTEXT.md) | Glossário canônico. Termo novo nasce aqui |
| [docs/RULES.md](docs/RULES.md) | Regras numeradas (P1–P5, R1…), com a auditoria da implementação. **Fonte dos tickets** |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Todas as decisões (D-NNN), em ordem, e as rodadas de perguntas (Q-…). **A decisão mais recente vence o texto antigo** |
| [docs/VISUAL.md](docs/VISUAL.md) | O que cada elemento visual significa (Dado, Legenda, Cenário, Heurística, Identidade), paletas, algoritmos de fachada, cidade e alturas |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Módulos, fronteiras, contratos, robustez, desempenho, testes |
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | Envelope de evento 0.2 e vocabulário fechado de sinais |
| [docs/adapters/](docs/adapters/) | O que cada provider expõe, **verificado** |
| [docs/adr/](docs/adr/) | Decisões difíceis de reverter |
| [docs/VISION.md](docs/VISION.md), [docs/IDEAS.md](docs/IDEAS.md), [docs/MVP.md](docs/MVP.md), [docs/PROGRESSION.md](docs/PROGRESSION.md) | Visão e princípios, backlog completo, escopo do MVP, progressão (XP) |

**Não invente.** Regra, cor, número, comportamento de provider, nome de campo: se não está escrito
nem verificado, pergunte ou verifique. Comportamento de provider só entra em `docs/adapters/` com a
evidência e a confiança.

## 3. Processo (obrigatório)

**Ordem:** discutir → documentar (RULES, VISUAL, ADR) → registrar em DECISIONS → tickets → implementar
ticket a ticket → rever a Situação da regra. Nada é implementado sem a regra escrita e o ticket
criado (P1).

**Fase atual (P5): tickets escritos.** A spec e os 25 tickets estão em
`.scratch/the-orb-cidade-viva/` (D-117). Implemente **um ticket por vez**, pela fronteira: só os que
têm todos os bloqueios (`Blocked by:`) concluídos. Nada fora de um ticket.

**Specs e tickets ficam em `.scratch/<feature>/`** (`spec.md` e `issues/NN-*.md`), arquivos
markdown versionados no git, com a linha `Status:` no topo (D-098; formato em
[docs/agents/issue-tracker.md](docs/agents/issue-tracker.md)). **Nunca em issues públicas do GitHub**: o repositório é
público e os documentos citam projetos e dados internos.

**Rodada de decisões** (formato aprovado pelo Lucas):

1. Liste as questões abertas com id (`Q-<ÁREA>-n`) e uma **proposta concreta** para cada uma.
2. O Lucas responde por número ("1 a 6 sim", "2 não").
3. Cada resposta vira `D-NNN` datado em DECISIONS.md (o próximo número livre) e é aplicada no
   documento do assunto (RULES, VISUAL, ARCHITECTURE, VISION, IDEAS, CONTEXT). A questão fica riscada
   (`~~Q-…~~ D-NNN`), nunca apagada.
4. Se o Lucas disser "deixo com você", registre como **Delegada**: vale até ele rever.
5. Se ele pedir "procure", pesquise referências e **cite as fontes**.

**Conflitos (P2):** um pedido que contradiz uma regra ou decisão é apontado **antes** de fazer, com
uma proposta de solução, e a escolha fica registrada.

**Nada se apaga (P3):** ideia ou regra abandonada muda de status, com motivo e a decisão que a
substituiu (texto riscado + referência).

**Antes de implementar um ticket, confira:** a regra existe em RULES.md? Todo elemento visual novo
tem entrada em VISUAL.md com tipo e fonte? Algum invariante da §4 é afetado?

## 4. Invariantes (nunca violar)

1. **Telemetria real (R12).** Todo elemento que parece dado **é** dado. Sem dado: `NO_SIGNAL`,
   nunca um estado inventado. Decoração só como **Cenário declarado** em VISUAL.md (R12a). Nada de
   padrões aleatórios que pareçam informação.
2. **Realms detectados pelos providers (R3, R3a–d).** Nunca crie opção, parâmetro ou configuração
   para o Lucas informar caminhos de projetos. `--root`, `--realm` e `--lookback` são provisórios e
   vão sair.
3. **Somente leitura (R16).** Arquivos e bancos dos providers e dos projetos são abertos só para
   leitura (SQLite com `mode=ro`). **Nunca grave no `.git`**: git só com `--no-optional-locks` (ou
   `GIT_OPTIONAL_LOCKS=0`). A única escrita é o Terminal Host levando ao CLI o que o Lucas digitou.
4. **O Orb nunca responde diálogos** dos CLIs (atualização, confiança, hooks, aprovações), nem em
   testes ou automação, e **nunca envia teclas às cegas** ([ADR 0006](docs/adr/0006-o-orb-nunca-responde-dialogos.md)).
   O observador do app-server do Codex **ignora** pedidos de servidor (não aprova nem recusa).
5. **O Orb não consome tokens (R38).** Nenhum módulo chama modelo de IA, nem para resumir,
   classificar, nomear ou derivar papel. Tudo sai de regras e tabelas sobre a telemetria.
6. **Cada provider como ele é (R13).** O evento nativo fica intacto em `native`; o mundo usa só os
   sinais do vocabulário fechado (`orb.protocol.vocab`). Mudar o vocabulário é mudar PROTOCOL.md
   primeiro.
7. **Fidelidade explícita (R14).** Pensamento declara `raw` ou `summary`; o que o Orb deduz nunca
   aparece como pensamento.
8. **Preferências ficam no Orb (R29):** tela de configurações + arquivo de preferências próprio.
   Nunca em arquivos dos providers, nunca como novo parâmetro de linha de comando.
9. **Cores com significado são só três famílias (R20a, R20c, R30):** janelas = paleta do git do VS
   Code; personagens = cor do provider (Claude laranja, Codex azul, Hermes amarelo, opencode cinza);
   magenta pulsante = esperando o Lucas. Todo o resto é neutro. Valores em VISUAL.md §5.
10. **O Orb não rastreia quem escreveu cada mensagem (R11).**
11. **Privacidade e confidencialidade (LGPD e política da UTC Óleo e Gás).**
    - Nunca leia as tabelas de credenciais do opencode (`credential`, `account`, `control_account`)
      nem arquivos `auth.json`; o adapter do opencode só lê `session_v2` e `session_message`.
    - Ao investigar dados reais de um provider, olhe a **estrutura** (tabelas, chaves, contagens),
      não o conteúdo das sessões, e não o imprima.
    - Fixtures reais (capturas, logs, prompts, caminhos locais) **nunca são versionadas**. Testes
      versionados usam amostras **sintéticas** com a forma verificada.
    - Nada de dados pessoais, tokens ou chaves em código, testes, URLs ou mensagens.

## 5. Arquitetura e modularidade

```
src/orb/
  protocol/       envelope OrbEvent, vocabulário fechado, limites, validação     (não importa nada)
  core/           o mundo: apply(event) / snapshot(); regras em rules.py         (só Protocol)
  adapters/
    _shared/      fábrica de eventos, JSONL incremental, SQLite ro, classificador de comandos
    claude/ codex/ hermes/ opencode/    mapping.py (tabelas) + leitores          (só Protocol e _shared)
  terminal_host/  ConPTY, linha de lançamento com valores do Orb, ambiente limpo (nada do domínio)
  gateway/        FastAPI + WebSocket, Observatório, Hub                         (todos, por interfaces)
clients/web/      mundo 3D (Three.js 0.170 por importmap, xterm.js), sem build   (só mensagens do Gateway)
```

**Regras de dependência** (detalhe em [ARCHITECTURE.md](docs/ARCHITECTURE.md) §2):

- Dependências apontam para Protocol e Core, nunca o contrário. O Core não importa nada além do
  Protocol.
- Adapters não importam uns aos outros. O que é comum e genérico vai para `adapters/_shared/`, sem
  conhecimento de provider.
- **Provider novo = adapter novo** (`mapping.py` + leitores), sem tocar em Core, Gateway ou clientes.
- Clientes falam só com o Gateway.
- Módulos já decididos e ainda não implementados (Probes, Weather, Energy, leitor de diálogos,
  registro local, contador de linhas) têm lugar definido em ARCHITECTURE.md §3. Siga-o; não crie
  outro lugar.

**Padrões que valem para todo código novo:**

- **Domínio puro, I/O na borda.** Regras do domínio não tocam disco, rede nem relógio; o tempo vem
  do `ts` dos eventos. PTY, home e relógio entram por parâmetro.
- **Tabelas, não `if`s espalhados.** Mapeamentos (ferramenta → atividade, atividade → área, sinal →
  transição, classe de prédio, XP) ficam em tabelas declarativas (`rules.py`, `mapping.py`). Mudar
  uma regra = mudar uma tabela.
- **Robustez.** Entrada externa é validada na borda e descartada com motivo se inválida; parsers
  ignoram campos desconhecidos e linhas parciais; a falha de um provider ou leitor nunca derruba os
  outros (fica em `errors`); degradação explícita.
- **Idempotência.** Ids determinísticos; reler uma fonte não duplica nada (janela de dedupe no Core).
- **Desempenho.** Leitura incremental por offset ou cursor; arquivo que já existia começa do fim;
  lotes limitados; nada lido duas vezes; nada cresce sem limite; trabalho bloqueante fora do loop
  (`to_thread`). Limites de tamanho em PROTOCOL.md.
- **Módulos pequenos e com um assunto.** Se um arquivo passa a cuidar de dois âmbitos, divida-o pela
  fronteira de ARCHITECTURE.md.

## 6. Código

- Python ≥ 3.12 (máquina do Lucas: 3.14). `from __future__ import annotations`, type hints,
  identificadores em inglês, **docstrings e comentários em pt-BR**, explicando o porquê. Siga o
  estilo do arquivo ao redor.
- Dependência nova só com justificativa, no `pyproject.toml`, e perguntando ao Lucas antes.
- Cliente web: módulos ES em `clients/web/js/`, sem etapa de build; Three.js e xterm.js por CDN.
  Todo elemento visual novo precisa da entrada em VISUAL.md antes.
- Windows 11 é a plataforma principal: ConPTY via `pywinpty`; caminhos com espaços (o repositório
  está em `...\Sistemas e Projetos\The Orb`); atenção ao limite de 260 caracteres de caminho nos
  testes (ver a fixture `short_tmp` em `tests/test_gateway.py`).

## 7. Testes e verificação

```bash
python -m pytest -q
```

- Todos os testes passam antes de qualquer commit de código. Lógica nova vem com testes; regra em
  tabela é testada por tabela de casos.
- Testes não usam rede nem CLI real. O que depende de `pywinpty` ou de um CLI instalado usa
  `pytest.importorskip` **dentro da função de teste**, nunca no topo do módulo.
- Mudança no cliente: abra o preview, confira o console sem erros e que nenhuma cor fora da legenda
  apareceu.
- Mudança em documento: links relativos válidos, "Última atualização" com a data do dia.
- Os experimentos de `spikes/` rodam os CLIs de verdade e **consomem cota**: não rode sem o Lucas
  pedir.

**Pontos de teste (D-099):** o principal é o mundo (eventos sintéticos + uma hora → estado do mundo,
incluindo cidade, fachada, classes e XP); os outros dois são os leitores dos CLIs (arquivos e bancos
sintéticos → eventos) e as leituras do mundo real (pasta falsa → eventos). Não crie pontos de teste
novos sem necessidade; o cliente web só desenha e não tem lógica de domínio.

**Pronto quando:** critérios de aceite do ticket cumpridos + testes + documentação atualizada +
coluna Situação da regra revista em RULES.md.

## 8. Git e GitHub

- Repositório: `DevLucasLourenco/The-Orb`, branch `main`.
- Mensagens de commit em pt-BR, verbo na 3ª pessoa do presente ("Registra…", "Corrige…",
  "Adiciona…"), uma ideia por commit.
- Documentação vai direto na `main`; **implementação: uma branch e um PR por ticket**, citando as
  regras e os critérios de aceite (D-114).
- Commits locais, sim; **`push` só quando o Lucas pedir**. Nunca force push, nunca reescrever
  histórico publicado, nunca pular hooks.
- Arquivos locais da máquina (`.claude/launch.json`, capturas dos spikes) ficam fora do git.

## 9. Rodar

```bash
pip install -e ".[dev]"
```

```bash
python -m orb.gateway.app --root ".."
```

O servidor escuta só em `127.0.0.1`, com token por execução e `Origin` local obrigatória; abra a URL
impressa. O terminal hospedado roda o **CLI de verdade** e consome a cota da conta logada.

## 10. Como falar com o Lucas

- Em pt-BR, direto, sem jargão desnecessário.
- Decisões são dele: proponha com uma recomendação, não decida sozinho o que é de produto.
- Diga o que foi feito e o que não foi, com a saída real quando algo falhar.
- Quando faltar dado, diga o que falta e pergunte; não suponha.

## Agent skills

### Issue tracker

Issues e specs vivem como markdown local em `.scratch/<feature>/`. Ver `docs/agents/issue-tracker.md`.

### Triage labels

Vocabulário padrão: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. Ver `docs/agents/triage-labels.md`.

### Domain docs

Single-context: um `CONTEXT.md` e `docs/adr/` na raiz. Ver `docs/agents/domain.md`.

### Complementos: acompanhamento e fechamento

`delivery-summary` e `phase-overview` (do pacote
[skills-matt-pocock-support](https://github.com/devlucaslourenco/skills-matt-pocock-support)) ficam em
`.claude/skills/` e complementam as skills do Matt Pocock.

- Use `delivery-summary` ao concluir ou pausar uma tarefa que alterou arquivos: gere o fechamento com
  o script da skill (resultado, mudanças, verificações, riscos, pendências e próximo passo). Pendências
  de um ticket vão para a seção `## Comments` dele, com `Status: needs-info` quando dependerem do Lucas.
- Use `phase-overview` quando o Lucas pedir progresso, fases, bloqueios ou o que falta. As fontes deste
  projeto são `.scratch/the-orb-cidade-viva/` (spec e tickets, com `Status:` e `Blocked by:`),
  `docs/RULES.md` (coluna Situação) e `docs/DECISIONS.md`. Diferencie implementação de conclusão e
  validações pendentes.
- Com `show_widget` disponível, exiba o HTML gerado e inclua a linha de marca na resposta; sem ela, use
  Markdown.
- Testes do pacote: `tests/governance/` (rodam junto com `python -m pytest -q`).

