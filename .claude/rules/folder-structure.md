# Folder Structure

This is a single Godot 4.7 game. Top-level folders by file type, with a subfolder per feature
inside each.

```
res://
├── addons/                    # shared plugins (leaf_tween)
├── assets/                    # media, grouped by kind
│   ├── animations/            # anim_*.tres (cutscene timeline, parked cars)
│   ├── audio/                 # sfx_*, music_*
│   ├── fonts/
│   ├── materials/             # mat_*.tres
│   ├── models/                # one folder per Kenney kit (+ meshes/ extracted from the FBX) and characters/
│   ├── shaders/               # *.gdshader (dissolve, water)
│   ├── textures/              # txt_*.png and ui/
│   └── ui/                    # theme_ui.tres
├── scenes/                    # .tscn, one subfolder per feature
│   ├── car/                   # player cars and the police car (generated)
│   ├── cutscene/              # opening cutscene (generated)
│   ├── environment/           # static and dynamic city (generated)
│   ├── levels/                # lvl_cutscene.tscn (main scene), lvl_game.tscn (generated)
│   ├── props/                 # lamp post, construction barrier (generated)
│   └── ui/                    # menus and loading screen
├── scripts/                   # .gd, one subfolder per feature
├── resources/                 # .tres data (cars, car database)
├── docs/                      # gdd.md, roadmap.md, feedback.md
├── tools/                     # unity_port/ (Python converter) and godot/ (headless tools) (.gdignore)
├── unity/                     # optional clone of the Unity project (git-ignored)
├── icon.svg
└── project.godot
```

Rules:

- Scenes go in `scenes/<feature>/`, scripts in `scripts/<feature>/`. The feature folder name
  matches in both.
- Level scenes live in `scenes/levels/` and are prefixed `lvl_`.
- Materials are prefixed `mat_`, textures `txt_`, and live under `assets/`.
- Kenney models keep their kit folder and file names (snake_case) and the kit's `license.txt`.
- Scenes marked generated are overwritten by `tools/unity_port/gen_godot.py`; change the generator,
  not the scene.
- Custom resources (`.tres` data defined by a `Resource` script) go in `resources/`; the script
  that defines them stays in `scripts/`.
- Project documentation lives in `docs/`.
- Don't create empty folders "for the future". A folder only exists once it has content.
- Build output (web export) is never committed; it goes in `build/`, which is git-ignored.
- Tweens go through the `LeafTween` autoload (`addons/leaf_tween`), not Godot's `Tween`.
