# 01: O mundo calcula o tempo

Status: ready-for-agent
Blocked by: None (can start immediately)
Origem: R47, R31, R7; D-044, D-045, D-050, D-086
Spec: [../spec.md](../spec.md)

## O que construir

O Lucas vê "dormindo" e o subagente "sem sinal" decididos pelo servidor, iguais em qualquer
cliente. O mundo passa a devolver o estado para uma hora dada e, com uma tabela de limites, deriva o
que depende do tempo; o cliente para de calcular e só desenha. O subagente sem sinal deixa de sumir:
fica cinza translúcido, sem halo e com o ícone de sinal cortado.

## Critérios de aceite

- [ ] O estado do mundo é pedido com uma hora; o mundo não lê relógio nenhum.
- [ ] Os limites (dormindo 15 min, sem sinal 5 min) ficam numa tabela de regras do mundo.
- [ ] Sessão parada há mais de 15 min aparece "dormindo" no estado do mundo; o cliente só desenha.
- [ ] Subagente sem atividade há 5 min e sem sinal de fim aparece "sem sinal" (não some); o opencode continua cinza sólido com halo.
- [ ] O cliente não tem mais nenhum cálculo de tempo para esses estados.
- [ ] O servidor envia o estado com a hora dele e reavalia periodicamente, sem esperar evento novo.

## Testes

Ponto de teste: o mundo (eventos sintéticos + horas diferentes → estados).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
