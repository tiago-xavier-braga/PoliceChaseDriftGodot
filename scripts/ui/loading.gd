## Autoload fade screen shown while a level loads (Unity's LoadingCanvasController).
extends CanvasLayer

const DURATION: float = 0.5
const SPINNER_SPEED: float = TAU

var _tween: TweenHandle

@onready var _screen: Control = $Screen
@onready var _spinner: Control = $Screen/Spinner


func _process(delta: float) -> void:
	if _screen.visible:
		_spinner.rotation += SPINNER_SPEED * delta


## Fades in, swaps the level and leaves the screen up: the new level calls hide_loading().
func change_scene(path: String) -> void:
	_screen.mouse_filter = Control.MOUSE_FILTER_STOP
	_screen.visible = true
	_fade(1.0, get_tree().change_scene_to_file.bind(path))


## Unity's EnableLoading(0): covers the screen at once.
func show_now() -> void:
	_cancel()
	_screen.visible = true
	_screen.modulate.a = 1.0


func hide_loading() -> void:
	_screen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade(0.0, _screen.hide)


func _fade(alpha: float, on_complete: Callable) -> void:
	_cancel()
	_tween = LeafTween.to(_screen.modulate.a, alpha, DURATION, _set_alpha) \
		.set_ease(LeafTweenEasing.EaseType.IN_OUT_QUAD).set_on_complete(on_complete).get_handle()


func _set_alpha(alpha: float) -> void:
	_screen.modulate.a = alpha


func _cancel() -> void:
	if _tween:
		LeafTween.cancel(_tween)
