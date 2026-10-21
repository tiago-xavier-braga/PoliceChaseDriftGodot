## Menu screen that fades and scales in or out (Unity's CanvasGroupController with UICoreSettings).
class_name MenuPanel
extends Control

const DURATION: float = 0.5
const ENABLED_SCALE: float = 1.0
const DISABLED_SCALE: float = 0.8

@export var enabled_on_start: bool = false

var _enabled: bool = false
var _fade_tween: TweenHandle
var _scale_tween: TweenHandle


func _ready() -> void:
	_enabled = enabled_on_start
	visible = _enabled
	modulate.a = 1.0 if _enabled else 0.0
	scale = Vector2.ONE * (ENABLED_SCALE if _enabled else DISABLED_SCALE)
	resized.connect(_center_pivot)
	_center_pivot()


func _exit_tree() -> void:
	_cancel_tweens()


func enable() -> void:
	if _enabled:
		return
	_enabled = true
	visible = true
	_animate(1.0, ENABLED_SCALE, Callable())


func disable() -> void:
	if not _enabled:
		return
	_enabled = false
	_animate(0.0, DISABLED_SCALE, hide)


func _animate(alpha: float, target_scale: float, on_complete: Callable) -> void:
	_cancel_tweens()
	_fade_tween = LeafTween.to(modulate.a, alpha, DURATION, _set_alpha) \
		.set_ease(LeafTweenEasing.EaseType.IN_OUT_QUAD).set_on_complete(on_complete).get_handle()
	_scale_tween = LeafTween.to(scale, Vector2.ONE * target_scale, DURATION, set_scale) \
		.set_ease(LeafTweenEasing.EaseType.IN_OUT_QUAD).get_handle()


func _set_alpha(alpha: float) -> void:
	modulate.a = alpha


func _cancel_tweens() -> void:
	if _fade_tween:
		LeafTween.cancel(_fade_tween)
	if _scale_tween:
		LeafTween.cancel(_scale_tween)


func _center_pivot() -> void:
	pivot_offset = size / 2.0
