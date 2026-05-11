# Overworld — Design

> The agreed design for the tile-and-sprite overworld scene, captured **before** code lands. Once Pass 1 ships, the implemented shape will be folded into [ARCHITECTURE.md](../ARCHITECTURE.md) and this file becomes a historical record of the decision points.

The roadmap places the tile-and-sprite overworld at [Layer 3](../ROADMAP.md). It is being kicked off early so it can advance in parallel with the Layer-1 text demo / battle polish. The point is to build the bones of the overworld scene against the existing scene-stack engine, not to ship Layer-3 content yet. Pass 1 is "a sprite walks around two test cells." Pass 2 is "a sprite walks around two test cells, talks to an NPC, and triggers a real `BattleScene` on a random-encounter roll."

---

## 1. Why this design, and not the predecessors'

Two prior projects share lineage with Nuitai's overworld work:

- **Dungeon Digger** is the senior project — a complete roguelike with a `DungeonLevel` (one 14×10 char grid), `Player` / `Monster` sprites, `MessageLog` with typewriter, fog of war, dig mechanics, intermission flow, treasure shop, leaderboard. Most of its weight is wrong for a JRPG overworld — fog, light, dig, treasure conversion, shop — and would actively drag if ported.
- **Adventure** is the descendant of Dungeon Digger — Dungeon Digger's UI scaffolding extracted and reduced. Its `World` class (cells + `WORLD_LAYOUT` + `step_to_neighbor`) is the right abstraction for a screen-by-screen overworld with cell-to-cell transitions, and is the **one piece of structure we are lifting in shape** (not file-by-file copying). Its player is a smooth-motion `DebugPlayer` we are intentionally *not* copying — Nuitai's overworld is grid-stepped (see §4).

Nuitai already has assets that Dungeon Digger and Adventure don't:

- A real **scene stack** with `OPAQUE = False` overlays.
- A real **`TextBox`** widget that does typewriter, pagination, ALL-CAPS, optional speaker.
- A real **`MenuScene`** translucent pause overlay.
- A real **`BattleScene`** that pops itself when the encounter ends.
- A centralised **`text_renderer`** that enforces the in-window ALL-CAPS rule.

So our shopping list from the predecessors is short: lift the `World` abstraction from Adventure; lift two generic sound effects (footsteps, wall-bump) from Dungeon Digger; write everything else fresh in Nuitai's conventions.

---

## 2. The screen layout

Inventory, map, status, save, settings live behind the existing `MenuScene` (pushed on Start). The exploration screen has only two things visible:

```
+----------------------------------------+
|              OVERWORLD                 |
|         (640 x 384, centered)          |
|                                        |
+----------------------------------------+
|                                        |
|             MESSAGE BOX                |
|         (full width, 160 tall)         |
+----------------------------------------+
```

Specific numbers (all driven from `settings.py`):

| Constant                       | Value | Notes                                                   |
| ------------------------------ | ----- | ------------------------------------------------------- |
| `GridSettings.TILE_SIZE`       | 32    | Pixels per tile.                                        |
| `OverworldSettings.COLS`       | 20    | Tiles wide per cell.                                    |
| `OverworldSettings.ROWS`       | 12    | Tiles tall per cell.                                    |
| `OverworldSettings.PIXEL_W`    | 640   | `COLS * TILE_SIZE`.                                     |
| `OverworldSettings.PIXEL_H`    | 384   | `ROWS * TILE_SIZE`.                                     |
| `OverworldSettings.X`          | 80    | `(ScreenSettings.WIDTH - PIXEL_W) // 2`; centered.      |
| `OverworldSettings.Y`          | 40    | Top margin.                                             |
| `UISettings.TEXT_BOX_HEIGHT`   | 160   | Existing; the box already anchors flush to the bottom.  |

The 16-pixel gap between the overworld bottom (`Y + PIXEL_H = 424`) and the message-box top (`600 - 160 = 440`) is intentional chrome.

Message-box behavior: the existing `TextBox` widget hides itself when empty. Pass 1 reuses that behavior unchanged — when nothing has been pushed, the bottom strip looks like the screen background. If we later want an always-visible bordered frame, the cleanest change is a `render_empty_frame` option on `TextBox`, not a parallel widget.

---

## 3. The world model

Lifted in shape from Adventure's `core/world.py`. Lives in a new `core/world.py` inside Nuitai:

```python
CELLS:          dict[name, list[list[char]]]   # tile grids keyed by cell name
WORLD_LAYOUT:   dict[(cx, cy), name]           # which cell sits at which world coord
START_CELL_POS: tuple[int, int]                # cell coord the player starts in
```

`World` owns `current_pos`, exposes `is_wall(col, row)` and `step_to_neighbor(dx_cells, dy_cells)`. The renderer reads `world.current_grid`; the player calls `is_wall` to validate a step and `step_to_neighbor` when stepping past a cell edge.

This is the only place in the codebase that knows the cell-grid representation. Adding interior layers (dungeon, house) means growing `World` with a `current_layer` field and an entrance-tile table; nothing else has to know.

**Tile representation: char grid.** `'.'` walkable floor, `'#'` wall, `'~'` water (visual + impassable), `'_'` sand/path (alt floor). Chars cap at ~30 tile types, which is comfortable through Pass 2. When we outgrow chars we migrate to JSON arrays of integer tile IDs; the `World` API hides the representation so the migration is local.

Pass 1 ships two test cells (`'beach_west'` and `'beach_east'`, or similarly evocative names). They sit at `(0, 0)` and `(1, 0)` in `WORLD_LAYOUT`. Each has a matching opening on its shared edge so the player can walk from one into the other.

Cells live in `core/overworld_cells.py` for Pass 1 (a module-level dict, like Adventure does it). When the cell count grows we migrate to `data/cells/*.json` and the `DataLoader` reads them like every other content pack.

**Camera:** screen-locked. One cell = one screenful = 20×12 tiles. Crossing the overworld edge swaps to the matching neighbor cell and snaps the sprite to its entry edge. No scrolling.

---

## 4. The player: grid-stepped with pixel interpolation

The player's logical position is `(col, row)` in cell-local tile coordinates. When a direction is pressed:

1. The scene asks the player to attempt a step in that direction.
2. The player checks `World.is_wall` for the destination tile.
3. If walkable: the player commits to the new logical tile and starts an animation that interpolates the sprite's pixel position from the previous tile to the new tile over `OverworldPlayerSettings.STEP_DURATION_MS` (target ≈ 150 ms).
4. If blocked: the player turns to face the wall (a "bump") and emits a wall-bump sound; the logical position does not change.
5. If the destination tile is past the cell edge: the player asks `World.step_to_neighbor`. On success, the sprite snaps to the matching entry tile of the new cell. On failure (no neighbor cell), the bump path applies.

Input arriving mid-step queues the next step; at step end the queued direction is consumed and a new step begins. This is the standard "buffered movement" feel that makes JRPG overworlds responsive without losing the grid discipline.

**Four-directional only.** Diagonals are not allowed. Pressing two perpendicular directions at once preserves the most recent press.

**Facing direction** is the most recent attempted step direction, success or failure. Used by Pass-2 interaction code ("face the NPC, press A") and by the Pass-2 sprite renderer to pick the right facing frame.

Why grid-stepped: matches Chrono Trigger / FF4 / DQ; makes step-counted random encounters trivial; makes NPC interaction natural; makes tile triggers (doors, warps, signs) clean. The player class is behind `OverworldScene.player`, so a Layer-4 swap to smooth motion (if ever wanted) is a local change.

Pass 1 player rendering is a colored rectangle (`OverworldPlayerSettings.COLOR`), same approach as Adventure's `DebugPlayer`. Pass 2 introduces real placeholder sprite art chosen for Nuitai's tropical-island setting — Dungeon Digger's dungeon-helmet sprites are deliberately not imported because they would set the wrong aesthetic.

---

## 5. The scene

`core/scenes/overworld_scene.py` defines `OverworldScene(Scene)` with `OPAQUE = True`. It owns:

- a `World` instance (current cell + cell layout),
- an `OverworldPlayer` instance (logical position, facing, step animation, input queue),
- a `TextBox` (the existing widget, reused unchanged),
- a step counter for encounter rolls (Pass 2).

Per-frame:

- **`handle_event`**:
  - If `text_box.is_done()` is False, `is_confirm` advances the box and consumes the event.
  - Else, `is_up` / `is_down` / `is_left` / `is_right` push a direction onto the player's input queue.
  - Else, `is_confirm` (A) interacts with the tile the player is facing (Pass 2 — Pass 1 is no-op).
  - Else, `is_cancel` (B) is reserved (Pass 2 — Pass 1 is no-op).
  - Else, Start button pushes `MenuScene` onto the stack.

- **`update(dt)`**: tick the text-box typewriter; tick the player's step animation (which may consume the next queued direction at step end and may also trigger a cell transition); in Pass 2, increment the encounter step counter on each completed step and roll for an encounter.

- **`render(surface)`**: paint the scene-background template via `render_scene_background`; draw the overworld grid (one filled rect per tile, color keyed off the tile char) into the cell area; draw the player on top; draw the text box on top of everything else.

**Persistence.** `to_dict` captures `world.current_pos`, the player's `(col, row)` and facing, and the step counter. `from_dict` restores them. A save/load round-trip drops the player back where they were.

**Wiring.** `TitleScene._new_game` and `_continue` currently `replace(TestWorldScene(...))`. Pass 1 changes those to `replace(OverworldScene(...))`. `TestWorldScene` stays in the tree as a reference but is no longer reachable from the title screen.

---

## 6. Encounters (Pass 2)

Step-counted random encounters. On every **successful** step, the encounter counter increments. A roll fires when the counter exceeds a per-cell-data-driven minimum-quiet-steps and a probability check passes; on hit, the scene pushes `BattleScene` with a random enemy id drawn from the cell's encounter table. When `BattleScene` pops, the overworld resumes and the counter resets.

Per-cell encounter data lives in the cell dict (or eventual cell JSON):

```python
'beach_west': {
    'grid': [...],
    'encounters': {
        'rate': 0.10,            # probability per eligible step
        'min_quiet_steps': 8,    # encounters cannot fire before this many steps
        'table': ['crab', 'shade'],  # enemy ids drawn at random
    },
}
```

Encounters are off entirely if a cell omits the `encounters` block. This means towns and interior cells (Pass-3 territory) are safe without special-casing.

---

## 7. NPCs, doors, signs (Pass 2)

Interactables are tagged in the cell data by tile coordinate:

```python
'beach_west': {
    'grid': [...],
    'interactables': {
        (10, 6): {'kind': 'npc', 'dialogue': 'kailo_intro'},
        (4, 11): {'kind': 'warp', 'target_cell': (0, 1), 'spawn': (4, 0)},
        (15, 3): {'kind': 'sign', 'text': 'Lehua trail — keep west.'},
    },
}
```

On A-press the scene reads the tile **in front of** the player (from the facing direction) and dispatches. Dialogues route through the existing `DialogueRunner` + `TextBox` path that `TestWorldScene._talk` already uses; warps call `World.step_to_neighbor`-equivalent plus a sprite snap; signs push their text onto the box.

---

## 8. What stays out of Pass 1 and Pass 2

- **Animated walk cycles.** Static colored rectangle in Pass 1; real placeholder sprite art in Pass 2 but a single static frame per facing direction. Animated cycles wait for Layer 4.
- **Multiple party members on the overworld.** Only the leader walks. Followers are a Layer-4 polish item if they happen at all.
- **A scrolling camera.** Screen-locked is enough through Layer 3.
- **Tile autotiling / variants.** One tile per char until we have actual art that needs autotiling.
- **Day/night, weather, time of day.** Reserve for Layer 4+.
- **Particle effects, footstep dust, water splashes.** Layer 4+.
- **Real sprite assets for the player.** Pass 2 picks one placeholder set; Layer 4 replaces it with original work.

---

## 9. Settings additions

Pass 1 adds the following classes to `settings.py`:

```python
class GridSettings:
    """Tile dimensions for the overworld grid."""

    TILE_SIZE = 32   # Pixels per tile.


class OverworldSettings:
    """Cell-area layout for the overworld scene."""

    COLS = 20
    ROWS = 12
    PIXEL_W = COLS * GridSettings.TILE_SIZE
    PIXEL_H = ROWS * GridSettings.TILE_SIZE
    X = (ScreenSettings.WIDTH - PIXEL_W) // 2
    Y = 40


class OverworldPlayerSettings:
    """Tunable values for the overworld player sprite."""

    STEP_DURATION_MS = 150     # Walk animation duration per tile.
    COLOR = ColorSettings.YELLOW   # Pass-1 placeholder fill.
    SIZE = GridSettings.TILE_SIZE  # Visual size; matches tile size for now.
```

Tile colors for the Pass-1 placeholder renderer go in `ColorSettings` (e.g. `OVERWORLD_FLOOR`, `OVERWORLD_WALL`, `OVERWORLD_WATER`, `OVERWORLD_SAND`). They are replaced by tile-sprite blits in Pass 2.

Audio additions (Pass 2, when sprite footsteps are wired):

```python
AudioSettings.SOUND_EFFECTS["footstep"] = ...  # from Dungeon Digger
AudioSettings.SOUND_EFFECTS["wall_bump"] = ...  # from Dungeon Digger
```

---

## 10. `input_map` additions

Pass 1 adds `is_left` and `is_right` helpers to [ui/input_map.py](../../ui/input_map.py), mirroring `is_up` / `is_down`. They route keyboard arrows, WASD, D-pad hat events, and the left-analog X axis through the same JOY_TRIGGER_THRESHOLD-driven logic. Scenes that already use `is_up` / `is_down` are unaffected; the new helpers are picked up by `OverworldScene`.

---

## 11. Implementation order (the two passes)

### Pass 1 — scaffolding, no playable demo

The goal is "the new bones exist and stand up." Acceptance criteria:

1. `python main.py` boots without crash.
2. NEW GAME from the title screen drops the player into the overworld instead of `TestWorldScene`.
3. The screen shows a centered cell area filled with placeholder-tile rects and an empty bottom strip where the message box will appear.
4. Arrow keys, WASD, the controller D-pad, and the left analog stick all move a colored rectangle one tile per press, stepping smoothly to the destination.
5. Walking into a wall tile bumps without entering it.
6. Walking off the east edge of `beach_west` transitions to `beach_east`; walking back west returns.
7. Start (controller) / Esc-equivalent (keyboard — TBD which key, probably Tab) pushes `MenuScene`; canceling out returns to the overworld with no state loss.
8. Save/load through `MenuScene → Save` and `TitleScene → Continue` returns the player to the same cell and tile.
9. `docs/CHANGELOG.md` has an entry for Pass 1.
10. `docs/ARCHITECTURE.md` has the "Planned" section folded into a current-systems section describing `OverworldScene`.
11. `docs/TESTING.md` has overworld smoke checks added.
12. `docs/TODO.md` Pass 1 items are marked `[x]`.

### Pass 2 — playable demo

Builds on the Pass 1 scaffolding. Acceptance criteria:

1. Two or three real cells with placeholder tile art (chosen for Nuitai's setting).
2. At least one NPC tile that, when faced and A-pressed, opens the existing dialogue path.
3. Step-counted random encounters fire on the configured cells and push the real `BattleScene`; winning, losing, or fleeing pops back to the overworld in the correct state.
4. At least one sign tile and at least one warp tile.
5. Save/load round-trips through a cell transition correctly.
6. Footstep and wall-bump audio cues are wired.
7. CHANGELOG / ARCHITECTURE / TESTING / TODO updated.

---

## 12. Decisions to revisit later

- **Char vs. JSON cell representation.** Char grids are fine through Pass 2. If we get past ~10 distinct tile types or want per-tile metadata (e.g. an encounter override on one specific tile), migrate to JSON.
- **Always-visible message-box frame.** If gameplay wants a permanently-visible empty frame at the bottom, add `render_empty_frame=True` to `TextBox`.
- **Diagonals.** If overworld traversal feels too slow at 150 ms per tile, the cheaper fix is lowering the step duration (~120 ms is still readable), not adding diagonals.
- **Animated step indicator.** A footstep-puff or shoreline-ripple effect would sit naturally on top of the cell renderer once we have art for it.
- **Map / mini-map.** Originally a dedicated sidebar in Dungeon Digger / Adventure; here it lives behind the menu (a future `MenuScene → Map` row).
