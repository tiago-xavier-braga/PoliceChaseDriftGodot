## Headless smoke test: starts a match, drives the car and prints what happens.
## Run: godot --headless --path . --fixed-fps 60 --script res://tools/godot/drive_test.gd
extends SceneTree

var _frame: int = 0
var _manager: Node


func _initialize() -> void:
	change_scene_to_file("res://scenes/levels/lvl_game.tscn")


func _process(_delta: float) -> bool:
	_frame += 1
	var car: Car = root.get_node("/root/GameEvents").car
	if _frame == 60:
		_manager = current_scene.get_node("MatchManager")
		print("car: ", car.name, " at ", car.global_position, " health ", root.get_node("/root/PlayerHealth").health)
		_manager.start_match()
		car.body_entered.connect(func(b: Node) -> void: print("  car hit %s (layer %d) t=%.2f kmh=%.1f" % [b.get_path(), (b as CollisionObject3D).collision_layer, _frame / 60.0, car.km_per_hour]))
		Input.action_press(&"move_up")
	if _frame in [90, 120, 180, 240]:
		print("t=%.1f pos=%s kmh=%.1f fwd=%s" % [_frame / 60.0, car.global_position, car.km_per_hour, car.global_basis.z])
	if _frame == 240:
		Input.action_press(&"move_right")
	if _frame in [270, 300]:
		print("turning t=%.1f pos=%s kmh=%.1f fwd=%s up=%s" % [_frame / 60.0, car.global_position, car.km_per_hour, car.global_basis.z, car.global_basis.y])
	if _frame == 300:
		Input.action_release(&"move_right")
		Input.action_release(&"move_up")
		Input.action_press(&"move_down")
	if _frame in [360, 420]:
		print("braking t=%.1f kmh=%.1f fwd_speed=%.2f" % [_frame / 60.0, car.km_per_hour, car.global_basis.z.dot(car.linear_velocity)])
	if _frame == 330:
		for bot: Node in current_scene.get_node("BotSpawner").get_children():
			if bot is Car:
				bot.body_entered.connect(func(b: Node) -> void: print("  bot hit %s t=%.2f" % [b.get_path(), _frame / 60.0]))
	if _frame == 480:
		var bots: int = current_scene.get_node("BotSpawner").get_child_count() - 6
		print("bots: ", bots, " health: ", root.get_node("/root/PlayerHealth").health, " state: ", root.get_node("/root/GameEvents").state, " night: ", root.get_node("/root/GameEvents").is_night)
		for bot: Node in current_scene.get_node("BotSpawner").get_children():
			if bot is Car:
				print("  bot ", bot.global_position, " kmh ", (bot as Car).km_per_hour)
	if _frame % 120 == 0 and _frame > 480:
		var line: String = "t=%d health=%d car=%s |" % [_frame / 60, root.get_node("/root/PlayerHealth").health, car.global_position.snapped(Vector3.ONE * 0.1)]
		for bot: Node in current_scene.get_node("BotSpawner").get_children():
			if bot is Car:
				line += " %s %.0fkmh d=%.0f;" % [(bot as Car).global_position.snapped(Vector3.ONE), (bot as Car).km_per_hour, (bot as Car).global_position.distance_to(car.global_position)]
		print(line)
	if _frame == 2400:
		print("t=20 state ", root.get_node("/root/GameEvents").state, " health ", root.get_node("/root/PlayerHealth").health, " night ", root.get_node("/root/GameEvents").is_night, " car ", car.global_position)
		return true
	return false
