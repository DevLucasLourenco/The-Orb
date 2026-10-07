# O Orb nunca responde diálogos do Lucas

Status: aceita (2026-10-06, Spike 4)

Diálogos dos CLIs (atualização, confiança de diretório, confiança de hooks, aprovações de
comando, perguntas ao usuário) são decisões do Lucas. Nenhum módulo do Orb os responde, e nenhuma
tecla é enviada a uma TUI sem a tela verificada.

No Spike 4, um script de teste enviou Enter às cegas e aceitou "Update now" na TUI do Codex (o
instalador falhou sem efeito). A regra vale para o produto, para automação e para testes.

## Consequências

- O Terminal Host só transporta o que o Lucas digita; as únicas escritas automáticas são as que
  ele pede pelo Gate ou pelo painel.
- Um observador de protocolo (ex.: o cliente do app-server do Codex) **nunca** responde a um
  `ServerRequest`, nem para recusar.
- A UI deve avisar quando um terminal está parado num diálogo esperando o Lucas (forma em aberto).
