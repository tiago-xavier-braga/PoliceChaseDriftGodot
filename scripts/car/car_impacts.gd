## Player car collisions, ported from Unity's CollisionDetection and CollisionSoundPlayer: every
## hit that isn't the floor or a road costs health, and props with an impact sound play it.
class_name CarImpacts
extends AudioStreamPlayer

const IMPACT_SOUND_META: StringName = &"impact_sound"

@export var damage: int = 1
@export var min_collision_speed: float = 0.1
@export_flags_3d_physics var ignored_layers: int = 0

@onready var _car: Car = get_parent() as Car


func _ready() -> void:
	_car.body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node) -> void:
	if GameEvents.state == GameEvents.State.IN_GAME and body.has_meta(IMPACT_SOUND_META):
		stream = body.get_meta(IMPACT_SOUND_META)
		play()
	if (body as CollisionObject3D).collision_layer & ignored_layers:
		return
	var other_velocity: Vector3 = (body as RigidBody3D).linear_velocity if body is RigidBody3D else Vector3.ZERO
	if (_car.linear_velocity - other_velocity).length() < min_collision_speed:
		return
	PlayerHealth.take_damage(damage)
