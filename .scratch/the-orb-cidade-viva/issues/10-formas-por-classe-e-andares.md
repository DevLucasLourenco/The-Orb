# 10: Formas por classe e andares

Status: ready-for-agent
Blocked by: 08, 09
Origem: R41, R19; D-052, D-072, D-075, D-099
Spec: [../spec.md](../spec.md)

## O que construir

Cada prédio ganha a altura absoluta da sua classe, a forma arquitetônica aprovada (Casa a
Arranha-céu), as cintas de luz neutra no topo e a antena no Arranha-céu. Cada pasta de primeiro nível
vira um andar proporcional às suas linhas, com os arquivos da raiz no térreo e as pastas pequenas em
"demais pastas". O mundo calcula; o cliente desenha.

## Critérios de aceite

- [ ] O mundo calcula altura em níveis (saltos entre classes, crescimento logarítmico dentro da classe) e os andares por pasta.
- [ ] Andares: arquivos da raiz no térreo; cada andar com pelo menos um nível; excedentes juntos em "demais pastas".
- [ ] O cliente desenha as 6 formas de VISUAL.md §8, com o Rooftop Room sempre do mesmo tamanho no topo.
- [ ] Cintas neutras (uma a mais por classe) e antena no Arranha-céu.
- [ ] Nenhuma cor de significado nas formas.

## Testes

Ponto de teste: o mundo (métricas → níveis e andares) e conferência no preview para as formas.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
