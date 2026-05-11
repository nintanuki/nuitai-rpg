# Nuitai RPG — TODO

> The current layer's actionable tasks. Code, writing, and art tasks all belong here as long as they are concrete and checkable. Aspirational items belong in [ROADMAP.md](ROADMAP.md); core artistic intent belongs in [VISION.md](VISION.md).

> **House rules:** Mark items `[x]` when complete; do not delete them. Move stale items to the bottom of their section if they are no longer current. New layers get a new section appended below; do not erase prior layers' history.

---

## Layer 0 — Engine spike — **shipped**

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

## Layer 1 — The one-shot (active)

> The playable cartridge milestone — full design at [docs/design/oneshot.md](design/oneshot.md). Organised by pass; passes ship independently testable. Asset patterns lifted from the predecessor projects are captured at [docs/design/patterns-from-predecessors.md](design/patterns-from-predecessors.md) so neither repo needs to be referenced again.

### Pass 3 — Asset bones

- [ ] Drop the Dungeon Digger sprite files Frankie's bringing in: player (4 facings), tiles (walkable + walls), doors (open + closed), NPC variants. Skip monsters — random encounters mean no overworld monster sprites needed.
- [ ] Add `assets/graphics/{player,tiles,npcs}/` directory tree.
- [ ] Add `AssetPaths` constants for player frames, door images, tile images. Use directory constants for the NPC pool.
- [ ] Replace `OverworldScene._TILE_COLORS` with a tile-sprite cache; swap the `pygame.draw.rect` call in `_render_cell` for a blit.
- [ ] Replace `OverworldPlayer.render` rect-fill with a sprite blit keyed off `self.facing`.
- [ ] Add the rounded-corner panel chrome to the overworld action window and to the existing `TextBox` (4-px corner radius, 2-px white border, black fill).
- [ ] Rebind `is_menu` from `START` to `Y` in [ui/input_map.py](../ui/input_map.py).
- [ ] Add a "GAME SAVED." line to the menu's `_save` (papercut from Pass 2's known-rough-edges list).
- [ ] Smoke: walk around, see real tiles, see the sprite face the way it last moved, see the bordered window chrome, save and see the feedback line.

### Pass 4 — Stats expansion + CTB scheduler

- [ ] Add `mp`, `def`, `matk`, `mdef`, `spd` fields across `PartyMember`, `Combatant`, JSON content packs (with backward-compat defaults for old saves).
- [ ] Add `current_mp` to `PartyMember` alongside `current_hp`.
- [ ] Replace `Battle._order` rotation with the next-turn-time scheduler (`combatant.next_turn_time` advanced by `action_cost / max(1, SPD)` after each act).
- [ ] Add `Battle.peek_upcoming(n)` returning the next n actors in scheduled order.
- [ ] Add the upcoming-turns strip to `BattleScene` rendering (~6–8 entries, each a small portrait or tinted block per the icon system).
- [ ] Update damage formula to use the new defense / magic stats per [oneshot.md](design/oneshot.md) §6.
- [ ] Bump party + enemy stats per [oneshot.md](design/oneshot.md) §11.

### Pass 5 — Icons + portraits + UI polish

- [ ] Create `assets/graphics/icons/` and `assets/graphics/portraits/`.
- [ ] Add `ui/icons.py` with a load-once cache + `draw_icon(surface, id, position)` helper.
- [ ] Placeholder element icons: render the element's first letter into a 16×16 surface with the element's accent color so the icon contract works on day one (replace with Aseprite art when it lands).
- [ ] Replace text element labels in `PartyScene` with element icons.
- [ ] Add portrait blits to `PartyScene` rows (placeholder: a colored 32×32 square with the member's name beside it).
- [ ] Add item icons to `InventoryScene` rows.
- [ ] Use icons in the battle command panel ability rows (in addition to or replacing the row color tint).

### Pass 6 — Inventory navigation + use-outside-battle

- [ ] `InventoryScene` grows a vertical cursor (uses `Menu` widget shape).
- [ ] Each item row has a description shown in a side panel when highlighted.
- [ ] Confirm on `potion` outside battle opens a target submenu listing party members; selecting one consumes the potion and heals the target by `BattleSettings.POTION_HEAL_AMOUNT`.
- [ ] Confirm on a non-usable item shows its description and nothing else.

### Pass 7 — Dungeon content + interactables

- [ ] Author the village hub cell + 4–6 dungeon cells in the cell representation. Decide whether to keep cells in `core/overworld_cells.py` or migrate to `data/cells/*.json` here (the migration was an open question from Pass 2).
- [ ] Add `interactables` to cell data; wire dispatch in `OverworldScene.handle_event` for: `npc`, `sign`, `warp`, `save`, `heal`, `shop`, `door`.
- [ ] Author 3–5 NPC dialogue trees in `data/dialogue/`.
- [ ] Build `ShopScene` + `data/shops/lehua_general_store.json` content.
- [ ] Author the boss enemy entry + boss room + ending screen scene.
- [ ] Add gold drops to enemy JSON + a small chunk to the boss.

### Pass 8 — Battle balance + writing pass

- [ ] Tune enemy stats against actual play. Adjust `EncounterSettings.RATE_PER_STEP` from the testing default (0.20) toward the production target (~0.08) once content is dense enough.
- [ ] Polish dialogue copy; replace the placeholder NPC names with named villagers.
- [ ] Smoke playthrough end-to-end; iterate. Any encounter that feels trivial gets a stat bump; any that feels punishing gets a stat trim.
- [ ] First-pass opening cutscene script (~1–2 pages).
- [ ] Boss intro / victory / defeat / ending text.

### Pass 9 — Layer-0.5 deferrals folded in

- [ ] Persist the **scene stack** in saves (so Continue resumes the player's exact tile, not just the party). Bump `SAVE_SCHEMA_VERSION` and ship a `migrate()` step.
- [ ] Promote `Combatant.statuses` (the field reserved at the close of Layer 0) and migrate the existing `aku_immune_turns` field into it; `curse`'s ATK/MATK debuff lives here too.

### Cross-cutting (Layer-1-wide)

- [ ] Each pass appends [docs/CHANGELOG.md](CHANGELOG.md) entries per file.
- [ ] [docs/ARCHITECTURE.md](ARCHITECTURE.md) gets a current-systems section for each shipped pass.
- [ ] [docs/TESTING.md](TESTING.md) grows new smoke checks for each shipped pass.
- [ ] Cross-checks against [docs/design/oneshot.md](design/oneshot.md) — if implementation diverges, update the design doc rather than letting the divergence drift.

### Definition of done

- [ ] A clean playthrough exists from title screen to ending text.
- [ ] Save / load works from anywhere outside of battle and restores the player's exact overworld tile (Pass 9).
- [ ] Element strength/weakness has a *felt* effect on combat.
- [ ] CTB turn order is visible and feels strategic.
- [ ] No `print()` calls in any production code path.
- [ ] Frankie can hand `python main.py` to a friend and they can play the one-shot from start to finish.

---

## Layer 0.5 — Scaffolding deferrals

> Identified at the close of Layer 0. **The two engine-seam items have been folded into Layer 1's pass plan** (scene-stack persistence is now Pass 9; the Combatant.statuses field is Pass 9 alongside it because Pass 4's `curse` ability needs status infrastructure). The tooling and writing-pipeline items remain ambient — pick them up when convenient.

### Tooling

- [ ] Add `tests/smoke_test.py` driven by `SDL_VIDEODRIVER=dummy` + `SDL_AUDIODRIVER=dummy`. Boot, advance N frames, push the NEW GAME → FIGHT → SAVE → QUIT TO TITLE → CONTINUE round-trip, assert the saved party reloads. One file, no test framework — runnable as `python tests/smoke_test.py`. Picking this up before Pass 4 would let CTB changes be regression-tested cheaply.
- [x] Delete the stray `.gitignore copy` at the repo root.

### Writing pipeline

- [ ] Create `docs/writing/` with templates for: cutscene script, NPC dialogue, room flavor, boss intro/victory/defeat, and ending text. One Markdown file per template, each showing the JSON shape it lowers into under `data/dialogue/`. Useful before Pass 7 / Pass 8 when the writing volume picks up.

---

## Layer 3 — Overworld (parallel track, accelerated) — **shipped**

> Historical record. Both passes shipped during the 2026-05-11 session. The overworld engine is the foundation Layer 1 builds on, and the original Layer 3 has been re-scoped to "the world map and the maelstrom" — see [ROADMAP.md](ROADMAP.md). Items that were still open at session-close have been absorbed into Layer 1 (Pass 3 for sprite art swap; Pass 7 for cells / NPCs / signs / warps; Pass 9 for mid-transition save). Annotated in line below.
>
> Full design: [docs/design/overworld.md](design/overworld.md). Read it before picking up Layer-1 Pass 3 (which builds on this engine).

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
- [x] **Run the Pass-1 manual smoke checks in [TESTING.md](TESTING.md) §22–30 and sign off.** (Verified by Frankie on Windows.)

### Pass 2 — playable demo

- [ ] Author two or three real cells with placeholder tile art chosen for Nuitai's tropical-island setting. *(Promoted to Layer 1 Pass 7 — village + 4–6 dungeon cells.)*
- [ ] Source a placeholder player sprite set (4 facings; static, no walk cycle yet). *(Promoted to Layer 1 Pass 3 — Dungeon Digger temp sprites going in.)*
- [ ] Add a static `interactables` dict to cell data and a "tile in front of me" interaction dispatch in `OverworldScene`. *(Promoted to Layer 1 Pass 7.)*
- [ ] Wire one NPC tile through `DialogueRunner` + `TextBox`. *(Promoted to Layer 1 Pass 7.)*
- [ ] Wire one sign tile. *(Promoted to Layer 1 Pass 7.)*
- [ ] Wire one warp tile. *(Promoted to Layer 1 Pass 7.)*
- [x] Step-counted random encounter system: rate + min-quiet-steps; push real `BattleScene` on hit; reset counter on battle resolution. (Global rate for now via `EncounterSettings`; per-cell tables are a follow-up once cell data migrates to JSON.)
- [x] Persist per-member current HP across battles and saves. Added `PartyMember.current_hp`, separated `Combatant.max_hp` from initial `hp`, wrote HP back at `BattleEndedEvent`, taught `Party.from_dict` to default to max when the field is missing for backward-compat.
- [x] Migrate potions from a battle-local pool to `Party.inventory["potion"]`. New games seed 5; battles read at construction and write the survivor count back at end.
- [x] Enable the PARTY menu row → new `PartyScene` showing each member's name + HP/max HP + element pair.
- [x] Enable the INVENTORY menu row → new `InventoryScene` listing inventory rows.
- [ ] Import `sfx_movement_footstepsloop4_slow.ogg` and `wall_bump_sound_effect.ogg` from Dungeon Digger. *(The footstep loop is wrong shape for grid-stepped movement — needs a discrete tap. Layer 1 Pass 3 stretch goal at most; otherwise defer to Layer 2 audio pass.)*
- [ ] Verify save/load mid-cell-transition and mid-dialogue resume cleanly. *(Promoted to Layer 1 Pass 9 — scene-stack-in-save will fix this naturally.)*
- [ ] Update CHANGELOG / ARCHITECTURE / TESTING / TODO marks for the remaining `[ ]` items. *(Standing item — every pass.)*

### Open design questions (carried forward into Layer 1)

- [ ] Decide if/when to migrate cells from `core/overworld_cells.py` module to `data/cells/*.json` via `DataLoader`. *(Pinned for Layer 1 Pass 7 — likely yes given the dungeon's cell count.)*
- [ ] Decide if `TextBox` should grow a `render_empty_frame` option for always-visible message-box chrome. *(Layer 1 Pass 3 — the action-window panel chrome is going in regardless; if it surrounds an empty box visually it's the same effect.)*
- [ ] Decide what keyboard key opens the menu. *(Resolved at session close: Tab on keyboard + Y on controller.)*

---

## Cross-cutting / always-on

- [ ] Append a [docs/CHANGELOG.md](CHANGELOG.md) entry for every meaningful change. (House rule.)
- [ ] Update [docs/ARCHITECTURE.md](ARCHITECTURE.md) when a system's shape changes.
- [ ] Update this file as items complete (`[x]`, do not delete).
- [ ] Run [docs/TESTING.md](TESTING.md) smoke checks before declaring a layer done.
- [x] Convert split per-article HTML files into clean markdown (Pass 2 of the docs migration). See `utils/lore_to_markdown.py`.
