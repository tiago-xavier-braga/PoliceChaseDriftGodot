## Headless check: frame-to-frame steps of the cutscene car's rendered (interpolated) position
## while it drives through. Even steps = smooth; alternating steps = jitter.
extends SceneTree

var _frame: int = 0
var _last: Vector3
var _steps: Array[float] = []


func _initialize() -> void:
	change_scene_to_file("res://scenes/levels/lvl_cutscene.tscn")


func _process(_delta: float) -> bool:
	_frame += 1
	if current_scene == null or current_scene.name != "Cutscene":
		return false
	var car: Node3D = current_scene.get_node("Opening/CarCutscene/Car")
	var pos: Vector3 = car.get_global_transform_interpolated().origin
	if _frame > 290 and _frame <= 330:
		_steps.append((pos - _last).length())
	_last = pos
	if _frame == 330:
		var mean: float = 0.0
		for s: float in _steps:
			mean += s
		mean /= _steps.size()
		var worst: float = 0.0
		for i: int in range(1, _steps.size()):
			worst = maxf(worst, absf(_steps[i] - _steps[i - 1]) / mean)
		print("mean step %.3f m, worst jump between frames %.0f%% of the mean" % [mean, worst * 100.0])
		print("steps: ", _steps.map(func(s: float) -> String: return "%.2f" % s))
		return true
	return false
