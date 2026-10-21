## Renders a level for a few seconds and saves screenshots (needs a display, not --headless).
## Run: godot --path . --script res://tools/godot/screenshot.gd -- <scene> <out_dir> <frames,...> [start]
extends SceneTree

var _frame: int = 0
var _frames: PackedInt32Array = []
var _out: String = ""
var _start: bool = false


func _initialize() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	_out = args[1]
	for f: String in args[2].split(","):
		_frames.append(int(f))
	_start = args.size() > 3
	change_scene_to_file(args[0])


func _process(_delta: float) -> bool:
	_frame += 1
	if _start and _frame == 30:
		current_scene.get_node("MatchManager").start_match()
		Input.action_press(&"move_up")
	if _start and _frame == 150:
		Input.action_press(&"move_right")
	if _start and _frame == 175:
		Input.action_release(&"move_right")
	if _frame in _frames:
		root.get_viewport().get_texture().get_image().save_png("%s/shot_%04d.png" % [_out, _frame])
	return _frame >= _frames[_frames.size() - 1]
