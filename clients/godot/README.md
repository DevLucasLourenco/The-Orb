# The Orb — cliente Godot

Cliente 3D do The Orb (ainda só o começo). Hoje tem uma cena, `terminal_view.tscn`: o terminal do
Inner World de um Alter Ego, **exibido** pelo addon `godot-xterm` a partir do Gateway em Python. O
Godot não abre PTY nem chama CLI; isso é do Terminal Host ([ADR 0004](../../docs/adr/0004-terminal-host-unico-em-python.md)).

O terminal como **monitor 3D** no Rooftop Room (`SubViewport` num quad, teclado encaminhado) foi
validado no experimento `spikes/02-terminal-godot/monitor3d.gd` e entra aqui com a sala 3D.

## Requisitos

Godot 4.7.2 e o addon `godot-xterm` v4.0.3 em `addons/godot_xterm/` (não versionado, ~33 MB):

```powershell
winget install --id GodotEngine.GodotEngine -e --scope user
gh release download v4.0.3 --repo lihop/godot-xterm --pattern "godot-xterm-v4.0.3.zip"
Expand-Archive godot-xterm-v4.0.3.zip -DestinationPath .
```

## Rodar

Suba o Gateway na raiz do repositório (`the-orb --cwd PASTA`) e use o token que ele imprime:

```powershell
& $godot --path . -- --url=ws://127.0.0.1:8765/ws --token=TOKEN --provider=claude
```

O Gateway exige `Origin` local; o script já envia `Origin: http://127.0.0.1`. A entrada vai em
base64 (`data_b64`) porque o `JSON.stringify` do Godot não escapa caracteres de controle.
