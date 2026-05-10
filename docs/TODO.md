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

## Cross-cutting / always-on

- [ ] Append a [docs/CHANGELOG.md](CHANGELOG.md) entry for every meaningful change. (House rule.)
- [ ] Update [docs/ARCHITECTURE.md](ARCHITECTURE.md) when a system's shape changes.
- [ ] Update this file as items complete (`[x]`, do not delete).
- [ ] Run [docs/TESTING.md](TESTING.md) smoke checks before declaring a layer done.
- [x] Convert split per-article HTML files into clean markdown (Pass 2 of the docs migration). See `utils/lore_to_markdown.py`.
