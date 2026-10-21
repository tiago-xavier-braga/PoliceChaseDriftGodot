## Autoload holding the player's health, like Unity's PlayerHealth ScriptableObject: the car's
## impacts, its smoke and the match all read it without knowing about each other.
extends Node

signal health_changed(health: int)

## Unity's PlayerHealth asset value, used when the match resets it after a game over.
const DEFAULT_HEALTH: int = 20

var health: int = DEFAULT_HEALTH


func take_damage(damage: int) -> void:
	set_health(maxi(0, health - damage))


func reset_health() -> void:
	set_health(DEFAULT_HEALTH)


func set_health(value: int) -> void:
	health = value
	health_changed.emit(health)
