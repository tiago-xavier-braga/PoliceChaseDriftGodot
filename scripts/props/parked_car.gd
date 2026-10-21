## Parked car that wobbles when something drives into it: a pitch from the front or back, a roll
## from the sides (Unity's PropCarAnimator and its Animator).
extends Node3D

const LONGITUDINAL_META: StringName = &"longitudinal"
const LONGITUDINAL_ANIMATION: StringName = &"parked_car/longitudinal_collision"
const SIDE_ANIMATION: StringName = &"parked_car/side_collision"

@onready var _animation_player: AnimationPlayer = $AnimationPlayer


func _ready() -> void:
	for trigger: Node in $Triggers.get_children():
		var longitudinal: bool = trigger.get_meta(LONGITUDINAL_META)
		(trigger as Area3D).body_entered.connect(_on_trigger_entered.bind(longitudinal))


func _on_trigger_entered(_body: Node3D, longitudinal: bool) -> void:
	_animation_player.stop()
	_animation_player.play(LONGITUDINAL_ANIMATION if longitudinal else SIDE_ANIMATION)
