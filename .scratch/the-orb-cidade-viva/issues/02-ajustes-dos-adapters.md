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

- [ ] Linhas `response_item/agent_message` do rollout do Codex viram narração no Inner World, com o nome nativo.
- [ ] `inter_agent_communication_metadata` e `event_msg/thread_settings_applied` avaliados pela estrutura; a decisão (mapear ou ignorar, e por quê) fica no documento do adapter do Codex.
- [ ] A fidelidade do pensamento do Hermes e do opencode é confirmada só pela estrutura (campos e contagens, sem ler conteúdo) e o adapter marca `raw` ou `summary` conforme o resultado; sem como confirmar, a dúvida fica registrada no documento do adapter.
- [ ] Documentos dos adapters do Codex, do Hermes e do opencode atualizados com a versão do CLI observada.

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
