## Headless check of the props: a lamp post knocked by the player, a parked car hit, the water.
extends SceneTree

var _frame: int = 0
var _lamp: RigidBody3D
var _parked: Node3D


func _initialize() -> void:
	change_scene_to_file("res://scenes/levels/lvl_game.tscn")


func _process(_delta: float) -> bool:
	_frame += 1
	var events: Node = root.get_node("/root/GameEvents")
	var car: Car = events.car
	match _frame:
		30:
			current_scene.get_node("MatchManager").start_match()
			_lamp = current_scene.get_node("DynamicEnvironment/Lampposts/Streat/Instance5")
			car.global_position = _lamp.global_position + Vector3(0, 0.3, -6)
			car.look_at_from_position(car.global_position, _lamp.global_position + Vector3(0, 0.3, 0), Vector3.UP, true)
			Input.action_press(&"move_up")
		150:
			Input.action_release(&"move_up")
			print("lamp broken=", _lamp._broken, " health=", root.get_node("/root/PlayerHealth").health, " lamp tilt=", _lamp.global_basis.y)
			_parked = current_scene.get_node("DynamicEnvironment/ParkedCars").get_child(0)
			car.linear_velocity = Vector3.ZERO
			car.global_position = _parked.global_position + _parked.global_basis.z * 5.0 + Vector3(0, 0.4, 0)
			car.look_at_from_position(car.global_position, _parked.global_position + Vector3(0, 0.4, 0), Vector3.UP, true)
			Input.action_press(&"move_up")
		230:
			print("parked car playing=", (_parked.get_node("AnimationPlayer") as AnimationPlayer).current_animation, " health=", root.get_node("/root/PlayerHealth").health)
			Input.action_release(&"move_up")
		800:
			print("lamp still in tree after 10 s: ", is_instance_valid(_lamp))
			car.linear_velocity = Vector3.ZERO
			car.global_position = Vector3(0, 2, 90)
		900:
			print("after falling in the water: state=", events.state, " (4 = game over)")
			return true
	return false
