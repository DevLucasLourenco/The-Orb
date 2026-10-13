# 07: Preferências e tela de configurações

Status: ready-for-agent
Blocked by: 03, 06
Origem: R29, R3c; D-022, D-030, D-032
Spec: [../spec.md](../spec.md)

## O que construir

O Orb ganha um arquivo de preferências próprio e uma tela de configurações. Nela o Lucas vê a lista
de todos os realms detectados e desmarca os que quer esconder, e muda o prazo das sessões recentes.
Nada disso toca os providers nem depende de linha de comando.

## Critérios de aceite

- [x] Arquivo de preferências na pasta do Orb, nunca nos providers.
- [x] Tela de configurações no cliente, aberta pela interface.
- [x] Lista de realms com marcação: desmarcado = não aparece na cidade; continua detectado.
- [x] Prazo das sessões recentes configurável (padrão 10 dias).
- [x] A tela está pronta para receber as opções dos tickets 09 (filtro de linhas) e 11 (x das janelas).

## Testes

Ponto de teste: o mundo (realm escondido sai do estado da cidade) e as leituras do mundo real (arquivo de preferências numa pasta temporária).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments

Implementado em 2026-10-13 (branch `ticket/07-preferencias-e-tela-de-configuracoes`). Só estrutura e contagens dos dados reais.

- **O que mudou:** `registry/preferences.py` (`Preferences`, `PreferencesFile`, tabela `SETTINGS`); `World.set_hidden` e `hidden_realms` no snapshot;
  `Observatory.set_recent_seconds`; `Hub.update_preferences` e `Hub.settings`; mensagens `settings` e `preferences` no `/world`; no cliente, o ⚙ da barra,
  a janela de configurações (lista de realms com caixa e opções numéricas) e a cidade que se redesenha na hora.
- **Testes:** `test_preferences.py` (arquivo, opção desconhecida, arquivo ilegível, faixas), `test_core.py` (realm escondido), `test_realms.py` (Hub, restart,
  recusa de valor inválido, `/world`). Suíte: 365 → 396 passed, 1 skipped.
- **Conferido com dados reais** (pasta do Orb temporária; só contagens): 23 realms na lista; desmarcar um deixou 22 na cidade e 23 na lista; prazo 400 recusado com
  a mensagem na tela e o valor voltou a 10; prazo 30 trouxe 67 sessões para a sala (eram 34 com 10 dias); `preferences.json` com `version`, `recent_days` e 1 realm
  escondido; depois de reiniciar o servidor tudo continuou igual; console sem erros; a pasta real do Orb não foi criada.
- **Revisões (2026-10-13):** padrões e spec feitas; corrigidos: a tabela `SETTINGS` virou a única fonte (o Hub e o arquivo derivam dela), Esc fecha a janela mesmo dentro de um campo e o teclado do mundo não age por trás dela, acessibilidade do modal (`aria-modal`, foco, `role=alert`), valor inválido no arquivo avisa em vez de voltar ao padrão em silêncio, caminhos escondidos de projetos não detectados são mantidos, uma opção chamada `self` derrubava a conexão (agora é recusada), o texto de erro do sistema não vai mais à tela, a mudança vale para todos os clientes (`settings` em broadcast), eventos e linhas de um realm escondido não são distribuídos, esconder o realm aberto fecha o overview e o Inner World, a sessão que sai da sala fecha o Inner World dela, e o tipo da opção (`kind`) vai na tabela. Não corrigidos, com motivo: lote vago de realm escondido (ticket 08); sessão esperando num realm escondido não acende nada (Q-T07-2); tela só desenha opções numéricas (os outros tipos chegam com os tickets 09 e 11); prazo máximo de 365 dias (Q-T07-3).
- **Decisões a confirmar:** Q-T07-1 a Q-T07-5 em `docs/DECISIONS.md`.
- **Fora deste ticket:** o lote vago de um realm escondido no traçado da cidade (ticket 08); as opções de filtro de linhas (09) e x das janelas (11), que só
  acrescentam linhas à tabela `SETTINGS`; posição dos prédios (V-PEND-5).
