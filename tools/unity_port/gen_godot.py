"""Generate the Godot scenes of Police Chase: Drift from the Unity scenes and prefabs.

Run from anywhere: python tools/unity_port/gen_godot.py (needs pyyaml, numpy and mutagen).
Run tools/godot/extract_meshes.gd first: the scenes use the meshes and shapes it writes.
Every scene listed in OUTPUTS is overwritten, so hand edits to those files are lost on the next run.

Unity is left-handed, Godot right-handed: every Unity transform is conjugated by Mz = diag(1, 1, -1).
Unity mirrors FBX geometry on X when importing, so FBX meshes get F = diag(-1, 1, -1) (a 180 degree turn
around Y) on the right. Godot lights and cameras look down -Z like Unity's look down +Z after the
conversion, so they take no F. Cars use F as their root frame so that they drive toward +Z, which is
what VehicleBody3D expects.
"""
import json
import math
import os
import re
import sys
import wave

import numpy as np
from mutagen.mp3 import MP3

sys.path.insert(0, os.path.dirname(__file__))
import unity_scene as us  # noqa: E402

GODOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UNITY = os.path.join(GODOT, "unity", "PoliceChaseDrift")
MZ = np.diag([1.0, 1.0, -1.0, 1.0])
F = np.diag([-1.0, 1.0, -1.0, 1.0])

LAYER_WORLD, LAYER_GROUND, LAYER_PLAYER_CAR, LAYER_BOT_CAR, LAYER_BUILDING, LAYER_PROP = 1, 2, 4, 8, 16, 32
ALL_LAYERS = 63
# Unity layer index -> Godot layer bit (TagManager: 6-8 Car, 9 Building, 10 Floor, 11 Road, 12-14 Bot Car).
UNITY_LAYERS = {6: LAYER_PLAYER_CAR, 7: LAYER_PLAYER_CAR, 8: LAYER_PLAYER_CAR, 9: LAYER_BUILDING, 10: LAYER_GROUND,
                11: LAYER_GROUND, 12: LAYER_BOT_CAR, 13: LAYER_BOT_CAR, 14: LAYER_BOT_CAR}

KITS = {
    "Assets/Art/Meshes/Cars/": "kenney_car_kit",
    "Assets/ThirdParty/Kenney City Kit Commercial 2.1/Meshes/": "kenney_city_kit_commercial",
    "Assets/ThirdParty/Kenney City Kit Industrial 1.0/Meshes/": "kenney_city_kit_industrial",
    "Assets/ThirdParty/Kenney City Kit Roads/Meshes/": "kenney_city_kit_roads",
}
# Unity names FBX sub-meshes by a hash of their node name (fileIdsGeneration 2); same ids in every car.
MESH_PARTS = {
    -8545447256379345787: "body", 1781033517927350220: "spoiler", 6903710634689097273: "grill",
    -7285368450605708904: "wheel_back_right", 5598877486925196537: "wheel_back_left",
    -8477954175203834860: "wheel_front_right", -7543623636664196183: "wheel_front_left",
    -3086061465205573400: "door_left", 5688017428630502997: "door_right", -4296368169539796129: "wheel_back",
}
KIT_MATERIAL = {
    "kenney_car_kit": "mat_kenney_car_kit", "kenney_city_kit_commercial": "mat_kenney_city_kit_commercial",
    "kenney_city_kit_industrial": "mat_kenney_city_kit_industrial", "kenney_city_kit_roads": "mat_kenney_city_kit_roads",
}
MATERIALS = {
    "MAT_KennyVariant.mat": "mat_kenney_car_kit", "colormap.mat": "mat_kenney_car_kit",
    "MAT_KennyVariant_2.mat": "mat_kenney_car_kit_variant_2", "MAT_KennyVariant_3.mat": "mat_kenney_car_kit_variant_3",
    "MAT_CityKitCommercial.mat": "mat_kenney_city_kit_commercial",
    "MAT_CityKitIndustrial.mat": "mat_kenney_city_kit_industrial",
    "MAT_CityKitResidentialA.mat": "mat_kenney_city_kit_residential_a",
    "MAT_CityKitResidentialC.mat": "mat_kenney_city_kit_residential_c",
    "MAT_CityKitRoads.mat": "mat_kenney_city_kit_roads", "MAT_Ground.mat": "mat_ground",
    "MAT_MAT_CityKitRoadsDissolve.mat": "mat_lamp_dissolve", "MAT_StylizedOceanWater.mat": "mat_water",
    "MAT_BandEffect.mat": "mat_band_effect", "MAT_EdgeEffect.mat": "mat_edge_effect",
}
SOUNDS = {
    "SFX_ImpactPlank.ogg": "res://assets/audio/sfx_impact_plank.ogg",
    "SFX_ImpactPlate.ogg": "res://assets/audio/sfx_impact_plate.ogg",
    "SFX_CarEngine.wav": "res://assets/audio/sfx_car_engine.wav",
    "SFX_PoliceSiren.mp3": "res://assets/audio/sfx_police_siren.mp3",
    "SFX_Smille.wav": "res://assets/audio/sfx_voice_smile.wav",
    "SFX_SpeakingNervously.wav": "res://assets/audio/sfx_voice_speaking_nervously.wav",
    "SFX_Sprint.wav": "res://assets/audio/sfx_voice_sprint.wav",
    "Overboard.mp3": "res://assets/audio/music_overboard.mp3",
}
SCRIPTS = {
    "car": "res://scripts/car/car.gd", "impacts": "res://scripts/car/car_impacts.gd",
    "smoke": "res://scripts/car/car_smoke.gd", "lights": "res://scripts/car/car_lights.gd",
    "engine": "res://scripts/car/car_engine_sound.gd", "bot": "res://scripts/bot/bot_controller.gd",
    "lamp": "res://scripts/props/lamp_post.gd", "parked_car": "res://scripts/props/parked_car.gd",
    "lighting": "res://scripts/game/lighting_cycle.gd", "cutscene": "res://scripts/cutscene/cutscene.gd",
}
# Unity prefab -> (Godot scene, CarParameter asset, Godot parameter resource)
CARS = {
    "Assets/Level/Prefabs/Car/PlayerCars/Sedan Sports.prefab":
        ("res://scenes/car/sedan_sports.tscn", "SedanSports_CarParameter.asset", "sedan_sports"),
    "Assets/Level/Prefabs/Car/PlayerCars/Race.prefab": ("res://scenes/car/race.tscn", "Race_CarParameter.asset", "race"),
    "Assets/Level/Prefabs/Car/PlayerCars/Taxi.prefab": ("res://scenes/car/taxi.tscn", "Taxi_CarParameter.asset", "taxi"),
    "Assets/Level/Prefabs/Car/PlayerCars/Ambulance.prefab":
        ("res://scenes/car/ambulance.tscn", "Ambulance_CarParameter.asset", "ambulance"),
    "Assets/Level/Prefabs/Car/BotCars/Police Car.prefab":
        ("res://scenes/car/police_car.tscn", "Police_CarParameter.asset", "police"),
}
PROPS = {
    "Assets/Level/Prefabs/Props/Light Curved.prefab": "res://scenes/props/lamp_post.tscn",
    "Assets/Level/Prefabs/Props/Construction Barrier.prefab": "res://scenes/props/construction_barrier.tscn",
}
# WheelCollider (spring 30000 N/m, damper 4500 N·s/m, distance 0.18 m) on a 1000 kg car. Godot multiplies
# stiffness and damping by the chassis mass, and its rest length is where the spring pushes nothing.
WHEEL = {"wheel_rest_length": 0.25, "suspension_travel": 0.2, "suspension_stiffness": 30.0,
         "damping_compression": 3.5, "damping_relaxation": 4.5, "wheel_friction_slip": 3.0}
# URP light intensities don't carry over to Godot energies; these look alike in the scene.
HEADLIGHT_ENERGY_AT_NIGHT = 3.0
LAMP_ENERGY_AT_NIGHT = 6.0
LIGHT_FAR_FROM_CAR = 5.0
# Unity's flat ambient at intensity 1 plus the sun saturates the Compatibility renderer; tuned by eye.
AMBIENT_ENERGY = 0.5
SUN_ENERGY = 0.8
TIMELINE_FPS = 30
SHAPES = json.load(open(os.path.join(os.path.dirname(__file__), "mesh_shapes.json")))


# ---------------------------------------------------------------- math

def quat_m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def euler_m(e):
    """Unity euler degrees (applied Z, X, Y) -> 3x3 rotation."""
    x, y, z = [math.radians(v) for v in e]
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return ry @ rx @ rz


def local_m(n, with_scale=True):
    m = np.eye(4)
    m[:3, :3] = quat_m(n.rot) @ (np.diag(n.scale) if with_scale else np.eye(3))
    m[:3, 3] = n.pos
    return m


def translate(v):
    m = np.eye(4)
    m[:3, 3] = v
    return m


def to_godot(m):
    return MZ @ m @ MZ


def scale_of(m):
    return np.array([np.linalg.norm(m[:3, i]) for i in range(3)])


def ortho(m):
    o = m.copy()
    for i in range(3):
        o[:3, i] = m[:3, i] / np.linalg.norm(m[:3, i])
    return o


def quat_of(r):
    """3x3 rotation -> (x, y, z, w)."""
    t = np.trace(r)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        return ((r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s, 0.25 * s)
    i = int(np.argmax([r[0, 0], r[1, 1], r[2, 2]]))
    j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(1.0 + r[i, i] - r[j, j] - r[k, k]) * 2
    q = [0.0, 0.0, 0.0, 0.0]
    q[i] = 0.25 * s
    q[j] = (r[j, i] + r[i, j]) / s
    q[k] = (r[k, i] + r[i, k]) / s
    q[3] = (r[k, j] - r[j, k]) / s
    return tuple(q)


def fmt(v):
    v = round(float(v), 4)
    if abs(v) < 1e-4:
        return "0"
    return ("%.4f" % v).rstrip("0").rstrip(".")


def tf(m):
    if np.allclose(m, np.eye(4), atol=1e-6):
        return None
    vals = [m[i][j] for i in range(3) for j in range(3)] + [m[0][3], m[1][3], m[2][3]]
    return "Transform3D(%s)" % ", ".join(fmt(v) for v in vals)


def vec3(v):
    return "Vector3(%s)" % ", ".join(fmt(x) for x in v)


def color(c, alpha=None):
    return "Color(%s, %s, %s, %s)" % (fmt(c["r"]), fmt(c["g"]), fmt(c["b"]), fmt(c["a"] if alpha is None else alpha))


def node_name(name):
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", name) if p]
    return "".join(p[0].upper() + p[1:] for p in parts) or "Node"


def snake(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ---------------------------------------------------------------- tscn writer

class Tscn:
    def __init__(self, kind="gd_scene"):
        self.kind = kind
        self.ext = []
        self.sub = []
        self.nodes = []
        self.names = {}
        self.connections = []

    def ext_res(self, typ, path):
        for i, (_, p) in enumerate(self.ext):
            if p == path:
                return 'ExtResource("%d")' % (i + 1)
        self.ext.append((typ, path))
        return 'ExtResource("%d")' % len(self.ext)

    def mat(self, name):
        return self.ext_res("Material", "res://assets/materials/%s.tres" % name)

    def sub_res(self, typ, props, share=True):
        key = (typ, tuple(props))
        if share:
            for i, (t, p) in enumerate(self.sub):
                if (t, tuple(p)) == key:
                    return 'SubResource("%s_%d")' % (t, i + 1)
        self.sub.append((typ, props))
        return 'SubResource("%s_%d")' % (typ, len(self.sub))

    def add(self, name, parent, typ=None, props=None, instance=None):
        """parent: None for the root, '.' or a path. Returns the new node's path."""
        used = self.names.setdefault(parent or "", set())
        base, i = name, 2
        while name in used:
            name = "%s%d" % (base, i)
            i += 1
        used.add(name)
        self.nodes.append([name, parent, typ, instance, list(props or [])])
        if parent is None:
            return "."
        return name if parent == "." else parent + "/" + name

    def set_root(self, typ, props):
        self.nodes[0][2] = typ
        self.nodes[0][4] += props

    def write(self, path):
        head = "[%s format=3]" % self.kind
        out = [head, ""]
        for i, (t, p) in enumerate(self.ext):
            out.append('[ext_resource type="%s" path="%s" id="%d"]' % (t, p, i + 1))
        if self.ext:
            out.append("")
        for i, (t, props) in enumerate(self.sub):
            out.append('[sub_resource type="%s" id="%s_%d"]' % (t, t, i + 1))
            out += ["%s = %s" % kv for kv in props]
            out.append("")
        for name, parent, typ, inst, props in self.nodes:
            line = '[node name="%s"' % name
            if typ:
                line += ' type="%s"' % typ
            if parent is not None:
                line += ' parent="%s"' % parent
            if inst:
                line += " instance=%s" % inst
            node_paths = [k for k, v in props if v is not None and str(v).startswith("NodePath(")]
            if node_paths:
                line += " node_paths=PackedStringArray(%s)" % ", ".join('"%s"' % k for k in node_paths)
            out.append(line + "]")
            out += ["%s = %s" % kv for kv in props if kv[1] is not None]
            out.append("")
        for sig, src, dst, method in self.connections:
            out.append('[connection signal="%s" from="%s" to="%s" method="%s"]' % (sig, src, dst, method))
        full = os.path.join(GODOT, path.replace("res://", ""))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as fh:
            fh.write("\n".join(out).rstrip() + "\n")
        print("wrote", path)


# ---------------------------------------------------------------- unity helpers

def find(nodes, name):
    for n in nodes:
        if n.name == name:
            return n
    raise KeyError(name)


def script(n, name):
    for s in n.scripts:
        if s["script"] == name:
            return s
    return None


def component(n, kind):
    for o in n.other:
        if kind in o:
            return o[kind]
    return None


def mesh_res(ref):
    """Unity 'fbx#fileID' -> (res path of the extracted mesh, its base name, its kit)."""
    fbx, fid = ref.split("#")
    kit = next(v for k, v in KITS.items() if fbx.startswith(k))
    model = snake(os.path.splitext(os.path.basename(fbx))[0])
    single = os.path.exists(os.path.join(GODOT, "assets/models", kit, "meshes", model + ".res"))
    base = model if single else "%s_%s" % (model, MESH_PARTS[int(fid)])
    return "res://assets/models/%s/meshes/%s.res" % (kit, base), base, kit


def unity_material(n):
    for m in n.materials:
        if m and os.path.basename(m) in MATERIALS:
            return MATERIALS[os.path.basename(m)]
    return None


def impact_sound(n):
    s = script(n, "CollisionSoundGroup.cs")
    if not s:
        return None
    clip = s["fields"].get("<AudioClip>k__BackingField")
    return SOUNDS[os.path.basename(clip.split("#")[0])]


# ---------------------------------------------------------------- baking

class Baker:
    """Flattens a Unity subtree under one Godot node (usually a physics body) at Godot transform body_g."""

    def __init__(self, t, body_path, body_g, area_parent=None):
        self.t = t
        self.body_path = body_path
        self.inv = np.linalg.inv(body_g)
        self.area_parent = area_parent
        self.lights = []

    def bake(self, n, m_parent, skip=()):
        if not n.active or n.name in skip:
            return
        m = m_parent @ local_m(n)
        if n.mesh:
            self.mesh(n, m)
        for c in n.colliders:
            self.shape(n, c, m)
        light = component(n, "Light")
        if light is not None:
            self.lights.append((n, m, light))
        for c in n.children:
            self.bake(c, m, skip)

    def mesh(self, n, m, parent=None, name=None):
        t = self.t
        parent = parent or self.body_path
        name = name or node_name(n.name)
        g = self.inv @ to_godot(m)
        mat = unity_material(n)
        if n.mesh.startswith("builtin:"):
            kind = n.mesh.split(":")[1]
            s = scale_of(g)
            props = [("material", t.mat(mat))] if mat else []
            if kind == "Cube":
                mesh = t.sub_res("BoxMesh", props + [("size", vec3(s))])
            elif kind == "Plane":
                mesh = t.sub_res("PlaneMesh", props + [("size", "Vector2(%s, %s)" % (fmt(10 * s[0]), fmt(10 * s[2])))])
            else:
                raise ValueError(kind)
            return t.add(name, parent, "MeshInstance3D", [("transform", tf(ortho(g))), ("mesh", mesh)])
        res, _, kit = mesh_res(n.mesh)
        props = [("transform", tf(g @ F)), ("mesh", t.ext_res("ArrayMesh", res))]
        if mat and mat != KIT_MATERIAL[kit]:
            props.append(("material_override", t.mat(mat)))
        return t.add(name, parent, "MeshInstance3D", props)

    def shape(self, n, c, m):
        t = self.t
        if "Box" in c:
            b = c["Box"]
            size = np.array([b["size"]["x"], b["size"]["y"], b["size"]["z"]]) * scale_of(m)
            g = self.inv @ ortho(to_godot(m @ translate([b["center"]["x"], b["center"]["y"], b["center"]["z"]])))
            shape = t.sub_res("BoxShape3D", [("size", vec3(np.maximum(size, 0.01)))])
            if b.get("trigger"):
                return self.trigger(n, g, shape)
            t.add("CollisionShape3D", self.body_path, "CollisionShape3D", [("transform", tf(g)), ("shape", shape)])
        elif "Mesh" in c:
            _, base, _ = mesh_res(c["Mesh"])
            full = self.inv @ to_godot(m) @ F
            if base + "_convex" in SHAPES:
                pts = self.points(SHAPES[base + "_convex"], full)
                shape = t.sub_res("ConvexPolygonShape3D", [("points", pts)])
            else:
                pts = self.points(SHAPES[base + "_trimesh"], full)
                shape = t.sub_res("ConcavePolygonShape3D", [("data", pts)])
            t.add("CollisionShape3D", self.body_path, "CollisionShape3D", [("shape", shape)])
        else:
            raise ValueError(c)

    def points(self, flat, m):
        p = np.array(flat).reshape(-1, 3)
        p = (m[:3, :3] @ p.T).T + m[:3, 3]
        return "PackedVector3Array(%s)" % ", ".join(fmt(v) for v in p.flatten())

    def trigger(self, n, g, shape):
        assert self.area_parent, "trigger outside a parked car: " + n.name
        animator = script(n, "PropCarAnimator.cs")
        longitudinal = animator["fields"]["_carDirection"] == 1
        area = self.t.add(node_name(n.name), self.area_parent, "Area3D", [
            ("transform", tf(g)), ("collision_layer", "0"), ("collision_mask", str(LAYER_PLAYER_CAR | LAYER_BOT_CAR)),
            ("metadata/longitudinal", "true" if longitudinal else "false")])
        self.t.add("CollisionShape3D", area, "CollisionShape3D", [("shape", shape)])

    def emit_lights(self, parent, keep=lambda g: True, name=None):
        """Unity spot lights -> SpotLight3D (Godot's spot_angle is the half angle)."""
        out = []
        for n, m, light in self.lights:
            g = self.inv @ to_godot(m)
            if not keep(g):
                print("  note: dropped light %s at %s, far from its car" % (n.name, g[:3, 3].round(2)))
                continue
            assert light["m_Type"] == 0, "only spot lights are expected here"
            out.append(self.t.add(name or node_name(n.name), parent, "SpotLight3D", [
                ("transform", tf(ortho(g))), ("light_color", color(light["m_Color"])), ("light_energy", "0.0"),
                ("spot_range", fmt(light["m_Range"])), ("spot_angle", fmt(light["m_SpotAngle"] / 2))]))
        return out


# ---------------------------------------------------------------- cars

def car_parameter(asset, name):
    with open(os.path.join(UNITY, "Assets/Level/ScriptableObjects/Cars", asset)) as fh:
        txt = fh.read()

    def val(key):
        return re.search(r"<%s>k__BackingField: (.+)" % key, txt).group(1).strip()

    t = Tscn("gd_resource")
    t.ext_res("Script", "res://scripts/car/car_parameter.gd")
    t.nodes = []
    body = ['[resource]', 'script = ExtResource("1")', 'id = "%s"' % val("Id"), "health = %s" % val("CarHealth"),
            "top_speed = %s" % val("TopSpeed"), "acceleration = %s" % val("Acceleration"),
            "brake_force = %s" % val("BreakForce"), "steering_range = %s" % val("SteeringRange"),
            "steering_range_at_max_speed = %s" % val("SteeringRangeAtMaxSpeed"),
            "center_of_gravity_offset = %s" % val("CenterOfGravityOffset")]
    path = "res://resources/cars/%s.tres" % name
    full = os.path.join(GODOT, path.replace("res://", ""))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as fh:
        fh.write('[gd_resource type="Resource" script_class="CarParameter" format=3]\n\n'
                 '[ext_resource type="Script" path="res://scripts/car/car_parameter.gd" id="1"]\n\n'
                 + "\n".join(body) + "\n")
    print("wrote", path)
    return path


def car_scene(r, prefab, scene, asset, name):
    roots, _ = r.load(prefab)
    root = roots[0]
    is_bot = script(root, "BotController.cs") is not None
    rigidbody = component(root, "Rigidbody")
    t = Tscn()
    t.add(node_name(root.name), None, "VehicleBody3D", [
        ("collision_layer", str(LAYER_BOT_CAR if is_bot else LAYER_PLAYER_CAR)),
        ("collision_mask", str(collision_mask(rigidbody))),
        ("mass", fmt(rigidbody["m_Mass"])), ("contact_monitor", "true"), ("max_contacts_reported", "8"),
        ("script", t.ext_res("Script", SCRIPTS["car"])),
        ("parameter", t.ext_res("Resource", car_parameter(asset, name)))])
    # The car's frame is F: Godot +Z is the Unity forward.
    baker = Baker(t, ".", F)
    # Meshes stay under Model (the cutscene animates it); their colliders go on the body.
    model = find(root.children, "Model")
    model_path = t.add("Model", ".", "Node3D", [("transform", tf(F @ to_godot(local_m(model)) @ F))])
    model_baker = Baker(t, model_path, F)
    for c in model.children:
        bake_car_part(model_baker, baker, c, local_m(model), np.eye(4))
    for wheel in find_all(root, lambda n: component(n, "WheelCollider") is not None):
        car_wheel(t, wheel, parent_matrix(root, wheel))
    for c in root.children:
        if c.name not in ("Model", "Wheels"):
            baker.bake(c, np.eye(4))
    for n in find_all(root, lambda n: component(n, "Light") is not None and n not in [x[0] for x in baker.lights]):
        baker.lights.append((n, parent_matrix(root, n) @ local_m(n), component(n, "Light")))
    if baker.lights:
        lights_path = t.add("Lights", ".", "Node3D", [("script", t.ext_res("Script", SCRIPTS["lights"])),
                                                     ("energy_at_night", fmt(HEADLIGHT_ENERGY_AT_NIGHT))])
        baker.emit_lights(lights_path, keep=lambda g: np.linalg.norm(g[:3, 3]) < LIGHT_FAR_FROM_CAR)
    if is_bot:
        bot_area(t, root)
    else:
        player_car_parts(t, root, baker)
    t.write(scene)


def collision_mask(rigidbody):
    """Every layer but the ones the Unity rigidbody excludes (the police car drives through buildings)."""
    excluded = rigidbody.get("m_ExcludeLayers", {}).get("m_Bits", 0)
    mask = ALL_LAYERS
    for index, layer in UNITY_LAYERS.items():
        if excluded & (1 << index):
            mask &= ~layer
    return mask


def bake_car_part(model_baker, body_baker, n, m_root_parent, m_model_parent):
    """m_root_parent / m_model_parent: Unity matrix of n's parent relative to the car root / to Model."""
    if not n.active:
        return
    m_root = m_root_parent @ local_m(n)
    m_model = m_model_parent @ local_m(n)
    if n.mesh:
        model_baker.mesh(n, m_model)
    for c in n.colliders:
        body_baker.shape(n, c, m_root)
    for c in n.children:
        bake_car_part(model_baker, body_baker, c, m_root, m_model)


def find_all(n, pred, out=None):
    out = [] if out is None else out
    for c in n.children:
        if pred(c):
            out.append(c)
        find_all(c, pred, out)
    return out


def parent_matrix(root, target):
    """Unity matrix of target's parent, relative to root."""
    def walk(n, m):
        for c in n.children:
            if c is target:
                return m
            found = walk(c, m @ local_m(c))
            if found is not None:
                return found
        return None
    return walk(root, np.eye(4))


def car_wheel(t, wheel, m_parent):
    collider = component(wheel, "WheelCollider")
    controller = script(wheel, "WheelController.cs")["fields"]
    center = collider["m_Center"]
    m = m_parent @ local_m(wheel) @ translate([center["x"], center["y"], center["z"]])
    g = F @ to_godot(m)
    g[:3, :3] = np.eye(3)
    path = t.add(node_name(wheel.name), ".", "VehicleWheel3D", [
        ("transform", tf(g)), ("use_as_traction", "true" if controller["<IsMotorized>k__BackingField"] else "false"),
        ("use_as_steering", "true" if controller["<IsSteerable>k__BackingField"] else "false"),
        ("wheel_radius", fmt(collider["m_Radius"]))] + [(k, fmt(v)) for k, v in WHEEL.items()])
    for c in wheel.children:
        if c.mesh:
            res, _, _ = mesh_res(c.mesh)
            # Unity's GetWorldPose puts the mesh on the collider's center: keep only its rotation and scale.
            local = F @ to_godot(local_m(c)) @ F
            local[:3, 3] = 0.0
            t.add("Model", path, "MeshInstance3D", [("transform", tf(local)), ("mesh", t.ext_res("ArrayMesh", res))])


def bot_area(t, root):
    """Area that notices buildings, so the police car can fade inside them."""
    bot = script(root, "BotController.cs")["fields"]
    path = t.add("BotController", ".", "Area3D", [
        ("collision_layer", "0"), ("collision_mask", str(LAYER_BUILDING)),
        ("script", t.ext_res("Script", SCRIPTS["bot"])),
        ("min_turn_angle_degrees", fmt(bot["_minTurnAngleDegrees"])),
        ("distance_threshold", fmt(bot["_distanceThresholdMeters"])),
        ("reverse_duration", fmt(bot["_reverseDurationSeconds"])),
        ("building_fade_alpha", fmt(bot["_buildingFadeAlpha"])),
        ("building_fade_duration", fmt(bot["_buildingFadeDurationSeconds"]))])
    shape = t.sub_res("BoxShape3D", [("size", "Vector3(1.6, 1.4, 3.2)")])
    t.add("CollisionShape3D", path, "CollisionShape3D", [("transform", tf(translate([0, 0.9, 0]))), ("shape", shape)])


def player_car_parts(t, root, baker):
    sound = script(root, "CarSoundController.cs")["fields"]
    impacts = script(root, "CollisionSoundPlayer.cs")["fields"]
    particles = script(root, "CarParticleController.cs")["fields"]
    smoke = find_all(root, lambda n: component(n, "ParticleSystem") is not None)[0]
    g = baker.inv @ to_godot(parent_matrix(root, smoke) @ local_m(smoke))
    mesh = t.sub_res("QuadMesh", [("material", t.mat("mat_car_smoke")), ("size", "Vector2(0.4, 0.4)")])
    t.add("Smoke", ".", "CPUParticles3D", [
        ("transform", tf(translate(g[:3, 3]))), ("emitting", "false"), ("amount", "24"), ("lifetime", "1.2"),
        ("local_coords", "false"), ("mesh", mesh), ("direction", "Vector3(0, 1, 0)"), ("spread", "15.0"),
        ("gravity", "Vector3(0, 0.5, 0)"), ("initial_velocity_min", "1.0"), ("initial_velocity_max", "1.6"),
        ("scale_amount_min", "0.6"), ("scale_amount_max", "1.4"),
        ("script", t.ext_res("Script", SCRIPTS["smoke"])),
        ("health_threshold", str(int(particles["_healthThreshold"])))])
    engine_volume = sound["_maxVolume"]
    t.add("EngineSound", ".", "AudioStreamPlayer", [
        ("stream", t.ext_res("AudioStream", SOUNDS["SFX_CarEngine.wav"])),
        ("volume_db", fmt(20 * math.log10(engine_volume)) if engine_volume > 0 else "-80.0"),
        ("script", t.ext_res("Script", SCRIPTS["engine"])),
        ("min_pitch", fmt(sound["_minMovingPitch"])), ("max_pitch", fmt(sound["_maxMovingPitch"]))])
    detection = script(root, "CollisionDetection.cs")["fields"]
    t.add("Impacts", ".", "AudioStreamPlayer", [
        ("volume_db", fmt(20 * math.log10(impacts["_maxVolume"]))), ("max_polyphony", "4"),
        ("script", t.ext_res("Script", SCRIPTS["impacts"])),
        ("min_collision_speed", fmt(detection["_minCollisionVelocity"])), ("ignored_layers", str(LAYER_GROUND))])


# ---------------------------------------------------------------- props

def prop_scene(r, prefab, scene):
    roots, _ = r.load(prefab)
    root = roots[0]
    t = Tscn()
    rigidbody = component(root, "Rigidbody")
    props = [("collision_layer", str(LAYER_PROP)), ("collision_mask", str(ALL_LAYERS)),
             ("mass", fmt(rigidbody["m_Mass"]))]
    sound = impact_sound(root)
    if sound:
        props.append(("metadata/impact_sound", t.ext_res("AudioStream", sound)))
    t.add(node_name(root.name), None, "RigidBody3D", props)
    baker = Baker(t, ".", np.eye(4))
    for c in root.children:
        baker.bake(c, np.diag(list(root.scale) + [1.0]))
    lamp = script(root, "LightObjectController.cs")
    if lamp:
        f = lamp["fields"]
        t.nodes[0][4] += [("contact_monitor", "true"), ("max_contacts_reported", "4"),
                          ("script", t.ext_res("Script", SCRIPTS["lamp"])),
                          ("energy_at_night", fmt(LAMP_ENERGY_AT_NIGHT)),
                          ("transition_seconds", fmt(f["_transitionSeconds"])),
                          ("disable_delay", fmt(f["_disableDelaySeconds"])),
                          ("breaking_layers", str(LAYER_PLAYER_CAR))]
        baker.emit_lights(".", name="SpotLight")
    t.write(scene)


# ---------------------------------------------------------------- environment

GROUND_GROUPS = ("Roads", "Slant Curve")


def body_props(t, layer, n):
    props = [("collision_layer", str(layer)), ("collision_mask", "0")]
    sound = impact_sound(n)
    if sound:
        props.append(("metadata/impact_sound", t.ext_res("AudioStream", sound)))
    return props


def static_object(t, n, m_parent, parent, layer):
    m = m_parent @ local_m(n)
    body_g = ortho(to_godot(m))
    path = t.add(node_name(n.name), parent, "StaticBody3D", [("transform", tf(body_g))] + body_props(t, layer, n))
    Baker(t, path, body_g).bake(n, m_parent)


def decals(t, n, m_parent, parent):
    """URP decal projectors -> flat quads (the Compatibility renderer has no decals)."""
    for d in n.children:
        if d.children:
            path = t.add(node_name(d.name), parent, "Node3D")
            decals(t, d, m_parent @ local_m(d), path)
            continue
        s = d.scripts[0]["fields"]
        m = m_parent @ local_m(d)
        g = ortho(to_godot(m))
        g[1, 3] = max(g[1, 3], 0.5) + 0.006
        mat = MATERIALS[os.path.basename(s["m_Material"])]
        mesh = t.sub_res("PlaneMesh", [("material", t.mat(mat)), ("orientation", "2"),
                                       ("size", "Vector2(%s, %s)" % (fmt(s["m_Size"]["x"]), fmt(s["m_Size"]["y"])))])
        t.add(node_name(d.name), parent, "MeshInstance3D", [("transform", tf(g)), ("mesh", mesh),
                                                           ("cast_shadow", "0")])


def static_environment(r):
    roots, _ = r.load("Assets/Level/Scenes/StaticEnvironment.unity")
    env = find(roots, "-- ENVIRONMENT --")
    t = Tscn()
    t.add("StaticEnvironment", None, "Node3D")
    for c in env.children:
        if c.name in ("Parking Marks", "Edge Effect"):
            decals(t, c, local_m(c), t.add(node_name(c.name), ".", "Node3D"))
        elif c.mesh or c.colliders:
            static_object(t, c, np.eye(4), ".", LAYER_GROUND)
        else:
            path = t.add(node_name(c.name), ".", "Node3D", [("transform", tf(to_godot(local_m(c))))])
            layer = LAYER_GROUND if c.name in GROUND_GROUPS else LAYER_BUILDING
            for o in c.children:
                static_object(t, o, np.eye(4), path, layer)
    light = find(roots, "Directional Light")
    l = component(light, "Light")
    cycle = script(find(roots, "Lighting Cycle Manager"), "LightingCycleManager.cs")["fields"]
    t.add("Sun", ".", "DirectionalLight3D", [
        ("transform", tf(to_godot(local_m(light)))), ("light_color", color(l["m_Color"])),
        ("light_energy", fmt(SUN_ENERGY)), ("shadow_enabled", "true"),
        ("directional_shadow_max_distance", "80.0"),
        ("script", t.ext_res("Script", SCRIPTS["lighting"])), ("cycle_seconds", fmt(cycle["_cycleTimeInSeconds"]))])
    sky_mat = t.sub_res("PanoramaSkyMaterial", [("panorama", t.ext_res("Texture2D", "res://assets/textures/txt_sky_morning.png"))])
    sky = t.sub_res("Sky", [("sky_material", sky_mat)])
    # Unity: flat ambient color, linear fog from 50 to 300 m, no tonemapping.
    settings = next(d["f"] for d in us.parse_file(os.path.join(UNITY, "Assets/Level/Scenes/StaticEnvironment.unity")).values()
                    if d["type"] == "RenderSettings")
    envr = t.sub_res("Environment", [
        ("background_mode", "2"), ("sky", sky), ("ambient_light_source", "2"),
        ("ambient_light_color", color(settings["m_AmbientSkyColor"])),
        ("ambient_light_energy", fmt(AMBIENT_ENERGY)), ("reflected_light_source", "1"),
        ("fog_enabled", "true"), ("fog_mode", "1"), ("fog_light_color", color(settings["m_FogColor"])),
        ("fog_density", "1.0"), ("fog_depth_begin", fmt(settings["m_LinearFogStart"])),
        ("fog_depth_end", fmt(settings["m_LinearFogEnd"])), ("fog_sky_affect", "0.0")])
    t.add("WorldEnvironment", ".", "WorldEnvironment", [("environment", envr)])
    t.write("res://scenes/environment/static_environment.tscn")


def parked_car(t, n, m_parent, parent):
    m = m_parent @ local_m(n)
    g = to_godot(m)
    path = t.add(node_name(n.name), parent, "Node3D", [("transform", tf(g)),
                                                       ("script", t.ext_res("Script", SCRIPTS["parked_car"]))])
    model = find(n.children, "Model")
    model_g = g @ to_godot(local_m(model))
    model_path = t.add("Model", path, "Node3D", [("transform", tf(to_godot(local_m(model))))])
    body = t.add("Body", model_path, "StaticBody3D", [("collision_layer", str(LAYER_PROP)), ("collision_mask", "0")])
    Baker(t, body, model_g).bake(model, m)
    wheels_path = t.add("Wheels", path, "Node3D")
    Baker(t, wheels_path, g).bake(find(n.children, "Wheels"), m)
    triggers = t.add("Triggers", path, "Node3D")
    Baker(t, triggers, g, area_parent=triggers).bake(find(n.children, "Colliders"), m)
    t.add("AnimationPlayer", path, "AnimationPlayer", [("callback_mode_process", "0"),
        ("libraries", '{&"parked_car": %s}' % t.ext_res("AnimationLibrary", "res://assets/animations/anim_parked_car.tres"))])


def dynamic_environment(r, prop_scales):
    roots, _ = r.load("Assets/Level/Scenes/DynamicEnvironment.unity")
    env = find(roots, "-- ENVIRONMENT --")
    t = Tscn()
    t.add("DynamicEnvironment", None, "Node3D")
    for c in env.children:
        path = t.add(node_name(c.name), ".", "Node3D", [("transform", tf(to_godot(local_m(c))))])
        if c.name == "Parked Cars":
            for o in c.children:
                parked_car(t, o, np.eye(4), path)
        elif c.name == "Water":
            mesh_g = np.eye(4)
            mesh = t.sub_res("PlaneMesh", [("material", t.mat("mat_water")),
                                           ("size", "Vector2(%s, %s)" % (fmt(10 * c.scale[0]), fmt(10 * c.scale[2])))])
            t.nodes[-1][4] = [("transform", tf(translate(MZ[:3, :3] @ np.array(c.pos))))]
            t.add("Surface", path, "MeshInstance3D", [("transform", tf(mesh_g)), ("mesh", mesh), ("cast_shadow", "0")])
            for o in c.children:
                static_object(t, o, np.diag(list(c.scale) + [1.0]), path, LAYER_GROUND)
        else:
            instances(t, c, path, prop_scales)
    t.write("res://scenes/environment/dynamic_environment.tscn")


def instances(t, n, parent, prop_scales):
    """Groups of prop prefab instances (barriers, lamp posts), kept as Unity nests them."""
    for c in n.children:
        scene = PROPS.get(c.prefab)
        if scene:
            g = to_godot(local_m(c, with_scale=False))
            ratio = np.array(c.scale) / np.array(prop_scales[c.prefab])
            if not np.allclose(ratio, 1, atol=1e-3):
                g[:3, :3] = g[:3, :3] @ np.diag(ratio)
            t.add(node_name(c.name), parent, instance=t.ext_res("PackedScene", scene), props=[("transform", tf(g))])
        else:
            path = t.add(node_name(c.name), parent, "Node3D", [("transform", tf(to_godot(local_m(c))))])
            instances(t, c, path, prop_scales)


# ---------------------------------------------------------------- cutscene

def hermite(keys, time, axis=None):
    def v(k, field="value"):
        x = k[field]
        return x[axis] if axis else x
    if time <= keys[0]["time"]:
        return v(keys[0])
    for a, b in zip(keys, keys[1:]):
        if a["time"] <= time <= b["time"]:
            dt = b["time"] - a["time"]
            s = (time - a["time"]) / dt
            out_slope, in_slope = v(a, "outSlope"), v(b, "inSlope")
            if not math.isfinite(out_slope) or not math.isfinite(in_slope):
                return v(a)
            h00, h10 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s
            h01, h11 = -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
            return h00 * v(a) + h10 * dt * out_slope + h01 * v(b) + h11 * dt * in_slope
    return v(keys[-1])


def audio_length(res):
    full = os.path.join(GODOT, res.replace("res://", ""))
    if full.endswith(".wav"):
        with wave.open(full) as w:
            return w.getnframes() / w.getframerate()
    return MP3(full).info.length


def cutscene(r):
    timeline = us.parse_file(os.path.join(UNITY, "Assets/Level/Timelines/Opening.playable"))
    roots, idmap = r.load("Assets/Level/Scenes/Cutscene.unity")
    director = next(d["f"] for d in us.parse_file(os.path.join(UNITY, "Assets/Level/Scenes/Cutscene.unity")).values()
                    if d["type"] == "PlayableDirector")
    bindings = {}
    for b in director["m_SceneBindings"]:
        target = idmap.get(b["value"]["fileID"])
        bindings[b["key"]["fileID"]] = target[0] if isinstance(target, tuple) else target
    cut = find(roots, "-- CUTSCENE --")
    t = Tscn()
    t.add("Cutscene", None, "Node3D", [("script", t.ext_res("Script", SCRIPTS["cutscene"]))])
    paths = {}
    car = find(cut.children, "Car Cutscene")
    paths[car.name] = t.add("CarCutscene", ".", "Node3D", [("transform", tf(to_godot(local_m(car))))])
    t.add("Car", paths[car.name], instance=t.ext_res("PackedScene", CARS["Assets/Level/Prefabs/Car/PlayerCars/Sedan Sports.prefab"][0]),
          props=[("transform", tf(F)), ("process_mode", "4")])
    police_car = find(cut.children, "Police Car")
    paths[police_car.name] = t.add("PoliceCar", ".", "Node3D", [("transform", tf(to_godot(local_m(police_car))))])
    t.add("Car", paths[police_car.name], instance=t.ext_res("PackedScene", CARS["Assets/Level/Prefabs/Car/BotCars/Police Car.prefab"][0]),
          props=[("transform", tf(F)), ("process_mode", "4")])
    for name, model in (("Police", "police"), ("Thief", "thief")):
        n = find(cut.children, name)
        paths[name] = t.add(name, ".", "Node3D", [("transform", tf(to_godot(local_m(n, with_scale=False))))])
        scale = np.diag(list(n.scale) + [1.0])
        t.add("Model", paths[name], instance=t.ext_res("PackedScene", "res://assets/models/characters/%s.fbx" % model),
              props=[("transform", tf(scale @ F))])
    cam = find(roots, "Camera")
    t.add("Camera3D", ".", "Camera3D", [("transform", tf(to_godot(local_m(cam)))), ("projection", "1"),
                                        ("size", "10.0"), ("near", "0.1"), ("far", "1000.0"), ("current", "true")])
    anim = Tscn("gd_resource")
    tracks = []
    length = 0.0
    players = 0
    root_tl = timeline[11400000]["f"]
    for ref in root_tl["m_Tracks"]:
        d = timeline[ref["fileID"]]["f"]
        target = bindings.get(ref["fileID"])
        clips = d.get("m_Clips") or []
        for c in clips:
            length = max(length, c["m_Start"] + c["m_Duration"])
        name = d["m_Name"]
        if name.startswith("Activation"):
            path = paths[target.name]
            c = clips[0]
            keys = [(0.0, False), (c["m_Start"], True), (c["m_Start"] + c["m_Duration"], False)]
            if c["m_Start"] == 0:
                keys = keys[1:]
            tracks.append(value_track("%s:visible" % path, keys))
        elif name.startswith("Animation") and d.get("m_InfiniteClip", {}).get("fileID"):
            recorded = timeline[d["m_InfiniteClip"]["fileID"]]["f"]
            offset_p = d["m_InfiniteClipOffsetPosition"]
            offset_r = euler_m([d["m_InfiniteClipOffsetEulerAngles"][a] for a in "xyz"])
            tracks += recorded_tracks(paths[target.name], recorded, np.array([offset_p[a] for a in "xyz"]), offset_r)
        elif name.startswith("Animation"):
            player = "%s/Model/AnimationPlayer" % paths[target.name]
            tracks.append(("animation", player, [(c["m_Start"], c["m_DisplayName"]) for c in clips]))
        elif name.startswith("Audio"):
            players += 1
            player = t.add("Audio%d" % players, ".", "AudioStreamPlayer")
            keys = []
            for c in sorted(clips, key=lambda c: c["m_Start"]):
                clip = timeline[c["m_Asset"]["fileID"]]["f"]["m_Clip"]
                res = SOUNDS[os.path.basename(r.path_of(clip))]
                start = c.get("m_ClipIn", 0) or 0
                end = max(0.0, audio_length(res) - start - c["m_Duration"])
                keys.append((c["m_Start"], res, start, end))
            tracks.append(("audio", player, keys))
    write_animation(anim, tracks, length)
    t.add("AnimationPlayer", ".", "AnimationPlayer", [("callback_mode_process", "0"),
        ("libraries", '{&"": %s}' % t.ext_res("AnimationLibrary", "res://assets/animations/anim_opening.tres"))])
    t.write("res://scenes/cutscene/cutscene.tscn")


def value_track(path, keys):
    return ("value", path, keys)


def recorded_tracks(path, clip, offset_p, offset_r):
    """Unity recorded root motion (relative to the infinite clip offsets) -> position/rotation tracks."""
    out = []
    pos = clip.get("m_PositionCurves") or []
    eul = clip.get("m_EulerCurves") or []
    stop = clip["m_AnimationClipSettings"]["m_StopTime"]
    times = [i / TIMELINE_FPS for i in range(int(stop * TIMELINE_FPS) + 1)]
    for c in pos:
        keys = c["curve"]["m_Curve"]
        samples = []
        for time in times:
            p = np.array([hermite(keys, time, a) for a in "xyz"])
            world = offset_p + offset_r @ p
            samples.append((time, MZ[:3, :3] @ world))
        out.append(("position_3d", path, samples))
    for c in eul:
        keys = c["curve"]["m_Curve"]
        sub = path if not c.get("path") else "%s/Car/%s" % (path, c["path"])
        samples = []
        for time in times:
            r = euler_m([hermite(keys, time, a) for a in "xyz"])
            if not c.get("path"):
                r = offset_r @ r
                g = MZ[:3, :3] @ r @ MZ[:3, :3]
            else:
                g = F[:3, :3] @ MZ[:3, :3] @ r @ MZ[:3, :3] @ F[:3, :3]
            samples.append((time, quat_of(g)))
        out.append(("rotation_3d", sub, samples))
    if not eul:
        g = MZ[:3, :3] @ offset_r @ MZ[:3, :3]
        out.append(("rotation_3d", path, [(0.0, quat_of(g))]))
    return out


def write_animation(anim, tracks, length):
    lines = ["[resource]", 'resource_name = "opening"', "length = %s" % fmt(length)]
    for i, (kind, path, keys) in enumerate(tracks):
        p = "tracks/%d/" % i
        lines += ['%stype = "%s"' % (p, kind), "%simported = false" % p, "%senabled = true" % p,
                  '%spath = NodePath("%s")' % (p, path)]
        if kind == "position_3d":
            flat = [x for time, v in keys for x in (time, 1, *v)]
            lines += ["%sinterp = 1" % p, "%skeys = PackedFloat32Array(%s)" % (p, ", ".join(fmt(x) for x in flat))]
        elif kind == "rotation_3d":
            flat = [x for time, q in keys for x in (time, 1, *q)]
            lines += ["%sinterp = 1" % p, "%skeys = PackedFloat32Array(%s)" % (p, ", ".join(fmt(x) for x in flat))]
        elif kind == "value":
            lines += ["%sinterp = 0" % p,
                      '%skeys = {"times": PackedFloat32Array(%s), "transitions": PackedFloat32Array(%s), '
                      '"update": 1, "values": [%s]}' % (p, ", ".join(fmt(k[0]) for k in keys),
                                                        ", ".join("1" for _ in keys),
                                                        ", ".join("true" if k[1] else "false" for k in keys))]
        elif kind == "animation":
            lines += ['%skeys = {"clips": PackedStringArray(%s), "times": PackedFloat32Array(%s)}'
                      % (p, ", ".join('"%s"' % k[1] for k in keys), ", ".join(fmt(k[0]) for k in keys))]
        elif kind == "audio":
            clips = ", ".join('{"end_offset": %s, "start_offset": %s, "stream": %s}'
                              % (fmt(end), fmt(start), anim.ext_res("AudioStream", res)) for _, res, start, end in keys)
            lines += ['%skeys = {"clips": [%s], "times": PackedFloat32Array(%s)}'
                      % (p, clips, ", ".join(fmt(k[0]) for k in keys)), "%suse_blend = true" % p]
    library = ['[resource]', 'resource_name = "opening"', '_data = {&"opening": SubResource("Animation_1")}']
    out = ['[gd_resource type="AnimationLibrary" format=3]', ""]
    for i, (typ, p) in enumerate(anim.ext):
        out.append('[ext_resource type="%s" path="%s" id="%d"]' % (typ, p, i + 1))
    out += ["", '[sub_resource type="Animation" id="Animation_1"]'] + lines[1:] + [""] + library
    path = os.path.join(GODOT, "assets/animations/anim_opening.tres")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("wrote res://assets/animations/anim_opening.tres")




# ---------------------------------------------------------------- levels

def car_database(r):
    """Garage order from Unity's CarDatabase."""
    with open(os.path.join(UNITY, "Assets/Level/ScriptableObjects/Cars/CarDatabase.asset")) as fh:
        guids = re.findall(r"guid: (\w+)", fh.read().split("CarsParameters")[1])
    by_asset = {asset: scene for scene, asset, _ in CARS.values()}
    scenes = [by_asset[os.path.basename(r.guids[g])] for g in guids]
    t = Tscn("gd_resource")
    script_id = t.ext_res("Script", "res://scripts/car/car_database.gd")
    cars = ", ".join(t.ext_res("PackedScene", s) for s in scenes)
    out = ['[gd_resource type="Resource" script_class="CarDatabase" format=3]', ""]
    out += ['[ext_resource type="%s" path="%s" id="%d"]' % (typ, p, i + 1) for i, (typ, p) in enumerate(t.ext)]
    out += ["", "[resource]", "script = %s" % script_id, "cars = Array[PackedScene]([%s])" % cars]
    with open(os.path.join(GODOT, "resources/car_database.tres"), "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("wrote res://resources/car_database.tres")


def environment(t):
    t.add("StaticEnvironment", ".", instance=t.ext_res("PackedScene", "res://scenes/environment/static_environment.tscn"))
    t.add("DynamicEnvironment", ".", instance=t.ext_res("PackedScene", "res://scenes/environment/dynamic_environment.tscn"))


def level_cutscene():
    t = Tscn()
    t.add("Cutscene", None, "Node3D")
    environment(t)
    t.add("Opening", ".", instance=t.ext_res("PackedScene", "res://scenes/cutscene/cutscene.tscn"))
    t.write("res://scenes/levels/lvl_cutscene.tscn")


def level_game(r):
    roots, _ = r.load("Assets/Level/Scenes/Game.unity")
    refs = find(roots, "-- REFERENCE POSITIONS --")
    managers = find(roots, "-- MANAGERS --")
    spawner = script(find(managers.children, "Bot Spawner Controller"), "BotSpawnerController.cs")["fields"]
    camera = find(roots, "Camera")
    controller = script(camera, "CameraController.cs")["fields"]
    water = find(roots, "Water Box Collider")
    t = Tscn()
    t.add("Game", None, "Node3D")
    environment(t)
    start = find(refs.children, "Start Position")
    t.add("Garage", ".", "Marker3D", [
        ("transform", tf(to_godot(local_m(refs) @ local_m(start)) @ F)),
        ("script", t.ext_res("Script", "res://scripts/player/garage.gd")),
        ("database", t.ext_res("Resource", "res://resources/car_database.tres"))])
    t.add("Player", ".", "Node", [("script", t.ext_res("Script", "res://scripts/player/player.gd"))])
    t.add("MatchManager", ".", "Node", [
        ("script", t.ext_res("Script", "res://scripts/game/match_manager.gd")),
        ("initial_menu", 'NodePath("../UI/InitialMenu")'), ("game_over_menu", 'NodePath("../UI/GameOverMenu")'),
        ("camera", 'NodePath("../Camera3D")')])
    path = t.add("BotSpawner", ".", "Node3D", [
        ("script", t.ext_res("Script", "res://scripts/bot/bot_spawner.gd")),
        ("bot_scene", t.ext_res("PackedScene", CARS["Assets/Level/Prefabs/Car/BotCars/Police Car.prefab"][0])),
        ("max_bots", str(spawner["_numberOfBotsToSpawn"])), ("spawn_interval", fmt(spawner["_spawnIntervalSeconds"])),
        ("first_bot_index", str(spawner["_spawnedBotsCount"]))])
    spawns = find(refs.children, "Bots Spawn Positions")
    for p in sorted(spawns.children, key=lambda p: p.name):
        t.add(node_name(p.name), path, "Marker3D",
              [("transform", tf(to_godot(local_m(refs) @ local_m(spawns) @ local_m(p)) @ F))])
    box = water.colliders[0]["Box"]["size"]
    size = np.array(water.scale) * np.array([box["x"], box["y"], box["z"]])
    path = t.add("WaterKillZone", ".", "Area3D", [
        ("transform", tf(to_godot(local_m(water, with_scale=False)))), ("collision_layer", "0"),
        ("collision_mask", str(LAYER_PLAYER_CAR)),
        ("script", t.ext_res("Script", "res://scripts/game/water_kill_zone.gd")),
        ("match_manager", 'NodePath("../MatchManager")')])
    t.add("CollisionShape3D", path, "CollisionShape3D", [("shape", t.sub_res("BoxShape3D", [("size", vec3(size))]))])
    offset = controller["_offset"]
    t.add("Camera3D", ".", "Camera3D", [
        ("transform", tf(to_godot(local_m(camera)))), ("projection", "1"), ("size", "10.0"), ("near", "0.1"),
        ("far", "1000.0"), ("current", "true"),
        ("script", t.ext_res("Script", "res://scripts/player/camera_follow.gd")),
        ("offset", vec3(MZ[:3, :3] @ np.array([offset["x"], offset["y"], offset["z"]]))),
        ("initial_size", fmt(2 * controller["_initialOrthographicSize"])),
        ("end_size", fmt(2 * controller["_endOrthographicSize"])),
        ("intro_duration", fmt(controller["_initialAnimationDuration"]))])
    t.add("UI", ".", instance=t.ext_res("PackedScene", "res://scenes/ui/game_ui.tscn"))
    # Unity wires these in the buttons' OnClick lists.
    t.connections += [
        ("pressed", "UI/InitialMenu/PlayButton", "MatchManager", "start_match"),
        ("pressed", "UI/InitialMenu/GarageButton", "UI/GarageMenu", "enable"),
        ("pressed", "UI/InitialMenu/GarageButton", "UI/InitialMenu", "disable"),
        ("pressed", "UI/GarageMenu/NextButton", "Garage", "switch_up"),
        ("pressed", "UI/GarageMenu/PreviousButton", "Garage", "switch_down"),
        ("pressed", "UI/GarageMenu/SelectButton", "Garage", "select_car"),
        ("pressed", "UI/GarageMenu/ExitButton", "Garage", "exit_garage"),
        ("pressed", "UI/GarageMenu/ExitButton", "UI/InitialMenu", "enable"),
        ("pressed", "UI/GarageMenu/ExitButton", "UI/GarageMenu", "disable"),
        ("pressed", "UI/GameOverMenu/HomeButton", "MatchManager", "reload_game"),
    ]
    t.write("res://scenes/levels/lvl_game.tscn")


def main():
    r = us.Resolver(UNITY)
    for prefab, (scene, asset, name) in CARS.items():
        car_scene(r, prefab, scene, asset, name)
    car_database(r)
    prop_scales = {}
    for prefab, scene in PROPS.items():
        prop_scene(r, prefab, scene)
        prop_scales[prefab] = r.load(prefab)[0][0].scale
    static_environment(r)
    dynamic_environment(r, prop_scales)
    cutscene(r)
    level_cutscene()
    level_game(r)


if __name__ == "__main__":
    main()
