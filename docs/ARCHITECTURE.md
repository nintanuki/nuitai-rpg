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

`GameManager` owns the screen, the clock, the cached joystick list, the fullscreen flag, and the `AudioManager`. Once Layer 0 lands, it will also own the **scene stack**. Everything else — gameplay, UI, animations, persistence, content data — lives in modules under `core/`, `systems/`, `ui/`, or `utils/` and is coordinated through `GameManager`.

## 2. Frame loop

`GameManager.run()` per frame:

1. `quit_combo_pressed()` — early-exit on the held quit chord.
2. `_process_events()` — drain pygame's event queue and dispatch to typed handlers (which forward to the top scene once Layer 0 lands).
3. `_update_world()` — currently a no-op stub; will forward to `scene_stack.top.update()`.
4. `_render_frame()` — `screen.fill(BG_COLOR)`, then `scene_stack.render_all(screen)`, then the CRT overlay (windowed only).
5. `pygame.display.flip()` and `clock.tick(FPS)`.

## 3. Input

Events are routed by type:

- `KEYDOWN` → `_handle_keydown`. Default: `Esc` quits, `F11` toggles fullscreen.
- `JOYBUTTONDOWN` → `_handle_joybuttondown`. Default: quit-chord check + `BACK` toggles fullscreen.
- `JOYHATMOTION` → `_handle_joyhatmotion` (stub).
- `JOYAXISMOTION` → `_handle_joyaxismotion` (stub).

Joysticks are cached at startup in `setup_controllers()`. Hot-plug requires re-running it.

The quit chord is `InputSettings.JOY_BUTTON_QUIT_COMBO`. When **all** of those buttons are held on **any** controller, the game closes.

Once the scene stack lands, all non-global input (anything that isn't fullscreen-toggle or quit-chord) is forwarded to `scene_stack.top.handle_event(event)`.

## 4. Audio

[systems/audio_manager.py](../systems/audio_manager.py) is a data-driven sound and music dispatcher. It reads `AudioSettings.SOUND_EFFECTS` (logical name → path) on construction, loads each sound, and exposes a single `play(name)` entry point. Music is rotated through `AudioSettings.MUSIC_TRACKS`, avoiding back-to-back repeats, and managed via `play_random_music`, `pause_music`, `resume_music`, and `stop_music`. `toggle_mute` flips `AudioSettings.MUTE` globally — mute is honored at the call site, so toggles are instant and reversible.

`GameManager.__init__` initialises the mixer with `_initialize_audio_mixer()` **before** constructing `AudioManager`. Failure to load a sound, music track, or even the mixer itself is non-fatal — the game keeps running silently.

## 5. CRT overlay

[crt.py](../crt.py) loads `AssetPaths.TV`, scales it to the screen, and on each `draw()` blits a fresh copy with a randomized alpha and per-row scanlines. `GameManager._render_frame` calls it only when not in fullscreen so it does not double-up on a real CRT cabinet.

## 6. Settings

[settings.py](../settings.py) is the single source of truth for tunables.

| Class            | Purpose                                                                       |
| ---------------- | ----------------------------------------------------------------------------- |
| `ColorSettings`  | Named colors + semantic aliases (`BG_COLOR`, `OVERLAY_BACKGROUND`).           |
| `ScreenSettings` | Resolution, FPS, title, CRT alpha range and scanline height.                  |
| `InputSettings`  | Controller button/axis indices + quit combo + analog threshold.               |
| `FontSettings`   | Font file paths.                                                              |
| `AudioSettings`  | Mute toggles, music + SFX volume, `SOUND_EFFECTS` and `MUSIC_TRACKS` registry. |
| `AssetPaths`     | Asset file paths for non-font assets.                                         |
| `DebugSettings`  | Debug-only toggles.                                                           |

**No magic numbers anywhere outside this file.** Future settings classes (planned for Layer 0): `SaveSettings`, `UISettings`.

## 7. Source tree (current)

```
assets/
  font/Pixeled.ttf              Pixel font for retro UI text.
  graphics/effects/tv.png       CRT overlay texture.
core/
  __init__.py                   (currently empty package)
systems/
  audio_manager.py              Data-driven music + SFX dispatcher.
ui/
  __init__.py                   (currently empty package)
utils/
  __init__.py                   (currently empty package)
  split_loredump.py             One-shot tool: split LOREDUMP.html into per-article HTML stubs.
  lore_to_markdown.py           One-shot tool: convert per-article HTML stubs to clean Markdown.
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
    <category>/<slug>.html      One file per article.
.github/copilot-instructions.md Editor rules.
```

## 8. Planned subsystems (Layer 0 architectural seams)

The following directories and modules are **planned** for Layer 0; they are documented here so contributors understand the seams the engine is being built around. See [TODO.md](TODO.md) for the actionable task list.

### `core/elements.py` — single source of truth for the element system

An `Element` enum (`AHI`, `LAU`, `WAI`, `RA`, `AKU`, `MANA`) and a strength/weakness lookup table:

```
Ahi  → burns      → Lau
Lau  → drinks     → Wai
Wai  → quenches   → Ahi
Ra   → purifies   → Aku
Aku  → corrupts   → Mana
Mana → transcends → Ra
```

Every battle damage calculation, every status-effect interaction, and every piece of element-flavored content reads from this module. It is **not duplicated** in JSON content packs; content packs reference element names by string and `data_loader` resolves them to enum members.

### `core/scene.py` — scene stack

`Scene` is a base class with:

```
class Scene:
    def handle_event(self, event): ...
    def update(self, dt): ...
    def render(self, surface): ...
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Scene": ...
```

`SceneStack` supports `push(scene)`, `pop()`, `replace(scene)`, and `top`. Only `top` receives input and `update`. All scenes in the stack render bottom-up (so a menu can layer over the world it was opened from). The stack is serializable.

### `core/events.py` — typed event records

Frozen dataclasses describe everything the game emits and consumes:

- Battle: `TurnStartEvent`, `AttackEvent`, `AbilityUsedEvent`, `DamageEvent`, `HealEvent`, `StatusAppliedEvent`, `StatusRemovedEvent`, `BattleEndedEvent`.
- World: `DialogueLineEvent`, `MenuOpenedEvent`, `ItemPickedUpEvent`, `FlagSetEvent`.

Game logic produces events; views consume them. Across the five layers, only the views change.

### `core/save.py` — persistence

JSON saves with a top-level `version: int`. On load, `migrate(data)` walks any older save up to the current schema. Saves capture the entire scene stack (each scene calls `to_dict()`) plus the party state, world flags, and RNG seed.

### `core/data_loader.py` — content packs

Reads JSON from `data/characters/`, `data/abilities/`, `data/enemies/`, `data/dungeons/`, `data/dialogue/`. Validates structure on load with clear error messages. Returns plain dataclasses or dicts that gameplay code consumes.

### `systems/battle.py`, `systems/party.py`, `systems/dialogue.py` — gameplay systems

`battle.Battle` owns a turn queue, applies abilities, computes damage using `core/elements.py`, and emits events. **It does not draw anything.**

`party.Party` is the serializable state of the player's roster: members, inventory, gold, story flags, RNG seed. It is the canonical source for save data.

`dialogue.DialogueRunner` walks a JSON dialogue tree and emits `DialogueLineEvent`s.

### `ui/text_renderer.py`, `ui/text_box.py`, `ui/menu.py`, `ui/battle_view.py` — rendering

`text_renderer` is the **only** module that draws text. Word-wraps to a `pygame.Rect`, supports a typewriter effect, enforces ALL CAPS at the renderer (so gameplay code can pass any case).

`text_box` is the bordered JRPG dialogue widget. Pages overflow text, advances on a button press.

`menu` is the cursor-driven vertical-list widget used by every menu in the game.

`battle_view` consumes battle events from `systems/battle.py` and pumps them into the text box. Layer 1: pure text. Layer 3: text + sprites. Layer 4: text + animated sprites + popups. The events themselves do not change.

### `data/` — content packs

```
data/
  characters/*.json    Stats, starting equipment, abilities, element pair.
  abilities/*.json     Cost, target, effects, element, animation tag.
  enemies/*.json       Stats, ability list, drops, element.
  dungeons/*.json      Rooms, encounter tables, treasure, scripted events.
  dialogue/*.json      Dialogue trees keyed by id.
```

JSON-first because it is hand-editable, diffable, and trivially mod-friendly.

### `saves/` — player data

`__file__`-relative directory. Gitignored. One file per save slot. Each file is a JSON document stamped with a schema version.

## 9. Extension points

When you add gameplay, the recommended seams are:

- Push a new `Scene` subclass onto the stack instead of branching inside `GameManager`.
- Emit events from gameplay code; consume them in views. Never have gameplay code reach into a renderer directly.
- Add new content by dropping JSON files into `data/`. Code changes only when a new *kind* of content is introduced.
- Add new constants to `settings.py`. Document the units and effect inline.
