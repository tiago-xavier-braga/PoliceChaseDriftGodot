# Police Chase: Drift

Godot 4.7 (GL Compatibility) port of the Unity game
[PoliceChaseDrift](https://github.com/tiago-xavier-braga/PoliceChaseDrift). Clone it into
`unity/PoliceChaseDrift/` (git-ignored) and run `git lfs pull` in it when you need the reference
or the converter. 3D, web build.

- Game design: `docs/gdd.md`. Plan: `docs/roadmap.md`. Keep all project docs in `docs/`.
- Vibe coded: no design note is needed before code, but stay inside the current roadmap phase;
  new ideas go to the backlog.
- The port must play like the Unity version; check behavior and numbers in its scripts, scenes
  and ScriptableObjects before guessing.
- `tools/unity_port/gen_godot.py` regenerates the car, prop, environment, cutscene and level
  scenes from the Unity data and overwrites them. Scripts, `game_ui.tscn` and `loading.tscn` are
  hand-written.
- Must run in a web export: no threads, no native-only APIs.
