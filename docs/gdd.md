# GDD

Written from the Unity version ([PoliceChaseDrift](https://github.com/tiago-xavier-braga/PoliceChaseDrift)),
which is the reference for the port. Numbers come from its scenes, prefabs and ScriptableObjects.

## Pitch

An arcade chase game: you drive through a city block while police cars spawn at the farthest
point and hunt you down. Every hit costs health; the run ends when health reaches zero or the
car falls into the water. A day/night cycle runs during the match, turning on street and car
lights at night.

## Overview

- **Genre:** Arcade car chase (survival)
- **Art:** 3D low poly (Kenney car and city kits), isometric orthographic camera
- **Platform:** Web build, desktop browsers
- **Flow:** opening cutscene → main menu (play / garage) → match → game over → restart

## Core Loop

1. Player does: drives around the block, dodging police cars, buildings and props
2. Game responds: police cars keep spawning and ramming the player; hits cost health
3. Player decides: where to drive to keep the police away and the car in one piece
4. Repeat: when health runs out, restart (with the same car)

## Rules

### Map

A 150 x 150 m city block on four 75 m floor tiles, ringed by roads, with buildings, parking
lots, two ramps (slant curves), parked cars, construction barriers along the edges and street
lamps. Water surrounds the block; falling into it ends the match.

### Player car

- Controls: `W`/`↑` accelerate, `S`/`↓` brake and then reverse, `A`/`D`/`←`/`→` steer
  (left stick too).
- Physics: a 1000 kg rigid body on four suspension wheels (radius 0.3 m). The motorized wheels
  get `acceleration` torque, fading to 0 at `top_speed` (compared with the forward speed in m/s,
  so in practice it never fades much). Pressing against the movement brakes every wheel with
  `brake_force`. Steering goes from `steering_range` at rest to `steering_range_at_max_speed`.
- Cars (garage order) — health / top speed / acceleration / brake / steering at rest → at max:

  | Car | Health | Top speed | Accel. | Brake | Steering |
  |---|---|---|---|---|---|
  | Sedan Sports (default) | 15 | 120 | 800 | 2000 | 30° → 20° |
  | Race | 10 | 180 | 1200 | 1300 | 20° → 20° |
  | Ambulance | 20 | 80 | 800 | 2000 | 30° → 20° |
  | Taxi | 15 | 100 | 1200 | 2000 | 55° → 30° |

- The car picked in the garage stays selected after a restart.

### Health and damage

- Health starts at the car's health. Every collision with something that isn't the floor or a
  road (buildings, police, parked cars, lamps, barriers, tanks) costs **1** health.
- Below **5** health the engine smokes.
- At **0** health the match ends (game over). Falling into the water ends it too.

### Police

- Up to **30** police cars per match (29 in practice, see the quirks), one every **5 s**, each
  at the spawn point (6 around the roads) farthest from the player.
- AI: steers toward the player when the angle is above 5°, drives forward while farther than
  2 m, reverses when closer. After hitting anything other than the player, it reverses for 1 s.
- Police car: health unused, top speed 100, acceleration 600, brake 4000, steering 30° → 10°,
  four-wheel drive.
- Police cars drive straight through buildings (their rigidbody excludes the Building layer) and
  fade to 30 % opacity while inside one.

### Day/night cycle

- During a match the sun turns a full circle every **30 s** (it starts at 50° high). Night is
  while the sun is below the horizon.
- At night the street lamps and the car headlights fade on over 1 s; at day they fade off.
- The cycle carries on after a restart.

### Props

- **Street lamps** (1000 kg rigid bodies): knocked by the player's car, their light dies, and
  10 s later they dissolve away in 0.5 s.
- **Construction barriers** (500 kg rigid bodies) line the edges of the map and can be pushed.
- **Parked cars** are static; driving into one makes it wobble (pitch from the front or back,
  roll from the sides) for 2.5 s.

## Camera

Orthographic, isometric (35.26° down, 45° around), following the player's car from
(-30, 30, -30) m in Unity space. Orthographic size 5 (Godot size 10) in the menu; when the
match starts it zooms out to 10 (Godot 20) over 2 s with an ease-in-out-expo.

## Menus

- **Main menu:** play, garage, settings (the settings button does nothing in Unity either).
- **Garage:** arrows browse the cars (the car swaps in place), the clapper button selects the
  shown car, the home button goes back to the menu with the selected car.
- **Game over:** "Game Over" title on a dark overlay; the home button restarts the match, the
  clapper button does nothing (as in Unity).
- Panels fade and scale (0.8 ↔ 1) over 0.5 s. Buttons play a sound on hover and on click.

## Opening cutscene

12 s, played once at startup: a thief runs down the street with a police officer chasing;
the player's sports car runs the officer over; the officer sits, looks around, gets up angry
and kicks; a police car arrives and the officer nods. Music "Overboard", siren, engine and
voice-overs. Then the game loads.

## Feedback

- Engine sound whose pitch follows the speed (0.8 → 1.2 up to 100 km/h), only during a match.
- Impact sounds when hitting buildings (plank) and lamps (plate).
- Engine smoke at low health; a loading screen fades between levels.

## Unity quirks to decide on

Ported as they are unless noted:

- **Bot counter starts at 1:** only 29 of the 30 police cars are ever spawned.
- **Spawning on top of each other:** with the player standing still, every bot spawns on the
  same farthest point and they get stuck together.
- **Top speed in m/s:** `TopSpeed` is compared with the forward speed in m/s, so the torque
  barely fades; cars are limited only by the physics.
- **Dead buttons:** the main menu's settings button and the game over's clapper button do
  nothing.
- **Ramp walls:** the slant-curve ramps are 4 m tall at their high end and stop a car that hits
  the side; they are on the road layer, so the hit costs no health.
- **Collision sounds (changed):** Unity's `CollisionSoundPlayer` never assigned its clip, so it
  played nothing. The port plays the clip of the hit object (plank for buildings, plate for
  lamps).
- **Drift (not ported):** `CarParameter` has a drift friction curve and the code a handbrake,
  but no input ever turns it on.
- **Bot respawn near the player (not ported):** `HandleTooFarFromPlayer` is empty in Unity.
