# 14: Tarefas do CLI

Status: ready-for-agent
Blocked by: 09
Origem: R50, R49; D-093, D-097
Spec: [../spec.md](../spec.md)

## O que construir

O overview mostra o progresso da tarefa de cada sessão ("7 de 12") a partir da lista que o próprio
CLI mantém, e a área Task Board mostra as tarefas concluídas. O rótulo do prédio mostra as tarefas
abertas. Sem lista gravada pelo provider, nada aparece.

## Critérios de aceite

- [ ] Formato da lista de tarefas levantado só pela estrutura em cada CLI (TodoWrite do Claude, plano do Codex, `todowrite` do opencode; Hermes se houver) e registrado nos documentos dos adapters.
- [ ] Sinal `tasks.updated` no protocolo 0.3, produzido pelos adapters que têm a lista.
- [ ] Overview: "concluídas de total" e uma barra por sessão.
- [ ] Task Board: as tarefas concluídas da sessão.
- [ ] Rótulo do prédio: tarefas abertas, quando houver dado.
- [ ] Nada estimado: sem lista, nenhum progresso.

## Testes

Ponto de teste: os leitores dos CLIs (amostras sintéticas → `tasks.updated`) e o mundo.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
