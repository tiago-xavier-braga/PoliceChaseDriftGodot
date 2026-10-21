## Plays through the menus and a match and saves the README screenshots (needs a display).
## Run: godot --path . --fixed-fps 60 --resolution 1280x720 --script res://tools/godot/readme_shots.gd -- <out_dir>
extends SceneTree

## A police car this close to the player makes the chase screenshot.
const CHASE_DISTANCE: float = 10.0
const MAX_MATCH_FRAMES: int = 3600
const CHASE_SHOTS: int = 3
const CHASE_SHOT_INTERVAL: int = 30

var _frame: int = 0
var _out: String = ""
var _start_frame: int = -1
var _chase_shots: int = 0
var _next_chase_frame: int = 0


func _initialize() -> void:
	_out = OS.get_cmdline_user_args()[0]
	change_scene_to_file("res://scenes/levels/lvl_game.tscn")


func _press(path: String) -> void:
	(current_scene.get_node(path) as Button).pressed.emit()


func _shot(name: String) -> void:
	root.get_viewport().get_texture().get_image().save_png("%s/%s.png" % [_out, name])


func _process(_delta: float) -> bool:
	_frame += 1
	match _frame:
		60:
			_shot("menu")
			_press("UI/InitialMenu/GarageButton")
		110:
			_press("UI/GarageMenu/NextButton")
		150:
			_shot("garage")
			_press("UI/GarageMenu/PreviousButton")
			_press("UI/GarageMenu/ExitButton")
		200:
			_press("UI/InitialMenu/PlayButton")
			_start_frame = _frame
	if _start_frame < 0:
		return false
	var t: int = _frame - _start_frame
	if _chase_shots < CHASE_SHOTS and t < MAX_MATCH_FRAMES:
		if t >= _next_chase_frame and _police_distance() < CHASE_DISTANCE:
			_shot("chase_%d" % t)
			_chase_shots += 1
			_next_chase_frame = t + CHASE_SHOT_INTERVAL
		return false
	if _chase_shots < CHASE_SHOTS + 1:
		_chase_shots = CHASE_SHOTS + 1
		root.get_node("/root/PlayerHealth").take_damage(100)
		_next_chase_frame = t + 60
	elif t >= _next_chase_frame:
		_shot("game_over")
		return true
	return false


func _police_distance() -> float:
	var car: Car = root.get_node("/root/GameEvents").car
	var closest: float = INF
	for bot: Node in current_scene.get_node("BotSpawner").get_children():
		if bot is Car:
			closest = minf(closest, (bot as Car).global_position.distance_to(car.global_position))
	return closest
