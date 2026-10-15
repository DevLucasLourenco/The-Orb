# 12: Papel, atributos por área e árvore da Team

Status: ready-for-agent
Blocked by: 01
Origem: R40, R57; D-069, D-096, D-116
Spec: [../spec.md](../spec.md)

## O que construir

No overview, cada Alter Ego mostra o seu papel ("revisor", "pesquisador"…), barras com a parcela do
trabalho em cada área e a árvore da Team (quem criou quem), tudo pela contagem das atividades
observadas, sem nenhuma chamada a modelo.

## Critérios de aceite

- [x] Papel derivado do que a sessão mais fez, por uma tabela de regras (atividade → papel).
- [x] Atributos: parcela do trabalho em cada área, pela mesma contagem.
- [x] Árvore da Team no overview, com tipo e estado de cada subagente; no mundo nada muda.
- [x] Nenhum módulo chama modelo de IA.

## Testes

Ponto de teste: o mundo (eventos de atividade → papel, atributos e árvore).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments

- **O que mudou:** `core/rules.py` (`ATTRIBUTE_AREAS`, `ROLE_BY_AREA`), `core/profile.py` (novo: `tally`, `role`, `attributes`, `team_order`), `core/world.py` (o Alter Ego guarda a contagem por área; o snapshot ganha `role`, `attributes` e `depth` na lista `team`), `clients/web/js/hud.js` e `styles.css` (etiqueta do papel, barras, árvore). Docs: RULES (R40, R57), VISUAL (V-HUD-8, 16, 17), ARCHITECTURE, DECISIONS (rodada Q-T12).
- **Testes:** `tests/test_profile.py` (19 casos): o papel por atividade, o papel que muda com a contagem, a parcela por área em ordem fixa, empate sem papel, sessão sem contagem, atividades sem área e da Team fora da conta, sessões separadas, evento repetido contado uma vez, as tabelas, a árvore (pai antes dos filhos, filho antes do pai, pai desconhecido ou o próprio, laço). Suíte inteira: 608 passed, 2 skipped; ruff sem aviso nos arquivos do Core; `node --check` no cliente.
- **Conferido na tela**, numa página temporária (não versionada) que desenha o overview com um snapshot real do mundo feito de eventos sintéticos: a etiqueta "revisor", as quatro barras com a porcentagem, a árvore com recuo (Explore › Plan › Review), o concluído sem filho ativo fora da lista e a sessão em empate sem etiqueta. Console sem erros; servidor de prévia encerrado.
- **Não verificado:** sessões reais dos quatro CLIs (o papel só nasce do que o Orb viu chegar, Q-T12-6); subagentes aninhados de verdade (hoje só o Codex informa o pai, e o Claude não); o overview com muitos subagentes (os Codex chegam a centenas); o mundo 3D, que não mudou.
- **Decisões a confirmar:** Q-T12-1 a Q-T12-6 em `docs/DECISIONS.md` (provisórias, P2).
