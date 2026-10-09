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

- [ ] Módulo puro de progressão, com a tabela v1 versionada (PROGRESSION.md §3) para X-TEST, X-FIX, X-DELEG e X-CRAFT, com os limites.
- [ ] Extrato por Alter Ego no registro local, com data, regra, evidência e a versão da tabela.
- [ ] XP dos subagentes para o líder; nada por tokens, mensagens ou espera; nunca negativa.
- [ ] Nível do Alter Ego pela curva k·n·(n−1) com k = 50 (valor provisório até o ticket 25).
- [ ] Nível ao lado do nome (V-EGO-13) e barra de XP no overview (V-HUD-13).
- [ ] Trocar a versão da tabela recalcula tudo a partir das fontes.

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
