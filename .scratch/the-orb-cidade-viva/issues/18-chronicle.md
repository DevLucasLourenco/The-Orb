# 18: Chronicle

Status: ready-for-agent
Blocked by: 04, 11
Origem: R44, R36; D-078
Spec: [../spec.md](../spec.md)

## O que construir

Uma barra de tempo no rodapé: arrastando, o Lucas vê a cidade como era (prédios, personagens,
janelas) em qualquer momento desde que o Orb começou a registrar.

## Critérios de aceite

- [ ] O registro local grava os eventos do mundo necessários para reconstruir a cidade.
- [ ] O mundo reconstrói o estado de qualquer momento a partir do registro.
- [ ] Barra de tempo no rodapé; soltar volta ao presente.
- [ ] Nada do conteúdo das sessões é copiado para o registro.

## Testes

Ponto de teste: o mundo (registro → estado num momento passado).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
