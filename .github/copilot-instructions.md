# Copilot Instructions for Nuitai RPG

These rules apply to **every** editor of this codebase, human or AI. Read this file before each session.

Nuitai RPG is a long-horizon, layered project. The artistic vision in [docs/VISION.md](../docs/VISION.md) is the North Star; the layered plan in [docs/ROADMAP.md](../docs/ROADMAP.md) is the strategy; the tasks in [docs/TODO.md](../docs/TODO.md) are the tactics. Engine work that looks like overkill for the current layer is usually correct — the engine has to support all five future layers without rewrites.

## Required reading order (before any change)

1. [README.md](../README.md)
2. [docs/VISION.md](../docs/VISION.md)
3. [docs/ROADMAP.md](../docs/ROADMAP.md)
4. [docs/TODO.md](../docs/TODO.md)
5. [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
6. [docs/CHANGELOG.md](../docs/CHANGELOG.md)
7. The relevant lore article(s) under [docs/lore/](../docs/lore/) if your task touches characters, places, factions, or world systems. The TOC is at [docs/lore/INDEX.md](../docs/lore/INDEX.md).
8. The source files relevant to your task.

If a question is asked about *why* code was written a certain way, that is a request for an **explanation**, not a request for a code change. Do not modify code unless the user explicitly asks for a change.

## Codebase survey discipline

This repo has grown beyond the size at which a single recursive glob is reliable. The `docs/lore/` directory alone contains ~100+ articles; a `**/*` sweep over the root will hit truncation limits and return a **prefix** of the file list with a warning that is easy to overlook. Add up the rest of the source and content directories and the same risk applies to any wide search.

Rules to avoid silently building a mental model from a partial view:

- **Never conclude that a file does not exist from a single glob.** If a file is referenced by another file you have read (an import, a doc link, a `from x.y import Z`) and a glob says it is missing, the glob is wrong before the codebase is. Verify with a targeted `bash ls` / `find` / `grep` against the absolute path before stating "this file is missing" to the user.
- **Prefer absolute-path glob patterns** (`C:\full\path\to\dir\**\*.py`) over relative ones with a `path:` parameter on this project. The relative form has misbehaved on Windows here at least twice.
- **Watch for truncation warnings** on any glob that returns close to its result cap. If you see "Results are truncated," treat the result as a prefix only — re-query with a tighter pattern (single subdirectory, single extension) and stitch the picture together from multiple narrower calls.
- **Cross-check with `bash`** for anything load-bearing: `ls -la`, `find <path> -name "<pattern>"`, `wc -l`, `tail`. These run in the Linux workspace mount and have not exhibited the truncation issue.
- **When in doubt, ask.** It is cheaper to ask "I'm not seeing X — is it really missing?" than to spend a turn confidently announcing a non-fact and the next turn apologising for it.

## File-repair discipline (when a file looks broken)

The Linux sandbox mount, the Cowork-side cache, and the canonical Windows file are three views of the same file. They can diverge mid-edit, especially while OneDrive is reconciling. A file that looks truncated mid-token on one side may be complete on another.

Two rules learned the hard way:

- **Do not bash-append to repair "truncation" on the Linux mount.** The mount may be showing a stale snapshot of a file that is actually complete on the Windows / Cowork side. A bash `cat >> file` against the mount gets resolved by OneDrive as a delta against the complete file — your append lands *after* the already-correct content, producing two copies of whatever you appended. The user's Python then hits the orphan first line and reports a syntax error that did not exist a moment ago.
- **Use the Edit tool for surgical repairs.** Edit operates on the canonical Cowork view, which is what the user actually opens and what `python main.py` reads. If you see a file looks broken, first re-read the same byte range through the Read tool — if Read shows a clean file, the bash view was stale and there was never a problem to fix. If Read shows duplicate or orphan content, use Edit with the orphan block as `old_string` and the empty (or merged) block as `new_string`.

If a file is genuinely incomplete in both views and you need to add content, use Write or Edit, not bash. Cross-check by running `python -c "import ast; ast.parse(open('path').read())"` against the same file via the Linux mount — if it parses there, it should parse for the user; if Cowork and Linux disagree, trust Cowork.

## The lore folder is read-only

The articles under [docs/lore/](../docs/lore/) are the authoritative world bible, maintained **outside** this repo (currently on World Anvil and imported via `utils/lore_to_markdown.py`). They are **never** edited from inside this repo — not by humans, not by AI assistants, not by linters or formatters. Read them freely for context; do not write to them.

When the user describes how a **game system** should work (battle math, element interactions, equipment rules, status effects, economy, etc.), that intent goes in `docs/ARCHITECTURE.md` (or a sibling doc under `docs/`) — **never in `docs/lore/`**. The lore folder describes the world; `docs/` describes the game.

If you believe a lore article is contradicted by gameplay, raise it with the user — do not "fix" the article. The resolution is either to change the gameplay or to update the lore externally and re-import.

## Required actions (after any change)

- Append an entry to [docs/CHANGELOG.md](../docs/CHANGELOG.md) using the format at the top of that file (ISO 8601 timestamp with timezone, file path, line numbers at time of edit, before/after blocks, why, editor name including the AI model used).
- Update [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) if your change altered how a system works.
- Update [docs/TODO.md](../docs/TODO.md) if you completed or added a roadmap item (mark `[x]`, do not delete).
- Run the manual smoke checks in [docs/TESTING.md](../docs/TESTING.md).

## Code style

- All Python is PEP-8 compliant.
- Less code is better; clean and readable is best.
- Prefer clear names over short ones. New class and function names must clearly describe their purpose.
- Do not change function or variable names unless the role has *completely* changed.
- No dead imports, unused variables, unused functions, or legacy code.

## Architecture rules

- `GameManager` ([main.py](../main.py)) stays thin. Offload responsibilities to dedicated classes under `core/`, `systems/`, `ui/`, or `utils/`.
- Classes communicate through `GameManager` where possible. Avoid direct cross-system reach-arounds.
- Keep middlemen minimal: if A calls B and B only calls C, have A call C directly.
- All constants live in [settings.py](../settings.py). **No magic numbers anywhere else.** When adding a constant, include a comment explaining its units and effect.
- Prefer adding a new `*Settings` class in `settings.py` over expanding an existing one when the new field is not closely related to its neighbors.
- **Gameplay logic emits events; views consume them.** A `Battle` does not draw; a `BattleView` does. A `DialogueRunner` does not draw; a `TextBox` does. This separation is what allows the same engine to drive Layers 1–5.
- **Element math has one home:** `core/elements.py`. Strength/weakness rules are not duplicated in JSON, in battle code, or in views.
- **Content is data, not code.** Characters, abilities, enemies, dungeons, and dialogue live as JSON under `data/`. Code only changes when a new *kind* of content is introduced.
- **Save/load is a first-class feature, not a Layer 5 add-on.** Every gameplay object that holds runtime state exposes `to_dict()` / `from_dict()`. Saves carry a schema version; schema changes ship with a migration.

## File and function layout

- Inside a class, group functions by role (init, input, update, render, etc.).
- `update` and `run` go **last** and should only call other functions on the class.
- Separate logical sections inside a file with an all-caps banner comment, exactly this style:

  ```python
      # ------------------------------------------------------------------
      # SECTION NAME
      # ------------------------------------------------------------------
  ```

  Match the leading indentation of the surrounding class body. Keep dashes the same length and the name in ALL CAPS.

## Comments and docstrings

- Every class and function has a docstring with a one-line summary, plus `Args:` / `Returns:` blocks where applicable.
- Do not remove docstrings — update them in place if behavior changes.
- Do not remove comments unless they are inaccurate; prefer updating them.
- Comments explain **why**, not what.
- Do not leave comments noting that a change was made unless they explain a non-obvious bug fix.

## UI text and presentation

- ALL text displayed to the user in-game must be **ALL CAPS**. The pixel font (`Pixeled`) is designed for caps-style retro display. Enforce this at the text renderer so gameplay code can pass any case.
- **Nothing is printed to the terminal as gameplay output.** All in-game text renders to the pygame surface. The console is for crash logs and developer diagnostics only.
- Documentation files stay in normal sentence case.
- Element names are mechanics-and-symbolism only. They are **never spoken by characters in dialogue** and never appear as flavor text in the world ("this sword has +5 fire damage" — no). The world has cooks, monks, priestesses, witch doctors. It does not have "fire mages."

## Mental testing checklist

- `python main.py` boots without console errors.
- The window opens at the resolution defined by `ScreenSettings`.
- `F11` and `BACK` toggle fullscreen.
- The quit chord (`START + SELECT + L1 + R1`) on any controller exits cleanly.
- The CRT overlay renders only in windowed mode.
- No new magic numbers leaked outside `settings.py`.
- No new `print()` calls in gameplay code paths (developer-only diagnostics excepted; gate them behind `DebugSettings`).
- Save / load round-trips cleanly for every new piece of runtime state introduced.

For the actionable run-through, see [docs/TESTING.md](../docs/TESTING.md).
