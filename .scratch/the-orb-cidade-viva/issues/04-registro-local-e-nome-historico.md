# 04: Registro local e nome histórico

Status: ready-for-agent
Blocked by: None (can start immediately)
Origem: R36, R37; D-062 a D-067
Spec: [../spec.md](../spec.md)

## O que construir

O Orb passa a ter o seu registro local (SQLite, na pasta de preferências do Orb), e cada Alter Ego
ganha um nome histórico sorteado da sacola de 60 nomes. O rótulo mostra o nome em destaque e, embaixo,
"provider · título da sessão".

## Critérios de aceite

- [ ] O registro local existe na pasta de preferências do Orb e guarda só o que o Orb derivou (nada do conteúdo das sessões).
- [ ] Sacola global: os 60 nomes de VISUAL.md §9 saem sem repetir até a sacola esvaziar; depois ela é embaralhada de novo.
- [ ] O nome fica com a sessão para sempre (também depois de reiniciar o Orb).
- [ ] Nunca dois nomes iguais visíveis na mesma sala.
- [ ] Subagentes não ganham nome: ficam com o tipo dado pelo CLI.
- [ ] Rótulo do personagem: nome em destaque; embaixo "provider · título"; depois atividade e última ação.

## Testes

Ponto de teste: o mundo (o nome entra no estado do Alter Ego) e o registro local com uma pasta temporária.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
