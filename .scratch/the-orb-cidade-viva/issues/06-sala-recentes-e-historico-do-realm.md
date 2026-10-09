# 06: Sala com sessões recentes e Histórico do realm

Status: ready-for-agent
Blocked by: 01, 03
Origem: R28, R28a, R48 (camada 2); D-024, D-027, D-035, D-059, D-087
Spec: [../spec.md](../spec.md)

## O que construir

Na sala ficam as sessões ativas e as dos últimos 10 dias; as mais antigas vão para o Histórico do
realm, no overview, e nenhuma some. Um realm sem sessão nos últimos 10 dias fica de "noite". O conteúdo
das sessões passa a ser lido só para as que estão na sala, a 250 ms nos realms com sessão ativa.

## Critérios de aceite

- [ ] O mundo separa sessões da sala (ativas + últimos 10 dias) das do Histórico do realm, pela hora recebida.
- [ ] Sessões encerradas continuam existindo: na sala enquanto recentes, depois no Histórico.
- [ ] O overview tem o Histórico do realm: nome, provider, título e datas de cada sessão antiga.
- [ ] Realm sem sessão nos últimos 10 dias: sala do teto apagada ("noite"); acende quando surge uma sessão.
- [ ] Conteúdo lido incrementalmente só das sessões da sala; leitura a 250 ms nos realms com sessão ativa; varredura de sessões novas a cada 2 s.
- [ ] O prazo de 10 dias vem de um valor que o ticket 07 tornará configurável.

## Testes

Ponto de teste: o mundo (eventos + hora) e os leitores dos CLIs (seleção do que é lido).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
