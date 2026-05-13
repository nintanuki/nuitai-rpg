# Nuitai RPG — Architecture

> **Maintenance rule:** every pass that meaningfully changes a system must update this document. The file describes the code as it **currently exists**, not as it is planned. Planned work lives in [ROADMAP.md](ROADMAP.md) and [TODO.md](TODO.md).

## 1. The shape of the program

```
                   +-------------------+
                   |     main.py       |
                   |   GameManager     |   (coordinator)
                   +---+-----+-----+---+
                       |     |     |
        +--------------+     |     +-------------+
        v                    v                   v
     events             scene stack           render
   (keyboard,         (top scene gets        (screen fill
    joystick)          input + render)        + CRT pass)
```

`GameManager` owns the screen, the clock, the cached joystick list, the fullscreen flag, the `AudioManager`, the shared `DataLoader`, the active `Party`, and the `SceneStack`. Everything else — gameplay, UI, animations, persistence, content data — lives in modules under `core/`, `systems/`, `ui/`, or `utils/` and is coordinated through `GameManager`.

## 2. Frame loop

`GameManager.run()` per frame:

1. `quit_combo_pressed()` — early-exit on the held quit chord.
2. `clock.tick(FPS)` produces the wall-clock `dt` in seconds.
3. `_process_events()` — drain pygame's event queue, run global handlers (quit, fullscreen), then forward every event to `scene_stack.handle_event(event)`.
4. `_update_world(dt)` — calls `scene_stack.update(dt)`.
5. `_render_frame()` — `screen.fill(BG_COLOR)`, then `scene_stack.render_all(screen)`, then the CRT overlay (windowed only).
6. `pygame.display.flip()`.

## 3. Input

Events are routed by type:

- `KEYDOWN` → `_handle_keydown`. Globals: `Esc` quits, `F11` toggles fullscreen.
- `JOYBUTTONDOWN` → `_handle_joybuttondown`. Globals: quit-chord check + `BACK` toggles fullscreen.
- `JOYHATMOTION` → `_handle_joyhatmotion` (stub; scenes read these via `ui/input_map.py`).
- `JOYAXISMOTION` → `_handle_joyaxismotion` (stub; scenes read these via `ui/input_map.py`).

After global handling, every event is forwarded to the active scene through `scene_stack.handle_event(event)`. Scenes use [ui/input_map.py](../ui/input_map.py) helpers — `is_confirm`, `is_cancel`, `is_up`, `is_down`, `is_left`, `is_right`, `is_menu` — to translate raw events into logical UI actions, so each scene does not reimplement the keyboard + controller routing. Confirm currently maps to keyboard (`Enter`, `Z`, `Space`) plus controller (`A`, `START`) so menu selection parity is preserved across input devices. `is_menu` opens the system menu; today it routes `Tab` (keyboard) + `START` (controller) — Layer 1 Pass 3 rebinds the controller side from `START` to `Y` per [docs/design/oneshot.md](design/oneshot.md) §5.

Movement on the overworld is **polled**, not event-driven: `OverworldPlayer.update` calls `input_map.read_held_direction(joysticks)` once per frame, which returns the currently-held cardinal `(dx, dy)` from keyboard state plus every connected joystick's D-pad and left analog stick. Polling for movement avoids reconfiguring `pygame.key.set_repeat` globally (which would bleed key-repeat into menus and the text box). Event-driven helpers (`is_up` etc.) are still used for menu cursor navigation, where one-press-equals-one-move is the right feel.

Joysticks are cached at startup in `setup_controllers()`. Hot-plug requires re-running it. The quit chord is `InputSettings.JOY_BUTTON_QUIT_COMBO`.

## 4. Audio

[systems/audio_manager.py](../systems/audio_manager.py) is a data-driven sound and music dispatcher. It reads `AudioSettings.SOUND_EFFECTS` (logical name → path) on construction, loads each sound, and exposes a single `play(name)` entry point. Each loaded sound resolves its volume from `AudioSettings.SFX_FILE_VOLUMES` first, then falls back to `AudioSettings.SFX_VOLUME`; setting one file override to `0.0` mutes only that cue. Music is rotated through `AudioSettings.MUSIC_TRACKS`, avoiding back-to-back repeats, and managed via `play_random_music`, `play_music_track`, `pause_music`, `resume_music`, and `stop_music`. Each track resolves volume from `AudioSettings.MUSIC_FILE_VOLUMES` first, then falls back to `AudioSettings.MUSIC_VOLUME`; this also applies to scene-specific tracks loaded directly with `play_music_track` (the title scene loops `waves.ogg` while active). `toggle_mute` flips `AudioSettings.MUTE` globally — mute is honored at the call site, so toggles are instant and reversible.

`GameManager.__init__` initialises the mixer with `_initialize_audio_mixer()` **before** constructing `AudioManager`. Failure to load a sound, music track, or even the mixer itself is non-fatal — the game keeps running silently. Mixer init failures are logged to `stderr`, never to gameplay output.

## 5. CRT overlay

[crt.py](../crt.py) loads `AssetPaths.TV`, scales it to the screen, and on each `draw()` blits a fresh copy with a randomized alpha and per-row scanlines. `GameManager._render_frame` calls it only when not in fullscreen so it does not double-up on a real CRT cabinet.

## 6. Settings

[settings.py](../settings.py) is the single source of truth for tunables.

| Class            | Purpose                                                                          |
| ---------------- | -------------------------------------------------------------------------------- |
| `ColorSettings`  | Named colors + semantic aliases (`BG_COLOR`, `OVERLAY_BACKGROUND`).              |
| `ScreenSettings` | Resolution, FPS, title, CRT alpha range and scanline height.                     |
| `InputSettings`  | Controller button/axis indices + quit combo + analog threshold.                  |
| `FontSettings`   | Font file paths and size rungs (`SIZE_SMALL`, `SIZE_BODY`, `SIZE_HEADING`, title-screen heading size). |
| `AudioSettings`  | Mute toggles, default music + SFX volume, per-file `MUSIC_FILE_VOLUMES`/`SFX_FILE_VOLUMES`, and `SOUND_EFFECTS`/`MUSIC_TRACKS` registry.   |
| `AssetPaths`     | Asset file paths for non-font assets.                                            |
| `DebugSettings`  | Debug-only toggles.                                                              |
| `SaveSettings`   | `SAVES_DIR` (file-relative), `MAX_SAVE_SLOTS`, `AUTOSAVE_SLOT_ID`.                |
| `BattleSettings` | Starting potion count, potion heal amount, defend damage divisor. Gameplay-feel knobs for the battle system; element multipliers stay in `core/elements.py`. |
| `UISettings`     | Text-box geometry, typewriter speed, menu cursor blink, menu spacing/alignment, title-screen layout anchors, command-panel width. |
| `BackgroundSettings` | Named scene-background templates (solid / vertical gradient) and the `SceneClassName → template` mapping consumed by `utils/backgrounds.py`. |
| `GridSettings`   | Tile dimensions for the overworld grid (`TILE_SIZE = 32`).                       |
| `OverworldSettings` | Cell-area layout (rows / cols / pixel dimensions / origin) plus the cell-tile alphabet (`WALL_CHAR`, `WATER_CHAR`, `SAND_CHAR`, `FLOOR_CHAR`). |
| `EncounterSettings` | Step-counted random-encounter parameters (`RATE_PER_STEP`, `MIN_QUIET_STEPS`).  |
| `OverworldPlayerSettings` | Tunables for the overworld player sprite (step duration, placeholder color, sprite size, spawn tile). |

**No magic numbers anywhere outside this file.**

## 7. Scenes

A `Scene` ([core/scene.py](../core/scene.py)) is one screenful of game state — title screen, room, battle, pause menu. Scenes are kept on a stack so transient overlays (pause, dialogue, battle) push on top of the gameplay beneath them and pop to return.

- The top scene receives input and updates each frame.
- Render walks bottom-up, starting at the deepest opaque scene, so a translucent overlay (`OPAQUE = False`) leaves the world below visible.
- Every concrete scene exposes `to_dict` / `from_dict` so the save system can rebuild the stack across sessions.

Layer-0 scenes:

- [core/scenes/title_scene.py](../core/scenes/title_scene.py) — NEW GAME / CONTINUE / LOAD GAME / QUIT. CONTINUE and LOAD GAME are disabled when no save exists. Loops `waves.ogg` while the scene is active. NEW GAME and CONTINUE both replace the stack with `OverworldScene`.
- [core/scenes/overworld_scene.py](../core/scenes/overworld_scene.py) — the grid-stepped, screen-locked exploration scene. Owns a `World`, an `OverworldPlayer`, and a `TextBox`; pushes `MenuScene` on `Tab` / `START`. See §12a for the world model and player behavior, and [docs/design/overworld.md](design/overworld.md) for the full design.
- [core/scenes/test_world_scene.py](../core/scenes/test_world_scene.py) — Layer-0 placeholder room with TALK / FIGHT / SAVE / QUIT TO TITLE commands. Still in the tree for reference but no longer reachable from the title screen.
- [core/scenes/battle_scene.py](../core/scenes/battle_scene.py) — hosts a `Battle` and a `BattleView`; resolves to victory, defeat, or flee. While a party member's turn waits on input, the bottom HUD splits into a left-side command panel (Attack / Defend / Ability / Potion x{N}) and a right-side prompt; choosing Ability swaps the panel for the active actor's ability submenu (cancel returns to the top level). Outside of awaiting-command moments the full bottom bar reverts to the standard text box. The active combatant's roster line renders in `ColorSettings.YELLOW` so the player always knows whose turn it is, and the roster rows now also render the combatant's elemental label(s) under the name / HP line so battle keeps the same elemental readout as the party screen.
- [core/scenes/menu_scene.py](../core/scenes/menu_scene.py) — translucent pause overlay (`OPAQUE = False`) with party / inventory / save / settings / quit-to-title rows. The PARTY and INVENTORY rows push the dedicated status scenes below; SETTINGS is still a placeholder.
- [core/scenes/party_scene.py](../core/scenes/party_scene.py) — read-only roster (name, current HP / max HP, element pair) used to verify HP persistence end-to-end. Cancel pops back to `MenuScene`.
- [core/scenes/inventory_scene.py](../core/scenes/inventory_scene.py) — read-only item list (item id + count) from `Party.inventory`. Cancel pops back to `MenuScene`.

## 7a. Scene backgrounds — template registry

Every opaque scene paints its backdrop by calling `render_scene_background(self, surface)` from [utils/backgrounds.py](../utils/backgrounds.py) at the top of its `render` method instead of issuing a raw `surface.fill`. The renderer looks up the scene class name in `BackgroundSettings.SCENE_BACKGROUNDS`, resolves it against `BackgroundSettings.TEMPLATES` in [settings.py](../settings.py), and either fills a solid color or blits a cached vertical-gradient surface (built once via `utils.graphics.build_gradient_surface`, then keyed in-memory by `(template_name, width, height)`).

To re-skin a scene, change one line in `SCENE_BACKGROUNDS`. To add a new look, add one entry to `TEMPLATES` — supported shapes are `(SOLID, (r, g, b))` and `(GRADIENT, (r, g, b), (r, g, b))`. Layer 1 will likely add a third (image-backed) shape; the renderer's `kind`-switch is the seam to extend.

The translucent pause overlay (`MenuScene`, `OPAQUE = False`) deliberately skips this path: it renders over the scene beneath it, so it has no background of its own.

## 8. Element system — single source of truth

[core/elements.py](../core/elements.py) defines the `Element` enum (`AHI`, `LAU`, `WAI`, `RA`, `AKU`, `MANA`) and the strength/weakness lookup:

```
Ahi  → burns      → Lau
Lau  → drinks     → Wai
Wai  → quenches   → Ahi
Ra   → purifies   → Aku
Aku  → corrupts   → Mana
Mana → transcends → Ra
```

`damage_multiplier(attacker, defender)` returns:

- `ADVANTAGE_MULTIPLIER` (2.0) — attacker beats defender per the table above.
- `DISADVANTAGE_MULTIPLIER` (0.5) — defender beats attacker, **or** attacker and defender share the same element (a target resists its own element; "the Shade does not bleed shadow").
- `NEUTRAL_MULTIPLIER` (1.0) — cross-triangle pairings.

Every battle damage calculation reads from this module. It is **not duplicated** anywhere — JSON content packs reference element names by string and `data_loader` resolves them.

### What carries an element, and what does not

- **Party basic attacks**: non-elemental. The element table is bypassed entirely (multiplier always 1.0). A character with the Ra element does not deal Ra damage by swinging their wand. Layer 1+ will introduce an augment system (only available to characters with Ahi or Mana) that imbues a basic attack with the augmentor's element; until then the basic attack is the player's neutral fallback.
- **Abilities**: every ability JSON carries an `element` and a `kind`. Supported kinds: `"damage"` (runs through the element table), `"heal"` (ignores the table), `"buff"` (applies a per-combatant status; today the only buff is Shaka's Light's Aku-immunity counter). Future kinds will include `"status"` for debuffs.
- **Enemy basic attacks**: keep the enemy's element for now. Layer 1+ will split enemy actions into *physical* (non-elemental) and *special* (elemental) attacks, the same way party characters work, and the inherent-element fallback will retire.
- **Aku-immunity status**: a per-`Combatant` turn counter (`aku_immune_turns`) granted by Shaka's Light. While positive, any incoming Aku-element strike is fully nullified — the strike still emits a `DamageEvent` with `amount=0` and `multiplier=0.0` so the view can narrate "It had no effect on X!" rather than silently swallowing the action. The counter ticks down at the top of the holder's own turn; reaching zero emits a closing `StatusAppliedEvent(applied=False)` so the view can announce the fade.
- **Same-element matchups**: neutral (1.0×). Per-combatant resistances to a specific element (e.g. "this Aku creature is immune to Aku status effects") will be authored case-by-case on enemy JSONs, not imposed as a global rule.

### Effectiveness narration

`ui/battle_view.py` consumes `DamageEvent.multiplier` and appends one Pokemon-style follow-up line:

- `multiplier > 1.0` → "It's super effective!"
- `multiplier < 1.0` → "It's not very effective..."
- `multiplier == 1.0` → no extra line. Non-elemental hits land here.

This is intentionally generic placeholder text; the per-character, per-element flavor pass happens later in the writing track.

## 9. Events — typed records

[core/events.py](../core/events.py) defines frozen dataclasses for what gameplay produces and views consume:

- Battle: `TurnStartEvent`, `AttackEvent`, `DamageEvent`, `DefendEvent`, `AbilityUsedEvent`, `HealEvent`, `PotionUsedEvent`, `StatusAppliedEvent`, `CombatantDefeatedEvent`, `BattleEndedEvent`.
- Dialogue: `DialogueLineEvent`, `DialogueEndedEvent`.

Game logic produces events; views consume them. Across the five layers, only the views change. New event types are added freely; views ignore unknown ones, so producers can extend the stream without breaking older views.

## 10. Persistence

[core/save.py](../core/save.py) writes JSON files at `SaveSettings.SAVES_DIR/slot_<id>.json`. Each file has a `version` stamp and a `data` payload. On load, `migrate(record)` walks any older save up to `SAVE_SCHEMA_VERSION`. Future versions raise `ValueError` rather than silently corrupting state.

The Layer-0 payload is just the party (`party.to_dict()`); future layers add scene-stack snapshots, world flags, and RNG seed.

## 11. Content loader

[core/data_loader.py](../core/data_loader.py) reads JSON from `data/<kind>/*.json`, requires a top-level `id` field on each file, and returns the contents indexed by id. Caches per-kind. Missing pack directories return an empty dict so the engine can boot without content. `GameManager` owns one shared `DataLoader` instance (`gm.data`); scenes reach into it rather than constructing their own.

The seam from JSON dict to runtime gameplay object lives in [core/factories.py](../core/factories.py): `party_member_from_data`, `combatant_from_party_member`, `combatant_from_enemy_data`. Every "build X from data" call site routes through this module so the JSON-to-runtime mapping is never duplicated.

## 12. Gameplay systems

- [systems/party.py](../systems/party.py) — `PartyMember` and `Party`: members, inventory, gold, story flags. `PartyMember` carries a `learnset` (list of ability ids) that survives save/load. Fully serialisable; the canonical source for save data.
- [systems/battle.py](../systems/battle.py) — `Combatant` and `Battle`: turn-queue logic. Pure data; emits events; never draws. The scene drives a battle in two beats: `start_turn()` advances the queue, emits `TurnStartEvent`, and **resolves enemy actions inline**; for a party actor it parks the battle in *awaiting-command* mode (`is_awaiting_command()`) until the scene calls one of `submit_attack`, `submit_defend`, `submit_ability(ability_id)`, or `submit_potion`. `Combatant.is_defending` halves incoming damage (per `BattleSettings.DEFEND_DAMAGE_DIVISOR`) until the defender's own next turn. Potions are a shared pool seeded from `BattleSettings.STARTING_POTIONS`. Turn order is the simple sequential `party + enemies` rotation; the eventual destination is an **FFX-style Conditional Turn-Based** queue driven by per-combatant speed and weighted by action cost — the command interface above is shaped so that swap is an internal change to this module only.
- [systems/dialogue.py](../systems/dialogue.py) — `DialogueRunner`: walks a JSON dialogue tree and emits `DialogueLineEvent`s, then `DialogueEndedEvent`.

## 12a. Overworld scene and world model

The Layer-3 destination — exploration on a tile grid — was kicked off early in Pass 1 and lives alongside the text-mode Layer-0 scenes. The overworld decomposes into three collaborators bound together by [core/scenes/overworld_scene.py](../core/scenes/overworld_scene.py):

- [core/world.py](../core/world.py) — `World`: owns `current_pos` (the active cell coordinate), exposes `is_wall(col, row)` (treats walls and water as impassable; out-of-bounds is non-wall so the player can fall through to the cell-transition path) and `step_to_neighbor(dx_cells, dy_cells)` (swaps to the named cell at the offset in `WORLD_LAYOUT`, returns False when no neighbor exists). Round-trips through `to_dict` / `from_dict` so saved games restore the active cell.
- [core/overworld_cells.py](../core/overworld_cells.py) — static module-level `CELLS`, `WORLD_LAYOUT`, and `START_CELL_POS`. Cells are char grids; the alphabet (`'.'` floor, `'#'` wall, `'~'` water, `'_'` sand) lives in `OverworldSettings.*_CHAR` so cells and code share one source of truth. `_validate_cells()` runs at import time and raises `ValueError` if any cell is misshaped. Migrating to `data/cells/*.json` is a Pass-2 decision.
- [entities/overworld_player.py](../entities/overworld_player.py) — `OverworldPlayer`: grid-stepped logical position (`col`, `row`) with pixel-interpolation animation over `OverworldPlayerSettings.STEP_DURATION_MS`. Held-input is polled inside `update` via [ui/input_map.py](../ui/input_map.py)'s `read_held_direction(joysticks)`; pressing two perpendicular directions keeps the dominant axis. Wall collisions and cell edges are both checked in `_begin_step` — walking into a wall just turns the sprite to face it (no animation); stepping over an edge calls `World.step_to_neighbor` and snaps the sprite to the matching entry tile.

`OverworldScene` (`OPAQUE = True`) owns one of each plus a shared `TextBox`. Its frame work is the same shape every other scene uses:

- **`handle_event`** — when the text box has content, confirm advances it and other keys fall through silently (so a held direction does not queue steps that fire the instant the player closes a dialogue); when the box is idle, `is_menu` (`Tab` keyboard or `START` controller) pushes `MenuScene` onto the stack. Movement is **not** event-driven — it is read polled in `OverworldPlayer.update`.
- **`update`** — ticks the text box, then ticks the player only when the box is idle (so the player cannot walk while reading).
- **`render`** — scene-background → cell grid (one filled rect per tile, color keyed off the cell char via the local `_TILE_COLORS` table) → player → text box.

The scene serialises through `to_dict` / `from_dict` (capturing both `world.to_dict()` and `player.to_dict()`), but the live save-payload schema still writes only `party`; restoring the overworld scene on load is a Layer-0.5 follow-up that the deferred scene-stack-in-save task tracks.

The new `entities/` package is reserved for **pixel-space actors** — anything with a screen position, a facing, and an update loop of its own (NPCs, party followers, ship sprites). Battle-side `Combatant`s stay in [systems/battle.py](../systems/battle.py); the split is "moves around a screen" vs. "appears in a turn queue."

### 12a.1. Random encounters

[`OverworldScene`](../core/scenes/overworld_scene.py) tracks an `_last_seen_step_count` against `OverworldPlayer.step_count` (a monotonic counter the player increments at the end of each animated step). On every newly-completed step the scene increments a running `_quiet_steps` counter; once `EncounterSettings.MIN_QUIET_STEPS` is satisfied, each subsequent step is a Bernoulli trial against `EncounterSettings.RATE_PER_STEP`. On a hit, the scene pushes the existing `BattleScene` and resets `_quiet_steps` so the player gets a guaranteed quiet window after the fight.

The battle scene was already self-popping on `BattleEndedEvent`; the overworld didn't need any "on resume" hook to bring itself back. Because the overworld scene was never destroyed, the player's `(col, row)`, facing, and step counter all survive the fight unchanged.

The encounter rate, threshold, and the enemy pool stay global for Pass 2 — `BattleScene._build_enemies` rolls from its existing `_DEMO_ENEMY_IDS` tuple. Per-cell encounter tables (different enemy lists for beach vs. jungle vs. temple) land when cell content migrates from `core/overworld_cells.py` to `data/cells/*.json`.

## 12b. Persistent state from battle to overworld

Two pieces of state need to survive a battle and roll back up through the save file: per-member current HP, and the shared potion stack. Both were previously battle-local — combatants spawned at full HP, potions reset to `BattleSettings.STARTING_POTIONS` every fight — so damage and potion use silently evaporated the moment the player won.

The fix is split across three modules:

- [`PartyMember`](../systems/party.py) gained a `current_hp: int` field, initialised from `stats["hp"]` (the member's max). It serialises in `to_dict` / `from_dict`; loads of older saves without the field default to max, so legacy save files keep loading at full health.
- [`Combatant`](../systems/battle.py) gained a `max_hp` constructor argument that defaults to `hp` for the common case (enemies always spawn at full health, so `hp == max_hp` and no caller needs to pass it). [`combatant_from_party_member`](../core/factories.py) uses `member.current_hp` for the combatant's starting HP and `stats["hp"]` for the max, so a damaged member walks into the battle already injured. A floor at 1 protects against a 0-HP-saved member spawning dead on contact (proper KO handling is a Layer-1 deliverable).
- [`BattleScene`](../core/scenes/battle_scene.py) reads `Party.inventory.get("potion", BattleSettings.STARTING_POTIONS)` at construction (so a brand-new game or an old save without the inventory key still gets the default starter stack) and runs `_sync_party_state_back` the instant `BattleEndedEvent` arrives — that method writes each combatant's HP back to its `PartyMember` (clamped to max) and writes the surviving potion count back to `Party.inventory["potion"]`.

Once a battle has run, `Party.inventory["potion"]` is authoritative for every subsequent fight; the `BattleSettings.STARTING_POTIONS` constant only matters for the new-game seed in [`build_default_party`](../core/scenes/title_scene.py) and as a one-time migration fallback for old saves.

## 13. UI

- [ui/text_renderer.py](../ui/text_renderer.py) — the **only** module that draws text. Word-wraps to a max width, caches fonts per (path, size), enforces ALL CAPS at the renderer so gameplay code can pass any case.
- [ui/text_box.py](../ui/text_box.py) — bordered JRPG dialogue widget. Queues lines, paginates with a typewriter effect at `UISettings.TYPEWRITER_CHARS_PER_SECOND`, advances on confirm.
- [ui/menu.py](../ui/menu.py) — cursor-driven vertical list with a blinking `>` cursor; skips disabled rows; supports an `on_cancel` callback.
- [ui/battle_view.py](../ui/battle_view.py) — consumes battle events and phrases them into the text box. Layer 1 will swap in richer phrasing per character/element; Layer 3+ will add sprite overlays alongside it without changing the event stream.
- [ui/input_map.py](../ui/input_map.py) — translates raw pygame events into logical UI actions (`is_confirm`, `is_cancel`, `is_up`, `is_down`).

## 14. Source tree (current)

```
assets/
  font/Pixeled.ttf              Pixel font for retro UI text.
  graphics/effects/tv.png       CRT overlay texture.
  graphics/                     Layer-1 sprite assets land under here (player/, tiles/,
                                npcs/, icons/, portraits/) once Pass 3 / Pass 5 ship.
  audio/sound/                  SFX (waves loop + menu cues today; footsteps + bumps later).
  audio/music/                  Music tracks (none yet — Layer 4).
core/
  elements.py                   Element enum + damage table (single source of truth).
  events.py                     Typed event records (battle + dialogue).
  scene.py                      Scene base class + SceneStack.
  save.py                       Versioned JSON save/load + migrations.
  data_loader.py                JSON content-pack loader.
  factories.py                  JSON-dict -> runtime-object factories.
  world.py                      Overworld cell pointer + is_wall + step_to_neighbor.
  overworld_cells.py            Static cell grids + WORLD_LAYOUT (Pass-1 placeholders).
  scenes/
    title_scene.py              Title screen.
    test_world_scene.py         Layer-0 placeholder room (in-tree reference; unreachable).
    overworld_scene.py          Grid-stepped exploration scene + encounter rolls.
    battle_scene.py             Hosts Battle + BattleView; syncs HP and potions back at end.
    menu_scene.py               Pause overlay.
    party_scene.py              Read-only party status (name, HP/max HP, elements).
    inventory_scene.py          Read-only inventory list.
entities/
  overworld_player.py           Grid-stepped player with pixel-interpolation animation.
systems/
  audio_manager.py              Data-driven music + SFX dispatcher.
  party.py                      Serialisable party state.
  battle.py                     Turn-queue battle simulation.
  dialogue.py                   Dialogue tree runner.
ui/
  text_renderer.py              All text drawing; ALL-CAPS enforced here.
  text_box.py                   Bordered dialogue widget.
  menu.py                       Cursor-driven vertical menu.
  battle_view.py                Battle event → text box bridge.
  input_map.py                  Raw event → logical UI action helpers.
utils/
  graphics.py                   Pure pygame helpers (vertical-gradient surface builder).
  backgrounds.py                Scene-background template renderer + gradient cache.
  split_loredump.py             One-shot tool: split LOREDUMP.html into per-article HTML stubs.
  lore_to_markdown.py           One-shot tool: convert per-article HTML stubs to clean Markdown.
data/
  characters/                   One JSON per party member.
  abilities/                    One JSON per ability.
  enemies/                      One JSON per enemy.
  dungeons/                     One JSON per region.
  dialogue/                     One JSON per dialogue tree.
  README.md                     Schema notes for the content packs.
saves/                          Player save files (gitignored).
crt.py                          CRT post-processing overlay.
main.py                         Entry point + GameManager.
settings.py                     All tunables.
docs/
  ARCHITECTURE.md               This file.
  CHANGELOG.md                  Append-only history.
  CONTRIBUTING.md               "I want to add X — what files do I touch?" lookup table.
  LOREDUMP.html                 Original World Anvil export (preserved verbatim).
  ROADMAP.md                    The six-layer plan (re-framed 2026-05-11; Layer 1 is now the playable cartridge).
  TESTING.md                    Manual smoke checks.
  TODO.md                       Current actionable tasks.
  TOOLING.md                    Engine + editor + AI choice; pygame vs Godot/GameMaker/RPG Maker tradeoffs.
  VISION.md                     The artistic North Star.
  design/
    oneshot.md                  The Layer-1 plan: stats / CTB / dungeon / shop / icons / window style.
    overworld.md                Pass-1 / Pass-2 design for the tile-based overworld.
    patterns-from-predecessors.md
                                Code patterns lifted from Dungeon Digger / Adventure (so neither
                                repo needs to be referenced again — sprite loading, walk animation,
                                NPC pattern, door pattern, color_with_alpha, tutorial cards, etc).
  lore/
    INDEX.md                    TOC for all 114 lore articles.
    <category>/<slug>.md        One file per article.
.github/copilot-instructions.md Editor rules.
```

## 15. Extension points

When you add gameplay, the recommended seams are:

- Push a new `Scene` subclass onto the stack instead of branching inside `GameManager`.
- Emit events from gameplay code; consume them in views. Never have gameplay code reach into a renderer directly.
- Add new content by dropping JSON files into `data/`. Code changes only when a new *kind* of content is introduced.
- Add new constants to `settings.py`. Document the units and effect inline.
