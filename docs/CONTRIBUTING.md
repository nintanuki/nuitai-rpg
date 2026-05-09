# Contributing to Nuitai RPG

This guide answers one question: **"I want to add or change X — what files do I touch?"**

The rules in [.github/copilot-instructions.md](../.github/copilot-instructions.md) still apply on top of this. The artistic intent in [VISION.md](VISION.md), the strategy in [ROADMAP.md](ROADMAP.md), and the live task list in [TODO.md](TODO.md) are still authoritative. This file is a quick lookup table that points you at the right seam.

## The cardinal rule

**Content is data, not code.** Adding a new ability, enemy, character, dungeon, or dialogue tree is a JSON-only change. Code changes only when a new *kind* of content is introduced.

If you find yourself writing a new `if name == "..."` branch in gameplay code, stop — that branch should be a field in a JSON file, not a line of code.

## How to add a new...

| Change                       | What to edit                                                                                   | Pattern to imitate                                                          |
| ---------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **Ability**                  | New file under [data/abilities/](../data/abilities/).                                          | [data/abilities/firebolt.json](../data/abilities/firebolt.json)             |
| **Enemy**                    | New file under [data/enemies/](../data/enemies/).                                              | [data/enemies/shade.json](../data/enemies/shade.json)                       |
| **Party member (character)** | New file under [data/characters/](../data/characters/).                                        | [data/characters/kailo.json](../data/characters/kailo.json)                 |
| **Dungeon / region**         | New file under [data/dungeons/](../data/dungeons/).                                            | [data/dungeons/demo_room.json](../data/dungeons/demo_room.json)             |
| **Dialogue tree**            | New file under [data/dialogue/](../data/dialogue/).                                            | [data/dialogue/opening.json](../data/dialogue/opening.json)                 |
| **Element interaction**      | [core/elements.py](../core/elements.py) only. **Single source of truth** — never duplicate.    | The `_BEATS` table.                                                         |
| **Battle event type**        | Add a frozen dataclass to [core/events.py](../core/events.py); have the producer emit it; have [ui/battle_view.py](../ui/battle_view.py) phrase it. | Existing events (e.g. `DamageEvent`).                                       |
| **Scene**                    | New file under [core/scenes/](../core/scenes/), subclassing [`Scene`](../core/scene.py).       | [core/scenes/test_world_scene.py](../core/scenes/test_world_scene.py)       |
| **Translucent overlay**      | Same as a scene, but set `OPAQUE = False` so the world below renders.                          | [core/scenes/menu_scene.py](../core/scenes/menu_scene.py)                   |
| **Save-payload field**       | Extend `to_dict` / `from_dict` of the owning class **and** bump `SAVE_SCHEMA_VERSION` in [core/save.py](../core/save.py) with a `migrate()` step. | `Party.to_dict` / `from_dict` in [systems/party.py](../systems/party.py).   |
| **JSON → runtime object**    | Add a factory function in [core/factories.py](../core/factories.py); call it from the scene.   | `combatant_from_enemy_data`.                                                |
| **UI widget**                | New file under [ui/](../ui/). Always render through [ui/text_renderer.py](../ui/text_renderer.py); never blit raw fonts. | [ui/text_box.py](../ui/text_box.py), [ui/menu.py](../ui/menu.py)            |
| **Sound effect / music**     | Drop the file in [assets/audio/](../assets/audio/) and register it in `AudioSettings.SOUND_EFFECTS` or `MUSIC_TRACKS` in [settings.py](../settings.py). | The `AudioSettings` registry.                                               |
| **Tunable / constant**       | [settings.py](../settings.py) only. **No magic numbers anywhere else.** Document units in a comment. | `UISettings.TYPEWRITER_CHARS_PER_SECOND`.                                   |
| **Input mapping**            | [ui/input_map.py](../ui/input_map.py) for the logical action; [settings.py](../settings.py) `InputSettings` for the raw button id. | `is_confirm`, `is_cancel`.                                                  |
| **Lore article**             | Edit or add a Markdown file under [docs/lore/](lore/) and update [docs/lore/INDEX.md](lore/INDEX.md). | Any existing article.                                                       |

## What does *not* belong in code

- **Element names in dialogue.** Characters never say "Ahi" or "fire mage." See the rule in [.github/copilot-instructions.md](../.github/copilot-instructions.md).
- **Hard-coded prose in scenes.** Every line a player reads should come from `data/dialogue/` (or its room's flavor field), not from a Python literal.
- **Strength/weakness tables.** Anywhere that needs them imports from [core/elements.py](../core/elements.py).
- **`print()` calls in gameplay paths.** All in-game text renders to the screen via [ui/text_renderer.py](../ui/text_renderer.py). The console is for crash logs and developer diagnostics only.

## After any change

The required actions in [.github/copilot-instructions.md](../.github/copilot-instructions.md) apply: append a [CHANGELOG.md](CHANGELOG.md) entry, update [ARCHITECTURE.md](ARCHITECTURE.md) if a system's shape changed, mark [TODO.md](TODO.md) items `[x]`, and run [TESTING.md](TESTING.md) smoke checks.
