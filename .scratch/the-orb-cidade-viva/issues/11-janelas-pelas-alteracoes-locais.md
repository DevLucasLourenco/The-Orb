# 11: Janelas pelas alterações locais

Status: ready-for-agent
Blocked by: 10
Origem: R20, R20a, R20b, R20d, R20e, R12; D-038 a D-043, D-092, D-115
Spec: [../spec.md](../spec.md)

## O que construir

As janelas deixam de ser decoração aleatória: acendem onde há alterações locais do git, no andar
da pasta e na cor do tipo de alteração (paleta do VS Code). Cada janela vale 5% das alterações, sem
nunca dividir uma alteração. O git é lido sem gravar nada.

## Critérios de aceite

- [x] Leitura do git só leitura (sem tocar no `.git`): alterações locais com tipo e linhas alteradas; submódulos ignorados; sinal `realm.changes`.
- [x] O mundo calcula a fachada de VISUAL.md §6: pacotes por andar e tipo, x = 5%, nada dividido, ordem estável pelo caminho, distribuição regular no andar.
- [x] x configurável na tela de configurações.
- [x] Janela só acesa ou apagada, com brilho fixo (sai o brilho geral por atividade, D-115).
- [x] Cores exatamente as de VISUAL.md §5.
- [x] O padrão aleatório de janelas some do cliente.

## Testes

Ponto de teste: as leituras do mundo real (repositório git falso → `realm.changes`) e o mundo (alterações → fachada).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments

Implementado em 2026-10-14 (branch `ticket/11-janelas-pelas-alteracoes-locais`). Só estrutura e contagens dos dados reais.

- **O que mudou:** `probes/git.py` (o jeito único de falar com o git, só leitura) e `probes/changes.py` (`git_changes`: alterações com tipo e linhas); o sinal `realm.changes`
  (protocolo 0.3, com o vocabulário `CHANGE_TYPES` e os limites validados na borda); `core/facade.py` (`windows`: pacotes por andar e tipo, x%, nada dividido, ordem pelo caminho,
  distribuição regular) e `World` (guarda a leitura por realm e entrega `facade` no snapshot); `gateway/probes.py` (a base `RealmScheduler` e o `ChangeScheduler`, a cada 15 s por realm);
  a opção `window_percent` (x) na tabela `SETTINGS`; no cliente, `realm3d.js` desenha as janelas por lado e bloco, na cor do tipo, com o vidro apagado nas outras posições, e a textura
  aleatória e o brilho por atividade saíram.
- **Testes:** `test_changes.py` (25, com um repositório git de verdade, só leitura), `test_facade.py` (22), `test_change_scheduler.py` (8) e o ajuste de `test_realms.py`.
- **Decisões:** o Lucas confirmou Q-T11-1 a Q-T11-9 em 2026-10-15 (D-172 a D-180 em `docs/DECISIONS.md`). **Aguarda:** o envio do PR.
- **Dados reais (pasta do Orb temporária; só estrutura):** 23 realms; 18 com contagem de linhas e leitura do git, e portanto com fachada; 16 limpos (vidro todo apagado) e 2 com alterações
  (2 e 18 alterações, em 2 e 14 janelas, dos tipos modificado e não rastreado); nenhuma janela fora da grade. Na tela, numa página temporária (não versionada) com janelas sintéticas dos seis
  tipos: as janelas acesas nas cores do git, o vidro apagado visível, o prédio sem leitura do git liso; console sem erros.
- **O que não foi visto:** as janelas dos dados reais de perto (o ângulo de câmera do preview não mostrou a fachada do prédio com alterações); as seis cores lado a lado, com ACES e brilho, não
  foram comparadas com os hex da VISUAL §5 pixel a pixel (a tabela do cliente tem os seis valores exatos); a leitura de um repositório grande demais (o custo contínuo do `git status`
  a cada 15 s por realm não foi medido, só a subida); o contador de linhas segue por minuto (ver Q-T11-5).

**Revisões (`/code-review`, padrões e spec):** nenhuma violação dura. Tratado: um caminho que o protocolo recusaria derrubava o evento inteiro (agora o Probe o descarta e conta em `more`, e a validação ficou
mais estrita: sem segmentos vazios, `.`, `..`, NUL nem letra de unidade); o peso de um arquivo novo contava só linhas não vazias e o `numstat` conta todas (agora todas); a impressão digital não incluía `more`;
`_floor_of` refazia o índice dos andares a cada alteração; a fachada levava `8` e `4` repetidos no cliente (agora o mundo manda `cols` e `faces`); a textura do vidro era recriada em cada lado; a base dos
agendadores agora é abstrata; o risco residual do filtro `clean` do git ficou anotado em `probes/git.py`; textos desatualizados na VISUAL ("hoje padrão aleatório", "proposta para validar", "as janelas chegam no ticket 11")
e na R20a (o tom renderizado não foi comparado pixel a pixel). **Não corrigido, com motivo:** o corte em 5.000 faz o x% ser das alterações que vieram (declarado na Q-T11-4 e na VISUAL); a regra de dobrar a capacidade
de um andar cheio é a Q-T11-7; `ChangeScheduler.notes` (por que um realm não tem leitura) fica como diagnóstico, sem aparecer na tela de configurações, para não acrescentar tela fora do ticket; `Change` existe no Core e
no Probe porque o Core não importa os Probes; o desenho refaz o corpo quando as janelas mudam (no máximo a cada 15 s por realm); o ticket continua `ready-for-agent` até o merge.
