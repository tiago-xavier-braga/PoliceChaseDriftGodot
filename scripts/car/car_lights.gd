## Headlights that fade on at night (Unity's CarLightController).
extends Node3D

@export var energy_at_day: float = 0.0
@export var energy_at_night: float = 3.0
@export var transition_seconds: float = 1.0

var _lights: Array[Light3D] = []
var _tween: TweenHandle


func _ready() -> void:
	for child: Node in get_children():
		_lights.append(child as Light3D)
	GameEvents.night_changed.connect(_on_night_changed)
	_on_night_changed(GameEvents.is_night)


func _exit_tree() -> void:
	if _tween:
		LeafTween.cancel(_tween)


func _on_night_changed(is_night: bool) -> void:
	if _tween:
		LeafTween.cancel(_tween)
	var target: float = energy_at_night if is_night else energy_at_day
	_tween = LeafTween.to(_lights[0].light_energy, target, transition_seconds, _set_energy) \
		.set_ease(LeafTweenEasing.EaseType.IN_OUT_SINE).get_handle()


func _set_energy(energy: float) -> void:
	for light: Light3D in _lights:
		light.light_energy = energy
