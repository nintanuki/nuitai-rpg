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
