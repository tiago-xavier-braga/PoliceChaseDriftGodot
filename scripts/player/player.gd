## Drives the selected car from the move input during a match and freezes it on game over
## (Unity's PlayerController).
extends Node

var _car: Car = null


func _ready() -> void:
	GameEvents.car_selected.connect(_on_car_selected)
	GameEvents.state_changed.connect(_on_state_changed)


func _physics_process(_delta: float) -> void:
	if GameEvents.state != GameEvents.State.IN_GAME:
		return
	_car.set_move_input(Input.get_vector(&"move_left", &"move_right", &"move_down", &"move_up"))


func _on_car_selected(car: Car) -> void:
	_car = car
	PlayerHealth.set_health(car.parameter.health)


func _on_state_changed(state: GameEvents.State) -> void:
	if state == GameEvents.State.GAME_OVER:
		_car.block()
