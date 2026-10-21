## Starts and ends a match: the menu hides and the camera zooms out on start; running out of
## health or falling in the water shows the game over panel (Unity's MatchManager and GameManager).
extends Node

const GAME_SCENE: String = "res://scenes/levels/lvl_game.tscn"

@export var initial_menu: MenuPanel
@export var game_over_menu: MenuPanel
@export var camera: Camera3D


func _ready() -> void:
	PlayerHealth.health_changed.connect(_on_health_changed)
	GameEvents.set_state(GameEvents.State.READY)
	Loading.hide_loading()


func start_match() -> void:
	if GameEvents.state == GameEvents.State.IN_GAME:
		return
	camera.start_intro()
	initial_menu.disable()
	GameEvents.set_state(GameEvents.State.IN_GAME)


func finish_match() -> void:
	if GameEvents.state != GameEvents.State.IN_GAME:
		return
	game_over_menu.enable()
	PlayerHealth.reset_health()
	GameEvents.set_state(GameEvents.State.GAME_OVER)


func reload_game() -> void:
	Loading.change_scene(GAME_SCENE)


func _on_health_changed(health: int) -> void:
	if health <= 0:
		finish_match()
