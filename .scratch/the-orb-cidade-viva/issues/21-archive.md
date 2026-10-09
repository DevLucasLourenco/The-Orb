# 21: Archive

Status: ready-for-agent
Blocked by: 03
Origem: R45; D-079
Spec: [../spec.md](../spec.md)

## O que construir

Uma aba Archive no Inner World lista o que molda a sessão (`CLAUDE.md`, `AGENTS.md`, skills,
memória de cada provider), só com nome, tamanho e data; o conteúdo aparece só quando o Lucas abre um
arquivo. Nada é alterado nem reenviado ao agente.

## Critérios de aceite

- [ ] Onde cada provider guarda instruções, skills e memória levantado só pela estrutura e registrado nos adapters.
- [ ] Aba Archive com nome, tamanho e data.
- [ ] Conteúdo só sob pedido explícito do Lucas.
- [ ] Somente leitura; nunca grava nem reinjeta nada.

## Testes

Ponto de teste: as leituras do mundo real (pastas falsas → lista do Archive).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
