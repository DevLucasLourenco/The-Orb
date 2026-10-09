# 19: Weather

Status: ready-for-agent
Blocked by: 09
Origem: R42, R49; D-076, D-084, D-097
Spec: [../spec.md](../spec.md)

## O que construir

Sobre cada prédio, céu limpo quando os últimos testes rodados nas sessões passaram, chuva quando
falharam, nada quando não há dado. O rótulo do prédio mostra o Weather.

## Critérios de aceite

- [ ] Sinal `command.result` no protocolo 0.3, produzido pelos quatro adapters: Codex (`exitCode` no app-server, `item.exit_code` no rollout), Hermes (`exit_code` do terminal), opencode (`metadata.exit` do bash), Claude (`is_error`/`interrupted`, sem código).
- [ ] O mundo guarda, por realm, o resultado do último comando de teste.
- [ ] Céu limpo / chuva / nada, em tons neutros, fora do orçamento de cores.
- [ ] Rótulo do prédio mostra o Weather quando houver dado.
- [ ] Sem rede: o CI do GitHub fica fora.

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
