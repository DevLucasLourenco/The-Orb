# 23: XP de commits e as três escalas

Status: ready-for-agent
Blocked by: 11, 22
Origem: R53, R54; D-090, D-103, D-104, D-106
Spec: [../spec.md](../spec.md)

## O que construir

Commits feitos nas sessões dão XP provisória, que vira confirmada quando o commit chega à branch
principal, é anulada se ele for revertido e expira em 30 dias. Aparecem os níveis do Realm e de
Mankind e o painel Progressão, com o extrato e o placar por provider.

## Critérios de aceite

- [x] Evidência de commit: `gitOperation` no Claude; `git commit` com `command.result` ok nos outros.
- [x] Leitura do git só leitura: o commit existe, chegou à branch principal (a padrão do remoto, senão `main`/`master`), foi revertido.
- [x] Estados provisória, confirmada, anulada e expirada no extrato; o nível usa só a confirmada e pode cair.
- [x] Commits do Lucas fora das sessões não dão XP.
- [x] Nível do Realm (k = 500) e de Mankind (k = 2.500); barra de cima e painel Progressão com extrato e placar por provider (V-HUD-12, V-HUD-13).

## Testes

Ponto de teste: as leituras do mundo real (repositório git falso → confirmações) e o mundo.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments

- **O que mudou:** Protocolo (`command.result.commit`, evento de realm `realm.commits`: PROTOCOL.md, `vocab.py`, `events.py`); adapters (`is_git_commit` e `result_signal(commit=, sha=)` em `_shared`; Claude pelo `gitOperation.commit.sha`; Codex passa o texto do comando); Probe `probes/commits.py` (`git_commits`, `main_branch`); Gateway (`CommitScheduler`, a mensagem `xp`, `Hub.xp_extract`); Core (`progression.py`: estados, X-COMMIT, `settle`, `commit_queries`, `scale`; `world.py`: `pending_commits`, `xp_extract`, níveis do Realm e de Mankind e o placar); registro local (`state`, esquema v3 com migração); cliente (barra de cima, painel Progressão, nível do realm, barra tracejada). Docs: PROTOCOL, RULES (R53, R54), VISUAL (V-HUD-12, 13), PROGRESSION §8, ARCHITECTURE, adapters/CLAUDE, DECISIONS (rodada Q-T23).
- **Testes:** `tests/test_commit_evidence.py` (a evidência: reconhecer `git commit`, o sinal, o `gitOperation` do Claude e o Codex), `tests/test_commit_probe.py` (repositório git **de verdade**: existe, linhas, principal com e sem remoto, `master`, reversão, achar por hora, só leitura), `tests/test_commit_scheduler.py` (quando perguntar e de ponta a ponta com o mundo), `tests/test_commit_xp.py` (estados, XP por linhas, reversão que derruba o nível, expiração, perguntas do mundo, Realm e Mankind, registro e migração) e o extrato; mais um no gateway (a mensagem `xp`). Suíte inteira: 766 passed, 2 skipped; ruff sem aviso nos arquivos novos e alterados; `node --check` no cliente.
- **Conferido na tela**, numa página temporária (não versionada) com um snapshot real do mundo feito de eventos sintéticos: a barra de cima "Mankind · nível 1 · 200 XP", o painel Progressão com o placar por provider e o extrato (commits confirmado, provisório e anulado riscado) e o nível do realm no overview. Console sem erros; servidor de prévia encerrado.
- **Não verificado:** sessões e commits reais dos quatro CLIs (só a estrutura do `gitOperation` do Claude foi conferida nesta máquina: `commit` com `sha`, `kind` e `branch`); o custo do Probe em repositórios grandes (cada commit pedido faz até 5 chamadas ao git, uma vez por minuto por realm com commit a conferir); a barra tracejada com XP provisória num cartão (só o painel e a barra de cima foram vistos); remoto de verdade (o teste usa um `origin/HEAD` montado à mão).
- **Decisões a confirmar:** Q-T23-1 a Q-T23-8 em `docs/DECISIONS.md` (provisórias, P2).
