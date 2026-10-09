# 05: Cores e áreas

Status: ready-for-agent
Blocked by: None (can start immediately)
Origem: R20c, R30; D-036, D-037, D-040; V-PEND-7d
Spec: [../spec.md](../spec.md)

## O que construir

Os personagens ganham as cores dos providers (Claude laranja, Codex azul, Hermes amarelo,
opencode cinza), as áreas perdem a cor própria e passam a ser identificadas por ícone, nome e um padrão
no piso, e tudo o que indica "esperando você" vira magenta pulsante. Os tons exatos e os ícones passam
antes por uma prévia que o Lucas aprova.

## Critérios de aceite

- [ ] Uma prévia visual com os tons dos providers, do magenta e os ícones das 5 áreas é mostrada ao Lucas; **só depois da aprovação** os valores entram em VISUAL.md §5 e no cliente.
- [ ] Personagens e pontos da lista de realms nas cores aprovadas.
- [ ] Áreas sem cor: piso neutro, ícone, nome e padrão.
- [ ] "Esperando você" em magenta pulsante em todos os lugares: feixe e anel do prédio, arestas da sala e o marcador sobre a cabeça (hoje âmbar).
- [ ] Nenhuma cor fora do orçamento (git nas janelas, provider nos personagens, magenta para espera).

## Testes

Ponto de teste: conferência no preview (o cliente só desenha; sem lógica de domínio a testar).

## Observação

Tem um ponto de parada com o Lucas (aprovação da prévia) antes de concluir.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments
