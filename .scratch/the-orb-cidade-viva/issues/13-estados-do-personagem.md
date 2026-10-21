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

- [x] Ícones neutros: erro = triângulo branco com "!" e corpo apagado; bloqueado = cadeado; sem sinal = sinal cortado. Nada em vermelho.
- [x] Até 8 personagens por área e um contador "+N"; o overview lista todos.
- [x] Com `subagent.ended`, o subagente caminha até o líder e então sai; sem o sinal, vale o cinza do ticket 01.
- [x] Duplo clique num personagem: a câmera o segue até o Lucas mexer nela.
- [x] Entradas novas em VISUAL.md conferidas (V-EGO-12, V-EGO-15, V-EGO-16).

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
- **Implementação (2026-10-21):** `core/room.py` (sala cheia, testada em `tests/test_room.py`, 31 casos), `ended_at` do subagente e `room` no snapshot; cliente: ícones, corpo apagado, "+N", subagente que caminha até o líder e duplo clique que segue.
- **Verificado:** suíte inteira passou; no preview, com um snapshot real feito de eventos sintéticos: 11 numa área mostram 8 e "+3"; erro (triângulo), bloqueado (cadeado) e sem sinal (sinal cortado) sobre o líder; o subagente terminado caminha até o líder e some; o duplo clique leva a câmera ao personagem; console sem erros.
- **Revisões (2026-10-21):** tratados: `flyTo` solta o personagem seguido; o seguido que passa do teto é solto; o subagente escondido pelo teto não reaparece só para sair; o magenta de espera não some com o sem sinal (R30); a janela de 30 s foi para o Core (`leaving`). Não tratados, por julgamento: a sessão encerrada não faz o subagente caminhar (ele vai ao dormitório com ela); o mapeamento estado → ícone no cliente segue em `update`, sem tabela; os nomes `__lobby`/`__dorm` repetem-se entre Core e cliente.
- **Não verificado:** nenhuma sessão ou CLI real; que a câmera solta ao arrastar foi conferido só pelo código (o evento `start` dos controles), não pelo gesto na tela; as decisões Q-T13-1 a Q-T13-7 aguardam o Lucas.
