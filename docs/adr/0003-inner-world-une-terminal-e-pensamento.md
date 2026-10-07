# Inner World une o terminal e o pensamento

Status: aceita (2026-10-07) · revista no mesmo dia: sem rastrear quem escreveu

"Intrusive Thoughts" (o que o Lucas escreve ao agente) e "Inner World" (o que o agente pensa)
eram dois conceitos que dependiam um do outro: um prompt só faz sentido ao lado do raciocínio
que ele provocou. Passam a ser **um só**, com o nome **Inner World**: o terminal com o CLI real
daquela sessão mais a linha do tempo de tudo o que se observa nela, do jeito que o provider grava.

**O Orb não rastreia quem escreveu cada entrada.** Quem usa o CLI é o Lucas, no próprio terminal;
separar "veio do Lucas" de "veio do sistema" não acrescenta nada ao que o Orb quer mostrar (cada
sessão e o mundo dela) e obrigaria a heurísticas frágeis em providers que não marcam a origem
(Codex, Hermes). As mensagens com papel de usuário aparecem como o provider as gravou.

## Consequências

- O terminal do CLI vive dentro do Inner World. É a **única porta de escrita** para um agente; o
  Gate escreve nesse mesmo terminal.
- Como o Alter Ego é uma sessão ([ADR 0001](0001-alter-ego-e-uma-sessao.md)), o Inner World é
  persistido pelo próprio provider (transcript/rollout) e pode ser reaberto.
- O termo "Intrusive Thought" sai do vocabulário; o evento `intrusive_thought` do protocolo 0.1
  deixa de existir, e não há sinal de "entrada humana" nem contagem de intervenções.
