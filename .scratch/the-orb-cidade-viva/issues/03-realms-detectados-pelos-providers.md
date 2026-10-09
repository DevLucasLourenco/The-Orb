# 03: Realms detectados pelos providers

Status: ready-for-agent
Blocked by: None (can start immediately)
Origem: R3, R3a, R3b, R3d, R48 (camada 1); D-018, D-021, D-023, D-029, D-031, D-088
Spec: [../spec.md](../spec.md)

## O que construir

O Lucas abre o Orb sem passar caminho nenhum e vê na cidade todo projeto que algum dos quatro
CLIs já registrou. Um índice leve com os metadados de todas as sessões (pasta, datas, título,
provider, modelo) alimenta a cidade; worktrees e subpastas contam para o projeto principal; a pasta do
usuário, as de sistema e temporárias e as pastas que não existem mais ficam de fora.

## Critérios de aceite

- [ ] Os leitores dos quatro providers listam todas as sessões, sem filtro por pasta, num índice de metadados barato (sem ler o conteúdo das sessões antigas).
- [ ] Pasta da sessão → projeto: vence a raiz informada pelo provider; senão sobe até o repositório git só lendo arquivos (sem executar nada); worktrees contam para o principal.
- [ ] Projetos com nomes parecidos nunca se misturam (ex.: `trisafe` × `trisafe-enhanced`); nomes iguais em lugares diferentes ganham sufixo.
- [ ] Pasta do usuário, `AppData`, `Temp`, `Downloads` e pastas inexistentes não viram realm.
- [ ] `--root`, `--realm` e `--lookback` deixam de ser necessários (no máximo, opções de depuração).
- [ ] O servidor abre e a cidade mostra todos os realms detectados nesta máquina.

## Testes

Ponto de teste: as leituras do mundo real (pastas de CLIs falsas → realms) e os leitores dos CLIs.

## Observação

O maior ticket da lista: se não couber num contexto, dividir em "índice e regras de pasta" e "um leitor por provider".

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
