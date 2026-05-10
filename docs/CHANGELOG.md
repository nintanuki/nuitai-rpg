# Change Log

This file is an append-only record of every code change made to **Nuitai RPG**
by a human, AI assistant, or copilot tool. Read it before making changes so you know the current state of the codebase.

## Format

Each entry covers one logical change (which may touch multiple files). Use the
template below, with one `**File:** ... **Why:** ...` block per file touched.

    ## YYYY-MM-DD HH:MM — short summary

    **File:** path/to/file.py
    **Lines (at time of edit):** 38-52 (modified)
    **Before:**
        [old code]
    **After:**
        [new code]
    **Why:** explanation

## Conventions

* Line numbers reflect the file as it existed at the moment of the edit. Edits
  above shift line numbers below, so older entries will not match the current
  file. Never go back and "fix" old line numbers.
* Entries are append-only. Never delete history. If a later edit reverts an
  earlier one, write a new entry that references the original.
* For new files, write `(new file)` instead of a line range. The "Before"
  block can be omitted or marked `(file did not exist)`.
* For deletes, write `(deleted)` and put the removed code in "Before" with no
  "After" block.
* Keep "Before" / "After" blocks short. If a change is huge, summarize with a
  diff-style excerpt of the most important lines plus a sentence describing the
  rest, instead of pasting the entire file.
* New Entries should be BELOW this line, do not add new log entries to the top. These instructions must stay on top.

---

## 2026-05-07 — Generic-template cleanup pass

**File:** main.py
**Lines (at time of edit):** 12-31 (modified)
**Before:** `__init__` docstring referenced "the first dungeon level"; kept an unused `self.game_active = False`; called `set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)` with redundant parens.
**After:** Generic docstring, no `game_active`, `set_mode(ScreenSettings.RESOLUTION, pygame.SCALED)`.
**Why:** Template was copy-pasted from a dungeon project; needed to be neutral so it can seed any new pygame project.
**Editor:** Bryan (Claude Opus 4.7)

**File:** main.py
**Lines (at time of edit):** 45-51 (modified)
**Before:** `reset_game` docstring was a 7-line block.
**After:** Tightened to a 4-line block with the same intent.
**Why:** Cosmetic; matches the docstring style of the rest of the file.
**Editor:** Bryan (Claude Opus 4.7)

**File:** main.py
**Lines (at time of edit):** 80-87 (modified)
**Before:** `_handle_keydown` only handled `F11`.
**After:** Added an `Esc` quit branch above the `F11` branch.
**Why:** So the template runs without a controller for development.
**Editor:** Bryan (Claude Opus 4.7)

**File:** settings.py
**Lines (at time of edit):** 22 (modified)
**Before:** `TITLE = "Mimic Dice"`
**After:** `TITLE = "Pygame Template"  # Replace with your project's name.`
**Why:** Generic placeholder for the template.
**Editor:** Bryan (Claude Opus 4.7)

**File:** settings.py
**Lines (at time of edit):** 58-66 (modified)
**Before:** `AssetPaths.TV = "assets/graphics/effects/tv.png"`; `DebugSettings.MUTE = False` duplicated `AudioSettings.MUTE`.
**After:** `AssetPaths.TV` is now `__file__`-relative via `os.path.join(os.path.dirname(__file__), ...)`; the duplicate `DebugSettings.MUTE` was removed.
**Why:** Cwd-relative paths break when launched via the arcade cabinet; duplicate mute flags caused ambiguity.
**Editor:** Bryan (Claude Opus 4.7)

**File:** crt.py
**Lines (at time of edit):** 1-3 (modified)
**Before:** `from settings import *`
**After:** `from settings import ScreenSettings, ColorSettings, AssetPaths`
**Why:** Explicit imports match `main.py` and make dependencies obvious.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/__init__.py
**Lines (at time of edit):** (new file)
**After:** `"""Core data classes and state machines for the game."""`
**Why:** Empty folders weren't tracked by git; gives the package a docstring and a stable home.
**Editor:** Bryan (Claude Opus 4.7)

**File:** systems/__init__.py
**Lines (at time of edit):** (new file)
**After:** `"""Gameplay systems (physics, AI, scoring, etc.)."""`
**Why:** Same as `core/__init__.py`.
**Editor:** Bryan (Claude Opus 4.7)

**File:** ui/__init__.py
**Lines (at time of edit):** (new file)
**After:** `"""User-interface widgets, screens, and HUD elements."""`
**Why:** Same as `core/__init__.py`.
**Editor:** Bryan (Claude Opus 4.7)

**File:** utils/__init__.py
**Lines (at time of edit):** (new file)
**After:** `"""Pure helper functions and small utilities."""`
**Why:** Same as `core/__init__.py`.
**Editor:** Bryan (Claude Opus 4.7)

**File:** README.md, docs/ARCHITECTURE.md, docs/TESTING.md, docs/TODO.md
**Why:** Reflected the code changes above (Esc now wired, `__init__.py` files exist) and added a "first-run setup, delete this block afterwards" section to README + a delete-this-section instruction on the first-run checklist in docs/TODO.md.
**Editor:** Bryan (Claude Opus 4.7)

## 2026-05-09 — Drop-in AudioManager template

**File:** systems/audio_manager.py
**Lines (at time of edit):** (new file)
**After:** Portable, data-driven `AudioManager`. Reads `AudioSettings.SOUND_EFFECTS` and `MUSIC_TRACKS`, exposes `play(name)`, `play_random_music`, `pause_music`, `resume_music`, `stop_music`, and `toggle_mute`. Failure to load any individual asset (or the mixer itself) is non-fatal — the game keeps running silently.
**Why:** Every game in the cabinet had its own audio module with a slightly different shape. Promoting this one into the template gives new games a single, opinionated baseline they can extend instead of re-inventing.
**Editor:** Bryan (Claude Opus 4.7)

**File:** settings.py
**Lines (at time of edit):** 56-76 (modified)
**Before:** `AudioSettings` had only `MUTE`, `MUTE_MUSIC`, `MUSIC_VOLUME`.
**After:** Added `SFX_VOLUME`, `SOUND_EFFECTS: dict[str, str]`, and `MUSIC_TRACKS: list[str]` so the new `AudioManager` is fully data-driven. Default values are empty so the boilerplate boots silently until a project registers its own audio.
**Why:** Match the contract documented in the AudioManager docstring.
**Editor:** Bryan (Claude Opus 4.7)

**File:** main.py
**Lines (at time of edit):** 7-8, 19-44 (modified)
**Before:** `GameManager.__init__` did not initialise the mixer or construct an audio manager.
**After:** Imports `AudioManager`, adds `_initialize_audio_mixer()`, calls it before `set_mode`, and assigns `self.audio = AudioManager()` after controllers are set up.
**Why:** The mixer must exist before sounds are loaded; constructing the manager here makes `self.audio.play("name")` available everywhere downstream.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** 45-51, 57-87 (modified)
**Before:** No "Audio" section; settings table described `AudioSettings` as just "Mute toggles + music volume"; source tree listed `systems/` as empty.
**After:** Added "## 4. Audio" describing the manager, updated settings table entry, and called out `systems/audio_manager.py` in the source tree. Renumbered later sections accordingly.
**Why:** Keep the architecture doc in sync with the new system.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/TESTING.md
**Lines (at time of edit):** 24 (modified)
**After:** Added an "Audio" section with three smoke checks covering boot logging, `play(name)`, and music control / mute toggle.
**Why:** Manual smoke list was missing the new system.
**Editor:** Bryan (Claude Opus 4.7)

**File:** README.md
**Lines (at time of edit):** 14-18 (modified)
**Before:** Bullet list described the empty `systems/` folder and made no mention of audio.
**After:** Added an `AudioManager` bullet and noted that `systems/` ships with the audio manager.
**Why:** Surface the new feature on the cover page so adopters notice it.
**Editor:** Bryan (Claude Opus 4.7)

## 2026-05-09T16:00-04:00 � Project rebrand: Pygame template -> Nuitai RPG

**File:** README.md
**Lines (at time of edit):** entire file (rewritten)
**Why:** README was still describing the generic pygame template (status, "first-run setup" block, asset credits). Replaced with a Nuitai RPG project page: pitch, layered status table, party roster, doc index, and project layout.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/VISION.md
**Lines (at time of edit):** (new file)
**After:** The artistic North Star. Pitch, "what done feels like", design pillars (element system, magic-is-motion, small party, the maelstrom as map, presentation-evolves-design-doesn't, in-window-only text), tone, anti-goals, and a meta-rule for when this file should change.
**Why:** Separates the immutable artistic intent from the changing strategy and tactics so future docs maintenance does not bleed across categories.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/ROADMAP.md
**Lines (at time of edit):** (new file)
**After:** The six-layer plan (engine spike -> text demo -> content & polish -> Dragon Quest stage -> original art & audio -> full vision) with acceptance criteria, asset requirements, and definitions-of-done per layer. Cross-cutting tracks (lore, architecture, testing, save compatibility) called out separately.
**Why:** The user requested a layered plan that lets the project ship at every checkpoint. Layer 3 specifically codified as a destination, not a transition (the "Dragon Quest stage" framing the user proposed).
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/TODO.md
**Lines (at time of edit):** entire file (rewritten)
**Before:** Pygame-template first-run checklist + suggested first features.
**After:** Layer-0/Layer-1 actionable task list (code, content, writing, art) with house rules ("[x] when complete; do not delete"), plus a cross-cutting always-on section.
**Why:** TODO is now scoped to the *current* layer's concrete work, per the documentation split (vision/roadmap/todo).
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** entire file (rewritten)
**Before:** "Pygame Template � Architecture", described template scaffolding only.
**After:** "Nuitai RPG � Architecture". Existing sections (frame loop, input, audio, CRT, settings, source tree) updated to match current state. New section 8 "Planned subsystems (Layer 0 architectural seams)" describes core/elements.py, scene stack, events, save, data_loader, gameplay systems, rendering, and content packs as the seams the engine is being built around.
**Why:** Architecture doc now describes both current state and the immediate-next-layer seams so contributors understand the shape the engine is being grown into.
**Editor:** Bryan (Claude Opus 4.7)

**File:** .github/copilot-instructions.md
**Lines (at time of edit):** 1-15, ~38, ~70, ~80 (modified)
**Before:** "Copilot Instructions for the Pygame Template" header, generic template note, 5-item required reading list, no project-specific architecture rules, "UI text" section limited to caps-only.
**After:** "Copilot Instructions for Nuitai RPG" header with vision/roadmap/todo framing. 8-item required reading list including VISION.md, ROADMAP.md, and the lore index. Architecture-rules section adds four Nuitai-specific rules (gameplay-emits-events; element math has one home; content is data not code; save/load is first-class). UI-text section renamed and expanded to forbid terminal output and disallow element names in in-world dialogue/flavor. Mental-testing checklist adds two checks (no print() in gameplay code; save/load round-trip).
**Why:** Codify the project-specific rules from the new VISION/ROADMAP/ARCHITECTURE docs so any future editor (human or AI) inherits them automatically.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/lore/INDEX.md, docs/lore/<category>/<slug>.html (new files; 114 articles + index)
**After:** docs/LOREDUMP.html split into one HTML file per article under docs/lore/<category>/<slug>.html, with a categorized markdown TOC at docs/lore/INDEX.md. Original LOREDUMP.html preserved verbatim as the source of truth.
**Why:** The 545 KB monolithic export is hard to grep, hard to diff, and hard for AI editors to load on demand. Per-article files allow targeted reads ("just Tawiri's article"). A future Pass 2 will convert these HTML stubs to clean markdown.
**Editor:** Bryan (Claude Opus 4.7)

**File:** utils/split_loredump.py
**Lines (at time of edit):** (new file)
**After:** One-shot tool that slices docs/LOREDUMP.html on its embedded `<!-- Type-Name-hash.html -->` comment markers and writes per-article files plus the INDEX.md TOC. Idempotent.
**Why:** Reproducible split; if the LOREDUMP is re-exported from World Anvil, re-running the tool regenerates the per-article files cleanly.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/CHANGELOG.md
**Lines (at time of edit):** 3-7 (modified)
**Before:** Header read "**<RENAME ME � your project name>**" with a "first step" instruction telling new projects to replace the placeholder.
**After:** Header reads "**Nuitai RPG**" and the placeholder-instruction line is removed.
**Why:** Project is no longer a template; the placeholder was stale.
**Editor:** Bryan (Claude Opus 4.7)

## 2026-05-09T16:30-04:00 � Pass 2: lore HTML -> Markdown

**File:** utils/lore_to_markdown.py
**Lines (at time of edit):** (new file)
**After:** Pass-2 converter. Walks every `docs/lore/<category>/<slug>.html` produced by `split_loredump.py`, builds a UUID -> (category, slug, title) index from the wrapping div class, extracts the article body from `.user-css-vignette` (balancing nested divs), converts the World-Anvil-flavored HTML to Markdown, rewrites `<a data-article-id=...>` anchors to relative `../<cat>/<slug>.md` links, decodes HTML entities, normalizes whitespace, and writes `<slug>.md` next to the source. Article-level infobox metadata exposed via `.section-title` / `.section-payload` pairs is preserved as either a key/value blockquote (single-line) or an `## Heading` section (multi-line). The `.html` source is deleted on success and the lore index is rewritten to point at the new `.md` files.
**Why:** The HTML-per-article files were one giant World Anvil scaffolding sandwich around a small slice of prose; that's hard to read and hard for AI editors to consume. Converting to Markdown gives clean prose plus working in-repo links. The split + convert pipeline stays reproducible: re-export `LOREDUMP.html` -> `split_loredump.py` -> `lore_to_markdown.py`.
**Editor:** Bryan (Claude Opus 4.7)

**File:** utils/split_loredump.py
**Lines (at time of edit):** ~55-66 (modified)
**Before:** Wrote per-article files alongside whatever was already in `docs/lore/<category>/`, so re-running on a tree that already contained `.md` output produced duplicate index entries and stale files.
**After:** Wipes any prior `.md` and `.html` files in each category subdirectory before regenerating, so the splitter always produces a clean slate. The original `LOREDUMP.html` and the top-level lore directory are untouched.
**Why:** Caught while re-running the pipeline end-to-end during pass 2; the duplicate-output bug would silently double the article count in the index on every alternating run.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/lore/INDEX.md, docs/lore/<category>/<slug>.md (114 articles)
**Lines (at time of edit):** entire tree (regenerated)
**Before:** 114 World Anvil HTML stubs (~545 KB total) heavy with template scaffolding (sidebars, panels, empty section blocks), with internal links pointing at World Anvil URLs.
**After:** 114 clean Markdown articles totaling ~95 KB, with relative in-repo links between them. Index regenerated to point at the `.md` files. All 492 internal links verified to resolve.
**Why:** Per-article Markdown is the form lore will be consumed in by future writing passes (Layer 1) and by AI editors loading just the article they need. HTML stubs are no longer needed; `LOREDUMP.html` remains the source of truth.
**Editor:** Bryan (Claude Opus 4.7)

## 2026-05-09T17:00-04:00 — Layer 0 engine spike

**File:** settings.py
**Lines (at time of edit):** 50-60 (modified), 95-145 (new)
**Before:** `FontSettings` had only the `FONT` path; `SaveSettings` and `UISettings` did not exist.
**After:** Added `FontSettings.SIZE_SMALL` (12), `SIZE_BODY` (16), `SIZE_HEADING` (24); added `SaveSettings` (`SAVES_DIR`, `MAX_SAVE_SLOTS = 3`, `AUTOSAVE_SLOT_ID = 0`) and `UISettings` (text-box geometry, typewriter speed, menu cursor blink, item spacing).
**Why:** Layer 0 needs centralized text sizing, save-system tunables, and UI-widget tunables � copilot-instructions: no magic numbers outside `settings.py`.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/elements.py
**Lines (at time of edit):** (new file)
**After:** `Element` enum (`AHI`, `LAU`, `WAI`, `RA`, `AKU`, `MANA`), `ADVANTAGE_MULTIPLIER` (2.0) / `DISADVANTAGE_MULTIPLIER` (0.5) / `NEUTRAL_MULTIPLIER` (1.0), `_BEATS` table, `beats(a, d)` and `damage_multiplier(a, d)`.
**Why:** Single source of truth for element math; every battle damage computation reads from this module so the table is never duplicated.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/events.py
**Lines (at time of edit):** (new file)
**After:** Frozen dataclasses `TurnStartEvent`, `AttackEvent`, `DamageEvent`, `StatusAppliedEvent`, `CombatantDefeatedEvent`, `BattleEndedEvent`, `DialogueLineEvent`, `DialogueEndedEvent`.
**Why:** Gameplay emits events; views consume them. This is the seam that lets the same engine drive every layer's presentation without rewrites.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/scene.py
**Lines (at time of edit):** (new file)
**After:** `Scene` base class (`OPAQUE` flag, `on_enter` / `on_exit` / `handle_event` / `update` / `render`, `to_dict` / `from_dict`) and `SceneStack` (`push` / `pop` / `replace` / `clear`, `top`, `handle_event`, `update`, `render_all` walking from the deepest opaque scene up).
**Why:** Lets transient scenes (battle, pause, dialogue) layer on top of gameplay and pop cleanly. `OPAQUE = False` allows translucent overlays.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/save.py
**Lines (at time of edit):** (new file)
**After:** `SAVE_SCHEMA_VERSION = 1`, `slot_path`, `slot_exists`, `save(slot_id, payload)`, `load(slot_id)` and `migrate(record)`. Files are written as `{"version": N, "data": ...}` JSON; future versions raise `ValueError`.
**Why:** Save / load is a first-class feature, not a Layer 5 add-on. Schema versioning lets later layers extend the payload without breaking older saves.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/data_loader.py
**Lines (at time of edit):** (new file)
**After:** `DataLoadError`, `DataLoader.load(kind)` reading every JSON file in `data/<kind>/`, requiring an `id` field, indexing by id, caching per-kind. Missing pack directory returns `{}` so the engine boots without content.
**Why:** Content is data, not code. Layer 1 will populate `data/` with characters, abilities, enemies, dungeons, dialogue.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/scenes/__init__.py
**Lines (at time of edit):** (new file)
**After:** Package docstring.
**Why:** Establishes the scenes subpackage.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/scenes/title_scene.py
**Lines (at time of edit):** (new file)
**After:** `TitleScene` with NEW GAME / CONTINUE (auto-disabled when no save) / QUIT. NEW GAME builds a default party (Kailo, Hina, Tawiri) and replaces the stack with `TestWorldScene`; CONTINUE loads slot 1.
**Why:** First scene the player sees. Default party is barebones placeholder data per Bryan's instruction; writer to overwrite.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/scenes/test_world_scene.py
**Lines (at time of edit):** (new file)
**After:** `TestWorldScene` with TALK / FIGHT / SAVE / QUIT TO TITLE. Talk pushes a placeholder line; Fight pushes `BattleScene`; Save writes party to slot 1; Quit replaces with title.
**Why:** Single placeholder room exercises every Layer-0 seam (text box, save, push/pop, scene replacement).
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/scenes/battle_scene.py
**Lines (at time of edit):** (new file)
**After:** `BattleScene` hosts `Battle` + `BattleView` + `TextBox`. Each frame the text box drains, the battle steps one turn, and events are pushed into the view. On `BattleEndedEvent` the scene pops itself once narration drains.
**Why:** Proves the events-and-views seam end to end. Confirm advances narration; cancel attempts flee.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/scenes/menu_scene.py
**Lines (at time of edit):** (new file)
**After:** Translucent (`OPAQUE = False`) `MenuScene` with PARTY / INVENTORY / SAVE / SETTINGS / QUIT TO TITLE / RESUME. Party / Inventory / Settings are stubs; Save writes slot 1; Quit clears the stack and pushes `TitleScene`.
**Why:** Demonstrates `OPAQUE = False` overlay rendering; Layer 1 will fill in the stub commands.
**Editor:** Bryan (Claude Opus 4.7)

**File:** systems/party.py
**Lines (at time of edit):** (new file)
**After:** `PartyMember(member_id, name, elements, stats)` with `to_dict` / `from_dict`. `Party` with members list, inventory dict, gold, flags, full save round-trip.
**Why:** The canonical save payload. Layer 1 extends with equipment, learnsets, and per-member abilities.
**Editor:** Bryan (Claude Opus 4.7)

**File:** systems/battle.py
**Lines (at time of edit):** (new file)
**After:** `Combatant` (id, name, hp, attack, element, is_party). `Battle(party, enemies)` with round-robin turn order; `step()` returns the events for one turn (TurnStart -> Attack -> Damage -> optional Defeated -> optional BattleEnded). `flee()` ends with outcome `"flee"`. Damage = `max(1, int(attack * damage_multiplier(actor.element, target.element)))`.
**Why:** Pure data; emits events; never draws. The Layer-0 simulation is intentionally minimal � Layer 1 plugs command selection and abilities on top of the same event stream.
**Editor:** Bryan (Claude Opus 4.7)

**File:** systems/dialogue.py
**Lines (at time of edit):** (new file)
**After:** `DialogueRunner(tree)` iterates `tree["lines"]`, emitting one `DialogueLineEvent` per `advance()`, then a trailing `DialogueEndedEvent`.
**Why:** Pure data emitter for dialogue trees; views consume the event stream. Branching is a Layer 1 extension on the same shape.
**Editor:** Bryan (Claude Opus 4.7)

**File:** ui/text_renderer.py
**Lines (at time of edit):** (new file)
**After:** `_FONT_CACHE`, `get_font(size)`, `wrap(text, font, max_width)`, `render_line(text, color, size)`, `draw_text(surface, text, position, color, size, max_width, line_spacing)`. **All-caps enforcement happens here** via `text.upper()`.
**Why:** Single chokepoint for text drawing means gameplay code can pass any case and the player only ever sees ALL CAPS.
**Editor:** Bryan (Claude Opus 4.7)

**File:** ui/text_box.py
**Lines (at time of edit):** (new file)
**After:** `TextBox(width, height)` with deque queue, `push(text, speaker)`, `clear`, `is_done`, `is_page_complete`, `advance()` (fast-forwards typewriter or pulls next line), `update(dt)` advances reveal at `UISettings.TYPEWRITER_CHARS_PER_SECOND`, `render()` draws bordered panel at the bottom of the host surface.
**Why:** JRPG-style dialogue widget. Speaker label rendered above text in `SIZE_HEADING` for easy reading.
**Editor:** Bryan (Claude Opus 4.7)

**File:** ui/menu.py
**Lines (at time of edit):** (new file)
**After:** `MenuItem(label, on_select, enabled)`. `Menu(items, on_cancel)` with `move_up` / `move_down` (skip disabled, wrap), `confirm`, `cancel`, `render(surface, position)` with blinking `>` cursor (`UISettings.MENU_CURSOR_BLINK_HZ`).
**Why:** Reusable menu primitive for title screen, world commands, pause overlay, and future battle command menu.
**Editor:** Bryan (Claude Opus 4.7)

**File:** ui/battle_view.py
**Lines (at time of edit):** (new file)
**After:** `BattleView(text_box).consume(event)` phrases each battle event into the text box (`TurnStartEvent`, `AttackEvent`, `DamageEvent` with effectiveness tag, `StatusAppliedEvent`, `CombatantDefeatedEvent`, `BattleEndedEvent`).
**Why:** Demonstrates the event-stream-to-view seam. Layer 3+ swaps in a sprite-aware view that listens to the same events.
**Editor:** Bryan (Claude Opus 4.7)

**File:** ui/input_map.py
**Lines (at time of edit):** (new file)
**After:** Helpers `is_confirm`, `is_cancel`, `is_up`, `is_down` translating raw pygame events into logical UI actions. Confirm = Enter / Z / Space / A button; Cancel = Backspace / X / B button; up/down = arrows / WASD / D-pad / left-stick Y past `JOY_TRIGGER_THRESHOLD`.
**Why:** Centralises keyboard + controller routing so each scene does not re-implement input mapping.
**Editor:** Bryan (Claude Opus 4.7)

**File:** main.py
**Lines (at time of edit):** 1-160 (modified)
**Before:** `_update_world` and `_render_frame` were stubs; `_initialize_audio_mixer` printed errors to stdout; `_process_events` did not forward events anywhere; no scene stack.
**After:** Imports `SceneStack`, `TitleScene`, and `Party`; `__init__` builds an empty `Party`, constructs `self.scene_stack`, and pushes `TitleScene`. `_process_events` forwards events to `scene_stack.handle_event` after globals run. `_update_world(dt)` calls `scene_stack.update(dt)`. `_render_frame` calls `scene_stack.render_all(self.screen)` before the CRT pass. `dt` is computed once per frame from `clock.tick(FPS) / 1000.0`. Mixer init failures now log to `stderr` (not gameplay stdout).
**Why:** Wires every Layer-0 subsystem into the running loop and removes the only `print()` call from the gameplay path.
**Editor:** Bryan (Claude Opus 4.7)

**File:** data/README.md, data/{characters,abilities,enemies,dungeons,dialogue}/.gitkeep
**Lines (at time of edit):** (new files)
**After:** `data/README.md` documents the per-kind schemas; each subfolder has a `.gitkeep` so the empty tree is committed.
**Why:** Reserves the content-pack tree so Layer 1 can drop JSON in without touching code.
**Editor:** Bryan (Claude Opus 4.7)

**File:** .gitignore
**Lines (at time of edit):** (appended at end)
**After:** Added `# Save files (player local state).` and `saves/`.
**Why:** Save files are local player state; never committed.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/TESTING.md
**Lines (at time of edit):** appended Layer-0 section
**After:** Added items 13-21: title screen, CONTINUE disabled state, NEW GAME flow, text box typewriter and confirm advance, FIGHT scene with HP, SAVE writes slot 1, QUIT TO TITLE re-enables CONTINUE, CONTINUE restores party, no console output during gameplay.
**Why:** Records the manual smoke checks that constitute Layer-0 sign-off.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** rewritten
**Before:** Section 8 "Planned subsystems" listed Layer-0 work as future; sections 1-7 referenced the stub frame loop.
**After:** Live sections describe SceneStack, elements, events, save, data_loader, gameplay systems, UI, scenes, and updated source tree. "Planned" content was promoted to live status.
**Why:** Doc must reflect the code as it currently exists, not as it is planned (house rule).
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/TODO.md
**Lines (at time of edit):** Layer 0 section
**Before:** Every Layer-0 task `[ ]`.
**After:** Every Layer-0 task `[x]`.
**Why:** All Layer-0 items are landed and verified end-to-end (NEW GAME -> FIGHT -> SAVE -> QUIT TO TITLE -> CONTINUE round-trip passes in headless smoke test).
**Editor:** Bryan (Claude Opus 4.7)

## 2026-05-09T17:30-04:00 � Layer 0.5 scaffolding pass

**File:** data/characters/{kailo,hina,tawiri}.json, data/abilities/firebolt.json, data/enemies/shade.json, data/dungeons/demo_room.json, data/dialogue/opening.json
**Lines (at time of edit):** (new files)
**After:** One worked example per content-pack subfolder, each with the schema fields described in `data/README.md`.
**Why:** Layer-0 acceptance criterion ("at least one example each of: character JSON, ability JSON, enemy JSON, dialogue JSON") was technically unmet � schemas were prose-only. Schema-by-example gives weaker contributors a file they can copy and edit.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/factories.py
**Lines (at time of edit):** (new file)
**After:** `party_member_from_data`, `combatant_from_party_member`, `combatant_from_enemy_data`. Single seam from JSON dict to runtime gameplay object.
**Why:** Without a factory module, the JSON-to-runtime mapping had no canonical home and was being inlined into scenes. New seam means every "load X from data" site lands in one file.
**Editor:** Bryan (Claude Opus 4.7)

**File:** main.py
**Lines (at time of edit):** import block + `GameManager.__init__`
**Before:** `GameManager` had no shared `DataLoader`.
**After:** Imports `DataLoader`; `__init__` builds `self.data = DataLoader()` before the first scene is pushed so any scene can reach `self.gm.data.load(kind)`.
**Why:** Caching content reads at the manager level avoids per-scene reload churn and gives scenes a single, obvious place to find content.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/scenes/title_scene.py
**Lines (at time of edit):** module top + `_DEFAULT_PARTY` block + `_new_game`
**Before:** `_DEFAULT_PARTY` was a hard-coded list of tuples; `build_default_party()` constructed `PartyMember` objects in code.
**After:** `_DEFAULT_PARTY_IDS = ("kailo", "hina", "tawiri")` resolves against `data/characters/`. `build_default_party(gm)` reads the loader and routes each entry through `party_member_from_data`. Missing files are skipped rather than crashing.
**Why:** Demonstrates the data-driven path that Layer 1 will rely on. Adding a fourth member becomes a JSON-only change.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/scenes/battle_scene.py
**Lines (at time of edit):** rewritten
**Before:** `_build_party_combatants` and `_build_default_enemies` constructed `Combatant` objects inline.
**After:** Both helpers route through `core.factories`. `_build_enemies` loads `data/enemies/` via `gm.data` and looks up the encounter by id; falls back to a hard-coded Shade only if content is missing.
**Why:** Demonstrates the JSON -> factory -> simulation path end to end. Layer 1 swaps the encounter id for a dungeon-driven roll without touching battle code.
**Editor:** Bryan (Claude Opus 4.7)

**File:** core/scenes/test_world_scene.py
**Lines (at time of edit):** import block + `_talk`
**Before:** `_talk` pushed a single literal string.
**After:** Loads `data/dialogue/opening.json` via `gm.data`, walks it with `DialogueRunner`, and pushes each emitted `DialogueLineEvent` (with speaker tag) into the text box. Falls back to the literal only if content is missing.
**Why:** The dialogue subsystem was built but not exercised by the running game. Now the full path `data_loader -> DialogueRunner -> DialogueLineEvent -> TextBox` is demonstrated for weak models to imitate.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/CONTRIBUTING.md
**Lines (at time of edit):** (new file)
**After:** "How to add X" lookup table mapping every kind of change to the file to edit and an existing file to imitate.
**Why:** `copilot-instructions.md` defines rules and `ARCHITECTURE.md` describes shape; neither answers "I want to add an ability � what files do I touch?". One short table closes the gap.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/TODO.md
**Lines (at time of edit):** new "Layer 0.5 � Scaffolding deferrals" section
**After:** Tracks scene-stack save persistence, status-effect stub, headless smoke test, `.gitignore copy` cleanup, and writing-pipeline templates.
**Why:** Real items identified during the close-of-Layer-0 audit; not blockers for Layer 1, but worth holding visible.
**Editor:** Bryan (Claude Opus 4.7)

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** �1, �11, �14
**After:** Notes that `GameManager` owns the shared `DataLoader`. �11 expanded to describe `core/factories.py` as the JSON-to-runtime seam. Source tree adds `factories.py`.
**Why:** Doc must reflect the code as it exists.
**Editor:** Bryan (Claude Opus 4.7)

## 2026-05-10T16:20-04:00 — Title screen menu + centering controls

**File:** settings.py
**Lines (at time of edit):** 64, 150, 153-154 (modified)
**Before:** Title text used `FontSettings.SIZE_HEADING`; menu cursor/text offset was hardcoded in `ui/menu.py`; title-screen vertical anchors were literal values in `core/scenes/title_scene.py`.
**After:** Added `FontSettings.SIZE_TITLE_SCREEN_HEADING`, `UISettings.MENU_LABEL_OFFSET`, `UISettings.TITLE_SCREEN_HEADING_Y`, and `UISettings.TITLE_SCREEN_MENU_TOP_Y`.
**Why:** Gives the title-screen heading size and title/menu layout dedicated constants so they can be tuned without affecting other scenes.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** core/scenes/title_scene.py
**Lines (at time of edit):** 62-74, 128-142 (modified)
**Before:** Menu rows were left-positioned and title text used a non-centered anchor. Menu offered `NEW GAME`, `CONTINUE`, `QUIT`.
**After:** Title menu now offers `NEW GAME`, `CONTINUE`, `LOAD GAME`, `QUIT`; `CONTINUE` and `LOAD GAME` are disabled when no save slots exist. Title heading width is measured and centered horizontally; title menu rendering is centered horizontally.
**Why:** Matches requested title-menu composition and centered layout while preserving existing scene flow.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/menu.py
**Lines (at time of edit):** 80-118 (modified)
**Before:** `render(surface, position)` always left-aligned rows and used a hardcoded `x + 24` label offset.
**After:** `render(surface, position, centered=False)` supports per-row horizontal centering when requested. Cursor offset now uses `UISettings.MENU_LABEL_OFFSET`.
**Why:** Lets title screen center menu options without changing alignment behavior in other menus.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** 65, 70, 84 (modified)
**Before:** Font/UI settings and title-scene description did not mention title-screen-specific size/layout controls or `LOAD GAME`.
**After:** Updated settings table to include title-screen size/layout responsibilities and updated title-scene bullet to `NEW GAME / CONTINUE / LOAD GAME / QUIT` with disabled-state behavior.
**Why:** Keep architecture docs in sync with the current code.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** docs/TESTING.md
**Lines (at time of edit):** 13, 33-34 (modified)
**Before:** Smoke checks referenced `ScreenSettings.TITLE` and a title menu without `LOAD GAME`.
**After:** Smoke checks now reference `ScreenSettings.WINDOW_TITLE` and assert `LOAD GAME` presence + disabled behavior alongside `CONTINUE`.
**Why:** Keep manual test expectations aligned with implemented behavior.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-10T16:36-04:00 — Title screen left-anchor positioning pass

**File:** settings.py
**Lines (at time of edit):** 156-160 (modified)
**Before:**
```python
# Title-screen layout anchors in pixels from the top of the screen.
TITLE_SCREEN_HEADING_Y = 150
TITLE_SCREEN_MENU_TOP_Y = 200
```
**After:**
```python
# Title-screen layout anchors in pixels from the top-left corner.
TITLE_SCREEN_HEADING_X = 90
TITLE_SCREEN_HEADING_Y = 90
TITLE_SCREEN_MENU_X = 90
TITLE_SCREEN_MENU_TOP_Y = 290
```
**Why:** Add explicit X/Y anchor constants so title/menu placement can match the requested left-aligned mockup without touching colors or fonts.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** core/scenes/title_scene.py
**Lines (at time of edit):** 128-140 (modified)
**Before:**
```python
heading_width = heading_font.size(ScreenSettings.TITLE_SCREEN_HEADING.upper())[0]
heading_x = (ScreenSettings.WIDTH - heading_width) // 2

self.menu.render(
  surface,
  (ScreenSettings.WIDTH // 4, menu_top_y),
  centered=True,
  item_spacing=UISettings.TITLE_SCREEN_MENU_ITEM_SPACING,
)
```
**After:**
```python
text_renderer.draw_text(
  surface,
  ScreenSettings.TITLE_SCREEN_HEADING,
  (UISettings.TITLE_SCREEN_HEADING_X, UISettings.TITLE_SCREEN_HEADING_Y),
  color=ColorSettings.WHITE,
  size=FontSettings.SIZE_TITLE_SCREEN_HEADING,
)

self.menu.render(
  surface,
  (UISettings.TITLE_SCREEN_MENU_X, UISettings.TITLE_SCREEN_MENU_TOP_Y),
  centered=False,
  item_spacing=UISettings.TITLE_SCREEN_MENU_ITEM_SPACING,
)
```
**Why:** Replace centered/derived placement with fixed top-left anchors to match the target composition while preserving existing font sizes and colors.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-10 20:45 UTC — Background template system (Ms. Fishy gradient as a reusable scene skin)

**File:** utils/graphics.py
**Lines (at time of edit):** 1-43 (new file)
**Before:** (file did not exist)
**After:** Adds `build_gradient_surface(width, height, color_top, color_bottom)` — a pure helper that pre-renders a vertical linear-gradient `pygame.Surface` row-by-row. Direct port of the helper used by Ms. Fishy's ocean background.
**Why:** Scenes need a cheap way to paint gradient backdrops without recomputing pixels each frame; cache once at scene construction (or at first render via `utils/backgrounds.py`) and blit on every frame.
**Editor:** Frankie (Claude Opus 4.7)

**File:** utils/backgrounds.py
**Lines (at time of edit):** 1-112 (new file)
**Before:** (file did not exist)
**After:** Adds `render_scene_background(scene, surface)`, `render_template(name, surface)`, `template_name_for_scene(scene)`, and `clear_cache()`. Caches gradient surfaces keyed by `(template_name, width, height)` so the per-row interpolation runs once. Unknown template names degrade to the configured default rather than crashing.
**Why:** Drop-in replacement for `surface.fill(BG_COLOR)` at the top of each scene's `render`. The class-name → template mapping in `BackgroundSettings.SCENE_BACKGROUNDS` is the single switchboard for what each scene looks like — no scene code has to change to re-skin one.
**Editor:** Frankie (Claude Opus 4.7)

**File:** settings.py
**Lines (at time of edit):** 16-78 (added)
**Before:** No background-template configuration; scenes called `surface.fill(ColorSettings.BG_COLOR)` directly.
**After:** Adds `BackgroundSettings` with `SOLID` / `GRADIENT` discriminators, a `TEMPLATES` dict (`ocean`, `midnight`, `dusk`, `ember`, `nero`, `black`), a `SCENE_BACKGROUNDS` scene-class-name → template-name map (defaulting `TitleScene` to `ocean` — the Ms. Fishy gradient), and a `DEFAULT_TEMPLATE` fallback.
**Why:** Match the Ms. Fishy aqua → navy gradient on the Nuitai title screen while keeping per-scene backgrounds toggleable in one place. Follows the project convention that new unrelated tunables go in a new `*Settings` class.
**Editor:** Frankie (Claude Opus 4.7)

**File:** core/scenes/title_scene.py
**Lines (at time of edit):** 17-21, 126 (modified)
**Before:**
```python
from settings import ColorSettings, FontSettings, SaveSettings, ScreenSettings, UISettings
...
surface.fill(ColorSettings.BG_COLOR)
```
**After:**
```python
from settings import ColorSettings, FontSettings, SaveSettings, ScreenSettings, UISettings
...
from utils.backgrounds import render_scene_background
...
render_scene_background(self, surface)
```
**Why:** Apply the configured template (default `ocean` — the Ms. Fishy gradient) instead of a flat fill so the title screen reads as the project's "front cover."
**Editor:** Frankie (Claude Opus 4.7)

**File:** core/scenes/test_world_scene.py
**Lines (at time of edit):** 25-27, 116 (modified)
**Before:** `surface.fill(ColorSettings.BG_COLOR)` at the top of `render`.
**After:** `render_scene_background(self, surface)` at the top of `render`; `from utils.backgrounds import render_scene_background` added with the existing UI imports.
**Why:** Route the test room through the same template system as the title so its background can be toggled from `BackgroundSettings.SCENE_BACKGROUNDS` without touching scene code.
**Editor:** Frankie (Claude Opus 4.7)

**File:** core/scenes/battle_scene.py
**Lines (at time of edit):** 26-29, 109 (modified)
**Before:** `surface.fill(ColorSettings.BG_COLOR)` at the top of `render`.
**After:** `render_scene_background(self, surface)` at the top of `render`; `from utils.backgrounds import render_scene_background` added with the existing UI imports.
**Why:** Same as test world — make every opaque scene speak through the template registry so re-skinning is one line in `settings.py`.
**Editor:** Frankie (Claude Opus 4.7)

## 2026-05-10T16:58-04:00 — Title waves loop, menu SFX wiring, and controller confirm parity

**File:** settings.py
**Lines (at time of edit):** 146-152 (modified)
**Before:**
```python
SOUND_EFFECTS: dict[str, str] = {}
```
**After:**
```python
SOUND_EFFECTS: dict[str, str] = {
  "menu_move": os.path.join(..., "sfx_menu_move2.ogg"),
  "menu_select": os.path.join(..., "sfx_menu_select3.ogg"),
}
```
**Why:** Register the new menu navigation and selection sounds in the central audio registry so scenes can trigger them by logical name.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/input_map.py
**Lines (at time of edit):** 23-31 (modified)
**Before:** Confirm only mapped controller `A`.
**After:** Confirm maps controller `A` and `START`.
**Why:** Ensure controller users can select menu items with START the same way keyboard users can confirm with multiple keys.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** systems/audio_manager.py
**Lines (at time of edit):** 99, 134-156 (modified)
**Before:** Loader failures were printed with `print(...)`; music selection only supported random tracks from `MUSIC_TRACKS`.
**After:** Loader failures now log to `stderr`; added `play_music_track(track_path, loops=-1)` for scene-specific looping music and reused it from `play_random_music`.
**Why:** Keep diagnostics out of gameplay output and add a clean API for title-only ambience playback.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/menu.py
**Lines (at time of edit):** 56-96, 153-163 (modified)
**Before:** `move_up`, `move_down`, `confirm`, and `cancel` returned `None`.
**After:** These methods now return booleans indicating whether an action fired (`cursor moved`, `item selected`, `cancel handled`).
**Why:** Lets scenes play menu SFX only when a real menu action occurred.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** core/scenes/title_scene.py
**Lines (at time of edit):** 15-22, 87-93, 127-136 (modified)
**Before:** No title-specific music lifecycle; menu navigation/confirm was silent.
**After:** `on_enter` loops `AssetPaths.WAVES_SOUND`, `on_exit` stops music; menu up/down play `menu_move` and confirm plays `menu_select`.
**Why:** Implement requested ambient title loop and wire both keyboard/controller menu interactions to the new SFX cues.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** core/scenes/menu_scene.py
**Lines (at time of edit):** 77-90 (modified)
**Before:** Pause menu navigation/confirm/cancel was silent.
**After:** Up/down play `menu_move`; confirm/cancel play `menu_select` when the action succeeds.
**Why:** Apply the same menu SFX behavior to the overlay menu for consistency.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** core/scenes/test_world_scene.py
**Lines (at time of edit):** 98-112 (modified)
**Before:** World command menu navigation/confirm was silent.
**After:** Up/down play `menu_move`; confirm plays `menu_select` on successful selection.
**Why:** Ensure all in-world command-menu interactions use the same SFX language as title/pause menus.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** 42, 48, 85 (modified)
**Before:** Input section did not document START-as-confirm; audio section did not mention direct track playback; title scene description had no ambience note.
**After:** Documented confirm parity (`A` + `START`), `play_music_track`, and title-scene `waves.ogg` loop behavior.
**Why:** Keep architecture docs aligned with the implemented input/audio/scene behavior.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-10T17:05-04:00 — Yellow menu cursor

**File:** settings.py
**Lines (at time of edit):** 10-14 (modified)
**Before:** `ColorSettings` did not define a dedicated yellow color.
**After:** Added `YELLOW = (255, 220, 0)`.
**Why:** Provide a shared color constant for cursor styling without introducing magic color tuples in UI modules.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/menu.py
**Lines (at time of edit):** 125-130 (modified)
**Before:** Cursor glyph `>` rendered using each row's text color.
**After:** Cursor glyph `>` now renders with `ColorSettings.YELLOW`; row label colors remain unchanged.
**Why:** Make the active menu cursor clearly visible and match the requested yellow cursor treatment across all menus.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-10T18:45-04:00 — Per-file audio volume toggles in settings

**File:** settings.py
**Lines (at time of edit):** 142-177 (modified)
**Before:**
```python
MUSIC_VOLUME = 1.0
SFX_VOLUME = 1.0

SOUND_EFFECTS = {
  "menu_move": ".../sfx_menu_move2.ogg",
  "menu_select": ".../sfx_menu_select3.ogg",
}

MUSIC_TRACKS = []
```
**After:**
```python
MUSIC_VOLUME = 1.0
SFX_VOLUME = 1.0

SFX_FILE_VOLUMES = {
  ".../sfx_menu_move2.ogg": 1.0,
  ".../sfx_menu_select3.ogg": 1.0,
}

MUSIC_TRACKS = []

MUSIC_FILE_VOLUMES = {
  ".../waves.ogg": 1.0,
}
```
**Why:** Add per-file volume constants so each individual sound/music asset can be muted by setting its value to `0.0` (or tuned independently) without muting the whole SFX/music category.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** systems/audio_manager.py
**Lines (at time of edit):** 82-111, 161 (modified)
**Before:**
```python
sound.set_volume(AudioSettings.SFX_VOLUME)
...
pygame.mixer.music.set_volume(AudioSettings.MUSIC_VOLUME)
```
**After:**
```python
sound.set_volume(self._sfx_volume_for(path))
...
pygame.mixer.music.set_volume(self._music_volume_for(track_path))
```
plus helper methods:
```python
def _sfx_volume_for(self, path: str) -> float: ...
def _music_volume_for(self, track_path: str) -> float: ...
```
**Why:** Ensure runtime playback honors the new per-file settings constants for both loaded SFX and direct music playback.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** 46-48, 66 (modified)
**Before:** Audio docs described only global music/SFX volume settings.
**After:** Audio docs now describe `SFX_FILE_VOLUMES` and `MUSIC_FILE_VOLUMES` precedence over global defaults and call out per-file muting via `0.0`.
**Why:** Keep architecture documentation synchronized with the implemented audio configuration behavior.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-10T19:23-04:00 — Interactive battle: command menu, abilities, potions, defending

**File:** systems/battle.py
**Lines (at time of edit):** whole-file rewrite of the public API
**Before:** A single `step()` call resolved one turn end-to-end, picking targets automatically for both sides. No notion of player commands; defending and items did not exist.
**After:** Turn loop is split into `start_turn()` (advances the queue, emits `TurnStartEvent`, auto-resolves enemy actions inline) and four player command verbs — `submit_attack`, `submit_defend`, `submit_ability(ability_id)`, `submit_potion`. `is_awaiting_command()` exposes the player-input gate; `current_actor` exposes the actor whose turn is live so the view can highlight them. `Combatant` gains `learnset` and `is_defending`; defending halves incoming damage (`BattleSettings.DEFEND_DAMAGE_DIVISOR`) until the defender's own next turn. `Battle.__init__` now takes an `abilities` dict and a starting `potions` count (defaulting to `BattleSettings.STARTING_POTIONS`). The module-level docstring documents the eventual FFX-style Conditional Turn-Based queue as the destination for the current sequential ordering.
**Why:** First baby step toward a real JRPG combat loop — the player can actually fight the demo encounter instead of watching it. Keeping the public command interface narrow and event-driven so the future CTB scheduler is a pure internal swap.
**Editor:** Frankie (Claude Opus 4.7)

**File:** core/events.py
**Lines (at time of edit):** appended after `CombatantDefeatedEvent`
**Before:** Battle event stream covered `TurnStartEvent`, `AttackEvent`, `DamageEvent`, `StatusAppliedEvent`, `CombatantDefeatedEvent`, `BattleEndedEvent`.
**After:** Added `DefendEvent`, `AbilityUsedEvent`, `HealEvent`, `PotionUsedEvent` so views can narrate the four new player verbs without inferring them from the existing stream.
**Why:** Keep the producer→view contract typed; new commands need new records, not overloads of existing ones.
**Editor:** Frankie (Claude Opus 4.7)

**File:** ui/battle_view.py
**Lines (at time of edit):** `consume` chain extended
**Before:** Phrased only turn-start / attack / damage / status / defeated / ended.
**After:** Phrases the four new events too: "{name} braces for the blow.", "{name} uses {ability}!", "{name} recovers {N} HP.", "{name} drinks a potion."
**Why:** Mirror the new event types in the text-narration layer so the player sees what just happened.
**Editor:** Frankie (Claude Opus 4.7)

**File:** core/scenes/battle_scene.py
**Lines (at time of edit):** whole-file rewrite of input + render
**Before:** Drained `battle.step()` while the text box was empty; pressing cancel attempted to flee.
**After:** When narration is draining, confirm still fast-forwards it. When the text box is empty and a party member's turn is waiting on input, the bottom HUD splits into a left command panel (Attack / Defend / Ability / Potion x{N}) and a right-side prompt. Picking Ability swaps the panel for the active actor's ability submenu; cancel from the submenu returns to the top-level menu, cancel from the top level still flees. The active combatant's roster line renders in `ColorSettings.YELLOW` so the player knows whose turn it is.
**Why:** Implement the requested interactive flow with the smallest possible footprint — one new render branch, no new widget classes.
**Editor:** Frankie (Claude Opus 4.7)

**File:** systems/party.py
**Lines (at time of edit):** `PartyMember` constructor + `to_dict` / `from_dict`
**Before:** `PartyMember` carried id, name, elements, stats.
**After:** Added a `learnset: list[str]` field; serialisation round-trips it.
**Why:** Battle commands need to know which ability ids each character knows; the data already exists in `data/characters/<id>.json` and was just being dropped on the floor.
**Editor:** Frankie (Claude Opus 4.7)

**File:** core/factories.py
**Lines (at time of edit):** `party_member_from_data`, `combatant_from_party_member`
**Before:** Neither factory read or propagated `learnset`.
**After:** `party_member_from_data` reads the JSON `learnset` array; `combatant_from_party_member` passes it to the new `Combatant(learnset=...)` keyword.
**Why:** Same plumbing reason — keep the JSON → runtime mapping single-seamed.
**Editor:** Frankie (Claude Opus 4.7)

**File:** settings.py
**Lines (at time of edit):** new `BattleSettings` class above `UISettings`, and `COMMAND_PANEL_WIDTH` added to `UISettings`
**Before:** No battle-feel tunables existed in settings; potion count and defend strength would have leaked as magic numbers into `systems/battle.py`.
**After:** `BattleSettings` holds `STARTING_POTIONS = 5`, `POTION_HEAL_AMOUNT = 15`, `DEFEND_DAMAGE_DIVISOR = 2`. `UISettings.COMMAND_PANEL_WIDTH = 280` controls the width of the new left-half command box.
**Why:** Honour the "no magic numbers outside settings.py" rule. New unrelated tunables get their own `*Settings` class.
**Editor:** Frankie (Claude Opus 4.7)

**File:** data/abilities/fire_punch.json (new file)
**After:** `{"id":"fire_punch","name":"Fire Punch","element":"ahi","power":0,"cost":0,"kind":"damage","target":"enemy","status":null}`
**Why:** Kailo's first ability. `power: 0` means "use the actor's base attack stat", per Layer-0 baby-step rule that damaging abilities feel like a basic attack until Layer 1 designs real numbers.
**Editor:** Frankie (Claude Opus 4.7)

**File:** data/abilities/heal.json (new file)
**After:** `{"id":"heal","name":"Heal","element":"ra","power":15,"cost":0,"kind":"heal","target":"kailo","status":null}`
**Why:** Hina's first ability. Hard-targeted at Kailo for now; target-selection UI ships when the second healable scenario does.
**Editor:** Frankie (Claude Opus 4.7)

**File:** data/abilities/curse.json (new file)
**After:** `{"id":"curse","name":"Curse","element":"aku","power":0,"cost":0,"kind":"damage","target":"enemy","status":null}`
**Why:** Tawiri's first ability. Same baby-step semantics as Fire Punch — Aku-flavored basic attack until Layer 1 wires up status effects.
**Editor:** Frankie (Claude Opus 4.7)

**File:** data/abilities/firebolt.json (deleted)
**Before:** `{"id":"firebolt","name":"Firebolt","element":"ahi","power":10,"cost":4,"status":null}`
**Why:** Unreferenced placeholder superseded by `fire_punch.json` for Kailo's interactive-battle ability. Removed rather than left around to keep the content pack honest.
**Editor:** Frankie (Claude Opus 4.7)

**File:** data/characters/kailo.json
**Before:** `"learnset": ["firebolt"]`
**After:** `"learnset": ["fire_punch"]`
**Why:** Points Kailo at the new ability id.
**Editor:** Frankie (Claude Opus 4.7)

**File:** data/characters/hina.json
**Before:** `"learnset": []`
**After:** `"learnset": ["heal"]`
**Why:** Hina now knows Heal so her command-menu Ability option resolves to something.
**Editor:** Frankie (Claude Opus 4.7)

**File:** data/characters/tawiri.json
**Before:** `"learnset": []`
**After:** `"learnset": ["curse"]`
**Why:** Same — Tawiri's Ability option now lists Curse.
**Editor:** Frankie (Claude Opus 4.7)

## 2026-05-10T19:50-04:00 — Battle UX pass: divider, compact menu, target selection

**File:** settings.py
**Lines (at time of edit):** UISettings — COMMAND_PANEL_WIDTH lowered; COMMAND_MENU_ITEM_SPACING added
**Before:** `COMMAND_PANEL_WIDTH = 280` and no per-menu spacing constant.
**After:** `COMMAND_PANEL_WIDTH = 200` so the divider sits just to the right of the party roster's widest line; `COMMAND_MENU_ITEM_SPACING = 4` so all four command rows fit inside the bottom HUD.
**Why:** Frankie's screenshot showed the divider sitting too far right and the Potion row falling off the bottom of the panel; both came down to two numbers.
**Editor:** Frankie (Claude Opus 4.7)

**File:** ui/menu.py
**Lines (at time of edit):** `Menu.render`
**Before:** Rendered at a hard-coded `FontSettings.SIZE_BODY`.
**After:** Accepts an optional `font_size` keyword; both the cursor glyph and the row label honour it. Default behaviour is unchanged.
**Why:** Lets the battle command panel use `SIZE_SMALL` so all four commands fit without enlarging the panel; other call sites (title, pause, world) keep the larger body font.
**Editor:** Frankie (Claude Opus 4.7)

**File:** core/scenes/battle_scene.py
**Lines (at time of edit):** scene rewrite for target selection
**Before:** Attack always hit the first living enemy; Heal always healed Kailo (hard-coded by the ability JSON); Potion always healed the user. No target picker.
**After:** Choosing Attack, a damage / heal ability, or Potion enters a target-selection state. The candidate pool is the living enemies for damaging commands and the living party for Heal / Potion. A blinking yellow `>` cursor appears next to the highlighted target on the roster; up / down cycle the cursor; confirm submits with `target_id`; cancel returns to the menu the player came from (ability submenu for abilities, top-level command menu otherwise). Defend skips targeting because it acts on the defender themselves. The command panel renders with `font_size=SIZE_SMALL` and the new tight `COMMAND_MENU_ITEM_SPACING`. Roster drawing was extracted into helper methods so the same loop handles both the active-actor yellow highlight and the targeting cursor.
**Why:** Implements Frankie's "you should be able to select which enemy / which ally" request and removes the placeholder hard-codes from the ability JSON path.
**Editor:** Frankie (Claude Opus 4.7)
