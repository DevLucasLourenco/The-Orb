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

- [ ] Arquivo de preferências na pasta do Orb, nunca nos providers.
- [ ] Tela de configurações no cliente, aberta pela interface.
- [ ] Lista de realms com marcação: desmarcado = não aparece na cidade; continua detectado.
- [ ] Prazo das sessões recentes configurável (padrão 10 dias).
- [ ] A tela está pronta para receber as opções dos tickets 09 (filtro de linhas) e 11 (x das janelas).

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
