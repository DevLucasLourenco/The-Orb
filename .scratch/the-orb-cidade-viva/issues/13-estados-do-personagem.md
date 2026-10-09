# 13: Estados do personagem

Status: ready-for-agent
Blocked by: 01, 05
Origem: R52, R33, R51, R17; D-057, D-094, D-095
Spec: [../spec.md](../spec.md)

## O que construir

O líder em erro, bloqueado ou sem sinal mostra um ícone neutro sobre a cabeça; cada área mostra até
8 personagens e um "+N"; o subagente que termina caminha até o líder antes de sair de cena; e o duplo
clique faz a câmera seguir um personagem.

## Critérios de aceite

- [ ] Ícones neutros: erro = triângulo branco com "!" e corpo apagado; bloqueado = cadeado; sem sinal = sinal cortado. Nada em vermelho.
- [ ] Até 8 personagens por área e um contador "+N"; o overview lista todos.
- [ ] Com `subagent.ended`, o subagente caminha até o líder e então sai; sem o sinal, vale o cinza do ticket 01.
- [ ] Duplo clique num personagem: a câmera o segue até o Lucas mexer nela.
- [ ] Entradas novas em VISUAL.md conferidas (V-EGO-12, V-EGO-15, V-EGO-16).

## Testes

Ponto de teste: o mundo (estados e contagem por área) e conferência no preview.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
