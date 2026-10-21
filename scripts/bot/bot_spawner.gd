## Brings police cars in during a match, one every few seconds, at the spawn point farthest from
## the player (Unity's BotSpawnerController).
extends Node3D

@export var bot_scene: PackedScene
@export var max_bots: int = 30
@export var spawn_interval: float = 5.0
## Unity serialized its counter as 1, so one bot of the pool is never used.
@export var first_bot_index: int = 1

var _spawned_count: int = 0
var _timer: float = 0.0
var _spawn_points: Array[Marker3D] = []


func _ready() -> void:
	_spawned_count = first_bot_index
	for child: Node in get_children():
		if child is Marker3D:
			_spawn_points.append(child as Marker3D)


func _process(delta: float) -> void:
	if GameEvents.state != GameEvents.State.IN_GAME or _spawned_count >= max_bots:
		return
	_timer += delta
	if _timer < spawn_interval:
		return
	_timer = 0.0
	_spawn_bot()


func _spawn_bot() -> void:
	var player_car: Car = GameEvents.car
	var farthest: Marker3D = _spawn_points[0]
	var max_distance: float = player_car.global_position.distance_to(farthest.global_position)
	for point: Marker3D in _spawn_points:
		var distance: float = player_car.global_position.distance_to(point.global_position)
		if distance > max_distance:
			farthest = point
			max_distance = distance
	var bot: Car = bot_scene.instantiate() as Car
	add_child(bot)
	bot.global_transform = farthest.global_transform
	(bot.get_node("BotController") as BotController).target = player_car
	_spawned_count += 1
