# 25: XP retroativa e calibração da curva

Status: ready-for-agent
Blocked by: 23
Origem: R48 (passado), R54; D-107, D-108
Spec: [../spec.md](../spec.md)

## O que construir

O Orb calcula a XP das sessões antigas numa leitura única em segundo plano, com o ponto de parada no
registro local, e mostra ao Lucas como o histórico real se distribui pelos níveis. Com a aprovação
dele, a curva calibrada vira uma nova versão da tabela.

## Critérios de aceite

- [ ] Leitura única do passado em segundo plano, com indicador de progresso e ponto de parada no registro local; nunca lê a mesma sessão duas vezes.
- [ ] Relatório da distribuição de níveis com o histórico real, mostrado ao Lucas.
- [ ] **Com a aprovação do Lucas**, os valores de k (e da tabela, se preciso) viram uma nova versão, registrada em DECISIONS.md.
- [ ] O desempenho do Orb não piora durante a leitura do passado.

## Testes

Ponto de teste: o mundo e os leitores dos CLIs com históricos sintéticos.

## Observação

Tem um ponto de parada com o Lucas (aprovação da curva) antes de concluir.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
