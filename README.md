# Nuitai RPG

A turn-based, sprite-based JRPG set in the world of **Nuitai**, an ocean planet of scattered islands that spiral around a permanent maelstrom, where magic is cast by motion and every fighter draws on two of six elements.

Long-term inspirations: *Chrono Trigger*, *Final Fantasy IV*, *Dragon Quest*. The eventual target is a complete SNES-style 2D JRPG with hand-drawn pixel art and an original score, all created by the author without using free assets.

## Status

**Layer 0 — engine bring-up.** The project is in early scaffolding. `python main.py` boots a windowed pygame surface with a CRT overlay and an initialized audio manager; there is no gameplay yet.

The game is being built in clearly-defined layers. See [docs/ROADMAP.md](docs/ROADMAP.md) for the full plan and acceptance criteria for each layer.

| Layer | Description | Status |
| ----- | ----------- | ------ |
| 0 | Engine spike: scenes, save/load, dialogue box, turn queue, in-window text rendering | In progress |
| 1 | Vertical-slice text demo: three-character party, one small dungeon, one boss | Planned |
| 2 | Content & polish on the same engine: town hub, second dungeon, full element coverage | Planned |
| 3 | Dragon-Quest stage: tile maps + sprite encounters, narration still in the text box | Planned |
| 4 | Art & audio pass: original sprites, original music, animated battles, ship/maelstrom system | Planned |
| 5 | Full vision: airship, Po'lelo stone-speech puzzles, complete world, full story arcs | Planned |

Every layer is **shippable on its own**. The Dragon Quest layer in particular is treated as a legitimate destination, not a stop-over.

## The world

Nuitai is documented in [docs/lore/INDEX.md](docs/lore/INDEX.md) — 114 articles across 12 categories (people, places, organizations, languages, professions, species, rituals, technologies). The World Anvil export is preserved at [docs/LOREDUMP.html](docs/LOREDUMP.html). The original World Anvil Page can be found [here](https://www.worldanvil.com/w/nuitai-nintanuki).

The artistic and design pillars that come from the lore are summarized in [docs/VISION.md](docs/VISION.md).

## The starting party

The Layer-1 demo will have three playable characters with different battle rolls. Together they cover all six elements with no overlap.

| Character | Elements | Role | Source article |
| --------- | -------- | ---- | -------------- |
| **Kailo** | Ahi (Fire) + Wai (Water) | Fighter / Defender | [docs/lore/person/kailo-the-wandering-chef.md](docs/lore/person/kailo-the-wandering-chef.md) |
| **Hina** | Ra (Light) + Lau (Nature) | Enhancer / Healer | [docs/lore/person/hina-the-māra-priestess.md](docs/lore/person/hina-the-māra-priestess.md) |
| **Tawiri** | Mana (Spirit) + Aku (Shadow) | Blaster / Saboteur | [docs/lore/person/tawiri-the-elderly-caller.md](docs/lore/person/tawiri-the-elderly-caller.md) |

A fourth character, **Maika** (Lau + Mana, healer / blaster — [docs/lore/person/maika-the-maki-sage.md](docs/lore/person/maika-the-maki-sage.md)), will also appear as an NPC in the demo and join the party in Layer 2.

## Requirements

- Python 3.10+
- `pygame` 2.5+

## Run

```powershell
python main.py
```

## Controls (defaults)

| Action            | Keyboard | Controller            |
| ----------------- | -------- | --------------------- |
| Toggle fullscreen | `F11`    | `BACK`                |
| Quit              | `Esc`    | `START+SELECT+L1+R1`  |

## Documentation

| Document | Purpose |
| -------- | ------- |
| [docs/VISION.md](docs/VISION.md) | The artistic North Star. What "done" feels like. Largely immutable. |
| [docs/ROADMAP.md](docs/ROADMAP.md) | The six-layer plan. Acceptance criteria and asset requirements per layer. |
| [docs/TODO.md](docs/TODO.md) | The current layer's actionable tasks (code, writing, and art alike). |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the code currently fits together. |
| [docs/TESTING.md](docs/TESTING.md) | Manual smoke checks. |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Append-only history of every change. |
| [docs/lore/INDEX.md](docs/lore/INDEX.md) | Per-article TOC of the Nuitai world bible. |
| [.github/copilot-instructions.md](.github/copilot-instructions.md) | Rules for human or AI editors. |

## Project layout

```
core/            Domain types: elements, scenes, save state, event records.
systems/         Gameplay systems: audio, battle, party, dialogue.
ui/              Renderers and widgets: text box, menu, battle view, world view.
utils/           Pure helpers and one-shot tools (e.g. the lore splitter).
data/            JSON content packs: characters, abilities, enemies, dungeons, dialogue.
assets/          Fonts, graphics, audio.
saves/           Player save files (gitignored).
docs/            Vision, roadmap, architecture, testing, changelog, lore.
crt.py           CRT post-processing overlay.
main.py          Entry point + GameManager.
settings.py      All tunable constants.
```

## Asset credits

- `assets/font/Pixeled.ttf` — *Pixeled* by OmegaPC777 (free for personal & commercial use).
- `assets/graphics/effects/tv.png` — CRT overlay reused from the arcade cabinet asset set. Originally created and coded by Clear Code of YouTube.
- The long-term goal is for **all** sprite art, music, and writing to be original work by the author. Free placeholder assets used during early layers will be credited here as they are added, and replaced as the project matures.
