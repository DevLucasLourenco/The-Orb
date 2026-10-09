# 20: Energy

Status: ready-for-agent
Blocked by: 01, 09
Origem: R43, R49; D-077
Spec: [../spec.md](../spec.md)

## O que construir

Tokens e custo só quando o provider informa, nunca estimados: por sessão e por realm no overview, o
total de hoje na barra de cima e um painel com os limites de uso da conta.

## Critérios de aceite

- [ ] O mundo soma `usage` por sessão, por realm e no dia (pela hora recebida).
- [ ] O adapter do Hermes passa a ler os totais de tokens por sessão.
- [ ] Sinal `account.limits` a partir de `account/rateLimits/updated` do Codex; o mundo guarda os limites do mundo.
- [ ] Barra de cima com o total de hoje; painel de Energy com os limites.
- [ ] Nada estimado: sem dado do provider, nada aparece.

## Testes

Ponto de teste: os leitores dos CLIs e o mundo (usos e limites → Energy).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
