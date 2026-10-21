## Engine loop whose pitch follows the speed, only during a match (Unity's CarSoundController).
extends AudioStreamPlayer

const PITCH_TOP_KMH: float = 100.0

@export var min_pitch: float = 0.8
@export var max_pitch: float = 1.2

@onready var _car: Car = get_parent() as Car


func _process(_delta: float) -> void:
	if GameEvents.state != GameEvents.State.IN_GAME:
		if playing:
			stop()
		return
	if not playing:
		play()
	pitch_scale = lerpf(min_pitch, max_pitch, clampf(_car.km_per_hour / PITCH_TOP_KMH, 0.0, 1.0))
