# Nuitai RPG — TODO

> The current layer's actionable tasks. Code, writing, and art tasks all belong here as long as they are concrete and checkable. Aspirational items belong in [ROADMAP.md](ROADMAP.md); core artistic intent belongs in [VISION.md](VISION.md).

> **House rules:** Mark items `[x]` when complete; do not delete them. Move stale items to the bottom of their section if they are no longer current. New layers get a new section appended below; do not erase prior layers' history.

---

## Layer 0 — Engine spike (current)

### Code: foundations

- [x] Add a top-level `data/` directory with subfolders for `characters/`, `abilities/`, `enemies/`, `dungeons/`, `dialogue/`. Add a `README.md` inside `data/` that describes the schema for each.
- [x] Add a top-level `saves/` directory and add it to `.gitignore`.
- [x] Create `core/elements.py` with an `Element` enum (`AHI`, `LAU`, `WAI`, `RA`, `AKU`, `MANA`) and an element strength/weakness lookup. **Single source of truth** — no other module duplicates this table.
- [x] Create `core/events.py` with dataclasses for battle and world events (`AttackEvent`, `StatusAppliedEvent`, `TurnStartEvent`, `BattleEndedEvent`, `DialogueLineEvent`, etc.).
- [x] Create `core/scene.py`: `Scene` base class (with `handle_event`, `update`, `render`, `to_dict`, `from_dict`) and `SceneStack` (push / pop / replace, top-of-stack receives input/render).
- [x] Wire `SceneStack` into `GameManager`. Replace `_update_world` and `_render_frame`'s placeholder bodies with calls into the stack's top scene.
- [x] Create `core/save.py`: JSON save/load with a `SAVE_SCHEMA_VERSION` constant and a `migrate(data)` hook that takes a dict and returns the current-version dict.
- [x] Create `core/data_loader.py`: load JSON content packs from `data/`, with helpful errors when a pack is malformed.

### Code: rendering & UI

- [x] Create `ui/text_renderer.py`: word-wrap, optional typewriter effect, ALL-CAPS enforcement at the renderer (so gameplay code can be lowercase). One central place for all text drawing.
- [x] Create `ui/text_box.py`: bordered JRPG-style dialogue box, advance-on-button, auto-paginating, optional speaker-name tag.
- [x] Create `ui/menu.py`: cursor-driven vertical menu, controller + keyboard, scroll if items exceed visible rows.
- [x] Create `ui/battle_view.py`: consumes a stream of `core/events.py` battle events and renders them via the text box.

### Code: gameplay systems

- [x] Create `systems/party.py`: party state (members, inventory, gold, story flags). Serializable.
- [x] Create `systems/battle.py`: turn-queue logic. Pure data; emits events; does not draw anything.
- [x] Create `systems/dialogue.py`: dialogue tree runner. Reads dialogue JSON; emits `DialogueLineEvent`s for the text box to consume.

### Code: scenes

- [x] Create `core/scenes/title_scene.py`: NEW GAME / CONTINUE / QUIT. Stack-pushes the appropriate next scene.
- [x] Create `core/scenes/test_world_scene.py`: a single placeholder room with a single placeholder NPC the player can talk to. Pushes a `BattleScene` when the player picks a "fight" option from a menu.
- [x] Create `core/scenes/battle_scene.py`: hosts a `Battle` and a `BattleView`. Resolves to victory/defeat/flee.
- [x] Create `core/scenes/menu_scene.py`: party status, inventory, save, settings, quit-to-title.

### Settings

- [x] Add `SaveSettings` to `settings.py`: `SAVES_DIR` (`__file__`-relative), `MAX_SAVE_SLOTS`, autosave-slot id, etc. **No magic numbers in `core/save.py`.**
- [x] Add `UISettings` to `settings.py`: text-box border thickness, padding, typewriter speed (chars-per-second), menu cursor blink rate. Document units in comments.

### Definition-of-done check

- [x] [docs/TESTING.md](TESTING.md) updated with Layer-0 smoke checks: title screen flow, save / quit / continue round-trip, fake battle resolves, in-window text only (no console output).
- [x] [docs/ARCHITECTURE.md](ARCHITECTURE.md) reflects the actual subsystems as built (not as planned).
- [x] [docs/CHANGELOG.md](CHANGELOG.md) has entries for every Layer-0 system as it lands.

---

## Layer 1 — Vertical-slice text demo (next)

> Listed at this level of detail to help shape Layer 0 — the engine seams must support these. Tasks here are not yet active; do not pick them up until Layer 0 is signed off.

### Writing (start early — runs in parallel with Layer 0 code)

- [ ] First-pass opening cutscene script (Kailo on Māra Iti; meeting Hina; Tawiri's arrival). ~2 pages.
- [ ] Dungeon flavor text: per-room descriptions, ambient lines, encounter intros.
- [ ] Boss intro and victory/defeat lines.
- [ ] Town NPC dialogue (~5 NPCs in the starting village, including Maika as recruitable-later NPC).
- [ ] Ending text.

### Content data

- [ ] `data/characters/kailo.json`, `hina.json`, `tawiri.json`. Stats, starting equipment, starting abilities. Maika as an NPC-only character at this layer.
- [ ] `data/abilities/*.json`: at least 4 abilities per character covering both elements. At least one boss-relevant interaction (e.g. an Aku ability the boss uses; an Ra ability Hina has that purifies it).
- [ ] `data/enemies/*.json`: 4–6 enemy types for the demo dungeon plus the boss.
- [ ] `data/dungeons/demo_dungeon.json`: room layout, encounter tables, treasure, boss room.
- [ ] `data/dialogue/*.json`: opening cutscene, town NPCs, dungeon flavor, boss, ending.

### Placeholder art

- [ ] Source free-licensed portrait placeholders for Kailo, Hina, Tawiri (and Maika as NPC). Drop into `assets/graphics/portraits/`. Credit in [README.md](../README.md).

### Definition-of-done check

- [ ] A clean playthrough exists from title screen to ending text.
- [ ] Save / load works from anywhere outside of battle.
- [ ] Element strength/weakness has a *felt* effect on combat speed.
- [ ] No `print()` calls in any production code path.

---

## Layer 0.5 — Scaffolding deferrals

> Identified at the close of Layer 0. None block Layer 1 from starting; each removes friction for weaker contributors and protects against regressions. Promote into the active layer when picked up.

### Engine seams

- [ ] Persist the **scene stack** in saves, not just the party. Each `Scene` already has `to_dict` / `from_dict`; have [core/save.py](../core/save.py) walk `gm.scene_stack` and rebuild it on load. Bump `SAVE_SCHEMA_VERSION` and ship a `migrate()` step.
- [ ] Reserve a `statuses` field on [`Combatant`](../systems/battle.py) and add a stub `core/status.py` registry so Layer 2's poison/burn/drench/blind/weaken/silence pass does not have to retrofit the data shape.

### Tooling

- [ ] Add `tests/smoke_test.py` driven by `SDL_VIDEODRIVER=dummy` + `SDL_AUDIODRIVER=dummy`. Boot, advance N frames, push the NEW GAME → FIGHT → SAVE → QUIT TO TITLE → CONTINUE round-trip, assert the saved party reloads. One file, no test framework — runnable as `python tests/smoke_test.py`.
- [x] Delete the stray `.gitignore copy` at the repo root.

### Writing pipeline

- [ ] Create `docs/writing/` with templates for: cutscene script, NPC dialogue, room flavor, boss intro/victory/defeat, and ending text. One Markdown file per template, each showing the JSON shape it lowers into under `data/dialogue/`.

---

## Layer 3 — Overworld (parallel track, accelerated)

> The tile-and-sprite overworld is officially a Layer-3 deliverable, but it is being kicked off early so it can advance in parallel with the Layer-1 text demo / battle polish. The point is to build the bones inside the existing scene-stack engine; Layer-3 *content* (real tilesets, real sprites, ship scenes) still waits its turn.
>
> Full design: [docs/design/overworld.md](design/overworld.md). Read it before picking up any task here.

### Pass 1 — scaffolding (no playable demo yet)

- [x] Add `GridSettings`, `OverworldSettings`, `OverworldPlayerSettings` to [settings.py](../settings.py). Document units in comments.
- [x] Add overworld tile colors to `ColorSettings` (`OVERWORLD_FLOOR`, `OVERWORLD_WALL`, `OVERWORLD_WATER`, `OVERWORLD_SAND`).
- [x] Add `is_left` and `is_right` helpers to [ui/input_map.py](../ui/input_map.py), mirroring `is_up` / `is_down`. (Also added `is_menu` for the Tab / START hotkey and `read_held_direction` for polled movement input.)
- [x] Create `core/world.py`: `World` class with `current_pos`, `is_wall`, `step_to_neighbor`, lifted in shape from Adventure's `core/world.py`.
- [x] Create `core/overworld_cells.py`: two test cells (`beach_west`, `beach_east`) with matching openings on their shared edge, plus `WORLD_LAYOUT` and `START_CELL_POS`. (Includes an import-time `_validate_cells()` that fails loudly on misshaped grids.)
- [x] Create `entities/overworld_player.py` (new package): grid-stepped player with pixel interpolation, facing direction, buffered-input queue, axis-separated `is_wall` checks, edge-crossing → `World.step_to_neighbor`. (Buffered "queue" landed as polled held-input instead — see [docs/design/overworld.md](design/overworld.md) §4 follow-up; same end behavior, no global `pygame.key.set_repeat` needed.)
- [x] Create `core/scenes/overworld_scene.py`: opaque scene that owns world + player + text box; routes input through `input_map`; pushes `MenuScene` on Start.
- [x] Add `BackgroundSettings.SCENE_BACKGROUNDS["OverworldScene"]` template.
- [x] Re-wire `TitleScene._new_game` and `_continue` to `replace(OverworldScene(...))`. Leave `TestWorldScene` in the tree for reference.
- [x] Extend `to_dict` / `from_dict` round-trip so the overworld scene is fully saveable. (World + player both serialise; full scene-stack persistence remains a Layer-0.5 deferral — the save payload still writes only `party` today.)
- [x] Update [docs/ARCHITECTURE.md](ARCHITECTURE.md) with current-systems sections for `World`, `OverworldPlayer`, `OverworldScene` once they land.
- [x] Add overworld smoke checks to [docs/TESTING.md](TESTING.md).
- [x] Append a [docs/CHANGELOG.md](CHANGELOG.md) entry per file touched.
- [ ] **Run the Pass-1 manual smoke checks in [TESTING.md](TESTING.md) §22–30 and sign off.** (Pending Frankie's machine — sandbox has no pygame/display.)

### Pass 2 — playable demo

- [ ] Author two or three real cells with placeholder tile art chosen for Nuitai's tropical-island setting (no Dungeon Digger dungeon assets).
- [ ] Source a placeholder player sprite set (4 facings; static, no walk cycle yet). Credit in README.
- [ ] Add a static `interactables` dict to cell data and a "tile in front of me" interaction dispatch in `OverworldScene`.
- [ ] Wire one NPC tile through `DialogueRunner` + `TextBox` (re-use the path `TestWorldScene._talk` already exercises).
- [ ] Wire one sign tile (push text onto the box).
- [ ] Wire one warp tile (cross-cell teleport with sprite snap).
- [x] Step-counted random encounter system: rate + min-quiet-steps; push real `BattleScene` on hit; reset counter on battle resolution. (Global rate for now via `EncounterSettings`; per-cell tables are a follow-up once cell data migrates to JSON.)
- [x] Persist per-member current HP across battles and saves. Added `PartyMember.current_hp`, separated `Combatant.max_hp` from initial `hp`, wrote HP back at `BattleEndedEvent`, taught `Party.from_dict` to default to max when the field is missing for backward-compat.
- [x] Migrate potions from a battle-local pool to `Party.inventory["potion"]`. New games seed 5; battles read at construction and write the survivor count back at end.
- [x] Enable the PARTY menu row → new `PartyScene` showing each member's name + HP/max HP + element pair.
- [x] Enable the INVENTORY menu row → new `InventoryScene` listing inventory rows.
- [ ] Import `sfx_movement_footstepsloop4_slow.ogg` and `wall_bump_sound_effect.ogg` from Dungeon Digger; register in `AudioSettings.SOUND_EFFECTS`; play on step-complete and bump. (Footstep loop is wrong shape for grid-stepped movement — Pass-2 footstep audio probably wants a discrete tap; revisit when sourcing audio.)
- [ ] Verify save/load mid-cell-transition and mid-dialogue resume cleanly.
- [ ] Update CHANGELOG / ARCHITECTURE / TESTING / TODO marks for the remaining `[ ]` items.

### Open design questions (revisit when needed)

- [ ] Decide if/when to migrate cells from `core/overworld_cells.py` module to `data/cells/*.json` via `DataLoader`.
- [ ] Decide if `TextBox` should grow a `render_empty_frame` option for always-visible message-box chrome.
- [ ] Decide what keyboard key opens the menu (probably `Tab` or `Enter` — `Enter` collides with confirm).

---

## Cross-cutting / always-on

- [ ] Append a [docs/CHANGELOG.md](CHANGELOG.md) entry for every meaningful change. (House rule.)
- [ ] Update [docs/ARCHITECTURE.md](ARCHITECTURE.md) when a system's shape changes.
- [ ] Update this file as items complete (`[x]`, do not delete).
- [ ] Run [docs/TESTING.md](TESTING.md) smoke checks before declaring a layer done.
- [x] Convert split per-article HTML files into clean markdown (Pass 2 of the docs migration). See `utils/lore_to_markdown.py`.
