extends Node3D
## Spike 2 (parte 3D): o terminal real projetado como textura num monitor dentro de uma cena 3D.
## É o desenho do "monitor do Rooftop Room": Terminal+PTY vivem num SubViewport; o resultado é
## a textura de um quad 3D. O teclado é encaminhado da janela para o SubViewport.
##
## Rodar:  godot --path . res://monitor3d.tscn -- --cli=none|claude --autotest ...

const POWERSHELL := "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
const CLIS := ["claude", "codex", "hermes"]

var args := {}
var vp: SubViewport
var terminal: Terminal
var pty: PTY
var monitor: MeshInstance3D


func _ready() -> void:
	_parse_args()
	# --- Terminal + PTY dentro do SubViewport (a "tela" do monitor)
	vp = SubViewport.new()
	vp.size = Vector2i(800, 480)
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	terminal = Terminal.new()
	terminal.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	vp.add_child(terminal)
	pty = PTY.new()
	vp.add_child(pty)
	pty.terminal_path = pty.get_path_to(terminal)
	terminal.grab_focus()

	# --- Cena 3D: quad com a textura do SubViewport, inclinado para provar que é 3D de verdade
	monitor = MeshInstance3D.new()
	var quad := QuadMesh.new()
	quad.size = Vector2(1.6, 0.96)
	monitor.mesh = quad
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_texture = vp.get_texture()
	monitor.material_override = mat
	monitor.rotation_degrees = Vector3(-8, 28, 0)
	add_child(monitor)
	var cam := Camera3D.new()
	cam.position = Vector3(0, 0, 1.55)
	add_child(cam)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.05, 0.07, 0.12)
	add_child(env)

	await get_tree().process_frame
	await get_tree().process_frame
	var err := pty.fork(POWERSHELL, PackedStringArray(["-NoLogo"]), args.get("cwd", ProjectSettings.globalize_path("res://")), terminal.get_cols(), terminal.get_rows())
	if err != OK:
		push_error("falha ao abrir o PTY: %d" % err)
		get_tree().quit(2)
		return
	var cli: String = args.get("cli", "none")
	if cli in CLIS:
		pty.write(("claude --session-id %s -n orb-3d" % _uuid4() if cli == "claude" else cli) + "\r")
	if args.has("autotest"):
		_run_autotest(cli)


func _input(event: InputEvent) -> void:
	# Em 3D o teclado não chega sozinho ao Terminal dentro do SubViewport: encaminha.
	if event is InputEventKey or event is InputEventShortcut:
		vp.push_input(event)
		get_viewport().set_input_as_handled()


func _type_text(text: String) -> void:
	## Digita como o usuário digitaria: eventos de teclado na janela (não escreve direto no PTY).
	for ch in text:
		var ev := InputEventKey.new()
		ev.pressed = true
		ev.unicode = ch.unicode_at(0)
		ev.keycode = OS.find_keycode_from_string(ch.to_upper()) if ch != "_" else KEY_UNDERSCORE
		Input.parse_input_event(ev)
		var up := ev.duplicate()
		up.pressed = false
		Input.parse_input_event(up)
		await get_tree().create_timer(0.03).timeout
	var enter := InputEventKey.new()
	enter.pressed = true
	enter.keycode = KEY_ENTER
	Input.parse_input_event(enter)
	var enter_up := enter.duplicate()
	enter_up.pressed = false
	Input.parse_input_event(enter_up)


func _run_autotest(cli: String) -> void:
	await get_tree().create_timer(float(args.get("wait", "6"))).timeout
	if cli == "none":
		await _type_text("echo 3D_KEY_OK")
		await get_tree().create_timer(2.5).timeout
	var text := terminal.copy_all()
	var result := {
		"cli": cli,
		"terminal_cols_rows": [terminal.get_cols(), terminal.get_rows()],
		"subviewport_size": [vp.size.x, vp.size.y],
		"keyboard_forwarded_and_executed": text.count("3D_KEY_OK") >= 2,
		"occurrences_3D_KEY_OK": text.count("3D_KEY_OK"),
		"contains_claude_banner": text.contains("Claude Code"),
		"terminal_text_head": text.substr(0, 500),
	}
	if args.has("shot"):
		get_viewport().get_texture().get_image().save_png(args["shot"])
	if args.has("out"):
		var f := FileAccess.open(args["out"], FileAccess.WRITE)
		f.store_string(JSON.stringify(result, "  "))
		f.close()
	get_tree().quit()


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
