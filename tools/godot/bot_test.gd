## Headless check of one police car chasing a parked player car.
extends SceneTree

var _frame: int = 0
var _bot: Car


func _initialize() -> void:
	change_scene_to_file("res://scenes/levels/lvl_game.tscn")


func _process(_delta: float) -> bool:
	_frame += 1
	var events: Node = root.get_node("/root/GameEvents")
	if _frame == 30:
		current_scene.get_node("MatchManager").start_match()
	if _frame == 31:
		var spawner: Node = current_scene.get_node("BotSpawner")
		_bot = (spawner.bot_scene as PackedScene).instantiate() as Car
		spawner.add_child(_bot)
		_bot.global_transform = spawner.get_node("Position2").global_transform
		_bot.get_node("BotController").target = events.car
		_bot.body_entered.connect(func(b: Node) -> void: print("  bot hit %s t=%.2f" % [b.get_path(), _frame / 60.0]))
	if _frame > 31 and _frame % 30 == 0:
		var ctl: Node = _bot.get_node("BotController")
		print("t=%.1f pos=%s kmh=%.1f fwd=%s rev=%.2f engine=%.0f brake=%.1f steer=%.2f contacts=%s" % [_frame / 60.0, _bot.global_position.snapped(Vector3.ONE * 0.01), _bot.km_per_hour, _bot.global_basis.z.snapped(Vector3.ONE * 0.01), ctl._reverse_time_left, _bot.engine_force, _bot.brake, _bot.steering, [_bot.get_node("FLWheel").is_in_contact(), _bot.get_node("RRWheel").is_in_contact()]])
	return _frame > 600
