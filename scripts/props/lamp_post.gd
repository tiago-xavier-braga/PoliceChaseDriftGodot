## Street lamp that lights up at night; when the player's car knocks it, the light dies and the
## post dissolves away a few seconds later (Unity's LightObjectController).
extends RigidBody3D

@export var energy_at_day: float = 0.0
@export var energy_at_night: float = 6.0
@export var transition_seconds: float = 1.0
@export var disable_delay: float = 10.0
@export var dissolve_duration: float = 0.5
@export_flags_3d_physics var breaking_layers: int = 0

var _broken: bool = false
var _tween: TweenHandle

@onready var _light: SpotLight3D = $SpotLight
@onready var _material: ShaderMaterial = ($Model as MeshInstance3D).material_override as ShaderMaterial


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	GameEvents.night_changed.connect(_on_night_changed)
	_on_night_changed(GameEvents.is_night)


func _exit_tree() -> void:
	if _tween:
		LeafTween.cancel(_tween)


func _on_night_changed(is_night: bool) -> void:
	if _broken:
		return
	var target: float = energy_at_night if is_night else energy_at_day
	if target > 0.0:
		_light.visible = true
	if _tween:
		LeafTween.cancel(_tween)
	_tween = LeafTween.to(_light.light_energy, target, transition_seconds, _set_energy) \
		.set_ease(LeafTweenEasing.EaseType.IN_OUT_SINE) \
		.set_on_complete(_on_fade_completed.bind(target)).get_handle()


func _set_energy(energy: float) -> void:
	_light.light_energy = energy


func _on_fade_completed(target: float) -> void:
	_light.visible = target > 0.0


func _on_body_entered(body: Node) -> void:
	if _broken or not ((body as CollisionObject3D).collision_layer & breaking_layers):
		return
	_broken = true
	if _tween:
		LeafTween.cancel(_tween)
	_light.light_energy = 0.0
	_light.visible = false
	get_tree().create_timer(disable_delay).timeout.connect(_dissolve)


func _dissolve() -> void:
	_tween = LeafTween.to(0.0, 1.0, dissolve_duration, _set_dissolve).set_on_complete(queue_free).get_handle()


func _set_dissolve(value: float) -> void:
	_material.set_shader_parameter(&"dissolve", value)
