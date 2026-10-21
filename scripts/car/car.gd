## Arcade car on a VehicleBody3D, ported from Unity's CarMovementController (WheelColliders).
## The player or a bot feeds it a move input; the car turns it into motor, brake and steering.
class_name Car
extends VehicleBody3D

const MS_TO_KMH: float = 3.6
## Unity's resting rigidbody reports exactly 0 m/s; Godot's wheels jitter around it, which would
## read as "moving backward" and brake instead of driving off.
const STOPPED_SPEED: float = 0.3

@export var parameter: CarParameter

var km_per_hour: float = 0.0

var _input: Vector2 = Vector2.ZERO
var _wheel_radius: float = 0.0


func _ready() -> void:
	center_of_mass_mode = CENTER_OF_MASS_MODE_CUSTOM
	center_of_mass = Vector3(0.0, parameter.center_of_gravity_offset, 0.0)
	for child: Node in get_children():
		if child is VehicleWheel3D:
			_wheel_radius = (child as VehicleWheel3D).wheel_radius


func _physics_process(delta: float) -> void:
	km_per_hour = linear_velocity.length() * MS_TO_KMH
	var forward_speed: float = global_basis.z.dot(linear_velocity)
	var speed_factor: float = clampf(inverse_lerp(0.0, parameter.top_speed, absf(forward_speed)), 0.0, 1.0)
	var motor_torque: float = lerpf(parameter.acceleration, 0.0, speed_factor)
	var steer_range: float = lerpf(parameter.steering_range, parameter.steering_range_at_max_speed, speed_factor)
	# Godot steers left with positive angles, Unity right.
	steering = deg_to_rad(-_input.x * steer_range)
	if absf(forward_speed) < STOPPED_SPEED or _unity_sign(_input.y) == _unity_sign(forward_speed):
		engine_force = _input.y * motor_torque / _wheel_radius
		brake = 0.0
	else:
		engine_force = 0.0
		# Godot's brake is the friction impulse per physics step.
		brake = absf(_input.y) * parameter.brake_force / _wheel_radius * delta


func set_move_input(value: Vector2) -> void:
	_input = value


func block() -> void:
	freeze = true


## Unity's Mathf.Sign: zero counts as positive.
func _unity_sign(value: float) -> float:
	return -1.0 if value < 0.0 else 1.0
