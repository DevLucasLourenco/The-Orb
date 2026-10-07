# Alter Ego é uma sessão

Status: aceita (2026-10-07)

Cada **sessão** de um CLI de IA é um Alter Ego: um personagem, o líder da sua Team. Os
subagentes nascidos nessa sessão aparecem na Team dele. O provider e o modelo pertencem à sessão
e não mudam.

A ideia anterior ("uma persona persistente que pode trocar de Claude para Codex") foi
abandonada: não havia sinal real que ligasse duas sessões à mesma persona, e o Orb só desenha o
que observa. A sessão, ao contrário, tem identidade verificável em todo provider (`--session-id`
do Claude, `thread.id` do Codex) e um registro persistido pelo próprio provider, que é o que dá
memória ao Inner World.

## Consequências

- Id do Alter Ego = `<provider>:<id da sessão>`. Duas sessões no mesmo realm são dois personagens
  no mesmo Rooftop Room.
- O Alter Ego continua existindo depois que o terminal fecha (a sessão está gravada pelo
  provider). Reabri-lo é retomar a sessão num terminal novo (`claude --resume`, `codex resume`),
  a confirmar por provider.
- O **Perfil** (o que dá identidade além da sessão: nome, papel, aparência, histórico entre
  sessões) **ainda não está decidido**. Ver [VISION.md](../VISION.md) §7.
- Ficam em aberto: retomada, bifurcação (`fork`), `clear` e compactação geram o mesmo Alter Ego
  ou um novo?
