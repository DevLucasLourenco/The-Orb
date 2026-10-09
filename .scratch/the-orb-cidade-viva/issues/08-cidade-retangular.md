# 08: Cidade retangular

Status: ready-for-agent
Blocked by: 03, 07
Origem: R32, R12a; D-046, D-047, D-099
Spec: [../spec.md](../spec.md)

## O que construir

A cidade vira um retângulo com bairros por letra inicial, em ordem alfabética como um texto, e
lotes em ordem alfabética. Cada prédio tem um pequeno deslocamento e giro tirados do nome: parece
orgânico, mas é sempre o mesmo lugar. O traçado é calculado no mundo e o cliente só desenha.

## Critérios de aceite

- [ ] O mundo calcula bairros, lotes, deslocamento e giro pela semente do nome (VISUAL.md §7).
- [ ] Projeto novo só reorganiza o seu bairro; realm escondido deixa o lote vago.
- [ ] Números e símbolos num bairro "#" no começo; só existem bairros de letras com realm.
- [ ] Placa com a letra do bairro no chão, na esquina.
- [ ] Chão retangular com ruas entre os bairros, como cenário neutro; a grade polar sai.
- [ ] Os atalhos 1–9 e o voo da câmera continuam funcionando.

## Testes

Ponto de teste: o mundo (lista de realms → traçado; estabilidade ao incluir e esconder).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
