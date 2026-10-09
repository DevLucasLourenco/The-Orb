# 17: Gate

Status: ready-for-agent
Blocked by: 08, 15, 16
Origem: R35, R46; D-061, D-080
Spec: [../spec.md](../spec.md)

## O que construir

Um portão na borda da cidade, de frente para a câmera inicial, mostra quantos Alter Egos esperam o
Lucas. Clicando, ele vê a lista de esperas de todos os realms e escreve para qualquer Alter Ego pelo
terminal dele; para uma sessão fechada, o Gate oferece reabrir e espera a confirmação.

## Critérios de aceite

- [ ] Portão no mundo, fora dos bairros, com a contagem de esperas.
- [ ] Lista de esperas de todos os realms, com o realm, o Alter Ego e o que ele pede.
- [ ] Escrever para um Alter Ego vai para o terminal dele, como se o Lucas tivesse digitado; não existe comando de aprovação.
- [ ] Sessão fechada: o Gate oferece reabrir (ticket 15) e só reabre com confirmação.
- [ ] Entrada V-CITY-7 conferida.

## Testes

Ponto de teste: o mundo (esperas de todos os realms) e o servidor com terminal falso.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
