## Isometric orthographic camera that follows the player's car and zooms out when the match
## starts (Unity's CameraController).
extends Camera3D

## Unity's (-30, 30, -30) with z flipped.
@export var offset: Vector3 = Vector3(-30.0, 30.0, 30.0)
@export var follow_target: bool = true
## Godot's size is the full view height: twice Unity's orthographic size (5 and 10).
@export var initial_size: float = 10.0
@export var end_size: float = 20.0
@export var intro_duration: float = 2.0

var _target: Node3D = null
var _tween: TweenHandle


func _ready() -> void:
	# Moved every frame from the car's interpolated transform: interpolating it again makes it shake.
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	size = initial_size
	GameEvents.car_selected.connect(_on_car_selected)


func _exit_tree() -> void:
	if _tween:
		LeafTween.cancel(_tween)


func _process(_delta: float) -> void:
	if _target == null or not follow_target:
		return
	var target_position: Vector3 = _target.get_global_transform_interpolated().origin
	global_position = target_position + offset
	look_at(target_position)


func start_intro() -> void:
	_tween = LeafTween.to(initial_size, end_size, intro_duration, _set_size) \
		.set_ease(LeafTweenEasing.EaseType.IN_OUT_EXPO).get_handle()


func _set_size(value: float) -> void:
	size = value


func _on_car_selected(car: Car) -> void:
	_target = car
