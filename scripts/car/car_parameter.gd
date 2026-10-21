## Tuning of one car, ported from Unity's CarParameter ScriptableObject.
## Unity's drift friction fields are left out: nothing in the game turns the handbrake on.
class_name CarParameter
extends Resource

@export var id: String = ""
@export var health: int = 15
## Unity compares it with the forward speed in m/s, not km/h, so cars rarely reach it.
@export var top_speed: float = 100.0
## Motor torque (N·m) per motorized wheel at standstill.
@export var acceleration: float = 800.0
## Brake torque (N·m) per wheel at full input.
@export var brake_force: float = 2000.0
@export var steering_range: float = 30.0
@export var steering_range_at_max_speed: float = 20.0
@export var center_of_gravity_offset: float = 0.0
