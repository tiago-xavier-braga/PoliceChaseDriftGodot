## Clicks through the menus (garage, play, game over, restart) and saves screenshots.
## Run: godot --path . --script res://tools/godot/ui_test.gd -- <out_dir>
extends SceneTree

var _frame: int = 0
var _out: String = ""


func _initialize() -> void:
	_out = OS.get_cmdline_user_args()[0]
	change_scene_to_file("res://scenes/levels/lvl_game.tscn")


func _press(path: String) -> void:
	(current_scene.get_node(path) as Button).pressed.emit()


func _shot(name: String) -> void:
	root.get_viewport().get_texture().get_image().save_png("%s/%s.png" % [_out, name])


func _process(_delta: float) -> bool:
	_frame += 1
	var events: Node = root.get_node("/root/GameEvents")
	match _frame:
		40:
			_press("UI/InitialMenu/GarageButton")
		80:
			_press("UI/GarageMenu/NextButton")
		110:
			_shot("1_garage_race")
			_press("UI/GarageMenu/NextButton")
		140:
			_shot("2_garage_ambulance")
			_press("UI/GarageMenu/SelectButton")
			_press("UI/GarageMenu/ExitButton")
		180:
			_shot("3_menu_after_garage")
			print("selected car: ", events.car.name, " index ", events.current_car_index, " health ", root.get_node("/root/PlayerHealth").health)
			_press("UI/InitialMenu/PlayButton")
		300:
			root.get_node("/root/PlayerHealth").take_damage(100)
		340:
			_shot("4_game_over")
			print("state after death: ", events.state, " health reset to ", root.get_node("/root/PlayerHealth").health, " frozen ", events.car.freeze)
			_press("UI/GameOverMenu/HomeButton")
		420:
			_shot("5_reloaded")
			print("after reload: scene ", current_scene.name, " state ", events.state, " car ", events.car.name if is_instance_valid(events.car) else "none")
			return true
	return false
