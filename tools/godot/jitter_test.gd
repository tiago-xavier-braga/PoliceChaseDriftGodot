## Headless check: samples the car's height and pitch while driving straight, and the cutscene
## characters' animation state.
extends SceneTree

var _frame: int = 0
var _samples: Array[String] = []


func _initialize() -> void:
	change_scene_to_file(OS.get_cmdline_user_args()[0])


func _physics_process(_delta: float) -> bool:
	_frame += 1
	var scene: Node = current_scene
	if scene == null:
		return false
	if scene.name == "Game":
		var car: Car = root.get_node("/root/GameEvents").car
		if _frame == 30:
			scene.get_node("MatchManager").start_match()
			Input.action_press(&"move_up")
		if _frame > 60 and _frame < 140 and _frame % 2 == 0:
			_samples.append("y=%.4f pitch=%.3f roll=%.3f v=%.1f" % [car.global_position.y, rad_to_deg(car.global_rotation.x), rad_to_deg(car.global_rotation.z), car.km_per_hour])
		if _frame == 140:
			print("\n".join(_samples))
			return true
	else:
		if _frame in [60, 120, 240, 330, 420, 500, 560]:
			var line: String = "t=%.1f" % (_frame / 50.0)
			for who: String in ["Opening/Police/Model/AnimationPlayer", "Opening/Thief/Model/AnimationPlayer"]:
				var player: AnimationPlayer = scene.get_node(who)
				line += " | %s anim=%s playing=%s pos=%.2f" % [who.get_slice("/", 1), player.current_animation, player.is_playing(), player.current_animation_position]
			print(line)
		if _frame == 600:
			var lib: AnimationLibrary = (scene.get_node("Opening/Police/Model/AnimationPlayer") as AnimationPlayer).get_animation_library(&"")
			print("walk length=", lib.get_animation(&"walk").length, " loop=", lib.get_animation(&"walk").loop_mode, " anims=", lib.get_animation_list())
			return true
	return false
