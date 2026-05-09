# Game data

This directory holds the JSON content the engine reads at runtime.
Code under `core/`, `systems/`, and `ui/` is generic; everything that
defines specific characters, places, abilities, enemies, dungeons, and
dialogue lives here.

Layer 0 ships an empty tree so the engine can boot. Layer 1 will
populate each subfolder with the real opening content.

## Subfolders

- `characters/` — One JSON per party member: id, display name, two
  elements, base stats, learnset.
- `abilities/` — One JSON per ability: id, name, element, power, cost,
  status effects.
- `enemies/` — One JSON per enemy: id, name, element, stats, loot.
- `dungeons/` — One JSON per region: id, name, room layout, encounter
  table, exits.
- `dialogue/` — One JSON per dialogue tree: id, lines, branches.

Every file in every subfolder must contain a top-level `id` field;
that id is what other content and code references.

## Loader

`core/data_loader.py` exposes `DataLoader.load(kind)` which reads
every JSON file in `data/<kind>/` and returns them indexed by id. The
loader caches per-kind, so reloading on a save/load round-trip is
free.
