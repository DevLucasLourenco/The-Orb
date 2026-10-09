# 23: XP de commits e as três escalas

Status: ready-for-agent
Blocked by: 11, 22
Origem: R53, R54; D-090, D-103, D-104, D-106
Spec: [../spec.md](../spec.md)

## O que construir

Commits feitos nas sessões dão XP provisória, que vira confirmada quando o commit chega à branch
principal, é anulada se ele for revertido e expira em 30 dias. Aparecem os níveis do Realm e de
Mankind e o painel Progressão, com o extrato e o placar por provider.

## Critérios de aceite

- [ ] Evidência de commit: `gitOperation` no Claude; `git commit` com `command.result` ok nos outros.
- [ ] Leitura do git só leitura: o commit existe, chegou à branch principal (a padrão do remoto, senão `main`/`master`), foi revertido.
- [ ] Estados provisória, confirmada, anulada e expirada no extrato; o nível usa só a confirmada e pode cair.
- [ ] Commits do Lucas fora das sessões não dão XP.
- [ ] Nível do Realm (k = 500) e de Mankind (k = 2.500); barra de cima e painel Progressão com extrato e placar por provider (V-HUD-12, V-HUD-13).

## Testes

Ponto de teste: as leituras do mundo real (repositório git falso → confirmações) e o mundo.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
