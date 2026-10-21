"""Resolve a Unity .unity/.prefab file into a node tree (prefab instances expanded).

Usage: python unity_scene.py <project_root> <scene_or_prefab_path> [--json out.json]
"""
import json
import math
import os
import re
import sys

import yaml

HEADER = re.compile(r"^--- !u!(\d+) &(-?\d+)( stripped)?", re.M)
MASK = 0x7FFFFFFFFFFFFFFF
BUILTIN_MESH = {10202: "Cube", 10206: "Cylinder", 10207: "Sphere", 10208: "Capsule", 10209: "Plane",
                10210: "Quad"}


class Loader(yaml.SafeLoader):
    pass


def build_guid_map(root):
    guid_map = {}
    for dirpath, _, files in os.walk(os.path.join(root, "Assets")):
        for f in files:
            if f.endswith(".meta"):
                p = os.path.join(dirpath, f)
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        if line.startswith("guid:"):
                            guid_map[line.split()[1]] = os.path.relpath(p[:-5], root)
                            break
    return guid_map


_cache = {}


def parse_file(path):
    if path in _cache:
        return _cache[path]
    with open(path, encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    docs = {}
    matches = list(HEADER.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        try:
            data = yaml.load(body, Loader=Loader) or {}
        except yaml.YAMLError:
            data = {}
        cls_name, fields = next(iter(data.items())) if data else ("?", {})
        docs[int(m.group(2))] = {"class": int(m.group(1)), "type": cls_name, "stripped": bool(m.group(3)),
                                 "f": fields or {}}
    _cache[path] = docs
    return docs


class Node:
    def __init__(self, name):
        self.name = name
        self.pos = [0.0, 0.0, 0.0]
        self.rot = [0.0, 0.0, 0.0, 1.0]
        self.scale = [1.0, 1.0, 1.0]
        self.active = True
        self.mesh = None
        self.materials = []
        self.colliders = []
        self.scripts = []
        self.other = []
        self.model = None  # FBX/GLB used as prefab source
        self.prefab = None
        self.children = []

    def to_dict(self):
        d = {"name": self.name, "pos": self.pos, "rot": self.rot, "euler": quat_to_euler(self.rot),
             "scale": self.scale}
        for k in ("mesh", "model", "prefab"):
            if getattr(self, k):
                d[k] = getattr(self, k)
        if not self.active:
            d["active"] = False
        for k in ("materials", "colliders", "scripts", "other"):
            if getattr(self, k):
                d[k] = getattr(self, k)
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        return d


def quat_to_euler(q):
    """Unity euler (ZXY order applied), degrees."""
    x, y, z, w = q
    sinx = 2 * (w * x - y * z)
    sinx = max(-1.0, min(1.0, sinx))
    ex = math.degrees(math.asin(sinx))
    ey = math.degrees(math.atan2(2 * (w * y + x * z), 1 - 2 * (x * x + y * y)))
    ez = math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (x * x + z * z)))
    return [round(ex, 3), round(ey, 3), round(ez, 3)]


class Resolver:
    def __init__(self, root):
        self.root = root
        self.guids = build_guid_map(root)

    def path_of(self, ref):
        if not ref or not ref.get("guid"):
            return None
        return self.guids.get(ref["guid"], "?" + ref["guid"])

    def asset_ref(self, ref):
        if not ref or ref.get("fileID", 0) == 0:
            return None
        if ref.get("guid") == "0000000000000000e000000000000000":
            return "builtin:" + BUILTIN_MESH.get(ref["fileID"], str(ref["fileID"]))
        if ref.get("guid") == "0000000000000000f000000000000000":
            return "builtin_extra:" + str(ref["fileID"])
        p = self.path_of(ref)
        return p if ref.get("fileID") in (2100000, 11400000, 4300000, 100100000) or p is None else \
            "%s#%s" % (p, ref["fileID"])

    def load(self, rel_path):
        """Return (roots, idmap) where idmap maps fileIDs in this file's space -> Node/component info."""
        path = os.path.join(self.root, rel_path)
        if rel_path.lower().endswith((".fbx", ".glb", ".obj", ".gltf", ".blend")):
            n = Node(os.path.splitext(os.path.basename(rel_path))[0])
            n.model = rel_path
            return [n], {"__model_root__": n}
        docs = parse_file(path)
        nodes = {}  # transform id -> Node
        go_to_tr = {}
        idmap = {}
        # Plain transforms
        for fid, d in docs.items():
            if d["class"] in (4, 224) and not d["stripped"]:
                f = d["f"]
                n = Node("?")
                p, r, s = f.get("m_LocalPosition", {}), f.get("m_LocalRotation", {}), f.get("m_LocalScale", {})
                n.pos = [p.get("x", 0), p.get("y", 0), p.get("z", 0)]
                n.rot = [r.get("x", 0), r.get("y", 0), r.get("z", 0), r.get("w", 1)]
                n.scale = [s.get("x", 1), s.get("y", 1), s.get("z", 1)]
                if d["class"] == 224:
                    n.other.append({"RectTransform": {k: f.get(k) for k in (
                        "m_AnchorMin", "m_AnchorMax", "m_AnchoredPosition", "m_SizeDelta", "m_Pivot")}})
                nodes[fid] = n
                idmap[fid] = n
                go_to_tr[f.get("m_GameObject", {}).get("fileID")] = fid
        # Names and components
        for fid, d in docs.items():
            if d["class"] == 1 and not d["stripped"]:
                tr = go_to_tr.get(fid)
                if tr is None:
                    continue
                n = nodes[tr]
                n.name = d["f"].get("m_Name", "?")
                n.active = bool(d["f"].get("m_IsActive", 1))
                idmap[fid] = n
        for fid, d in docs.items():
            if d["stripped"] or d["class"] in (1, 4, 224, 1001):
                continue
            go = d["f"].get("m_GameObject", {}).get("fileID") if isinstance(d["f"], dict) else None
            if go is None or go_to_tr.get(go) is None:
                continue
            n = nodes[go_to_tr[go]]
            idmap[fid] = (n, d)
            self.add_component(n, d)
        # Prefab instances
        instances = {}
        for fid, d in docs.items():
            if d["class"] == 1001:
                instances[fid] = self.instantiate(d["f"])
        # Stripped objects -> nodes inside instances
        for fid, d in docs.items():
            if d["stripped"]:
                inst = instances.get(d["f"].get("m_PrefabInstance", {}).get("fileID"))
                if inst is None:
                    continue
                src = d["f"].get("m_CorrespondingSourceObject", {}).get("fileID")
                target = inst[1].get(src)
                if target is None and src is not None:
                    target = inst[0][0] if inst[1].get("__model_root__") else None
                if target is not None:
                    idmap[fid] = target
        # XOR ids for objects in nested instances (used by outer overrides)
        for ifid, (iroots, imap) in instances.items():
            for sid, obj in imap.items():
                if isinstance(sid, int):
                    idmap.setdefault((ifid ^ sid) & MASK, obj)
            if imap.get("__model_root__"):
                idmap.setdefault(("model_root", ifid), imap["__model_root__"])
        # Components added to stripped GameObjects
        for fid, d in docs.items():
            if d["stripped"] or d["class"] in (1, 4, 224, 1001):
                continue
            go = d["f"].get("m_GameObject", {}).get("fileID") if isinstance(d["f"], dict) else None
            if go is not None and go_to_tr.get(go) is None and isinstance(idmap.get(go), Node):
                self.add_component(idmap[go], d)
                idmap[fid] = (idmap[go], d)
        # Hierarchy
        roots = []
        for fid, d in docs.items():
            if d["class"] in (4, 224) and not d["stripped"]:
                father = d["f"].get("m_Father", {}).get("fileID", 0)
                self.attach(nodes[fid], father, idmap, roots)
        for ifid, d in docs.items():
            if d["class"] == 1001:
                parent = d["f"].get("m_Modification", {}).get("m_TransformParent", {}).get("fileID", 0)
                for r in instances[ifid][0]:
                    self.attach(r, parent, idmap, roots)
        return roots, idmap

    def attach(self, node, father, idmap, roots):
        if father == 0:
            roots.append(node)
            return
        parent = idmap.get(father)
        if isinstance(parent, tuple):
            parent = parent[0]
        if isinstance(parent, Node):
            parent.children.append(node)
        else:
            roots.append(node)

    def add_component(self, n, d):
        f = d["f"]
        c = d["class"]
        if c == 33:
            n.mesh = self.asset_ref(f.get("m_Mesh"))
        elif c in (23, 137):
            n.materials = [self.asset_ref(m) for m in f.get("m_Materials", []) or []]
            if c == 137:
                n.mesh = self.asset_ref(f.get("m_Mesh"))
                n.other.append({"SkinnedMeshRenderer": True})
        elif c == 65:
            n.colliders.append({"Box": {"size": f.get("m_Size"), "center": f.get("m_Center"),
                                        "trigger": f.get("m_IsTrigger")}})
        elif c == 135:
            n.colliders.append({"Sphere": {"radius": f.get("m_Radius"), "center": f.get("m_Center"),
                                           "trigger": f.get("m_IsTrigger")}})
        elif c == 136:
            n.colliders.append({"Capsule": {"radius": f.get("m_Radius"), "height": f.get("m_Height"),
                                            "center": f.get("m_Center"), "trigger": f.get("m_IsTrigger")}})
        elif c == 64:
            n.colliders.append({"Mesh": self.asset_ref(f.get("m_Mesh"))})
        elif c == 114:
            script = self.path_of(f.get("m_Script"))
            fields = {k: v for k, v in f.items() if not k.startswith("m_") or k in ("m_Text", "m_text", "m_Size", "m_Material", "m_Offset")}
            n.scripts.append({"script": script and os.path.basename(script), "fields": self.clean(fields)})
        else:
            keep = {k: v for k, v in f.items() if k not in ("m_ObjectHideFlags", "m_CorrespondingSourceObject",
                                                            "m_PrefabInstance", "m_PrefabAsset", "m_GameObject")}
            n.other.append({d["type"]: self.clean(keep)})

    def clean(self, v):
        if isinstance(v, dict):
            if set(v) >= {"fileID"} and "guid" in v:
                return self.asset_ref(v) or None
            return {k: self.clean(x) for k, x in v.items()}
        if isinstance(v, list):
            return [self.clean(x) for x in v]
        return v

    def instantiate(self, f):
        src = f.get("m_SourcePrefab", {})
        rel = self.path_of(src)
        if rel is None or rel.startswith("?"):
            n = Node("MISSING_PREFAB " + str(rel))
            return [n], {}
        roots, imap = self.load(rel)
        roots = [self.deep_copy(r) for r in roots]
        # Rebuild map against copies
        imap = self.remap(roots, imap)
        model_root = imap.get("__model_root__")
        for m in f.get("m_Modification", {}).get("m_Modifications", []) or []:
            tid = m.get("target", {}).get("fileID")
            target = imap.get(tid)
            if target is None and model_root is not None:
                target = self.model_target(rel, tid, model_root)
            if target is None:
                continue
            self.apply_mod(target, m.get("propertyPath", ""), m.get("value"), m.get("objectReference"))
        removed = [imap.get(ref.get("fileID")) for ref in
                   f.get("m_Modification", {}).get("m_RemovedGameObjects", []) or []]
        removed = [id(n) for n in removed if isinstance(n, Node)]
        if removed:
            def prune(n):
                n.children = [c for c in n.children if id(c) not in removed]
                for c in n.children:
                    prune(c)
            for r in roots:
                prune(r)
        for r in roots:
            r.prefab = r.prefab or rel
        return roots, imap

    def model_target(self, rel, tid, model_root):
        # Overrides on FBX model prefabs: only the root transform/GameObject is supported.
        names = self.model_ids(rel)
        name = names.get(tid)
        if name is None:
            return model_root
        if name == "__root__" or name.split("/")[0] == model_root.name or True:
            return model_root

    def model_ids(self, rel):
        meta = os.path.join(self.root, rel + ".meta")
        ids = {}
        try:
            with open(meta, encoding="utf-8", errors="ignore") as fh:
                txt = fh.read()
            for m in re.finditer(r"first:\s*\n\s*(\d+):\s*(-?\d+)\s*\n\s*second:\s*(.+)", txt):
                ids[int(m.group(2))] = m.group(3).strip()
        except OSError:
            pass
        return ids

    def remap(self, new_roots, imap):
        # deep_copy keeps an "orig" link; map old Node -> new Node
        mapping = {}

        def walk(n):
            mapping[id(n._orig)] = n
            for c in n.children:
                walk(c)

        for r in new_roots:
            walk(r)
        out = {}
        for k, v in imap.items():
            if isinstance(v, Node):
                out[k] = mapping.get(id(v), v)
            elif isinstance(v, tuple):
                out[k] = (mapping.get(id(v[0]), v[0]), v[1])
            else:
                out[k] = v
        return out

    def deep_copy(self, n):
        c = Node(n.name)
        c._orig = n
        c.pos, c.rot, c.scale = list(n.pos), list(n.rot), list(n.scale)
        c.active, c.mesh, c.model, c.prefab = n.active, n.mesh, n.model, n.prefab
        c.materials = list(n.materials)
        c.colliders = json.loads(json.dumps(n.colliders))
        c.scripts = json.loads(json.dumps(n.scripts, default=str))
        c.other = json.loads(json.dumps(n.other, default=str))
        c.children = [self.deep_copy(x) for x in n.children]
        return c

    def apply_mod(self, target, path, value, obj_ref):
        comp = None
        if isinstance(target, tuple):
            target, comp = target
        n = target
        axis = {"x": 0, "y": 1, "z": 2, "w": 3}
        try:
            num = float(value)
        except (TypeError, ValueError):
            num = None
        if path.startswith("m_LocalPosition.") and num is not None:
            n.pos[axis[path[-1]]] = num
        elif path.startswith("m_LocalRotation.") and num is not None:
            n.rot[axis[path[-1]]] = num
        elif path.startswith("m_LocalScale.") and num is not None:
            n.scale[axis[path[-1]]] = num
        elif path == "m_Name":
            n.name = str(value)
        elif path == "m_IsActive":
            n.active = bool(int(value))
        elif path.startswith("m_Materials.Array.data["):
            i = int(path.split("[")[1].split("]")[0])
            while len(n.materials) <= i:
                n.materials.append(None)
            n.materials[i] = self.asset_ref(obj_ref)
        elif path == "m_Mesh":
            n.mesh = self.asset_ref(obj_ref)
        elif comp is not None and comp["class"] == 114:
            ref = self.asset_ref(obj_ref) if obj_ref and obj_ref.get("fileID") else None
            script = self.path_of(comp["f"].get("m_Script"))
            for s in n.scripts:
                if s["script"] == (script and os.path.basename(script)):
                    s.setdefault("overrides", {})[path] = ref if ref else value
                    break


def main():
    root, target = sys.argv[1], sys.argv[2]
    r = Resolver(root)
    roots, _ = r.load(target)
    out = [x.to_dict() for x in roots]
    if "--json" in sys.argv:
        with open(sys.argv[sys.argv.index("--json") + 1], "w") as fh:
            json.dump(out, fh, indent=1, default=str)
    else:
        def show(d, depth=0):
            bits = [d["name"], "pos=%s" % [round(v, 3) for v in d["pos"]]]
            if any(abs(e) > 1e-3 for e in d["euler"]):
                bits.append("rot=%s" % d["euler"])
            if d["scale"] != [1.0, 1.0, 1.0] and d["scale"] != [1, 1, 1]:
                bits.append("scale=%s" % d["scale"])
            for k in ("model", "mesh"):
                if k in d:
                    bits.append("%s=%s" % (k, d[k]))
            if "materials" in d:
                bits.append("mat=%s" % [os.path.basename(m or "None") for m in d["materials"]])
            if "colliders" in d:
                bits.append("col=%s" % json.dumps(d["colliders"]))
            if "scripts" in d:
                bits.append("scripts=%s" % [s["script"] for s in d["scripts"]])
            if "other" in d:
                bits.append("other=%s" % [list(o)[0] for o in d["other"]])
            if d.get("active") is False:
                bits.append("INACTIVE")
            print("  " * depth + " ".join(bits))
            for c in d.get("children", []):
                show(c, depth + 1)

        for d in out:
            show(d)


if __name__ == "__main__":
    main()
