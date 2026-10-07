# Spike 2 — Terminal dentro do Godot

Responde: dá para ter o terminal real (com o CLI do agente) **dentro do Godot**, inclusive como
tela num monitor 3D? Resultado e análise: [MVP.md](../../MVP.md) §7.

Requisitos: Godot 4.7.2 e o addon `godot-xterm` v4.0.3.

O addon (~33 MB, com binários de todas as plataformas) **não é versionado**. Para obtê-lo
(release oficial `lihop/godot-xterm`, 11 MB):

```powershell
winget install --id GodotEngine.GodotEngine -e --scope user      # Godot 4.7.2 (uma vez)
gh release download v4.0.3 --repo lihop/godot-xterm --pattern "godot-xterm-v4.0.3.zip"
Expand-Archive godot-xterm-v4.0.3.zip -DestinationPath .          # cria addons/godot_xterm/ aqui
```

## Cenas

| Cena | O que mostra | Como o PTY é aberto |
|---|---|---|
| `main.tscn` | Terminal 2D com PTY **dentro do Godot** (opção A) | godot-xterm (ConPTY) |
| `monitor3d.tscn` | Mesmo terminal, mas como **textura de um monitor 3D** (`SubViewport` num quad), teclado encaminhado | godot-xterm (ConPTY) |
| `bridge.tscn` | Terminal que só **exibe** bytes de um servidor Python, via WebSocket (opção B) | Terminal Host em Python (spike 1) |

## Rodar

Argumentos do projeto vão depois de `--`. Em `main`/`monitor3d`: `--cli=none|claude|codex`
`--cwd=PASTA`. Em `bridge`: `--url=ws://127.0.0.1:PORTA/ws --token=TOKEN --provider=shell|claude|auto`.
`--autotest --wait=S --out=r.json --shot=captura.png` roda um teste automático e fecha.

```powershell
$g = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.7.2-stable_win64.exe"
# Terminal 2D com claude (o Godot deve ser aberto SEM redirecionar stdin/stdout)
& $g --path . -- --cli=claude --cwd="C:\caminho\do\projeto"
# Monitor 3D
& $g --path . res://monitor3d.tscn -- --cli=claude
```

Para a opção B, suba o servidor do spike 1 (`python server.py --port 8766`) e use o token
que ele imprime.

## Armadilhas já encontradas

- **Opção A só funciona se o Godot for aberto sem stdio redirecionado.** Com stdin/stdout
  redirecionados (pipe, `> arquivo`, `subprocess` com pipes) o ConPTY entrega ao filho os
  handles do pai: o shell imprime no stdout do Godot e sai na hora.
- Caminhos de executável e `cwd` no Windows com **barra invertida**.
- `JSON.stringify` do Godot **não escapa caracteres de controle** (ESC): mande bytes de
  entrada em base64 (`data_b64`).
- Glifos de caixa e bloco (`─ █ ▐`) saem com espaços entre as células (cosmético; o texto, as
  cores e o redimensionamento estão corretos).
