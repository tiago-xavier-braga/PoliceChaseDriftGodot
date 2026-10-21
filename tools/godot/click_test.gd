## Runs the real game from the main scene and clicks the play button with mouse events,
## like a player would. Run with a display: godot --path . --script res://tools/godot/click_test.gd
extends SceneTree

var _frame: int = 0
var _clicked_at: int = -1


func _initialize() -> void:
	change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))


func _process(_delta: float) -> bool:
	_frame += 1
	var scene: Node = current_scene
	if scene and scene.name == "Game" and _clicked_at < 0 and _frame % 30 == 0:
		var button: Button = scene.get_node("UI/InitialMenu/PlayButton")
		var center: Vector2 = button.get_global_rect().get_center()
		var hovered: Control = root.gui_get_hovered_control()
		print("frame %d: play button at %s, loading visible=%s alpha=%.2f filter=%d" % [_frame, center, root.get_node("/root/Loading/Screen").visible, root.get_node("/root/Loading/Screen").modulate.a, root.get_node("/root/Loading/Screen").mouse_filter])
		if _frame > 60 * 15:
			_click(center)
			_clicked_at = _frame
	if _clicked_at > 0 and _frame == _clicked_at + 5:
		print("hovered control after click: ", root.gui_get_hovered_control())
		print("state after click: ", root.get_node("/root/GameEvents").state, " (2 = in game)")
		return true
	return _frame > 60 * 30


func _click(at: Vector2) -> void:
	var motion: InputEventMouseMotion = InputEventMouseMotion.new()
	motion.position = at
	motion.global_position = at
	root.push_input(motion, true)
	for pressed: bool in [true, false]:
		var event: InputEventMouseButton = InputEventMouseButton.new()
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		event.position = at
		event.global_position = at
		root.push_input(event, true)
