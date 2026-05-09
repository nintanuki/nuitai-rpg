# Nuitai RPG — Roadmap

> The strategic plan. This document is alive. Update it when a layer's scope changes, when a layer ships, or when a new dependency between layers is discovered.

This roadmap describes the project as a sequence of **vertical slices**. Every layer is end-to-end playable on its own and is shippable as a checkpoint. The underlying engine (battle math, scene stack, save format, dialogue trees, content data) is shared across every layer; only the renderers and the asset library grow.

For the artistic North Star, see [VISION.md](VISION.md). For the current actionable task list, see [TODO.md](TODO.md).

---

## Layer 0 — Engine spike

**Goal:** Prove that the engine can host a JRPG. No story, no encounters, no characters yet — just the systems a JRPG depends on, exercised by trivial placeholder scenes.

### Acceptance criteria

- [ ] A scene **stack** (push / pop, not switch). Scenes can layer on top of each other (e.g. menu over world).
- [ ] A `TextRenderer` that draws word-wrapped, typewriter-effect text into a `pygame.Rect` using the `Pixeled` font. **Zero `print()` calls in production code paths.**
- [ ] A standard JRPG-style `TextBox` widget: bordered, advance-on-button, auto-paginating.
- [ ] A cursor-driven `Menu` widget (controller- and keyboard-driven).
- [ ] A `Battle` object that runs a turn queue and emits **events** (`AttackEvent`, `StatusAppliedEvent`, `TurnStartEvent`, `BattleEndedEvent`) rather than rendering directly.
- [ ] A `BattleView` that consumes battle events and renders them via the `TextBox`.
- [ ] A save / load subsystem: every scene and gameplay object exposes `to_dict()` / `from_dict()`. Saves are JSON, schema-versioned, with a migration hook.
- [ ] A `data/` directory with at least one example each of: character JSON, ability JSON, enemy JSON, dialogue JSON. A `data_loader` reads them.
- [ ] An `Element` enum and an element strength/weakness table — the **single source of truth** for all element math. Lives in `core/elements.py`.
- [ ] A title scene with **NEW GAME** and **CONTINUE** options. **CONTINUE** loads the most recent save.

### Asset requirements

- None beyond what already ships (the `Pixeled` font, the CRT overlay).

### Definition of done

A test scene exists where the player can: sail through a placeholder dialogue tree, open a menu, enter a placeholder battle against a placeholder enemy, win or lose, save the game, quit, relaunch, choose **CONTINUE**, and resume exactly where they left off. No real content; no real story.

---

## Layer 1 — The vertical-slice text demo

**Goal:** Ship a complete, end-to-end playable demo. ~20–30 minutes of content. All in-window text rendering, no sprites yet, free placeholder portraits for the three party members. **This is the "is the game fun?" milestone.**

### Acceptance criteria

- [ ] **Three playable party members:** Kailo (Ahi + Wai), Hina (Ra + Lau), Tawiri (Mana + Aku). Each has at least 4 abilities representing both of their elements.
- [ ] An opening cutscene (text + free placeholder portrait) on Māra Iti introducing Kailo, then Hina, then Tawiri.
- [ ] **One small dungeon** (3–5 rooms) with text-based room descriptions, ~3 random encounters per room, environmental flavor text.
- [ ] **One boss** with a thematic gimmick that requires understanding the element system to defeat (e.g. uses Aku to corrupt the party's Mana — Hina's Ra purifies it).
- [ ] **Maika appears** as an NPC in town. Refuses to join. Hints at his order's interest. Not playable yet.
- [ ] A short ending screen / credits roll.
- [ ] Save points (or save-anywhere outside of battle) work across the whole demo.
- [ ] Element strength/weakness is **felt** in combat — players who pick the right ability deal noticeably more damage and finish fights faster.

### Asset requirements

- Free portrait placeholders for Kailo, Hina, Tawiri (and optionally Maika as NPC).
- No sprites required. No music required (silence + the existing audio manager hooks are fine; SFX optional).

### Writing requirements

- Opening cutscene script (~2 pages).
- Dungeon flavor text (per room, per encounter, per boss).
- Town NPC dialogue (handful of NPCs in the starting village).
- Maika's introduction scene.
- Ending text.

### Definition of done

A friend who has never seen the project can be handed `python main.py`, play through the entire demo without help, and tell you whether it was fun. They can save mid-dungeon, quit, and resume. They never see a console window.

---

## Layer 2 — Content & polish on the same engine

**Goal:** Demonstrate that the engine can carry a full game's worth of content. Still text-rendered, still placeholder portraits, but **the world is bigger and the systems are deeper**.

### Acceptance criteria

- [ ] **Town hub** with shops (weapons, armor, items), an inn (rest / save), and ~6 named NPCs with dialogue.
- [ ] **Maika joins** the party as the fourth recruit (Lau + Mana).
- [ ] **Second dungeon** in a different region (Makua Archipelago or Lanuroa). Different enemy mix, different aesthetic in the text descriptions.
- [ ] **Status ailments** fully implemented: poison, burn, drench, blind, weaken, silence (the Mana counterpart, since silence-as-such doesn't apply when magic is motion — see [VISION.md](VISION.md) for the constraint).
- [ ] **All 6 elements** appear in at least one party member ability and one enemy attack.
- [ ] **At least one example of every element-pair affinity** (15 combos) appears in the bestiary or NPC roster, even if briefly.
- [ ] Equipment system: at least 6 weapons and 6 armor pieces, distributed by element affinity.
- [ ] Item system: consumables (food, potions, antidotes, escape rope equivalent).

### Asset requirements

- Free portrait placeholder for Maika.
- Optional: a single placeholder battle theme and a single placeholder town theme (free-licensed).

### Definition of done

A 1–2 hour playthrough exists. The player can grind, shop, gear up, learn abilities, and clear two dungeons. The element system is felt to be deep, not gimmicky.

---

## Layer 3 — The Dragon Quest stage

**Goal:** Add **graphics** without abandoning text-narrated combat. This layer is treated as a **legitimate destination**, not a way-station. A player who only ever sees Layer 3 should still be playing a complete game.

### Acceptance criteria

- [ ] A **tile-based world map and dungeon renderer**. Free-licensed tilesets are acceptable; original tiles preferred when ready.
- [ ] **Sprite-based encounter view**: enemy sprites appear on a battle background; the player's party is represented by an offscreen "first-person" perspective (à la Dragon Quest), or by static portrait stripes at the bottom of the screen — author's choice.
- [ ] **Static character portraits** during dialogue, with simple facial expression variants (neutral, surprised, angry, etc.).
- [ ] **Combat narration stays in the text box.** "THE BOAR ATTACKS! KAILO TAKES 6 DAMAGE!" is the canonical style. No animated battle moves yet.
- [ ] **Animated overworld sprites**: party leader visible on the world map, basic 4-direction walking animation.
- [ ] **NPC sprites** in towns, with basic interact-to-talk.
- [ ] **At least one ship** rendered on the world map. The maelstrom-zone speed system from [VISION.md](VISION.md) takes its first concrete form (clockwise vs counterclockwise affects travel time on the world map).

### Asset requirements

- Tilesets for at least: ocean, beach, jungle, town interior, dungeon stone.
- Enemy sprite sheets for ~10 enemies.
- Character portraits + walking sprites for the four party members.
- Basic UI tiles for menus, the text box border, and the inventory grid.
- One battle theme, one town theme, one dungeon theme — original or free-licensed; original preferred when the author's music skills support it.

### Definition of done

A player can boot the game, see a sprited title screen, walk Kailo around Māra Iti, board a ship, sail to the next island, fight enemies on a sprited battle screen with text narration, win, level up, and save. The Layer 1+2 story content has been ported into the new presentation; nothing has been *cut*, only *re-rendered*.

---

## Layer 4 — Art & audio pass (original)

**Goal:** Replace every free placeholder asset with original work by the author. Animate combat. Add the maelstrom and ship-upgrade systems. This is the "*looks like a real SNES JRPG*" milestone.

### Acceptance criteria

- [ ] **All sprites are original.** Tilesets, characters, enemies, UI.
- [ ] **All music is original.** At least one theme per major region, per major character, plus battle / boss / town / dungeon variants.
- [ ] **Animated battle sprites**: party members visible on the battle screen (à la Final Fantasy), with attack, cast, hit, and KO animations.
- [ ] **Damage popups, status icons, hit flashes.** The `BattleView` consumes the same events as Layer 0 — they just render richer.
- [ ] **Full ship-and-maelstrom system**: zones affect travel time, ship upgrades unlock new zones, the airship is foreshadowed but not yet available.
- [ ] **Sound effects** for every battle event, menu interaction, and notable world event.
- [ ] **Cutscene engine**: scripted camera moves, sprite movement, dialogue advancement, music transitions.

### Asset requirements

- Multi-month art pass. The author's own pixel-art skill is on the critical path.
- Multi-month music pass. The author's own composition is on the critical path.
- A **palette discipline document** (a sub-doc under `docs/`, when this layer begins) so every region has a coherent look.

### Definition of done

A player who plays Layer 4 cannot tell at a glance that the game is a hobbyist project. Every asset feels intentional, original, and consistent.

---

## Layer 5 — Full vision

**Goal:** Ship the complete game described in [VISION.md](VISION.md).

### Acceptance criteria

- [ ] **Airship** unlocked, lifting the party out of the maelstrom. Sky islands accessible.
- [ ] **Po'lelo (stone speech)** puzzle mechanic implemented: carve glyphs to animate stone, summon Pohaku golems, open ancient doors. See [docs/lore/article/stone-speech.md](lore/article/stone-speech.md).
- [ ] **The full party** (5–7 members; final roster TBD).
- [ ] **The full world**: every region described in the lore is visitable.
- [ ] **The full main story** — beginning, middle, end, with branching side content.
- [ ] **Endgame content**: optional superboss(es), optional dungeons, post-credits.
- [ ] **Polish pass**: balance review, dialogue editing pass, accessibility (font size options, controller remap, color-blind-safe element icons).

### Definition of done

The game is the lost SNES cartridge described in [VISION.md](VISION.md).

---

## Cross-cutting tracks

Some work doesn't belong to a single layer.

### Lore

The world bible at [docs/lore/INDEX.md](lore/INDEX.md) is the authoritative source for all setting questions. As the game writes specific scenes, the bible may be **expanded** (new NPCs for Kota Emas, new items in The Witch Doctors' inventory) but rarely *contradicted*. Contradictions go through a deliberate update to the lore file with a CHANGELOG entry.

A future Pass 2 will convert the per-article HTML files into clean markdown.

### Architecture

[ARCHITECTURE.md](ARCHITECTURE.md) is updated whenever a system's shape changes. Major engine refactors will tend to cluster between layers (e.g. the Layer 2 → Layer 3 transition will be the largest, since it introduces the sprite renderer).

### Testing

Manual smoke checks live in [TESTING.md](TESTING.md). They grow with each layer.

### Save compatibility

Saves carry a schema version. Every layer that changes the save schema **must** ship with a migration function. **Old saves never break silently.** Old saves may, in extreme cases, refuse to load with a clear in-game message ("THIS SAVE IS FROM AN OLDER VERSION AND CANNOT BE LOADED.") — but this is a last resort.
