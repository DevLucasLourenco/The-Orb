extends Control
## The Orb — terminal do Inner World no Godot. O Terminal (godot-xterm) só EXIBE bytes; o terminal
## real e o CLI vivem no Terminal Host em Python (ADR 0004). Conecta no Gateway por WebSocket, com o
## mesmo protocolo da página web (docs/PROTOCOL.md §9-§10).
##
## Rodar:  godot --path . -- --url=ws://127.0.0.1:8765/ws --token=XXX --provider=shell|claude|auto [--model=...]
## Autoteste: --autotest --wait=6 --out=resultado.json --shot=captura.png

var args := {}
var terminal: Terminal
var ws := WebSocketPeer.new()
var connected := false
var received_bytes := 0
var events: Array = []
var world: Dictionary = {}


func _ready() -> void:
	_parse_args()
	terminal = Terminal.new()
	terminal.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(terminal)
	terminal.grab_focus()
	# Entrada do usuário (teclado) -> servidor; tamanho -> servidor.
	# base64: o JSON do Godot não escapa caracteres de controle (ESC etc.), então bytes crus quebrariam.
	terminal.data_sent.connect(func(data: PackedByteArray) -> void: _send({"type": "input", "data_b64": Marshalls.raw_to_base64(data)}))
	terminal.size_changed.connect(func(_s) -> void: _send_resize())
	await get_tree().process_frame
	await get_tree().process_frame
	var url := "%s?token=%s&provider=%s&model=%s" % [args.get("url", "ws://127.0.0.1:8765/ws"), args.get("token", "").uri_encode(), args.get("provider", "shell").uri_encode(), args.get("model", "").uri_encode()]
	# O servidor exige Origin local (proteção contra páginas de terceiros).
	ws.handshake_headers = PackedStringArray(["Origin: http://127.0.0.1"])
	var err := ws.connect_to_url(url)
	if err != OK:
		push_error("falha ao conectar: %d" % err)
		get_tree().quit(2)
		return
	if args.has("autotest"):
		_run_autotest()


func _process(_delta: float) -> void:
	ws.poll()
	var state := ws.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		if not connected:
			connected = true
			_send_resize()
		while ws.get_available_packet_count() > 0:
			_on_message(ws.get_packet().get_string_from_utf8())


func _on_message(raw: String) -> void:
	var msg = JSON.parse_string(raw)
	if typeof(msg) != TYPE_DICTIONARY:
		return
	match msg.get("channel", ""):
		"term":
			var bytes := String(msg["data"]).to_utf8_buffer()
			received_bytes += bytes.size()
			terminal.write(bytes)
		"event":
			events.append(msg["event"]["native"]["kind"])
		"world":
			world = msg["world"]
		"system":
			print("[servidor] ", msg.get("info", msg.get("error", "")))


func _send(obj: Dictionary) -> void:
	if ws.get_ready_state() == WebSocketPeer.STATE_OPEN:
		ws.send_text(JSON.stringify(obj))


func _send_resize() -> void:
	_send({"type": "resize", "cols": terminal.get_cols(), "rows": terminal.get_rows()})


func _type_text(text: String) -> void:
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


func _run_autotest() -> void:
	await get_tree().create_timer(float(args.get("wait", "6"))).timeout
	var provider: String = args.get("provider", "shell")
	if provider == "shell":
		await _type_text("echo BRIDGE_KEY_OK")
		await get_tree().create_timer(2.5).timeout
	var text := terminal.copy_all()
	var result := {
		"provider": provider,
		"ws_connected": connected,
		"bytes_received_from_python_host": received_bytes,
		"terminal_cols_rows": [terminal.get_cols(), terminal.get_rows()],
		"keyboard_roundtrip_ok": text.count("BRIDGE_KEY_OK") >= 2,
		"occurrences_BRIDGE_KEY_OK": text.count("BRIDGE_KEY_OK"),
		"contains_claude": text.replace(" ", "").contains("ClaudeCode"),
		"telemetry_events_received": events.size(),
		"terminal_text_head": text.substr(0, 400),
	}
	if args.has("shot"):
		get_viewport().get_texture().get_image().save_png(args["shot"])
	if args.has("out"):
		var f := FileAccess.open(args["out"], FileAccess.WRITE)
		f.store_string(JSON.stringify(result, "  "))
		f.close()
	get_tree().quit()


func _parse_args() -> void:
	for a in OS.get_cmdline_user_args():
		if not a.begins_with("--"):
			continue
		var kv := a.substr(2).split("=", true, 1)
		args[kv[0]] = kv[1] if kv.size() > 1 else "true"
