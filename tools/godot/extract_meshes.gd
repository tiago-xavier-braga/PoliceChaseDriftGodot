## Saves every mesh of the imported Kenney models as its own resource, so the generated scenes can
## place sub-meshes (wheels, bodies) one by one the way the Unity prefabs do.
## Also writes the convex hull points of car bodies and the triangles of curved roads to
## tools/unity_port/mesh_shapes.json, so gen_godot.py can bake each instance's scale into its shapes.
## Run after an import: godot --headless --path . --script res://tools/godot/extract_meshes.gd
extends SceneTree

const MODELS_ROOT: String = "res://assets/models"
const KITS: Array[String] = [
	"kenney_car_kit",
	"kenney_city_kit_commercial",
	"kenney_city_kit_industrial",
	"kenney_city_kit_roads",
]
const CONVEX_PARTS: Array[String] = ["body", "grill"]
const TRIMESH_MODELS: Array[String] = ["road_bend", "road_slant_curve"]
const SHAPES_PATH: String = "res://tools/unity_port/mesh_shapes.json"

var _shapes: Dictionary = {}


func _init() -> void:
	for kit: String in KITS:
		var kit_dir: String = MODELS_ROOT.path_join(kit)
		DirAccess.make_dir_recursive_absolute(kit_dir.path_join("meshes"))
		for file: String in DirAccess.get_files_at(kit_dir):
			if file.get_extension() == "fbx":
				_extract(kit_dir, file.get_basename())
	var file: FileAccess = FileAccess.open(SHAPES_PATH, FileAccess.WRITE)
	file.store_string(JSON.stringify(_shapes))
	quit()


func _extract(kit_dir: String, model: String) -> void:
	var scene: Node = (load(kit_dir.path_join(model + ".fbx")) as PackedScene).instantiate()
	var meshes: Array[MeshInstance3D] = []
	_collect(scene, meshes)
	for instance: MeshInstance3D in meshes:
		var part: String = instance.name.to_snake_case().replace("-", "_")
		var base: String = model if meshes.size() == 1 else "%s_%s" % [model, part]
		var mesh: Mesh = instance.mesh
		mesh.resource_name = base
		ResourceSaver.save(mesh, kit_dir.path_join("meshes/%s.res" % base))
		if part in CONVEX_PARTS:
			_shapes[base + "_convex"] = _flatten((mesh.create_convex_shape() as ConvexPolygonShape3D).points)
		if model in TRIMESH_MODELS:
			_shapes[base + "_trimesh"] = _flatten(mesh.get_faces())
	scene.free()


func _flatten(points: PackedVector3Array) -> Array[float]:
	var out: Array[float] = []
	for point: Vector3 in points:
		out.append_array([snappedf(point.x, 0.0001), snappedf(point.y, 0.0001), snappedf(point.z, 0.0001)])
	return out


func _collect(node: Node, out: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D:
		out.append(node as MeshInstance3D)
	for child: Node in node.get_children():
		_collect(child, out)
