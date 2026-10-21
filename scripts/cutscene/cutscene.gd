## Plays the opening cutscene once and then loads the game (Unity's CutsceneManager with the
## Opening timeline).
extends Node3D

const GAME_SCENE: String = "res://scenes/levels/lvl_game.tscn"
const OPENING_ANIMATION: StringName = &"opening"

@onready var _animation_player: AnimationPlayer = $AnimationPlayer


func _ready() -> void:
	GameEvents.set_state(GameEvents.State.READY)
	Loading.hide_loading()
	_animation_player.animation_finished.connect(_on_animation_finished)
	_animation_player.play(OPENING_ANIMATION)


func _on_animation_finished(_animation: StringName) -> void:
	Loading.show_now()
	get_tree().change_scene_to_file(GAME_SCENE)
