## Prints the node tree, meshes, materials and animations of every imported model.
## Run: godot --headless --path . --script res://tools/godot/dump_models.gd
extends SceneTree


func _init() -> void:
	for dir_path: String in _model_dirs("res://assets/models"):
		for file: String in DirAccess.get_files_at(dir_path):
			if file.get_extension() == "fbx":
				_dump(dir_path.path_join(file))
	quit()


func _model_dirs(root: String) -> Array[String]:
	var dirs: Array[String] = []
	for sub: String in DirAccess.get_directories_at(root):
		dirs.append(root.path_join(sub))
	return dirs


func _dump(path: String) -> void:
	var scene: Node = (load(path) as PackedScene).instantiate()
	print("## ", path)
	_walk(scene, scene, 1)
	scene.free()


func _walk(node: Node, root: Node, depth: int) -> void:
	var line: String = "  ".repeat(depth) + "%s (%s)" % [node.name, node.get_class()]
	if node is Node3D and node != root:
		line += " xf=%s" % [(node as Node3D).transform]
	if node is MeshInstance3D:
		var mesh: Mesh = (node as MeshInstance3D).mesh
		var mats: Array[String] = []
		for i: int in mesh.get_surface_count():
			var mat: Material = mesh.surface_get_material(i)
			mats.append(mat.resource_name if mat else "null")
		line += " mesh=%s aabb=%s mats=%s" % [mesh.resource_name, mesh.get_aabb(), mats]
	if node is AnimationPlayer:
		line += " anims=%s" % [(node as AnimationPlayer).get_animation_list()]
	print(line)
	for child: Node in node.get_children():
		_walk(child, root, depth + 1)
