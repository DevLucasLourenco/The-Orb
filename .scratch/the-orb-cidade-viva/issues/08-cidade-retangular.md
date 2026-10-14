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

- [x] O mundo calcula bairros, lotes, deslocamento e giro pela semente do nome (VISUAL.md §7).
- [x] Projeto novo só reorganiza o seu bairro; realm escondido deixa o lote vago.
- [x] Números e símbolos num bairro "#" no começo; só existem bairros de letras com realm.
- [x] Placa com a letra do bairro no chão, na esquina.
- [x] Chão retangular com ruas entre os bairros, como cenário neutro; a grade polar sai.
- [ ] Os atalhos 1–9 e o voo da câmera continuam funcionando. (a lógica não mudou; o voo não pôde ser visto: ver Comments)

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

Implementado em 2026-10-14 (branch `ticket/08-cidade-retangular`). Só estrutura e contagens dos dados reais.

- **O que mudou:** `core/city.py` (`plan`, `district_letter`, `seed`) e a tabela `rules.CITY_*`; `World.layout()` e, no snapshot, `city` (bairros, tamanho, calçada)
  e `place` em cada realm; o Hub passa a dar lote a todo realm detectado (antes de qualquer leitura); no cliente, `scene.js` (`setCity`: laje, calçadas, placas;
  a grade polar saiu), `realm3d.js` (`setPlace` com giro; os lugares do piso giram junto) e `main.js` (posiciona o que o mundo mandou e abre na visão geral).
- **Testes:** 21 em `tests/test_city.py` (letras, ordem de leitura, 16:9, semente fixa, limites do deslocamento, estabilidade ao incluir e esconder, mundo) e 1 no Hub.
- **Decisões:** o Lucas confirmou Q-T08-1 a Q-T08-7 em 2026-10-14 (D-159 a D-165 em `docs/DECISIONS.md`). **Aguarda:** o envio do PR e ver o voo da câmera na tela.
- **Dados reais (pasta do Orb temporária; só contagens):** 23 realms, 23 com lote, 10 bairros; o chão retangular, as letras no chão e os prédios girados apareceram na tela.
- **O que não foi visto:** o painel do navegador estava oculto (a janela do Claude em segundo plano) e não desenhou mais quadros; assim, o voo da câmera
  (atalhos 1–9, F, Esc e a visão geral) **não foi conferido na tela**. Ficou só o que o primeiro quadro mostrou. A proporção desta máquina era 1,13 antes de eu escolher a quebra mais próxima de 16:9; o traçado só depende
  da quantidade de realms por letra, e o mesmo desenho com nomes sintéticos dá 2,25 (a tela real não foi reaberta com essa correção).

**Revisões (`/code-review`, padrões e spec):** nenhuma violação dura. Tratado: a geometria-molde da borda do chão não era descartada; a chave de cache do chão ignorava a calçada;
números soltos do chão mínimo (260 × 150) agora têm nome e estão na VISUAL §7; tuplas posicionais e um alias inútil em `core/city.py`; a VISUAL dizia "nenhuma cor nova" e a
calçada e a letra da placa são dois tons novos da mesma família azul (corrigido o texto); V-CITY-4 passa a ⚠️ até as decisões; Q-T08-5 diz como lê "só existem bairros de letras com realm".
**Não corrigido, com motivo:** o Hub chamar `world.add_realm` ao montar o snapshot (idempotente; o `poll_once` já faz o mesmo e é o jeito de dar lote ao realm detectado
entre duas leituras); a estabilidade só de lote e giro, que é a Q-T08-1 aguardando o Lucas; a abertura na visão geral e a sombra da lua redimensionada, que são consequência de a cidade
ter outro tamanho (Q-T08-7). O critério dos atalhos 1–9 e do voo segue aberto até alguém ver o voo na tela.
