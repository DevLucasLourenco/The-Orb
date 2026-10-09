# 11: Janelas pelas alterações locais

Status: ready-for-agent
Blocked by: 10
Origem: R20, R20a, R20b, R20d, R20e, R12; D-038 a D-043, D-092, D-115
Spec: [../spec.md](../spec.md)

## O que construir

As janelas deixam de ser decoração aleatória: acendem onde há alterações locais do git, no andar
da pasta e na cor do tipo de alteração (paleta do VS Code). Cada janela vale 5% das alterações, sem
nunca dividir uma alteração. O git é lido sem gravar nada.

## Critérios de aceite

- [ ] Leitura do git só leitura (sem tocar no `.git`): alterações locais com tipo e linhas alteradas; submódulos ignorados; sinal `realm.changes`.
- [ ] O mundo calcula a fachada de VISUAL.md §6: pacotes por andar e tipo, x = 5%, nada dividido, ordem estável pelo caminho, distribuição regular no andar.
- [ ] x configurável na tela de configurações.
- [ ] Janela só acesa ou apagada, com brilho fixo (sai o brilho geral por atividade, D-115).
- [ ] Cores exatamente as de VISUAL.md §5.
- [ ] O padrão aleatório de janelas some do cliente.

## Testes

Ponto de teste: as leituras do mundo real (repositório git falso → `realm.changes`) e o mundo (alterações → fachada).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
