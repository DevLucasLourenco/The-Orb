# 12: Papel, atributos por área e árvore da Team

Status: ready-for-agent
Blocked by: 01
Origem: R40, R57; D-069, D-096, D-116
Spec: [../spec.md](../spec.md)

## O que construir

No overview, cada Alter Ego mostra o seu papel ("revisor", "pesquisador"…), barras com a parcela do
trabalho em cada área e a árvore da Team (quem criou quem), tudo pela contagem das atividades
observadas, sem nenhuma chamada a modelo.

## Critérios de aceite

- [ ] Papel derivado do que a sessão mais fez, por uma tabela de regras (atividade → papel).
- [ ] Atributos: parcela do trabalho em cada área, pela mesma contagem.
- [ ] Árvore da Team no overview, com tipo e estado de cada subagente; no mundo nada muda.
- [ ] Nenhum módulo chama modelo de IA.

## Testes

Ponto de teste: o mundo (eventos de atividade → papel, atributos e árvore).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
