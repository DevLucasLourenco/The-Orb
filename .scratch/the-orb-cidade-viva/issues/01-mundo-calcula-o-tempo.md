# 01: O mundo calcula o tempo

Status: implementado
Blocked by: None (can start immediately)
Origem: R47, R31, R7; D-044, D-045, D-050, D-086
Spec: [../spec.md](../spec.md)

## O que construir

O Lucas vê "dormindo" e o subagente "sem sinal" decididos pelo servidor, iguais em qualquer
cliente. O mundo passa a devolver o estado para uma hora dada e, com uma tabela de limites, deriva o
que depende do tempo; o cliente para de calcular e só desenha. O subagente sem sinal deixa de sumir:
fica cinza translúcido, sem halo e com o ícone de sinal cortado.

## Critérios de aceite

- [x] O estado do mundo é pedido com uma hora; o mundo não lê relógio nenhum.
- [x] Os limites (dormindo 15 min, sem sinal 5 min) ficam numa tabela de regras do mundo.
- [x] Sessão parada há mais de 15 min aparece "dormindo" no estado do mundo; o cliente só desenha.
- [x] Subagente sem atividade há 5 min e sem sinal de fim aparece "sem sinal" (não some); o opencode continua cinza sólido com halo.
- [x] O cliente não tem mais nenhum cálculo de tempo para esses estados.
- [x] O servidor envia o estado com a hora dele e reavalia periodicamente, sem esperar evento novo.

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

Implementado em 2026-10-09 na branch `ticket/01-mundo-calcula-o-tempo`; falta a revisão e o merge.
**Fora do que o ticket pedia, decidido na implementação (confira):**

- Um subagente "sem sinal" **deixa de manter o líder em `DELEGATING`**. Sem isso, um subagente em
  segundo plano que nunca avisa o fim mantinha a sessão "delegando" para sempre e ela nunca dormia.
- **Qualquer evento do subagente** conta como atividade (antes, só os que traziam sinal).
- O total de subagentes ativos de Mankind passa a **não contar** os sem sinal (não se sabe que estão ativos).
- A hora do snapshot precisa ter fuso; data ilegível no evento não quebra nada (o mundo não afirma nada).

**Verificação ao vivo:** console do navegador sem erros; o canal `/world` entrega `asleep` e
`no_signal` com dados reais (8 sessões, 1 dormindo, 119 subagentes). O desenho do ícone de sinal
cortado no 3D ainda não foi visto numa sessão real com subagente sem sinal.

**Observação para o ticket 06:** o primeiro poll com os 19 realms demora mais de 100 s e aplica
~10 mil eventos antes de aparecer a primeira sessão (já era assim; é o que a leitura em duas camadas, R48, resolve).

