# Um único Terminal Host, em Python; os clientes só exibem

Status: aceita (2026-10-06, Spike 2)

O Orb abre o terminal real (PowerShell em ConPTY) e chama o CLI dentro dele num único Terminal
Host em Python. O cliente (página web com xterm.js, Godot com godot-xterm) só exibe bytes e envia
teclas por WebSocket.

## Opções consideradas

- **PTY dentro do Godot (godot-xterm abrindo o ConPTY):** funciona, mas quebra quando o Godot é
  aberto com stdio redirecionado e divide sessão, ambiente e telemetria entre dois lados.
- **PTY no Python (escolhida):** um só lugar para `--session-id`, limpeza de ambiente e leitura
  do transcript; serve web e Godot com o mesmo protocolo.

## Consequências

- O Godot depende do Gateway estar no ar para mostrar terminais.
- Latência extra de WebSocket local (desprezível; ainda a medir de ponta a ponta).
