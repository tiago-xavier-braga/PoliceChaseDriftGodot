# Police Chase: Drift

An arcade chase game: you drive through a city block while police cars spawn at the farthest
point and hunt you down. Every hit costs health; the run ends when health reaches zero or the
car falls into the water. A day/night cycle runs during the match, turning on street and car
lights at night.

This is the Godot port of the Unity game Police Chase: Drift, built as a 3D web game.

> **Vibe coded:** this port was made by prompting an AI coding assistant, not written by hand.
> The code, scenes, converter and docs were generated from prompts, using the Unity game as the
> reference, and checked with headless test scripts and screenshots rather than by a
> line-by-line code review.

> **Status:** the port is playable: cutscene, menus, garage, car physics, police, day/night,
> props and game over all work. See the [roadmap](docs/roadmap.md) for the phases and the open
> decisions.

## How to play

| Action | Keys |
|---|---|
| Accelerate / brake and reverse | `W` `S` / `↑` `↓` / left stick |
| Steer | `A` `D` / `←` `→` / left stick |

- **Play** starts the match; police cars start arriving every 5 seconds.
- **Garage** lets you pick another car (sports, race, ambulance, taxi); each has its own health,
  speed and handling.
- Every hit costs 1 health; at 0, or in the water, it's game over. The home button restarts.

## Documentation

- [Game design document](docs/gdd.md): the rules, numbers and feedback, plus the Unity quirks
  that were ported or dropped.
- [Roadmap](docs/roadmap.md): the port, phase by phase, and the Unity-to-Godot notes.
- [Playtest feedback](docs/feedback.md): player suggestions and bug reports.

## Requirements

- Godot `4.7` (GL Compatibility renderer)
- [LeafTween](https://github.com/tiago-xavier-braga/LeafTween), the tween library behind every
  animation, already included in `addons/leaf_tween/`

## Run locally

1. Install [Godot 4.7](https://godotengine.org/download).
2. Open `project.godot` in the editor.
3. Press **F5** to play (it starts with the opening cutscene).

## Web build

Install the Godot `4.7` export templates (**Editor → Manage Export Templates**), then export
the `Web` preset from the project folder:

```sh
mkdir -p build
godot --headless --export-release "Web" build/index.html
```

`build/` is git-ignored. Thread support is off, so the build doesn't need cross-origin
isolation headers and runs on static hosts such as GitHub Pages or itch.io.

## Porting from Unity

The Unity project, [PoliceChaseDrift](https://github.com/tiago-xavier-braga/PoliceChaseDrift), is
the reference for the port. It isn't part of this repository: clone it into
`unity/PoliceChaseDrift/` (git-ignored) and pull its Git LFS files. The converter needs Python
with `pyyaml`, `numpy` and `mutagen`:

```sh
python tools/unity_port/copy_assets.py                                  # media into assets/
godot --headless --path . --import                                       # import the models
godot --headless --path . --script res://tools/godot/extract_meshes.gd  # FBX sub-meshes and shapes
python tools/unity_port/gen_godot.py                                     # scenes
```

`gen_godot.py` overwrites the scenes it generates (cars, props, environment, cutscene,
levels); the scripts and the UI scenes are written by hand.

Headless checks in `tools/godot/` (`drive_test.gd`, `bot_test.gd`, `props_test.gd`) drive the
game and print what happens; `ui_test.gd` and `screenshot.gd` need a display and save
screenshots:

```sh
godot --headless --path . --fixed-fps 60 --script res://tools/godot/drive_test.gd
```

## License

Third-party assets keep their own licenses:

- The 3D models in `assets/models/kenney_*` and the characters are by
  [Kenney](https://www.kenney.nl) and released under CC0 (each kit's `license.txt` is next to its
  models).
- [LeafTween](https://github.com/tiago-xavier-braga/LeafTween), in `addons/leaf_tween/`, is
  licensed under MIT.

The other art (UI sprites, sky, water textures), the fonts, the sounds and the music come from
the original Unity project.
