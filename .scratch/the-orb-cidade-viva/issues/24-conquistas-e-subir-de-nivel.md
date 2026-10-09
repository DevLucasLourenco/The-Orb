# 24: Conquistas e subir de nível

Status: ready-for-agent
Blocked by: 15, 23
Origem: R55; D-109, D-110
Spec: [../spec.md](../spec.md)

## O que construir

As 16 conquistas iniciais passam a valer, cada uma com o seu recibo e sem XP; uma conquista nova
gera um aviso curto no HUD, e subir de nível faz um anel de luz neutra subir pelo personagem.

## Critérios de aceite

- [ ] As 16 conquistas de PROGRESSION.md §5 numa tabela, cada uma com a condição sobre dado observado e o recibo.
- [ ] Conquistas não dão XP.
- [ ] Aviso de conquista nova (V-HUD-14) e anel ao subir de nível (V-EGO-14), em branco neutro.
- [ ] Conquistas que dependem de dados ainda não existentes ficam registradas como pendentes, sem inventar.

## Testes

Ponto de teste: o mundo (eventos → conquistas), por tabela de casos.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
