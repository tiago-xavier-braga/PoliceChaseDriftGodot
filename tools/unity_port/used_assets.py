"""List the assets the Unity scenes, prefabs and materials actually use.

Usage: python used_assets.py <unity_project_root>
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from unity_scene import build_guid_map
root = sys.argv[1]
g = build_guid_map(root)
seen = {}
todo = [p for p in g.values() if p.endswith(('.unity', '.prefab', '.mat', '.asset', '.controller', '.anim')) and 'ThirdParty' not in p and 'CrazySDK' not in p and 'AI Toolkit' not in p]
done = set()
while todo:
    p = todo.pop()
    if p in done: continue
    done.add(p)
    try: txt = open(os.path.join(root, p), encoding='utf-8', errors='ignore').read()
    except Exception: continue
    for guid in set(re.findall(r'guid: ([0-9a-f]{32})', txt)):
        q = g.get(guid)
        if not q: continue
        seen.setdefault(q, set()).add(p)
        if q.endswith(('.prefab', '.mat', '.controller', '.anim', '.asset')): todo.append(q)
for q in sorted(seen):
    if q.endswith(('.cs', '.shader', '.shadergraph')): continue
    print(q)
