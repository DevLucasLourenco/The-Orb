extends Control
## Spike 2: terminal real dentro do Godot (godot-xterm + ConPTY).
## Abre um PowerShell e, se pedido, chama o CLI do agente dentro dele (mesmo modelo do Spike 1).
##
## Argumentos (depois de `--`):  --cli=claude|codex|none  --cwd=PASTA
## Autoteste:  --autotest --wait=10 --out=resultado.json --shot=captura.png

# Caminhos de executável no Windows precisam de barra invertida: com "/" a linha de comando que o
# ConPTY monta chega malformada ao filho (o cmd.exe interpreta "/..." como opção).
const POWERSHELL := "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
const CLIS := ["claude", "codex", "hermes"]  # lista fixa: o Orb nunca executa comando arbitrário

var terminal: Terminal
var pty: PTY
var args := {}


func _ready() -> void:
	_parse_args()
	terminal = Terminal.new()
	terminal.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(terminal)
	pty = PTY.new()
	add_child(pty)
	if args.has("manual"):
		# Ligação manual PTY <-> Terminal, para isolar problemas da ligação automática por terminal_path.
		pty.data_received.connect(func(d): terminal.write(d))
		terminal.data_sent.connect(func(d): pty.write(d))
		terminal.size_changed.connect(func(_new_size): pty.resize(terminal.get_cols(), terminal.get_rows()))
	else:
		pty.terminal_path = pty.get_path_to(terminal)  # liga PTY <-> Terminal (dados e tamanho)
	if args.has("debug"):
		pty.data_received.connect(func(d): print("[pty] data_received tam=%d conteudo=%s" % [d.size(), d.get_string_from_utf8().c_escape()]))
		pty.exited.connect(func(code, sig): print("[pty] exited code=%s sig=%s" % [code, sig]))
		terminal.data_sent.connect(func(d): print("[term] data_sent tam=%d" % d.size()))
	if args.has("nothreads"):
		pty.use_threads = false
	_apply_font()
	terminal.grab_focus()
	# Espera o layout para o terminal ter colunas/linhas reais antes de abrir o PTY.
	await get_tree().process_frame
	await get_tree().process_frame
	# Só o PowerShell: nenhum executável vem de argumento (lista fixa, como no Terminal Host).
	var shell: String = POWERSHELL
	var shell_args := PackedStringArray(["-NoLogo"])
	var cwd: String = args.get("cwd", ProjectSettings.globalize_path("res://"))
	print("[spike] fork shell=%s args=%s cwd=%s cols=%d rows=%d" % [shell, shell_args, cwd, terminal.get_cols(), terminal.get_rows()])
	var err := pty.fork(shell, shell_args, cwd, terminal.get_cols(), terminal.get_rows())
	if err != OK:
		push_error("falha ao abrir o PTY: %d" % err)
		get_tree().quit(2)
		return
	var cli: String = args.get("cli", "none")
	if cli in CLIS:
		pty.write(_cli_line(cli) + "\r")  # o terminal enfileira: o CLI sobe quando o shell estiver pronto
	if args.has("autotest"):
		_run_autotest(cli)


func _apply_font() -> void:
	## --font="Cascadia Mono" usa uma fonte do sistema; --fontsize=N muda o tamanho.
	if args.has("font"):
		var f := SystemFont.new()
		f.font_names = PackedStringArray([args["font"]])
		for k in ["normal_font", "bold_font", "italics_font", "bold_italics_font"]:
			terminal.add_theme_font_override(k, f)
	if args.has("fontsize"):
		for k in ["normal_font_size", "bold_font_size", "italics_font_size", "bold_italics_font_size"]:
			terminal.add_theme_font_size_override(k, int(args["fontsize"]))


const ANSI_TEST := '$e=[char]27; Write-Host "$e[38;2;255;100;0mTRUECOLOR$e[0m $e[31mRED16$e[0m $e[38;5;208mCOR256$e[0m $e[1mBOLD$e[0m"; Write-Host (([string][char]0x2500)*30); Write-Host ([string][char]0x2590 + [char]0x259B + [char]0x2588 + [char]0x2588 + [char]0x2588 + [char]0x259B + [char]0x258C)'


func _cli_line(cli: String) -> String:
	if cli == "claude":
		return "claude --session-id %s -n orb-godot" % _uuid4()
	return cli


func _uuid4() -> String:
	var b := Crypto.new().generate_random_bytes(16)
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	var h := b.hex_encode()
	return "%s-%s-%s-%s-%s" % [h.substr(0, 8), h.substr(8, 4), h.substr(12, 4), h.substr(16, 4), h.substr(20, 12)]


func _parse_args() -> void:
	for a in OS.get_cmdline_user_args():
		if not a.begins_with("--"):
			continue
		var kv := a.substr(2).split("=", true, 1)
		args[kv[0]] = kv[1] if kv.size() > 1 else "true"


func _run_autotest(cli: String) -> void:
	await get_tree().create_timer(float(args.get("wait", "10"))).timeout
	if cli == "none":
		pty.write("echo ORB_GODOT_OK\r")
		if args.has("ansi"):
			pty.write(ANSI_TEST + "\r")
		await get_tree().create_timer(2.0).timeout
	var before := _geometry()
	get_window().size = Vector2i(800, 420)
	await get_tree().create_timer(2.5).timeout
	var after := _geometry()
	var text := terminal.copy_all()
	var font: Font = terminal.get_theme_font("normal_font")
	var fsize: int = terminal.get_theme_font_size("normal_font_size")
	var metrics := {
		"cell_size": str(terminal.get_cell_size()),
		"font_size": fsize,
		"advance_M": str(font.get_char_size("M".unicode_at(0), fsize)),
		"advance_box_2500": str(font.get_char_size(0x2500, fsize)),
		"advance_block_2588": str(font.get_char_size(0x2588, fsize)),
		"has_2500": font.has_char(0x2500),
		"has_2588": font.has_char(0x2588),
	}
	var result := {
		"metrics": metrics,
		"cli": cli,
		"before_resize": before,
		"after_resize": after,
		"terminal_text_length": text.length(),
		"contains_echo": text.contains("ORB_GODOT_OK"),
		"contains_claude_banner": text.contains("Claude Code"),
		"terminal_text_head": text.substr(0, 600),
	}
	if args.has("shot"):
		get_viewport().get_texture().get_image().save_png(args["shot"])
	if args.has("out"):
		var f := FileAccess.open(args["out"], FileAccess.WRITE)
		f.store_string(JSON.stringify(result, "  "))
		f.close()
	get_tree().quit()


func _geometry() -> Dictionary:
	return {"term_cols": terminal.get_cols(), "term_rows": terminal.get_rows(),
			"pty_cols": pty.cols, "pty_rows": pty.rows}
