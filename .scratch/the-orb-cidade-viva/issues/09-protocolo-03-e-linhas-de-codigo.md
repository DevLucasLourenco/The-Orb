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

- [x] Protocolo 0.3 em PROTOCOL.md e no código: eventos com `alter_ego` nulo e o sinal `realm.metrics`; o mundo guarda estado por realm.
- [x] Contagem: linhas não vazias dos arquivos acompanhados pelo git, sem ignorados, sem a lista visível de gerados e, por padrão, sem `.md`; nada é gravado no projeto nem no `.git`.
- [x] Recálculo ao abrir e quando as alterações locais mudam, no máximo 1 vez por minuto por realm.
- [x] Filtro de tipos e lista de exclusões editáveis na tela de configurações, por realm ou para todos.
- [x] O mundo deriva a classe (as 6 de VISUAL.md §8) pelas faixas fixas.
- [x] Rótulo e overview mostram as linhas reais e a classe.

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

Implementado em 2026-10-14 (branch `ticket/09-protocolo-0-3-e-linhas-de-codigo`). Só estrutura e contagens dos dados reais.

- **O que mudou:** protocolo `0.3` (`realm.metrics`, eventos de realm); `rules.BUILDING_CLASSES`, `building_class`, `GENERATED_FILE_PATTERNS` e `LineFilter`;
  `World.metrics` (estado por realm) com `metrics` no snapshot; pacote `orb.probes` (contador de linhas); `gateway/probes.py` (`LineScheduler`, thread própria);
  filtro de linhas nas preferências (geral e por realm); a tela de configurações ganhou a seção "Contagem de linhas"; rótulo e overview mostram "N mil linhas · Classe".
- **Testes:** `test_realm_metrics.py` (protocolo, faixas, estado por realm), `test_probes.py` (pasta falsa e um repositório git real), `test_line_scheduler.py`
  (quando contar, filtro, Hub), `test_preferences_lines.py`. Suíte: 395 → 451 passed, 2 skipped.
- **Conferido com dados reais** (pasta do Orb temporária; só contagens): dos 23 realms, 19 são repositórios git e 18 foram contados em ~4 min na primeira subida
  (1 realm segue sem número); distribuição de classes plausível (Sobrado, Prédio, Edifício, Arranha-céu); rótulo e overview mostram "N mil linhas · Classe";
  o filtro por realm abriu e salvou no `preferences.json`; depois de reiniciar o servidor tudo voltou igual; ~140 MB e ~27 s de CPU em ~7 min de servidor; console sem erros.
- **Decisões a confirmar:** Q-T09-1 a Q-T09-8 em `docs/DECISIONS.md`.
- **Fora deste ticket:** a **altura**, a forma e os andares do prédio (ticket 10); o Probe de alterações locais do git, que daria o gatilho "quando as alterações locais
  mudam" de verdade (ticket 11); os outros sinais da 0.3 (`command.result`, `realm.changes`, `account.limits`, `tasks.updated`).
