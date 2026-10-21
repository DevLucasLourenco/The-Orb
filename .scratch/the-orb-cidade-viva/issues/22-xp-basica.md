# 22: XP básica

Status: ready-for-agent
Blocked by: 04, 19
Origem: R53, R54; D-101, D-102, D-105, D-110
Spec: [../spec.md](../spec.md)

## O que construir

O módulo de progressão nasce: cada Alter Ego ganha XP por testes verdes, consertos (vermelho →
verde), subagentes concluídos e ofício, com um extrato em que cada entrada aponta para a evidência. O
nível aparece ao lado do nome e a barra de XP no overview.

## Critérios de aceite

- [x] Módulo puro de progressão, com a tabela v1 versionada (PROGRESSION.md §3) para X-TEST, X-FIX, X-DELEG e X-CRAFT, com os limites.
- [x] Extrato por Alter Ego no registro local, com data, regra, evidência e a versão da tabela.
- [x] XP dos subagentes para o líder; nada por tokens, mensagens ou espera; nunca negativa.
- [x] Nível do Alter Ego pela curva k·n·(n−1) com k = 50 (valor provisório até o ticket 25).
- [x] Nível ao lado do nome (V-EGO-13) e barra de XP no overview (V-HUD-13).
- [ ] Trocar a versão da tabela recalcula tudo a partir das fontes. **Parcial:** a tabela é versionada, `replay` recalcula de uma lista de eventos e o extrato de outra versão fica de lado; mas nenhum caminho de produção relê as fontes (o passado vem com o ticket 25).

## Testes

Ponto de teste: o mundo (eventos → extrato e nível), por tabela de casos.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments

- **O que mudou:** `core/rules.py` (`XpTable`, `XP_TABLE` v1), `core/progression.py` (novo: `Entry`, `Ledger`, `level_of`, `replay`, `XpSource`), `core/world.py` (cada Alter Ego tem um `Ledger`; o snapshot ganha `xp`; `World(xp=, xp_table=)`), `registry/store.py` (tabela `xp_ledger`, `entries_of` e `record`; o esquema vai à versão 2), `gateway/app.py` (o registro é também a fonte do extrato), `clients/web` (nível ao lado do nome e barra de XP no cartão). Docs: RULES (R53, R54), VISUAL (V-EGO-13, V-HUD-13), PROGRESSION §8, ARCHITECTURE, CONTEXT, DECISIONS (rodada Q-T22).
- **Testes:** `tests/test_progression.py` (59 casos): X-TEST (recibo, código de saída, só teste que passou, 1 a cada 10 min, por sessão), X-FIX (vermelho → verde, um por falha, não depende do limite do teste), X-DELEG (para o líder, falho não rende, um por subagente, teto por dia), X-CRAFT (janelas de 5 min, o que não é trabalho, subagentes, teto), o que nunca rende (tokens, custo, espera, erro) e a XP nunca negativa, a curva k·n·(n−1) em 15 níveis, a barra, a tabela versionada que recalcula, `replay`, o extrato no registro (sobrevive ao reinício, não paga duas vezes, os limites também valem, só a versão em uso, só os campos do recibo, disco quebrado cai para a memória). Mais um teste no gateway (o registro é a fonte do extrato) e o do esquema do registro atualizado. Suíte inteira: 669 passed, 2 skipped; ruff sem aviso nos arquivos novos e alterados; `node --check` no cliente.
- **Conferido na tela**, numa página temporária (não versionada) que desenha o overview com um snapshot real do mundo feito de eventos sintéticos: "Fermi · 3", a barra "nível 3 · 464 / 600 XP" e "Tales · 1" com a barra vazia; console sem erros; servidor de prévia encerrado. O rótulo do personagem no mundo 3D também foi visto, numa página de prévia com cinco personagens: "Fermi · 2", "Tales · 3"…, ao lado do nome.
- **Não verificado:** sessões reais dos quatro CLIs (a XP só nasce do que o Orb vê chegar; o passado, no ticket 25); o painel Progressão, o nível do realm e o de Mankind (ticket 23); a barra tracejada da XP provisória (ticket 23).
- **Decisões a confirmar:** Q-T22-1 a Q-T22-8 em `docs/DECISIONS.md` (provisórias, P2).

**Revisões (`/code-review`, padrões e spec):** nenhuma violação dura de invariante. Tratado: um `ts` ilegível, sem fuso ou fora do alcance (ano 0001 com fuso estoura `OverflowError`) podia derrubar o lote inteiro do Hub, e agora não rende nada nem quebra; uma linha estragada do extrato no SQLite derrubaria o `apply` e agora fica de fora; um teste atrasado recuava o limite de 10 min (agora vale o mais recente); o total virou uma soma corrente; a memória do registro deixou de varrer a lista a cada gravação; o recibo sem código de saída (Claude) e o vermelho compartilhado entre líder e subagentes entraram na rodada; o critério de recálculo foi reaberto como parcial; a coluna "Conhece" do registro no ARCHITECTURE; o nome de um teste. **Não corrigido, com motivo:** entradas só em memória depois de uma falha de disco não são regravadas quando o disco volta (o registro de nomes tem o mesmo limite); o extrato em memória cresce com o trabalho (no máximo algumas centenas por sessão por dia, com tetos); o `xp` que significa três coisas é o vocabulário do mundo (fonte, conta e snapshot); `Entry.evidence` sem tipo próprio é um dicionário de ids e números, como o resto do snapshot; a falha aberta não sobrevive ao reinício (Q-T22-6); o `isinstance` do Gateway liga o extrato ao registro real e deixa sem XP persistente o modo sem pasta do Orb; o ticket continua `ready-for-agent` até o merge.
