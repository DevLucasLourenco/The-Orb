# Spike 2 — Terminal dentro do Godot (experimento)

Respondeu: dá para ter o terminal real (com o CLI do agente) **dentro do Godot**, inclusive como
tela de um monitor 3D? **Sim.** Resultado e análise: [SPIKES.md](../../docs/SPIKES.md#spike-2--terminal-no-godot-).

A peça escolhida (opção B: o Godot só **exibe**, o terminal fica no Terminal Host em Python) foi
promovida para [`clients/godot/`](../../clients/godot/) ([ADR 0004](../../docs/adr/0004-terminal-host-unico-em-python.md)).
Ficam aqui os experimentos da opção A (PTY dentro do Godot), guardados como referência.

Requisitos: Godot 4.7.2 e o addon `godot-xterm` v4.0.3 em `addons/godot_xterm/` (não versionado;
instruções em [clients/godot/README.md](../../clients/godot/README.md)).

## Cenas

| Cena | O que mostra | Como o PTY é aberto |
|---|---|---|
| `main.tscn` | Terminal 2D com PTY **dentro do Godot** (opção A) | godot-xterm (ConPTY), sempre PowerShell |
| `monitor3d.tscn` | Mesmo terminal como **textura de um monitor 3D** (`SubViewport` num quad), teclado encaminhado | godot-xterm (ConPTY) |

## Rodar

Argumentos depois de `--`: `--cli=none|claude|codex` `--cwd=PASTA`. Autoteste:
`--autotest --wait=S --out=r.json --shot=captura.png`.

```powershell
$g = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.7.2-stable_win64.exe"
& $g --path . -- --cli=claude --cwd="C:\caminho\do\projeto"     # o Godot deve abrir SEM stdio redirecionado
& $g --path . res://monitor3d.tscn -- --cli=claude
```

## Armadilhas encontradas

- **Opção A só funciona se o Godot for aberto sem stdio redirecionado.** Com stdin/stdout
  redirecionados o ConPTY entrega ao filho os handles do pai: o shell imprime no stdout do Godot e
  sai na hora. (Motivo principal da opção B.)
- Caminhos de executável e `cwd` no Windows com **barra invertida**.
- `JSON.stringify` do Godot **não escapa caracteres de controle**: bytes de entrada vão em base64.
- Glifos de caixa e bloco (`─ █ ▐`) saem com espaços entre as células (cosmético).
- Em 3D o teclado não chega sozinho ao `SubViewport`: é preciso encaminhar o evento.
