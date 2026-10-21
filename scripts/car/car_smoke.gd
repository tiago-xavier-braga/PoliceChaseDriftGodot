## Engine smoke shown while the player's health is low (Unity's CarParticleController).
extends CPUParticles3D

@export var health_threshold: int = 5


func _ready() -> void:
	PlayerHealth.health_changed.connect(_on_health_changed)


func _on_health_changed(health: int) -> void:
	emitting = health < health_threshold
