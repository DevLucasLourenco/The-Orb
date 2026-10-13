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

- [x] O registro local existe na pasta de preferências do Orb e guarda só o que o Orb derivou (nada do conteúdo das sessões).
- [x] Sacola global: os 60 nomes de VISUAL.md §9 saem sem repetir até a sacola esvaziar; depois ela é embaralhada de novo.
- [x] O nome fica com a sessão para sempre (também depois de reiniciar o Orb).
- [x] Nunca dois nomes iguais visíveis na mesma sala.
- [x] Subagentes não ganham nome: ficam com o tipo dado pelo CLI.
- [x] Rótulo do personagem: nome em destaque; embaixo "provider · título"; depois atividade e última ação. (O nome também aparece no cartão da sessão e na dica dos pontos do realm: D-139.)

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

Implementado em 2026-10-13 (branch `ticket/04-registro-local-e-nome-historico`). Só estrutura e contagens dos dados reais.

- **O que mudou:** `orb.core.names` (os 60 nomes de VISUAL.md §9, `NameBag`, `NameBook`, `NameSource`); `World(names=...)` dá o
  `name` ao Alter Ego quando a sessão aparece (subagente fica sem nome); pacote `orb.registry` (`LocalRegistry`,
  `orb_home()`) com `registry.db` em `%LOCALAPPDATA%\the-orb\`, tabelas `names` e `bag`; o Gateway entrega o registro ao
  mundo (`GatewayConfig.state_dir`, `/config` com `registry_error`); o cliente mostra o nome no rótulo, no cartão e na dica dos pontos.
- **Testes:** `tests/test_names.py` (sacola, pulo de nome em uso, a lista confere com VISUAL.md), `tests/test_registry.py`
  (pasta temporária: reabrir mantém o nome e a sacola; só tabelas derivadas; disco quebrado, arquivo corrompido e registro de
  Orb mais novo degradam sem tocar o arquivo), acréscimos em `test_core.py` e `test_gateway.py`. Suíte: 310 → 342 passed, 1 skipped.
- **Conferido com dados reais** (pasta do Orb temporária, nada gravado na pasta real; só contagens): 4 sessões ativas, 4 nomes
  distintos, nenhum subagente com nome; reiniciar o servidor devolveu os mesmos 4 nomes; o rótulo vem em três linhas
  (nome, "provider · título", atividade) e o console sem erros; só as cores neutras já existentes.
- **Revisões (2026-10-13):** padrões e spec feitas; corrigidos: a docstring de `orb_home` virava TAB (`\t`), o sorteio descartava a sacola quando só restavam nomes em uso (agora sai um nome de fora e a sacola fica), uma falha passageira do banco desligava o registro até o fim da execução (agora tenta de novo a cada pedido e a cópia em memória segue a mesma sacola), erro próprio para registro de Orb mais novo, `error` no contrato `NameSource`, título do rótulo só encolhe quando há nome, teste de dois Orbs abertos ao mesmo tempo. R37 ficou ⚠️ ("sem gêmeos" vale pelo realm até a sala do ticket 06). Não corrigidos, com motivo: `BEGIN IMMEDIATE` também na leitura de nome existente (só roda quando uma sessão aparece); `registry_error` sem tela (entra na configuração do ticket 07); mensagem de `OSError` pode trazer caminho local (o `/config` já lista as pastas dos realms; servidor só local); imports dentro das funções de `test_gateway` seguem o estilo do arquivo.
- **Decisões:** o Lucas confirmou Q-T04-1 a Q-T04-5 em 2026-10-13 (D-135 a D-139 em `docs/DECISIONS.md`; a D-138 reescreve o invariante 3 do CLAUDE.md: a única escrita nos arquivos de terceiros é o Terminal Host; o Orb grava nos próprios) e aprovou o envio da branch com PR.
  a única escrita nos arquivos de terceiros é o Terminal Host; o Orb grava nos próprios).
- **Fora deste ticket:** a sala só com as sessões recentes e o Histórico do realm (ticket 06: até lá "visível na sala" é o
  realm inteiro que o mundo conhece); eventos do mundo, índice de sessões, pontos de parada e extrato de XP no registro
  (tickets 06, 18, 22); o nível ao lado do nome (V-EGO-13, ticket 22).
