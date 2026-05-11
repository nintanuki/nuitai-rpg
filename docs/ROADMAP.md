# Nuitai RPG — Roadmap

> The strategic plan. This document is alive. Update it when a layer's scope changes, when a layer ships, or when a new dependency between layers is discovered.

This roadmap describes the project as a sequence of **vertical slices**. Every layer is end-to-end playable on its own and is shippable as a checkpoint. The underlying engine (battle math, scene stack, save format, dialogue trees, content data) is shared across every layer; only the renderers and the asset library grow.

For the artistic North Star, see [VISION.md](VISION.md). For the current actionable task list, see [TODO.md](TODO.md).

> **2026-05-11 reframe:** at the close of the Pass-1 / Pass-2 overworld work, the layer plan was significantly compressed. The original five-layer "text → text+portraits → tile-and-sprite → animated → original-art" ramp existed to de-risk the engine, but the engine has now been de-risked: the scene stack, save round-trip, battle simulation, dialogue runner, and tile-based overworld with grid-stepped movement / random encounters / HP-and-inventory persistence are all in the tree and verified. **Layer 1 has absorbed most of the original Layers 2 and 3** and is now framed as "the playable cartridge" — a complete short JRPG that ships as a one-shot. See [docs/design/oneshot.md](design/oneshot.md) for the full Layer-1 plan. Layers 2+ still describe the longer-arc work (more dungeons, more story, original art and music, the maelstrom + ship system, the airship and stone-speech endgame) but their scope contracts because Layer 1 is doing more of the foundational work up front.

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

## Layer 1 — The one-shot (the playable cartridge)

**Goal:** Ship a complete, end-to-end playable JRPG. One dungeon, one boss, three party members, ~30 minutes of content. The tile-based overworld engine carries the exploration; battles stay narrated in the text box. This is the **"is the game fun?"** milestone, and it is also the milestone where the engine stops growing and content starts.

> Full design: [docs/design/oneshot.md](design/oneshot.md). Read it before picking up Layer-1 work.

### Acceptance criteria

- [ ] **Three playable party members:** Kailo (Ahi + Wai), Hina (Ra + Lau), Tawiri (Mana + Aku). Each has at least 4 abilities representing both of their elements.
- [ ] An opening cutscene introducing the party — text-driven, with placeholder portraits visible in the menu.
- [ ] **One dungeon** (4–6 rooms / cells) with placeholder tile art, walked on the overworld, with random encounters via the step-counted system already shipping in Pass 2.
- [ ] **One village hub** at the dungeon's mouth — ~3–5 NPCs, one shop, one save point, one heal point. Dialogue trees flat (one screen each, no branching beyond first-time / repeat).
- [ ] **One boss** with a thematic gimmick that requires understanding the element system to defeat. Pinned down during dungeon design.
- [ ] **Maika appears** as an NPC. Refuses to join. Hints at his order's interest. Not playable yet.
- [ ] **A short ending screen** when the boss is defeated.
- [ ] **Save anywhere outside of battle** (and at save points specifically, with on-screen feedback).
- [ ] **Heal points** restore HP and MP to full with confirmation feedback.
- [ ] **The seven-stat schema** (HP / MP / ATK / DEF / MATK / MDEF / SPD) drives party + enemy stats; element strength/weakness still gates damage on top per `core/elements.py`.
- [ ] **FFX-style CTB** turn order with a visible upcoming-turns strip during battle.
- [ ] **Each enemy has an ability** in addition to a basic attack — `curse` (Aku debuff), `firebolt`, `wave_fist`, `heal`, `shakas_light`, `spirit_blast`, plus the boss's signature.
- [ ] **Inventory navigable outside battle**, with item descriptions, with potions usable on a chosen party member.
- [ ] **Window-frame style** consistent across battle, overworld, and menus — rounded white border, black fill, the same widget for every text panel.
- [ ] **Y opens the menu, B closes it** on controller; Tab opens it on keyboard.
- [ ] Element strength/weakness is **felt** in combat — players who pick the right ability deal noticeably more damage and finish fights faster.

### Asset requirements

- **Temporary, borrowed from Dungeon Digger:** player sprite (4 facings), walkable / non-walkable tiles, doors, NPC sprites. Replaced by original Aseprite work as the art track catches up.
- **Original, in this milestone:** none required to ship — placeholder borrowed art is acceptable for the milestone. Original art ships as it lands.
- **Element + item icons** at 16×16 (placeholder rendered as letters until Aseprite icons land).
- **Character portraits** at 32×32 (placeholder rendered as colored squares with name labels until art lands).
- **No music required.** SFX optional; the borrowed Dungeon Digger walk / wall-bump are easy wins when sourced.

### Writing requirements

- Opening cutscene script (~1–2 pages).
- Village NPC dialogue (3–5 NPCs).
- Shop greeting + flavor text.
- Save / heal point flavor lines.
- Dungeon flavor text (per cell on entry, per encounter intro, per boss intro).
- Boss intro / victory / defeat.
- Ending text.

### Definition of done

A friend who has never seen the project can be handed `python main.py`, play through the entire one-shot without help, and tell you whether it was fun. They can save mid-dungeon, quit, and resume. They never see a console window. They feel the element system in combat. The art is rough, but the *game* is whole.

---

## Layer 2 — Bigger world, deeper systems

**Goal:** Take the one-shot and grow it into a multi-region story arc. This is where the world stops being one island and starts being the maelstrom-ringed archipelago described in the lore.

### Acceptance criteria

- [ ] **Second region** (Makua Archipelago or Lanuroa) with its own dungeon and its own town hub. Different enemy mix, different aesthetic.
- [ ] **Maika joins** the party as the fourth recruit (Lau + Mana).
- [ ] **Status ailments** fully implemented: poison, burn, drench, blind, weaken, silence (the Mana counterpart). The `Combatant.statuses` field promoted from Layer 0.5 deferral.
- [ ] **All 6 elements** appear in at least one party member ability and one enemy attack at every difficulty tier.
- [ ] **At least one example of every element-pair affinity** (15 combos) appears in the bestiary.
- [ ] **Equipment system**: at least 6 weapons and 6 armor pieces, distributed by element affinity.
- [ ] **Stance / augment system** — per-character ability augments that imbue basic attacks with the augmenter's element (the Layer-1 deliberate "basic attacks are non-elemental" gate gets unlocked here).
- [ ] **MP replaced by lore-correct caster cost** — stamina, rhythm-game inputs, or cooldowns (decided here based on Layer-1 playtesting).
- [ ] **Branching dialogue** for at least the major NPCs (story-relevant ones get multiple states).

### Asset requirements

- Original Aseprite tile sets for the second region.
- Original portraits for Maika and any new named NPC.
- Optional: first original music track (one region theme).

### Definition of done

A 1–2 hour playthrough exists, with the player travelling between two named regions, recruiting Maika, learning the stance / augment system, and clearing both dungeons. The element system is felt to be deep, not gimmicky.

---

## Layer 3 — The world map and the maelstrom

**Goal:** Add the third dimension the lore depends on — sailing. The world goes from "two regions you can hop between" to "an archipelago ringed around a maelstrom, with sailing direction that matters."

> Originally Layer 3 was where the tile-and-sprite engine was supposed to land. That work shipped early in Layer 1; this layer is now about the **maelstrom-as-map** instead.

### Acceptance criteria

- [ ] **A world map** rendering the maelstrom and its concentric zones.
- [ ] **At least one ship** the party can board and pilot around the ring.
- [ ] **The maelstrom-zone speed system** from [VISION.md](VISION.md): clockwise sailing is fast, counterclockwise is slow and dangerous. Travel between regions becomes a meaningful resource decision.
- [ ] **Three more regions** visitable by ship, each with at least one dungeon and one town.
- [ ] **First ship upgrade** unlocking deeper-zone access.
- [ ] **Animated overworld sprites** (4-direction walk cycles) — the static-facing sprites of Layer 1 grow walk frames.

### Asset requirements

- Tile sets for ocean, deep ocean, the maelstrom itself, three more regions.
- Ship sprites (one or two variants).
- Walk-cycle frames for the four party members and any visible NPCs.
- Optional: more region themes; first dedicated battle theme.

### Definition of done

A player can boot, sail clockwise to a new region, fight there, dock, return — and feel the directionality of the world. The first ship upgrade is earned and unlocks at least one new region.

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
