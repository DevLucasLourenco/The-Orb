# 19: Weather

Status: ready-for-agent
Blocked by: 09
Origem: R42, R49; D-076, D-084, D-097
Spec: [../spec.md](../spec.md)

## O que construir

Sobre cada prédio, céu limpo quando os últimos testes rodados nas sessões passaram, chuva quando
falharam, nada quando não há dado. O rótulo do prédio mostra o Weather.

## Critérios de aceite

- [x] Sinal `command.result` no protocolo 0.3, produzido pelos quatro adapters: Codex (`exitCode` no app-server, `item.exit_code` no rollout), Hermes (`exit_code` do terminal), opencode (`metadata.exit` do bash), Claude (`is_error`/`interrupted`, sem código).
- [x] O mundo guarda, por realm, o resultado do último comando de teste.
- [x] Céu limpo / chuva / nada, em tons neutros, fora do orçamento de cores.
- [x] Rótulo do prédio mostra o Weather quando houver dado.
- [x] Sem rede: o CI do GitHub fica fora.

## Testes

Ponto de teste: os leitores dos CLIs (amostras → `command.result`) e o mundo (resultados → Weather).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments

Implementado em 2026-10-15 (branch `ticket/19-weather`). Só estrutura e contagens dos dados reais.

- **O que mudou:** o sinal `command.result` (`ok`, `exit_code?`, `activity?`) no protocolo 0.3, validado na borda; `result_signal` em `adapters/_shared/commands.py`; nos quatro adapters:
  Claude (`is_error`/`interrupted`, ligado à chamada pelo `tool_use_id`), Codex (`exitCode` no app-server, `item.exit_code` no rollout), Hermes (`exit_code` no JSON do `terminal`, ligado pelo `tool_call_id`)
  e opencode (`state.metadata.exit` do `bash`); no mundo, `World.tests` (o último teste de cada realm) e `weather` no snapshot; no cliente, a lua ou a nuvem com chuva sobre o prédio e a linha "Weather" no rótulo.
- **Testes:** `tests/test_command_result.py` (19): o vocabulário, os quatro CLIs e o mundo (último vence, resultado atrasado, comando que não é teste, subagente, prazo da sala, sem hora, `time_key`).
- **Decisões a confirmar:** Q-T19-1 a Q-T19-6 em `docs/DECISIONS.md` (provisórias, P2).
- **Dados reais:** só conferi a **estrutura** do `event_msg/item_completed` do Codex nesta máquina (6.562 comandos concluídos, `exit_code` inteiro em todos, `command` como lista de argumentos); não li conteúdo.
  Não rodei os quatro CLIs de verdade (isso consome cota): os formatos do Claude, Hermes e opencode seguem o que a D-084 já tinha conferido.
- **Na tela:** numa página temporária (não versionada) com Weather sintético: a lua branca, a nuvem com chuva acima do rótulo, e o prédio sem dado sem nada; console sem erros. A animação da chuva não foi vista em movimento.
- **O que não foi visto:** o Weather ao vivo com um CLI de verdade (um teste rodando de ponta a ponta); a chuva em movimento; o Arranha-céu com antena e chuva por inteiro (a câmera cortou o topo).
