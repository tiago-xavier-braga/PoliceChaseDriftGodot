## Ends the match when the player's car falls into the water (Unity's water box collider).
extends Area3D

@export var match_manager: Node


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(_body: Node3D) -> void:
	match_manager.finish_match()
