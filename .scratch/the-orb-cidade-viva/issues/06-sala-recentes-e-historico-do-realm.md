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

- [x] O mundo separa sessões da sala (ativas + últimos 10 dias) das do Histórico do realm, pela hora recebida.
- [x] Sessões encerradas continuam existindo: na sala enquanto recentes, depois no Histórico.
- [x] O overview tem o Histórico do realm: nome, provider, título e datas de cada sessão antiga.
- [x] Realm sem sessão nos últimos 10 dias: sala do teto apagada ("noite"); acende quando surge uma sessão.
- [x] Conteúdo lido incrementalmente só das sessões da sala; leitura a 250 ms nos realms com sessão ativa; varredura de sessões novas a cada 2 s.
- [x] O prazo de 10 dias vem de um valor que o ticket 07 tornará configurável.

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

Implementado em 2026-10-13 (branch `ticket/06-sala-com-sessoes-recentes-e-historico-do-realm`). Só estrutura e contagens dos dados reais.

- **O que mudou:** `rules.RECENT_SESSION_SECONDS` (10 dias, um só valor), `World(recent_seconds=...)`, `in_room` por Alter Ego, `night` por realm,
  `World.add_realm` e `World.any_active`; o Observatório lê só a sala (`since` = 10 dias; `fresh_after` separa o replay), anuncia a
  presença das sessões da sala pelo índice e entrega o Histórico do realm; o Hub fala `history` no `/world` e escolhe o ritmo
  (250 ms com sessão ativa, 2 s sem); o cliente mostra só a sala, apaga a sala do teto de noite e lista o Histórico no overview.
- **Testes:** `test_core.py` (janela, noite, `add_realm`, `time_key`), `test_adapter_claude.py` e `test_adapter_codex.py` (seleção do que é
  lido), `test_realms.py` (presença pelo índice, histórico, noite, ritmo, mensagem `history`). Suíte: 346 → 365 passed, 1 skipped.
- **Conferido com dados reais** (pasta do Orb temporária; só contagens): 23 realms, 15 de noite e 8 acesos; 34 sessões na sala (27 dormindo), 34
  nomes distintos; 79 sessões no Histórico dos 4 providers, nenhuma com nome; sem erro de leitor; console sem erros; o servidor usou ~130 MB.
- **Revisões (2026-10-13):** padrões e spec feitas; corrigidos: nomes do Histórico em uma consulta e fora do loop, o Observatório reusa `rules.in_room` e a hora do Hub, a janela de leitura anda com a sala (antes era fixa na subida), o Histórico mostra "N de TOTAL" em vez de cortar em silêncio, Mankind conta só a sala, o Histórico do cliente se atualiza quando uma sessão entra ou sai da sala, testes sem atributo privado. Não corrigidos, com motivo: ritmo global em vez de por realm (Q-T06-3); presença pelo índice cria Alter Ego sem evento lido (Q-T06-1, é dado real do índice); sem teste de `--lookback` estreito (opção de depuração); `fresh_after` repetido nos dois leitores (adapters não se importam); data ISO sem fuso no índice não ocorre (as datas vêm em UTC).
- **Decisões a confirmar:** Q-T06-1 a Q-T06-6 em `docs/DECISIONS.md`.
- **Fora deste ticket:** a tela de configurações para mudar o prazo (ticket 07); a leitura única do passado em segundo plano (ticket 25);
  nome para as sessões do Histórico; ritmo de leitura por realm.
