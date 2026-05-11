# Nuitai RPG — Tooling

> Why this project is built in **pygame + VS Code + AI assistance**, what the realistic alternatives are, and the conditions under which switching would actually be the right call. This document is alive — revisit it at the end of every layer.

For the artistic North Star, see [VISION.md](VISION.md). For the current code shape, see [ARCHITECTURE.md](ARCHITECTURE.md). For the layer plan, see [ROADMAP.md](ROADMAP.md).

## The question

Is building a full JRPG in pygame, hand-written in Python, with AI assistance via VS Code, sustainable — or is it a trap that gets worse as the project grows?

## The short answer

**Stay in pygame.** The risks people usually cite — "pygame can't handle a full JRPG," "code dives for every GUI tweak," "huge projects drown in their own files" — are about *architecture*, not about pygame. The architecture in [ARCHITECTURE.md](ARCHITECTURE.md) already addresses them: a scene stack, an event-driven battle/dialogue model, a JSON content loader with factory seams, a single-source-of-truth settings module, no magic numbers, no `print()` calls in gameplay paths, and the cardinal rule from [CONTRIBUTING.md](CONTRIBUTING.md) — **content is data, not code**. Most of what makes large projects unmaintainable is already prevented here.

The remaining costs of pygame are real but bounded, and the costs of switching engines mid-project are larger than they look.

## Pros and cons

### Pygame + VS Code + AI (the current stack)

**Pros**

- **The architecture already exists.** Scene stack, event bus, content packs, save migrations, audio manager, CRT pass — all written, all tested at Layer 0. An engine switch throws this away.
- **Counts as a coding hobby.** The project is hand-written Python with explicit architecture. Refactoring, schema design, save migration, event modeling — this is real CS practice, not engine-config practice. That's the framing that justifies the time spent.
- **Content scales independently of code.** Adding a new ability, enemy, character, dungeon, or dialogue tree is a JSON-only change (see the table in [CONTRIBUTING.md](CONTRIBUTING.md)). The project can grow to hundreds of content files without the code growing proportionally.
- **AI assistance works well with the current structure.** Because each content file is small and isolated, the AI rarely needs to load the whole codebase to make a content change. Token usage is bounded by the size of the *seam* being edited, not the size of the project.
- **No engine lock-in.** All gameplay data is JSON. If a future port is ever needed, the content survives.
- **Total control over presentation.** The CRT overlay, the typewriter text box, the ALL-CAPS Pixeled-font convention, the precise battle-event phrasing — pygame imposes no UI of its own to fight against. The "lost SNES cartridge" feel from [VISION.md](VISION.md) is easier to hit when nothing in the engine is trying to look modern.

**Cons**

- **No visual editor.** Every UI tweak is a code edit. Mitigated by `UISettings` and `BackgroundSettings` in [settings.py](../settings.py) — most cosmetic changes are already a single-line constant edit, not a code dive — but adding new UI widgets is still raw pygame work.
- **No built-in scene editor, tilemap editor, or animation editor.** Layer 3+ (the Dragon Quest tier) will need a tilemap workflow; Tiled + a JSON exporter is the standard answer, but it's a thing to build.
- **Animation is manual.** Sprite sheets, frame timing, easing — all hand-rolled. Fine at Layer 0–2, real work at Layer 4–5.
- **AI token cost grows with code complexity.** Even with good architecture, *engine-level* changes (battle system, save schema, scene stack) require the AI to read multiple core files. Mitigated by keeping `core/` small and well-documented, but real.
- **Solo problem-solving on engine bugs.** No "ask in the Godot forum"-sized community for niche pygame issues.

### Godot

**Pros**

- **Scene/node system + Resource files** solve the data problem natively. Custom Resources in Godot are roughly what `data/*.json` is here, with editor support.
- **GDScript is Python-like.** Of all engine switches, this is the smallest cognitive jump from the current code.
- **Built-in tilemap, animation, particle, and UI editors.** Layer 3–5 work would be substantially faster.
- **Still counts as coding.** GDScript is real scripting; Godot has a strong "code-first" culture. The hobby framing survives.
- **Improving AI tooling.** Modern AI assistants handle GDScript reasonably well now.

**Cons**

- **Throws away the existing engine.** Scene stack, save migrations, event records, audio manager, factories — all rewritten. That's weeks of work to get back to where Layer 0 already is.
- **Learning curve.** Node lifecycle, signals, the editor's quirks, export pipelines, scene instancing — not hard, but not free either.
- **Less control over retro presentation.** Achievable, but the engine's defaults pull toward "modern indie" rather than "SNES cartridge." More work to fight defaults than to define from scratch.
- **The data files reshape.** Existing JSON would need to be converted to `.tres` Resource files or kept as JSON with a custom loader — either way, [core/factories.py](../core/factories.py) and [core/data_loader.py](../core/data_loader.py) get rewritten.

### GameMaker

**Pros**

- **Battle-tested for 2D pixel-art games.** *Undertale*, *Hyper Light Drifter*, *Hotline Miami*. The target aesthetic is exactly what GameMaker is good at.
- **Sprite, room, and animation tools are excellent** out of the box.

**Cons**

- **GML is a proprietary scripting language.** It's a real language and a real skill, but it's a GameMaker-only skill — harder to defend as general CS practice.
- **Licensing.** Free for non-commercial; paid for export to most platforms.
- **Everything is rewritten.** Same cost as Godot, with less skill transfer back to general programming.

### RPG Maker (MZ / MV / Unite)

**Pros**

- **Purpose-built for exactly this genre.** Turn-based JRPG, tile-based maps, event-driven NPCs, dialogue trees, items, equipment, classes, skills — all first-class.
- **Fastest path to a finished JRPG, full stop.** The thing that takes years in pygame is the thing RPG Maker hands you on day one.
- **Active asset and plugin ecosystem.**

**Cons**

- **Largely *not* coding.** Most of the workflow is the editor; plugin scripting (JavaScript in MV/MZ) is real but secondary. The "coding hobby" framing weakens significantly.
- **Hard to escape the RPG Maker *look* and *feel*.** Possible, but the default combat UI, menu layout, and pacing are recognisable from a mile away. The lost-SNES-cartridge identity from [VISION.md](VISION.md) would have to fight the engine the whole way.
- **Custom systems are awkward.** The element system in [core/elements.py](../core/elements.py), the FFX-style CTB queue planned for [systems/battle.py](../systems/battle.py), the data-driven background templates — all of these would be plugin work or workarounds, not native expression.

## Why architecture matters more than engine

The reason a 60-hour JRPG drowns its developer is almost never the engine. It's that **content lives inside code**, and the codebase grows linearly with the game's content. Every new NPC adds a Python class. Every new ability is a new branch in a damage function. Every dialogue beat is a string literal in a scene. By the time the project has 200 NPCs, the code is unmaintainable, and the AI can't make targeted edits because everything touches everything.

This project is *not* on that path. The Layer 0 architecture forces a separation: gameplay code is small and stable; content is many small JSON files. [core/factories.py](../core/factories.py) is the only place that converts data to runtime objects. [core/elements.py](../core/elements.py) is the only place that knows the strength/weakness table. [settings.py](../settings.py) is the only place tunables live. As content grows, the *number of files* grows, but the *complexity of any one file* does not.

That's the property that makes the project scalable in pygame — and it's the property that makes AI assistance affordable, because the AI almost never has to load the whole project to make a change.

## Conditions under which switching is the right call

Stay in pygame **unless one of the following becomes true**:

1. **Layer 3+ tilemap and animation work consistently takes more than ~30% of total dev time per layer.** That's the threshold where Godot's editor starts paying for the switch cost.
2. **Engine-level changes (battle, save, scene stack) become the bottleneck, not content.** If the AI is regularly thrashing through `core/` to make small edits, the engine itself has grown too big and a Godot rewrite *of just the engine* (with content ported) starts to look reasonable.
3. **A platform requirement appears that pygame can't meet** — e.g. shipping to consoles or mobile. Godot and GameMaker both export to platforms pygame cannot.
4. **Motivation collapses around tooling friction specifically.** If three consecutive sessions stall on "I wanted to tweak the UI and ended up rewriting a renderer," the editor-based engines are objectively the better tool. Note the word *specifically* — general project fatigue is a different problem, and an engine switch will not fix it.

None of these are true today. Revisit at the end of each layer.

## On AI token usage

The token cost of working on this project is a function of three things:

1. **How much of the codebase the AI has to read to make a change.** Mitigated by the data-driven architecture; most changes are confined to one JSON file plus, at most, one factory.
2. **How much of the lore the AI has to read to write in-world content.** This is the *real* token cost on this project. The 114-article lore library in [docs/lore/](lore/) is large, and writing a single new dialogue tree may need five to ten of those articles in context. Worth keeping an eye on; the [INDEX.md](lore/INDEX.md) is the file the AI should learn to use as a router rather than reading everything.
3. **How much architectural reasoning a change requires.** Engine-level work (event types, save migrations, scene-stack invariants) is expensive because the AI has to hold multiple `core/` files at once. Content work is cheap.

The structural fix is the one this project already applies: keep the engine small, keep content as data, and keep documentation tight enough that the AI can rebuild context from `docs/` rather than from re-reading source.

A switch to Godot would not reduce token usage in any meaningful way — the lore is still the lore, and the architectural reasoning is still architectural reasoning. It would reduce *some* editor-driven friction, at the cost of throwing away an engine that already exists.

## Decision

**Pygame + VS Code + AI assistance, indefinitely, with the conditions above as the only triggers to reconsider.** No engine switch is planned. The energy that would go into an engine switch goes instead into Layer 1 content, the Tiled integration planned for Layer 3, and keeping `docs/` tight so AI assistance stays affordable.
