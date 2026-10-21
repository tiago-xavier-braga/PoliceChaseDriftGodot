## Police AI, ported from Unity's BotController: steer toward the player's car and drive at it,
## back off for a moment after hitting anything else, and fade while inside a building.
class_name BotController
extends Area3D

@export var min_turn_angle_degrees: float = 5.0
@export var distance_threshold: float = 2.0
@export var steer_input: float = 1.0
@export var forward_input: float = 1.0
@export var reverse_input: float = -1.0
@export var reverse_duration: float = 1.0
@export var building_fade_alpha: float = 0.3
@export var building_fade_duration: float = 0.25

var target: Node3D = null

var _reverse_time_left: float = 0.0
var _fade_tween: TweenHandle
var _meshes: Array[GeometryInstance3D] = []

@onready var _car: Car = get_parent() as Car


func _ready() -> void:
	_car.body_entered.connect(_on_car_body_entered)
	body_entered.connect(_on_building_entered)
	body_exited.connect(_on_building_exited)
	for mesh: Node in _car.find_children("*", "GeometryInstance3D"):
		_meshes.append(mesh as GeometryInstance3D)


func _exit_tree() -> void:
	if _fade_tween:
		LeafTween.cancel(_fade_tween)


func _physics_process(delta: float) -> void:
	if GameEvents.state != GameEvents.State.IN_GAME or target == null:
		_car.set_move_input(Vector2.ZERO)
		return
	if _reverse_time_left > 0.0:
		_reverse_time_left -= delta
		_car.set_move_input(Vector2(0.0, reverse_input) if _reverse_time_left > 0.0 else Vector2.ZERO)
		return
	var to_target: Vector3 = target.global_position - _car.global_position
	var input: Vector2 = Vector2.ZERO
	# Positive angle: target on the car's right, like Unity's SignedAngle around up.
	var angle: float = rad_to_deg(_car.global_basis.z.signed_angle_to(to_target, Vector3.DOWN))
	if absf(angle) > min_turn_angle_degrees:
		input.x = steer_input if angle > 0.0 else -steer_input
	var distance: float = to_target.length()
	if distance > distance_threshold:
		input.y = forward_input
	elif distance < distance_threshold:
		input.y = reverse_input
	_car.set_move_input(input)


func _on_car_body_entered(body: Node) -> void:
	if target == null or body == target:
		return
	_reverse_time_left = reverse_duration


func _on_building_entered(_body: Node3D) -> void:
	_fade_to(building_fade_alpha)


func _on_building_exited(_body: Node3D) -> void:
	_fade_to(1.0)


func _fade_to(alpha: float) -> void:
	if _fade_tween:
		LeafTween.cancel(_fade_tween)
	_fade_tween = LeafTween.to(1.0 - _meshes[0].transparency, alpha, building_fade_duration, _set_alpha) \
		.get_handle()


func _set_alpha(alpha: float) -> void:
	for mesh: GeometryInstance3D in _meshes:
		mesh.transparency = 1.0 - alpha
