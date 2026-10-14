# 10: Formas por classe e andares

Status: concluído (2026-10-14)
Blocked by: 08, 09
Origem: R41, R19; D-052, D-072, D-075, D-099
Spec: [../spec.md](../spec.md)

## O que construir

Cada prédio ganha a altura absoluta da sua classe, a forma arquitetônica aprovada (Casa a
Arranha-céu), as cintas de luz neutra no topo e a antena no Arranha-céu. Cada pasta de primeiro nível
vira um andar proporcional às suas linhas, com os arquivos da raiz no térreo e as pastas pequenas em
"demais pastas". O mundo calcula; o cliente desenha.

## Critérios de aceite

- [x] O mundo calcula altura em níveis (saltos entre classes, crescimento logarítmico dentro da classe) e os andares por pasta.
- [x] Andares: arquivos da raiz no térreo; cada andar com pelo menos um nível; excedentes juntos em "demais pastas".
- [x] O cliente desenha as 6 formas de VISUAL.md §8, com o Rooftop Room sempre do mesmo tamanho no topo.
- [x] Cintas neutras (uma a mais por classe) e antena no Arranha-céu.
- [x] Nenhuma cor de significado nas formas.

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

Implementado em 2026-10-14 (branch `ticket/10-formas-por-classe-e-andares`). Só estrutura e contagens dos dados reais.

- **O que mudou:** `core/building.py` (`levels`, `floors`) e as tabelas `rules.BUILDING_LEVELS`, `BUILDING_TRIM`, `ANTENNA_CLASSES`, `CITY_MAX_BASE`; o snapshot passa a ter, em
  `realm.metrics`, `levels`, `bands`, `antenna` e `floors`; o Probe conta a raiz e cada pasta de primeiro nível (`Count.root`, `Count.folders`) e o evento `realm.metrics` leva
  `root` e `folders` (as 64 maiores; validação em `protocol/events.py`); no cliente, `realm3d.js` desenha as 6 formas (`SHAPES`), as cintas, a coroa e a antena, e a sala do teto sobe
  e desce com a altura.
- **Testes:** 27 em `tests/test_building.py` (níveis por classe, saltos, logaritmo, andares, junção em "demais pastas") e os novos de `test_realm_metrics.py`, `test_probes.py` e
  `test_line_scheduler.py`.
- **Decisões:** o Lucas confirmou Q-T10-1 a Q-T10-6 em 2026-10-14 (D-166 a D-171 em `docs/DECISIONS.md`). PR 9 mesclado.
- **Dados reais (pasta do Orb temporária; só estrutura):** 18 dos 23 realms contados, com as seis classes presentes (7 Sobrados, 4 Prédios, 3 Torres, 2 Edifícios, 1 Casa e 1 Arranha-céu),
  de 1 a 36 níveis e de 1 a 18 andares; a soma dos níveis dos andares é a altura do prédio em todos. Na tela: prédios de alturas e formas diferentes e a sala do teto igual em todos; o
  voo para um realm (atalho `2`) e o Esc funcionaram; console sem erros. As seis formas também foram conferidas numa página temporária com métricas sintéticas (não versionada).
- **O que não foi visto:** a fachada ainda usa a textura decorativa de antes (as janelas de verdade são o ticket 11), então ela segue contradizendo a R12; os **andares não são
  desenhados** (só calculados); a posição real de uma Torre ao lado de outra no mesmo bairro (a maior largura, 30, cabe no lote de 46 pela conta, não vi um par na tela).

**Revisões (`/code-review`, padrões e spec):** nenhuma violação dura de invariante. Tratado: o realm sem contagem era idêntico à Casa (agora é só uma laje lisa, sem janelas); o Sobrado não tinha
terraço em volta da sala (corpo de 22 sobre a sala de 18); o térreo se juntava no prédio de 1 nível (o andar único agora é o térreo); a altura do Arranha-céu truncava enquanto as outras
classes arredondavam; o desempate dos níveis dos andares usava ponto flutuante (agora inteiros); o parâmetro `levels` de `floors` escondia a função de mesmo nome (agora `height`); o nome de
pasta do evento aceitava barra; o PROTOCOL não dizia o limite de 255; o R41 dizia "falta ver na tela" depois de vista. **Não corrigido, com motivo:** a divisão da altura entre os blocos
(`tierLevels`) e a coroa ficam no cliente, por serem desenho (forma), e não têm teste porque o ponto de teste do projeto é o mundo (D-099); `BUILDING_TRIM` é o índice da classe, mas fica em tabela
própria para a marca poder mudar sem mexer na ordem das classes; `_biggest` e `floors` ordenam do mesmo jeito (maior primeiro, depois o nome), cada um no seu módulo (o Probe não importa o Core);
a `RULES.md` R32 e a caixa marcada do ticket 08 entram aqui porque o voo da câmera pendente do 08 foi visto na conferência deste ticket; `floors` vai no snapshot sem uso no cliente porque o ticket 11
o usa (V-REALM-12).
