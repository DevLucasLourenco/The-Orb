# 16: Leitor de diálogos

Status: ready-for-agent
Blocked by: 05
Origem: R34; D-060; ADR 0006
Spec: [../spec.md](../spec.md)

## O que construir

Nos terminais abertos pelo Orb, quando o CLI para num diálogo conhecido (atualização, confiança de
diretório, revisão de hooks, aprovação), o personagem aparece "esperando você" em magenta. O Orb nunca
responde nem envia tecla.

## Critérios de aceite

- [ ] Módulo próprio, separado do terminal, que lê a tela e reconhece diálogos por uma tabela por provider.
- [ ] Ao reconhecer, emite espera; quando o diálogo some, resolve a espera.
- [ ] Nenhuma tecla é enviada pelo módulo, nem em testes.
- [ ] Tabela de diálogos documentada nos adapters (com os conhecidos de Codex, Hermes, Claude e opencode).

## Testes

Ponto de teste: o servidor com terminal falso (tela sintética → espera).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
