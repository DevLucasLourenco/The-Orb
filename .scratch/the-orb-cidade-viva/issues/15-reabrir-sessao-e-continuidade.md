# 15: Reabrir sessão e continuidade

Status: ready-for-agent
Blocked by: 04, 06
Origem: R10, R39; D-068
Spec: [../spec.md](../spec.md)

## O que construir

Do Histórico do realm ou do overview, o Lucas reabre qualquer sessão num terminal novo. Retomar
mantém o mesmo Alter Ego (mesmo nome); bifurcar cria um Alter Ego novo, com nome novo, mostrando de quem
nasceu; `/clear` e compactação seguem o que cada CLI registra.

## Critérios de aceite

- [ ] Botão para reabrir a sessão num terminal novo, com a linha de retomada de cada CLI (só valores controlados pelo Orb).
- [ ] Verificado por CLI, só pela estrutura, como o id muda ao retomar, bifurcar, limpar e compactar; o resultado fica nos documentos dos adapters.
- [ ] Retomar = mesmo Alter Ego e mesmo nome; bifurcar = Alter Ego novo, com nome novo e a origem visível.
- [ ] Nenhum diálogo do CLI é respondido; nada de teclas às cegas.

## Testes

Ponto de teste: o mundo (eventos de retomada e bifurcação → identidade) e o servidor com terminal falso.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
