# The Orb — guia para agentes

Este repositório tem um único guia de trabalho para agentes: **[CLAUDE.md](CLAUDE.md)**. Leia-o
inteiro antes de qualquer tarefa e siga-o como se fosse este arquivo; ele vale para qualquer CLI
(Codex, opencode, Hermes, Claude Code).

Resumo do que nunca muda (detalhe e motivo no CLAUDE.md):

- Documentar → tickets → implementar. Specs e tickets ficam em `.scratch/`, nunca em issues públicas.
- O Orb só observa: somente leitura nos providers e nos projetos; nunca gravar no `.git`.
- O Orb nunca responde diálogos dos CLIs e nunca envia teclas às cegas.
- O Orb não consome tokens: nenhum módulo chama modelo de IA.
- Respostas, documentos e commits em português do Brasil; `push` só quando o Lucas pedir.
