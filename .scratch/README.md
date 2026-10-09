# .scratch — specs e tickets do The Orb

Rastreador local do projeto (D-098): **specs e tickets são arquivos markdown aqui, versionados no
git**. Nada vai para issues públicas do GitHub, porque o repositório é público e o trabalho cita
projetos e dados internos. O formato é o de [docs/agents/issue-tracker.md](../docs/agents/issue-tracker.md);
as etiquetas, as de [docs/agents/triage-labels.md](../docs/agents/triage-labels.md).

## Convenção (resumo)

- Uma pasta por feature: `.scratch/<feature>/`, com a spec em `spec.md`.
- Tickets, um arquivo cada: `.scratch/<feature>/issues/NN-<assunto>.md`, numerados a partir de `01`.
- O estado fica numa linha `Status:` no topo (ex.: `Status: ready-for-agent`).
- Comentários vão no fim do arquivo, sob `## Comments`.
- A fonte da verdade continua em `docs/` (regras, decisões, linguagem visual). A spec e os tickets
  apontam para lá; quando divergirem, vale o documento e a divergência é apontada.
- Tickets só são escritos quando o Lucas pedir (P5).

## Conteúdo

| Feature | O quê | Status |
|---|---|---|
| [the-orb-cidade-viva/](the-orb-cidade-viva/spec.md) | A primeira spec (D-001 a D-117) e os **25 tickets** em `issues/` (01 a 05 sem bloqueio; 05 e 25 com aprovação do Lucas no meio) | ready-for-agent |
