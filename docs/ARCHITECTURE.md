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

After global handling, every event is forwarded to the active scene through `scene_stack.handle_event(event)`. Scenes use [ui/input_map.py](../ui/input_map.py) helpers (`is_confirm`, `is_cancel`, `is_up`, `is_down`, ...) to translate raw events into logical UI actions, so each scene does not reimplement the keyboard + controller routing.

Joysticks are cached at startup in `setup_controllers()`. Hot-plug requires re-running it. The quit chord is `InputSettings.JOY_BUTTON_QUIT_COMBO`.

## 4. Audio

[systems/audio_manager.py](../systems/audio_manager.py) is a data-driven sound and music dispatcher. It reads `AudioSettings.SOUND_EFFECTS` (logical name → path) on construction, loads each sound, and exposes a single `play(name)` entry point. Music is rotated through `AudioSettings.MUSIC_TRACKS`, avoiding back-to-back repeats, and managed via `play_random_music`, `pause_music`, `resume_music`, and `stop_music`. `toggle_mute` flips `AudioSettings.MUTE` globally — mute is honored at the call site, so toggles are instant and reversible.

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
| `AudioSettings`  | Mute toggles, music + SFX volume, `SOUND_EFFECTS` and `MUSIC_TRACKS` registry.   |
| `AssetPaths`     | Asset file paths for non-font assets.                                            |
| `DebugSettings`  | Debug-only toggles.                                                              |
| `SaveSettings`   | `SAVES_DIR` (file-relative), `MAX_SAVE_SLOTS`, `AUTOSAVE_SLOT_ID`.                |
| `UISettings`     | Text-box geometry, typewriter speed, menu cursor blink, menu spacing/alignment, title-screen layout anchors. |

**No magic numbers anywhere outside this file.**

## 7. Scenes

A `Scene` ([core/scene.py](../core/scene.py)) is one screenful of game state — title screen, room, battle, pause menu. Scenes are kept on a stack so transient overlays (pause, dialogue, battle) push on top of the gameplay beneath them and pop to return.

- The top scene receives input and updates each frame.
- Render walks bottom-up, starting at the deepest opaque scene, so a translucent overlay (`OPAQUE = False`) leaves the world below visible.
- Every concrete scene exposes `to_dict` / `from_dict` so the save system can rebuild the stack across sessions.

Layer-0 scenes:

- [core/scenes/title_scene.py](../core/scenes/title_scene.py) — NEW GAME / CONTINUE / LOAD GAME / QUIT. CONTINUE and LOAD GAME are disabled when no save exists.
- [core/scenes/test_world_scene.py](../core/scenes/test_world_scene.py) — placeholder room with TALK / FIGHT / SAVE / QUIT TO TITLE commands.
- [core/scenes/battle_scene.py](../core/scenes/battle_scene.py) — hosts a `Battle` and a `BattleView`; resolves to victory, defeat, or flee.
- [core/scenes/menu_scene.py](../core/scenes/menu_scene.py) — translucent pause overlay (`OPAQUE = False`) with party / inventory / save / settings / quit-to-title rows.

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

`damage_multiplier(attacker, defender)` returns `ADVANTAGE_MULTIPLIER`, `DISADVANTAGE_MULTIPLIER`, or `NEUTRAL_MULTIPLIER`. Every battle damage calculation, status-effect interaction, and element-flavored content reads from this module. It is **not duplicated** anywhere — JSON content packs reference element names by string and `data_loader` resolves them.

## 9. Events — typed records

[core/events.py](../core/events.py) defines frozen dataclasses for what gameplay produces and views consume:

- Battle: `TurnStartEvent`, `AttackEvent`, `DamageEvent`, `StatusAppliedEvent`, `CombatantDefeatedEvent`, `BattleEndedEvent`.
- Dialogue: `DialogueLineEvent`, `DialogueEndedEvent`.

Game logic produces events; views consume them. Across the five layers, only the views change. New event types are added freely; views ignore unknown ones, so producers can extend the stream without breaking older views.

## 10. Persistence

[core/save.py](../core/save.py) writes JSON files at `SaveSettings.SAVES_DIR/slot_<id>.json`. Each file has a `version` stamp and a `data` payload. On load, `migrate(record)` walks any older save up to `SAVE_SCHEMA_VERSION`. Future versions raise `ValueError` rather than silently corrupting state.

The Layer-0 payload is just the party (`party.to_dict()`); future layers add scene-stack snapshots, world flags, and RNG seed.

## 11. Content loader

[core/data_loader.py](../core/data_loader.py) reads JSON from `data/<kind>/*.json`, requires a top-level `id` field on each file, and returns the contents indexed by id. Caches per-kind. Missing pack directories return an empty dict so the engine can boot without content. `GameManager` owns one shared `DataLoader` instance (`gm.data`); scenes reach into it rather than constructing their own.

The seam from JSON dict to runtime gameplay object lives in [core/factories.py](../core/factories.py): `party_member_from_data`, `combatant_from_party_member`, `combatant_from_enemy_data`. Every "build X from data" call site routes through this module so the JSON-to-runtime mapping is never duplicated.

## 12. Gameplay systems

- [systems/party.py](../systems/party.py) — `PartyMember` and `Party`: members, inventory, gold, story flags. Fully serialisable; the canonical source for save data.
- [systems/battle.py](../systems/battle.py) — `Combatant` and `Battle`: turn-queue logic. Pure data; emits events; never draws.
- [systems/dialogue.py](../systems/dialogue.py) — `DialogueRunner`: walks a JSON dialogue tree and emits `DialogueLineEvent`s, then `DialogueEndedEvent`.

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
core/
  elements.py                   Element enum + damage table (single source of truth).
  events.py                     Typed event records (battle + dialogue).
  scene.py                      Scene base class + SceneStack.
  save.py                       Versioned JSON save/load + migrations.
  data_loader.py                JSON content-pack loader.
  factories.py                  JSON-dict -> runtime-object factories.
  scenes/
    title_scene.py              Title screen.
    test_world_scene.py         Layer-0 placeholder room.
    battle_scene.py             Hosts Battle + BattleView.
    menu_scene.py               Pause overlay.
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
  LOREDUMP.html                 Original World Anvil export (preserved verbatim).
  ROADMAP.md                    The six-layer plan.
  TESTING.md                    Manual smoke checks.
  TODO.md                       Current actionable tasks.
  VISION.md                     The artistic North Star.
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
