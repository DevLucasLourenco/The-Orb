# 05: Cores e áreas

Status: ready-for-agent
Blocked by: None (can start immediately)
Origem: R20c, R30; D-036, D-037, D-040; V-PEND-7d
Spec: [../spec.md](../spec.md)

## O que construir

Os personagens ganham as cores dos providers (Claude laranja, Codex azul, Hermes amarelo,
opencode cinza), as áreas perdem a cor própria e passam a ser identificadas por ícone, nome e um padrão
no piso, e tudo o que indica "esperando você" vira magenta pulsante. Os tons exatos e os ícones passam
antes por uma prévia que o Lucas aprova.

## Critérios de aceite

- [x] Uma prévia visual com os tons dos providers, do magenta e os ícones das 5 áreas é mostrada ao Lucas; **só depois da aprovação** os valores entram em VISUAL.md §5 e no cliente.
- [x] Personagens e pontos da lista de realms nas cores aprovadas.
- [x] Áreas sem cor: piso neutro, ícone, nome e padrão.
- [x] "Esperando você" em magenta pulsante em todos os lugares: feixe e anel do prédio, arestas da sala e o marcador sobre a cabeça (hoje âmbar).
- [x] Nenhuma cor fora do orçamento (git nas janelas, provider nos personagens, magenta para espera).

## Testes

Ponto de teste: conferência no preview (o cliente só desenha; sem lógica de domínio a testar).

## Observação

Tem um ponto de parada com o Lucas (aprovação da prévia) antes de concluir.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments

- **Prévia:** mostrada ao Lucas antes de escrever qualquer valor; aprovada como mostrada (`previa05`, D-187). O cinza do opencode, claro: `qt05-1`, D-188.
- **O que mudou:** `providers.js` (os quatro tons e `WAIT_COLOR`), `avatar.js` (marcador magenta), `realm3d.js` (áreas sem cor, decalque com ícone e padrão, feixe, anel e arestas magenta), `areaicons.js` (novo: ícones e padrões das cinco áreas) e `styles.css` (providers e espera). Docs: VISUAL (V-REALM-5, 6, 8, V-EGO-1, 6, §5, V-PEND-7d), RULES (R20c, R30), IDEAS, ARCHITECTURE, DECISIONS (D-187, D-188 e a rodada Q-T05).
- **Testes:** nenhum novo. O ponto de teste do ticket é a conferência no preview (o cliente só desenha, D-099). Suíte inteira: 589 passed, 2 skipped; `node --check` em todos os módulos do cliente.
- **Conferido na tela**, numa página temporária (não versionada) com um prédio sintético: um personagem de cada provider, um esperando e um subagente sem sinal. Console sem erros; o opencode claro se distingue do sem sinal escuro; as cinco áreas aparecem com piso neutro, padrão e ícone; o feixe, o anel, as arestas, o marcador e o rótulo estão em magenta. Servidor de prévia encerrado.
- **Não verificado:** o tom renderizado com o *tone mapping* e a luz da cena, comparado com a prévia aprovada (a prévia foi desenhada em canvas plano); um prédio real com sessões reais; o Hermes `#ffd60a` ao lado das janelas âmbar (`#E2C08D`) de um prédio com alterações do git; o painel (contador, selo, cartão, chip, aviso) em magenta, que só foi conferido pelo código e pelo CSS; a visão de longe da cidade com vários prédios esperando.
- **Pontos abertos, provisórios (P2):** Q-T05-2 (arestas e anel azuis de repouso ficam), Q-T05-3 (o desenho do piso: cinza `#2a3550`, padrão a 16%, ícone no fundo da área), Q-T05-4 (o magenta também no painel e nos rótulos). Em `docs/DECISIONS.md`.
- **Ruff:** `ruff check src tests` aponta 47 avisos, todos em arquivos que este ticket não tocou (nenhum arquivo Python mudou).

**Revisões (`/code-review`, padrões e spec):** nenhuma violação dura. Tratado: o marcador sobre a cabeça e as arestas da sala só trocavam de cor e agora pulsam, como o feixe e o anel (R20c pede magenta *pulsante*); os valores de neutros, do magenta e do texto do selo entraram na VISUAL §5; o azul de repouso virou a constante `ROOM_REST` e o magenta uma só `WAIT` no `realm3d.js`; `areaDecal` falha com mensagem clara se a área não está em `AREA_MARKS`; a coluna Situação da R20c passou a ⚠️ (falta confirmar Q-T05-2 e Q-T05-3) e a data do IDEAS foi atualizada. **Não corrigido, com motivo:** os hex repetidos em `styles.css` e `providers.js` (o CSS não importa módulos; já era assim); `AREAS` e `AREA_MARKS` com as mesmas cinco chaves (juntar acoplaria o traçado ao desenho); o `--err` do chip de erro e o azul de repouso, que já existiam (Q-T05-2); o painel em magenta e os ajustes do piso, que o spec não pedia e estão em Q-T05-3 e Q-T05-4; o ticket continua `ready-for-agent` até o merge.
