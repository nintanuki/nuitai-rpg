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
