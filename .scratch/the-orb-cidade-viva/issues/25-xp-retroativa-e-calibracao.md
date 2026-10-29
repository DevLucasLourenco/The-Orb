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
- [ ] **Com a aprovação do Lucas**, os valores de k (e da tabela, se preciso) viram uma nova versão, registrada em DECISIONS.md. *(Depende do k que o Lucas escolher ao ver o relatório do histórico real (D-239: até lá, 50 / 500 / 2.500); o mecanismo da nova versão já existe, D-203.)*
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

- **Ticket 25 implementado em 2026-10-29 (decisões confirmadas pelo Lucas; falta só o k):** leitura única do passado (`gateway/past.py` e um `past.py` por adapter), ponto de parada no registro local (`xp_past`, junto com o extrato), indicador de progresso (V-HUD-18),
  relatório de calibração (`core/calibration.py`, V-HUD-19). Decisões Q-T25-1 a Q-T25-9 confirmadas pelo Lucas em 2026-10-29 (D-231 a D-239, [DECISIONS.md](../../../docs/DECISIONS.md)). **Pendente do Lucas (critério 3, D-239):** abrir o Orb, esperar a leitura do passado, ver o
  painel Progressão (Distribuição de níveis) e dizer qual *k* quer; só então o ticket fecha (nova versão da tabela, D-NNN). Não visto: nenhum histórico real; o aspecto do painel na tela.

- **Critério 3 e `needs-info`:** o ticket só fecha quando o Lucas escolher o k com o relatório do histórico real (painel Progressão, depois de o Orb ler o passado); até lá os k seguem 50 / 500 / 2.500 e o ticket fica em `needs-info`.
- **Limites conhecidos (sem mudar o comportamento):** sessão que falha (arquivo sumido, transcript sem evento) não ganha marca e é tentada a cada abertura, só aparece na contagem de erros; o plano roda uma vez por abertura, então sessão listada depois da primeira varredura (e o cache das filhas no Codex, Hermes e opencode) só entra na próxima; `xp_report` lê `world.realms` e `world.past` fora da thread do loop só com `list(...)`; `PastXp._close` usa o relógio de parede em `ledger.settle([], ...)`, como `expire_commits`; desempenho com rollouts de centenas de MB não medido e sessão interrompida recomeça do início.
