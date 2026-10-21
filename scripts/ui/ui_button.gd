## Menu button with the UI Core sounds: one when the pointer enters, one on click
## (Unity's ButtonExtension).
extends Button

@export var hover_sound: AudioStream
@export var click_sound: AudioStream

@onready var _player: AudioStreamPlayer = $AudioStreamPlayer


func _ready() -> void:
	mouse_entered.connect(_play.bind(hover_sound))
	pressed.connect(_play.bind(click_sound))


func _play(sound: AudioStream) -> void:
	_player.stream = sound
	_player.play()
