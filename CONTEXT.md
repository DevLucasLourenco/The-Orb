# The Orb — Glossário

Vocabulário canônico do **The Orb**: um mundo 3D onde cada projeto real é um prédio e cada sessão
de um agente de IA é um personagem que trabalha nele. Se um termo muda de significado, este
arquivo muda primeiro; código, protocolo e interface usam estes termos exatamente assim.

Este arquivo é **só glossário**. Visão e princípios: [docs/VISION.md](docs/VISION.md). Decisões:
[docs/adr/](docs/adr/). Contratos técnicos: [docs/PROTOCOL.md](docs/PROTOCOL.md).

Última atualização: 2026-10-07

## O mundo

**The Orb**:
O produto e o mundo que ele desenha: uma cidade conceitual, vista de cima, que contém todos os
projetos do Lucas. Na prosa, "o Orb" é a forma curta.
_Evite_: Orb IA, Orb AI, Agent World

**Mankind**:
A sociedade de todas as IAs presentes no Orb: todos os Alter Egos e subagentes, de todos os
providers, em todos os realms.
_Evite_: população, frota

**Realm**:
Um projeto real (um repositório), desenhado no Orb como um prédio. A altura do prédio é a
quantidade de linhas de código do projeto, sempre ignorando o que o `.gitignore` ignora.
_Evite_: projeto (no contexto do mundo), prédio (como nome do conceito), workspace

**Rooftop Room** *(nome provisório)*:
O quartinho no teto de cada prédio onde os Alter Egos daquele realm trabalham. Todo Rooftop
Room tem as mesmas cinco áreas do Environment.
_Evite_: escritório, sala

**Environment**:
O conjunto fixo de áreas de um Rooftop Room, cada uma correspondendo a um tipo de atividade:
**Development Center** (escrever e executar), **Testing Lab** (testar), **Research Center** (ler e
pesquisar), **Code Review** (revisar) e **Task Board** (concluir tarefas).
_Evite_: cenário, mapa

## Os agentes

**Alter Ego**:
Uma **sessão** de um CLI de IA (Claude Code, Codex, Hermes…) em um realm, desenhada como um
personagem: o **líder** da sua Team. Uma sessão é um Alter Ego; duas sessões são dois Alter
Egos. O provider e o modelo pertencem à sessão e não mudam.
_Evite_: agente principal, persona do provider, bot

**Perfil** *(em aberto)*:
O que dá identidade a um Alter Ego além da sessão (nome, papel, aparência, histórico). O
conceito ainda não está maduro: ver as questões em aberto de [docs/VISION.md](docs/VISION.md).

**Subagente**:
Uma unidade temporária que nasce dentro da sessão de um Alter Ego para cumprir uma missão e
depois se desmobiliza. Aparece no Orb como um personagem da Team do seu Alter Ego.
_Evite_: worker, filho, agente secundário

**Team**:
Um Alter Ego e os subagentes que nasceram na sessão dele, vistos e endereçados como grupo.
Subagentes podem ter subagentes (profundidade).
_Evite_: squad, equipe (como nome do conceito)

**Provider**:
O CLI de IA de onde vem uma sessão (`claude`, `codex`, `hermes`). Cada provider aparece no Orb
**como ele é**, com o seu próprio vocabulário de eventos.
_Evite_: engine, motor, LLM (como sinônimo de provider)

## O que acontece dentro de um Alter Ego

**Inner World**:
O interior de um Alter Ego: o **terminal com o CLI real** daquela sessão e a linha do tempo de
tudo o que se observa nela, nos dois sentidos. **De dentro**: o que o agente pensa, narra e
faz. **De fora**: o que o Lucas escreve no terminal (prompts, comandos, interrupções). É o único
lugar onde se escreve para um agente.
_Evite_: Intrusive Thoughts, chat espelhado, console

**Origem**:
De quem é uma entrada do Inner World: `agente` (veio da sessão) ou `humano` (o Lucas escreveu).
Uma entrada só é `humano` quando a origem humana é confirmada pela fonte do provider.
_Evite_: autor, remetente

**Fidelity**:
O quanto uma entrada de pensamento é literal: `raw` (texto exposto pelo provider), `summary`
(resumo fornecido pelo provider) ou `inferred` (deduzido pelo Orb, nunca mostrado como
pensamento).
_Evite_: confiança, precisão

## Telemetria

**Evento nativo**:
Um fato observado no formato original do provider (um hook do Claude, uma notificação do
app-server do Codex, uma linha de transcript). O Orb o preserva e mostra como ele é, sem
renomear.
_Evite_: evento universal, evento traduzido

**Sinal de mundo**:
O mínimo que o Orb deriva de um evento nativo para desenhar o mundo: em que atividade o
personagem está, se espera o Lucas, se um subagente nasceu ou terminou. Nunca substitui o evento
nativo; só o acompanha.
_Evite_: estado traduzido, evento normalizado

**Atividade**:
O estado de um personagem no mundo, que decide em que área do Environment ele aparece:
`IDLE`, `THINKING`, `READING`, `RESEARCHING`, `CODING`, `EXECUTING`, `TESTING`, `REVIEWING`,
`DELEGATING`, `WAITING`, `BLOCKED`, `ERROR`, `COMPLETED`, e `NO_SIGNAL` quando não há dados.
_Evite_: status, fase

**Mapa do provider**:
A tabela declarativa, uma por provider, que diz que sinal de mundo e que entrada de Inner World
cada evento nativo gera.
_Evite_: tradutor, normalizador

**Nível de pegada**:
Quanto o Orb toca no ambiente para observar uma sessão. **Nível 0**: só lê arquivos que o
provider já grava. **Nível 1**: observação em tempo real ligada só àquela sessão, sem alterar
configuração do Lucas.
_Evite_: modo de integração, instrumentação

**Hospedar**:
O Orb abre o terminal e chama o CLI dentro dele; a sessão nasce já ligada a um Alter Ego.
_Evite_: executar, rodar o agente

**Observar**:
O Orb lê uma sessão que nasceu fora dele (por exemplo, `claude` aberto direto no terminal).
_Evite_: anexar, espelhar

## Camadas vivas

**Gate**:
O portão central do Orb: mostra tudo o que espera o Lucas em todos os realms e permite escrever a
qualquer Alter Ego sem entrar no realm, sempre pelo terminal do Inner World dele.
_Evite_: inbox, central de aprovações

**Archive**:
A memória de um Alter Ego, só para ver: instruções, skills, arquivos de memória e contexto que
moldam a sessão.
_Evite_: memória (sozinho), knowledge base

**Chronicle**:
A história do Orb reproduzível no tempo: a cidade como era em qualquer momento.
_Evite_: histórico, log (como nome do conceito)

**Weather**:
O clima de um realm, que mostra a saúde dele (CI e testes).
_Evite_: status do build

**Energy**:
O que o Orb consome: tokens e custo, por Alter Ego, por realm e por Mankind.
_Evite_: custo (sozinho), billing

## Relações

- Um **Realm** tem um **Rooftop Room**; um Rooftop Room tem zero ou mais **Alter Egos**.
- Um **Alter Ego** é exatamente uma sessão de um **Provider** e tem exatamente um **Inner World**.
- Um **Alter Ego** lidera uma **Team**; a Team tem zero ou mais **Subagentes**, que podem ter os
  seus próprios subagentes.
- Todo **evento nativo** pertence a um Alter Ego (e, se for o caso, a um Subagente) e pode gerar
  um **sinal de mundo** e uma entrada de **Inner World**, conforme o **Mapa do provider**.

## Exemplo de diálogo

> **Lucas:** "Abri duas sessões do Claude no TriSafe."
> **Orb:** "Então o Rooftop Room do TriSafe tem dois Alter Egos, cada um com o seu Inner World. O
> segundo chamou um subagente Explore: ele aparece na Team desse Alter Ego, em `READING`, no
> Research Center."
> **Lucas:** "E o que o subagente está fazendo?"
> **Orb:** "No Inner World do Alter Ego aparece o evento nativo `PreToolUse · Grep`, do jeito
> que o Claude o chama."

## Ambiguidades resolvidas

- **Alter Ego**: antes era "a persona persistente que troca de provider". Agora é **uma sessão**;
  ver [ADR 0001](docs/adr/0001-alter-ego-e-uma-sessao.md).
- **Intrusive Thoughts**: deixou de ser um conceito próprio; o que o Lucas escreve é a parte "de
  fora" do Inner World. Ver [ADR 0003](docs/adr/0003-inner-world-une-terminal-e-pensamento.md).
- **Neutro de provider**: substituído por "cada provider aparece como ele é", com sinais de mundo
  derivados. Ver [ADR 0002](docs/adr/0002-eventos-nativos-por-provider.md).
