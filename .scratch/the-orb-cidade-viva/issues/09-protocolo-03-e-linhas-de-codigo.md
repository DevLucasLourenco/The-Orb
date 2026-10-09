# 09: Protocolo 0.3 e linhas de código

Status: ready-for-agent
Blocked by: 03, 07
Origem: R49, R19; D-051 a D-056, D-085, D-091
Spec: [../spec.md](../spec.md)

## O que construir

O protocolo ganha os eventos de realm, e o mundo passa a guardar estado por realm. A primeira
leitura do mundo real conta as linhas de código de cada projeto, só lendo, e o mundo deriva a classe
do prédio. O rótulo e o overview mostram, por exemplo, "48 mil linhas · Edifício".

## Critérios de aceite

- [ ] Protocolo 0.3 em PROTOCOL.md e no código: eventos com `alter_ego` nulo e o sinal `realm.metrics`; o mundo guarda estado por realm.
- [ ] Contagem: linhas não vazias dos arquivos acompanhados pelo git, sem ignorados, sem a lista visível de gerados e, por padrão, sem `.md`; nada é gravado no projeto nem no `.git`.
- [ ] Recálculo ao abrir e quando as alterações locais mudam, no máximo 1 vez por minuto por realm.
- [ ] Filtro de tipos e lista de exclusões editáveis na tela de configurações, por realm ou para todos.
- [ ] O mundo deriva a classe (as 6 de VISUAL.md §8) pelas faixas fixas.
- [ ] Rótulo e overview mostram as linhas reais e a classe.

## Testes

Ponto de teste: as leituras do mundo real (pasta de projeto falsa → `realm.metrics`) e o mundo (métricas → classe).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
