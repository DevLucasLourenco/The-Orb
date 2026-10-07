# Cada provider aparece como ele é; o mundo usa sinais derivados

Status: aceita (2026-10-07) · substitui o princípio "neutro de provider" do protocolo 0.1

O Orb **não traduz** os eventos de Claude, Codex e Hermes para um vocabulário comum. Cada evento
é preservado no formato nativo (nome e corpo) e é assim que aparece no Inner World: o Claude com
`PreToolUse · Read`, o Codex com `commandExecution · Get-Content`, o Hermes com o vocabulário
dele.

Para desenhar o mundo, porém, o Orb precisa de pouquíssimas coisas em comum: em que área o
personagem está, se espera o Lucas, se um subagente nasceu ou terminou. Por isso cada evento
nativo carrega, **ao lado** e sem substituí-lo, um **sinal de mundo** opcional e uma entrada de
Inner World opcional, gerados pelo **Mapa do provider** (uma tabela declarativa por adapter).

## Opções consideradas

- **Tradução completa (protocolo 0.1):** clientes simples, mas apaga o que cada provider tem de
  próprio e obriga a inventar equivalências (o Codex não tem `Read`; o Claude não tem
  `serverRequest/resolved`).
- **Nativo puro:** fiel, mas o Core e o 3D passariam a conhecer cada provider, quebrando a
  modularidade (adicionar um provider exigiria mexer no mundo).
- **Nativo + sinais derivados (escolhida):** fidelidade no que se mostra, contrato pequeno e
  estável no que o mundo consome.

## Consequências

- O Core e os clientes só conhecem o envelope, os sinais de mundo e as entradas de Inner World;
  nunca o significado de um evento nativo. Adicionar um provider = adicionar um adapter.
- O texto mostrado no Inner World é sempre o texto do provider, sem reescrita.
- Detalhes do envelope em [PROTOCOL.md](../PROTOCOL.md).
