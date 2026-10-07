# Inner World une o terminal e o pensamento

Status: aceita (2026-10-07)

"Intrusive Thoughts" (o que o Lucas escreve ao agente) e "Inner World" (o que o agente pensa)
eram dois conceitos que dependiam um do outro: um prompt só faz sentido ao lado do raciocínio
que ele provocou. Passam a ser **um só**, com o nome **Inner World**: o terminal com o CLI real
daquela sessão mais a linha do tempo de tudo o que se observa nela, com a **origem** de cada
entrada (`agente` ou `humano`).

## Consequências

- O terminal do CLI vive dentro do Inner World. É a **única porta de escrita** para um agente; o
  Gate escreve nesse mesmo terminal.
- Como o Alter Ego é uma sessão ([ADR 0001](0001-alter-ego-e-uma-sessao.md)), o Inner World é
  persistido pelo próprio provider (transcript/rollout) e pode ser reaberto.
- Uma entrada só tem origem `humano` quando a fonte do provider confirma (no Claude,
  `UserPromptSubmit` também dispara para prompts do sistema).
- O termo "Intrusive Thought" sai do vocabulário; o evento `intrusive_thought` do protocolo 0.1
  deixa de existir.
