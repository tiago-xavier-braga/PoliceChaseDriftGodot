## Spawns the player's car at the start position and lets the garage menu browse and pick cars
## (Unity's GarageController and PlayerData).
extends Marker3D

@export var database: CarDatabase

var _index: int = 0
var _car: Car = null


func _ready() -> void:
	_index = GameEvents.current_car_index
	# Unity spawns in Start(), after every listener subscribed in OnEnable.
	_spawn_car.call_deferred(_index)


func switch_up() -> void:
	if _index >= database.cars.size() - 1:
		return
	_index += 1
	_spawn_car(_index)


func switch_down() -> void:
	if _index <= 0:
		return
	_index -= 1
	_spawn_car(_index)


func select_car() -> void:
	GameEvents.current_car_index = _index
	_spawn_car(_index)


func exit_garage() -> void:
	_index = GameEvents.current_car_index
	_spawn_car(_index)


func _spawn_car(index: int) -> void:
	if _car:
		_car.queue_free()
	_car = database.cars[index].instantiate() as Car
	get_parent().add_child(_car)
	_car.global_transform = global_transform
	GameEvents.select_car(_car)
