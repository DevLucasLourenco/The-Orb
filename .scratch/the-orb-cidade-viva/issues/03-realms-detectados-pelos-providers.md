# 03: Realms detectados pelos providers

Status: ready-for-agent
Blocked by: None (can start immediately)
Origem: R3, R3a, R3b, R3d, R48 (camada 1); D-018, D-021, D-023, D-029, D-031, D-088, D-128 (achado do ticket 01)
Spec: [../spec.md](../spec.md)

## O que construir

O Lucas abre o Orb sem passar caminho nenhum e vê na cidade todo projeto que algum dos quatro
CLIs já registrou. Um índice leve com os metadados de todas as sessões (pasta, datas, título,
provider, modelo) alimenta a cidade; worktrees e subpastas contam para o projeto principal; a pasta do
usuário, as de sistema e temporárias e as pastas que não existem mais ficam de fora.

## Critérios de aceite

- [x] Os leitores dos quatro providers listam todas as sessões, sem filtro por pasta, num índice de metadados barato (sem ler o conteúdo das sessões antigas).
- [x] Pasta da sessão → projeto: vence a raiz informada pelo provider; senão sobe até o repositório git só lendo arquivos (sem executar nada); worktrees contam para o principal.
- [x] Projetos com nomes parecidos nunca se misturam (ex.: `trisafe` × `trisafe-enhanced`); nomes iguais em lugares diferentes ganham sufixo.
- [x] Pasta do usuário, `AppData`, `Temp`, `Downloads` e pastas inexistentes não viram realm.
- [x] `--root`, `--realm` e `--lookback` deixam de ser necessários (no máximo, opções de depuração).
- [x] O servidor abre e a cidade mostra todos os realms detectados nesta máquina.
- [x] Os eventos de abertura de sessão e de subagente do Claude e do Hermes usam a data de início real (a do índice), não a hora da leitura (D-128): um subagente antigo não nasce "recém-ativo".

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

**Vindo do ticket 01 (D-128, 2026-10-13):** os eventos de abertura de sessão e de subagente do Claude e do Hermes
não trazem a hora do evento e usam a **hora da leitura**. Um subagente descoberto agora parece "recém-ativo"
mesmo que tenha começado horas atrás, e só vira "sem sinal" 5 min depois: na máquina do Lucas, 117 dos 120
subagentes ativos ficaram "sem sinal" 5 min depois do primeiro poll. O índice de sessões deste ticket traz as
datas de início; a abertura passa a usá-las (último critério de aceite). Se o ticket for dividido (ver
Observação), este item vai com "um leitor por provider".

Implementado em 2026-10-13 (branch `ticket/03-realms-detectados-pelos-providers`), numa só branch, na ordem sugerida
pela Observação: índice e regras de pasta, depois um leitor por provider. Só estrutura e contagens dos dados reais.

- **Ao vivo, sem nenhum argumento:** o servidor detectou 23 projetos nesta máquina (23 ids únicos, 2 com sufixo), todos
  existentes no disco, nenhum na pasta do usuário, `AppData`, `Downloads` ou `Temp`, sem erro de leitor; o cliente 3D
  abriu com "23 realms" e o console sem erros. Os subagentes antigos já nasceram sem sinal (40 de 40 no primeiro
  snapshot), sem o "recém-ativo" de 5 min do ticket 01 (D-128).
- **Medido:** índice dos 4 providers com 486 sessões: ~5 s na primeira varredura (Codex, 428 rollouts) e ~30 ms nas
  seguintes; resolução de 41 pastas distintas em 190 ms.
- **Decisões a confirmar:** Q-T03-1 a Q-T03-5 em `docs/DECISIONS.md` (a Q-T03-1 toca o invariante 11 do CLAUDE.md).
- **Fora deste ticket:** esconder realms pela lista (R3c); a sala de 10 dias e o conteúdo só das sessões da sala (R48,
  camada 2, ticket 06); o realm de uma pasta apagada com o Orb aberto só sai na próxima subida do servidor.
