# 02: Ajustes dos adapters: fala do Codex e fidelidade do pensamento

Status: ready-for-agent
Blocked by: None (can start immediately)
Origem: R13, R14; D-089
Spec: [../spec.md](../spec.md)

## O que construir

No Inner World, a fala do agente do Codex que hoje some passa a aparecer como narração, e o
pensamento do Hermes e do opencode passa a declarar a fidelidade certa (texto bruto ou resumo),
confirmada pela estrutura dos dados.

## Critérios de aceite

- [x] Linhas `response_item/agent_message` do rollout do Codex viram narração no Inner World, com o nome nativo.
- [x] `inter_agent_communication_metadata` e `event_msg/thread_settings_applied` avaliados pela estrutura; a decisão (mapear ou ignorar, e por quê) fica no documento do adapter do Codex.
- [x] A fidelidade do pensamento do Hermes e do opencode é confirmada só pela estrutura (campos e contagens, sem ler conteúdo) e o adapter marca `raw` ou `summary` conforme o resultado; sem como confirmar, a dúvida fica registrada no documento do adapter.
- [x] Documentos dos adapters do Codex, do Hermes e do opencode atualizados com a versão do CLI observada.

## Testes

Ponto de teste: os leitores dos CLIs (arquivos e bancos sintéticos → eventos).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments

Implementado em 2026-10-13 (branch `ticket/02-ajustes-dos-adapters`). Só estrutura e contagens dos dados
reais; nenhum conteúdo foi lido nem versionado.

- **`agent_message` é fala entre agentes**, não a fala do agente ao Lucas (autor e destinatário são caminhos
  `/root` e `/root/<nome>`): vira narração mesmo assim (D-089), com o autor no corpo nativo (D-125).
- **`inter_agent_communication_metadata`** (só `trigger_turn`) e **`thread_settings_applied`** (o modelo já
  vem de `turn_context`) ficam ignorados, com o motivo em `docs/adapters/CODEX.md` §8 (D-124).
- **Fidelidade:** Hermes e opencode seguem `raw`, agora confirmado pela estrutura no modelo observado (todo o
  texto guardado explica os tokens de saída); o Hermes passa a marcar `summary` quando a linha traz itens da
  Responses API (`codex_reasoning_items`) (D-126 e D-127).
- **Dúvidas que seguem abertas** (em `docs/adapters/HERMES.md` §1 e `OPENCODE.md` §2): modelos gpt-5.x pelo caminho
  de chat e Anthropic no Hermes; só um modelo foi observado nos dois CLIs.
- Versões: Codex `0.160.1` (rollouts de `0.142.5` a `0.162.0`), Hermes `0.20.5`, opencode `2.0.23`.
- Decisões confirmadas pelo Lucas em 2026-10-13: D-124 a D-127 (antes Q-T02-1 a Q-T02-4) em `docs/DECISIONS.md`.
- **Revisão de spec (2026-10-13):** a conferência achou que a mesma fala de `agent_message` pode estar gravada
  em dois rollouts (124 textos distintos em 184 linhas; 6 na raiz e num subagente): corrigido o texto de
  CODEX.md §8 e ampliada a Q-T02-2 (D-125: sem deduplicar). Também registrados: o modelo dos subagentes não é lido (D-124), a coluna
  `reasoning` do Hermes recebe texto de fase `commentary` (HERMES.md §1, dúvida 4) e o rollout `0.162.0` (VS Code).
- **Não tratado aqui:** o achado do ticket 01 (abertura de sessão e de subagente do Claude e do Hermes usa a hora da
  leitura, e 117 de 120 subagentes ficam "sem sinal") apontava "ticket 02 ou 03". Não está nos critérios deste
  ticket; o Lucas decidiu em 2026-10-13 que ele é tratado no ticket 03 (D-128).
