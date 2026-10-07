# O mundo 3D é um cliente web (Three.js)

Status: aceita (2026-10-07) · muda a escolha de cliente prevista na visão (Godot 4)

O mundo 3D navegável do The Orb é uma página web com **Three.js**, servida pelo próprio Gateway
(`clients/web/`). Abre no navegador, sem instalar nada, e usa o mesmo servidor e os mesmos
terminais (xterm.js) que já funcionavam.

## Opções consideradas

- **Godot 4 (o plano anterior):** motor de jogo completo e terminal 3D já validado no Spike 2, mas
  exige instalar o Godot, e cada ajuste visual é lento de verificar.
- **Web com Three.js (escolhida):** nada a instalar, iteração rápida (dá para ver e testar cada
  versão no navegador enquanto se constrói) e um único cliente para o mundo e para os terminais.

## Consequências

- O ADR 0004 continua valendo: o Terminal Host é um só, em Python; o cliente só exibe.
- `clients/godot/` fica como alternativa (o terminal remoto validado), sem ser o foco.
- O painel 2D de validação foi substituído pelo cliente 3D, que traz o overview do realm e o Inner
  World na mesma tela.
