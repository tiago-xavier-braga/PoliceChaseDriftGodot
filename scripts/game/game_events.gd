## Autoload replacing Unity's ScriptableObject event channels (OnGameStateChanged, OnCarSelected,
## OnNightChanged). Like those channels, it keeps the last value so late listeners can read it.
extends Node

signal state_changed(state: State)
signal car_selected(car: Car)
signal night_changed(is_night: bool)

enum State { NONE, READY, IN_GAME, PAUSE, GAME_OVER }

var state: State = State.NONE
var car: Car = null
var is_night: bool = false
## Car picked in the garage (Unity's PlayerData.CurrentCar): survives restarting the match.
var current_car_index: int = 0
## Sun rotation: Unity never reloads the static environment on restart, so the cycle carries on.
var sun_angle_degrees: float = 0.0


func set_state(new_state: State) -> void:
	state = new_state
	state_changed.emit(state)


func select_car(new_car: Car) -> void:
	car = new_car
	car_selected.emit(car)


func set_night(value: bool) -> void:
	is_night = value
	night_changed.emit(is_night)
