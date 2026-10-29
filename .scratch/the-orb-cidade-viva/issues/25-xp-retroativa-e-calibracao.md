# 25: XP retroativa e calibração da curva

Status: needs-info
Blocked by: 23
Origem: R48 (passado), R54; D-107, D-108
Spec: [../spec.md](../spec.md)

## O que construir

O Orb calcula a XP das sessões antigas numa leitura única em segundo plano, com o ponto de parada no
registro local, e mostra ao Lucas como o histórico real se distribui pelos níveis. Com a aprovação
dele, a curva calibrada vira uma nova versão da tabela.

## Critérios de aceite

- [x] Leitura única do passado em segundo plano, com indicador de progresso e ponto de parada no registro local; nunca lê a mesma sessão duas vezes. *(Feita e testada com históricos sintéticos dos quatro CLIs; nenhum histórico real foi lido.)*
- [x] Relatório da distribuição de níveis com o histórico real, mostrado ao Lucas. *(Pronto no painel Progressão, V-HUD-19; "com o histórico real" só acontece quando o Lucas abrir o Orb: o relatório é calculado das sessões lidas.)*
- [ ] **Com a aprovação do Lucas**, os valores de k (e da tabela, se preciso) viram uma nova versão, registrada em DECISIONS.md. *(Aguarda o Lucas: ver o relatório real e escolher o k; o mecanismo da nova versão já existe, D-203.)*
- [x] O desempenho do Orb não piora durante a leitura do passado. *(Por construção e por teste: uma sessão por vez, um lote por passo, descanso de 3 vezes o tempo gasto, a thread nunca toca no mundo. Não foi medido com um histórico real grande.)*

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

- **Herdado do ticket 22 (D-203):** trocar a versão da tabela de XP só recomeça o extrato; a releitura das sessões antigas para recalcular tudo a partir das fontes é deste ticket. `core/progression.replay` já recalcula de uma lista de eventos; falta um caminho de produção que leia o passado.

- **Ticket 25 implementado em 2026-10-29 (aguarda o Lucas):** leitura única do passado (`gateway/past.py` e um `past.py` por adapter), ponto de parada no registro local (`xp_past`, junto com o extrato), indicador de progresso (V-HUD-18),
  relatório de calibração (`core/calibration.py`, V-HUD-19). Decisões provisórias Q-T25-1 a Q-T25-9 em [DECISIONS.md](../../../docs/DECISIONS.md). **Pendente do Lucas:** abrir o Orb, esperar a leitura do passado, ver o
  painel Progressão (Distribuição de níveis) e dizer qual *k* quer; só então o ticket fecha (nova versão da tabela, D-NNN). Não visto: nenhum histórico real; o aspecto do painel na tela.
