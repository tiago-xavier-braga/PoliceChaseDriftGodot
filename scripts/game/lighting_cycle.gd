## Turns the sun around during a match and tells everyone when night starts and ends
## (Unity's LightingCycleManager).
extends DirectionalLight3D

@export var cycle_seconds: float = 30.0

var _start_basis: Basis


func _ready() -> void:
	_start_basis = basis
	_apply_angle()


func _physics_process(delta: float) -> void:
	if GameEvents.state != GameEvents.State.IN_GAME:
		return
	GameEvents.sun_angle_degrees = fmod(GameEvents.sun_angle_degrees + 360.0 / cycle_seconds * delta, 360.0)
	_apply_angle()
	# Night while the sun shines upward, from below the horizon.
	var is_night: bool = -global_basis.z.y > 0.0
	if is_night != GameEvents.is_night:
		GameEvents.set_night(is_night)


func _apply_angle() -> void:
	# Negative: like Unity's positive X rotation, the sun first climbs toward noon.
	basis = _start_basis * Basis(Vector3.RIGHT, -deg_to_rad(GameEvents.sun_angle_degrees))
