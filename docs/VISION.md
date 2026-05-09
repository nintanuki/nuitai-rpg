# Nuitai RPG — Vision

> The artistic North Star. This document changes rarely. When it does change, the change is significant.

## The pitch

**Nuitai RPG** is a turn-based, sprite-based 2D JRPG in the lineage of *Chrono Trigger*, *Final Fantasy VI*, and *Dragon Quest*. The player journeys clockwise around the Great Maelstrom, recruiting a small party of friends, learning two-element martial arts and magic, and slowly uncovering the truth of the lost sky people who left their ruins behind three thousand years ago.

The setting is the original world of **Nuitai**, an ocean planet of scattered islands. Magic is motion; every fighter draws on two of six elements. The world bible lives in [docs/lore/INDEX.md](lore/INDEX.md).

## What "done" feels like

The finished game should feel like a **lost SNES cartridge** that a player picks up in a thrift store, plays for thirty hours, and then talks about for the rest of their life. Specifically:

- 16-bit pixel art, hand-drawn, deliberate palette per region.
- Original chiptune-adjacent score that loops without grating, with a distinct theme per region and major character.
- Battle text that is short, punchy, and slightly *flavored* — the way Dragon Quest writes "THE SLIME ATTACKED. KAILO TAKES 4 DAMAGE."
- Dialogue that respects the player's intelligence. No tutorial pop-ups. No quest markers. Characters say what they mean and the player figures out the rest.
- A world that is **explorable**, not gated. Sailing direction (clockwise vs counterclockwise around the maelstrom) matters; the maelstrom's six zones make exploration a real commitment.
- A small party of distinct, well-written characters, every one of whom has a reason to be there and an internal life that goes beyond their combat role.

## Design pillars

These constraints shape every decision. When in doubt, return here.

### 1. The element system is the spine

There are six elements, organized into two strength/weakness triangles:

```
Ahi  ──burns──▶  Lau  ──drinks──▶  Wai  ──quenches──▶  Ahi
Ra   ──purifies──▶  Aku  ──corrupts──▶  Mana  ──transcends──▶  Ra
```

Every playable character, enemy, ability, and piece of equipment has an elemental identity. There are 15 affinity pairs; the world bible already maps each one to a personality, a culture, and a battle role. **The element system is not a bolted-on combat layer — it is the principal organizing metaphor of the world's people, their faiths, and their fights.** Battle math, character writing, and asset palettes should all be downstream of it.

The elements are never named in dialogue or by the characters themselves. They are mechanics and symbolism, not lore. (The world has no concept of "elemental damage type"; it has cooks, monks, priestesses, witch doctors, and pirates.)

### 2. Magic is motion

In Nuitai, casting requires somatic movement. There is no incantation-based magic, no scrolls fired from behind cover. A bound mage cannot cast. A dancer is a magician. A martial artist *is* a magician of a particular school. This implies:

- All magic-using characters must visually move when they cast (Layer 4+).
- Restraint, paralysis, and silence-equivalent status effects are *real* threats to casters, not flavor text.
- Heavy armor is rare in Nuitai; encumbrance is a meaningful cost.
- Equipment design favors light, flowing silhouettes — robes, sashes, simple weapons, ceremonial implements.

### 3. The party is small and every member is essential

The Layer-1 demo ships with three party members; the full game tops out at six or seven. **No filler.** Every character has:

- A two-element affinity that defines their combat role and is *distinct* from every other party member.
- A home region in the world, which the party visits as part of the main story.
- An internal conflict that resolves over the course of their personal arc.
- A dynamic with at least two other party members — friction or harmony, but specific.

The four named recruits as of Layer 2:

| Character | Elements | Role | Internal conflict |
| --------- | -------- | ---- | ----------------- |
| **Kailo** | Ahi + Wai | Fighter / Defender | Wants to follow his father across the world; cannot leave his siblings. Hides anxiety behind warmth. |
| **Hina** | Ra + Lau | Enhancer / Healer | Devout perfectionist; her serenity is performed, not real. Easily provoked. |
| **Tawiri** | Mana + Aku | Blaster / Saboteur | Lived too long among the dead. World-weary humor as armor. |
| **Maika** | Lau + Mana | Healer / Blaster | Performs above-it-all wisdom; quietly indulgent. Has a sister he's avoiding. |

### 4. The maelstrom is the map

The world has a built-in directionality. Clockwise sailing is fast; counterclockwise is slow and dangerous. The six zones around the maelstrom (from the calm outer ring to the deadly core) provide natural difficulty pacing — late-game content lives closer to the spiral. The airship in the late game lifts the party out of the maelstrom's pull entirely, which mechanically opens the sky islands.

This means:
- The world map is essentially **a ring**, not a continent. Ship upgrades extend its accessible interior.
- The "go anywhere" feeling of *Chrono Trigger* arrives gradually — first the calm ring, then the driftbelt, then deeper.
- Backtracking has a built-in narrative cost (counterclockwise is slower) which the player can pay if they want.

### 5. Presentation evolves; design does not

The game ships in five increasingly polished presentations (text → text+portraits → tile-and-sprite → animated → full SNES-tier; see [ROADMAP.md](ROADMAP.md)). At every layer the **underlying systems are the same**: the same battle math, the same scene stack, the same save format, the same dialogue trees. Only the renderers change.

**The Dragon Quest layer (Layer 3) is a destination, not a transition.** A player who picks up the game at Layer 3 and never sees Layer 4 should still be playing a complete, coherent game.

### 6. Everything happens in the pygame window

There is no terminal output. There are no console-printed game events. Every line of in-game text is rendered by the in-game text renderer onto the pygame surface, in the `Pixeled` font (or its eventual successor), in **ALL CAPS**. The CRT overlay is the boundary between the player and the world; nothing about the game's identity should leak past it.

## Tone

Nuitai is **warm but not cute**. It draws aesthetically and culturally from Polynesia, maritime southeast Asia, and Indo-Pacific traditions. The music should feel oceanic and percussive; the art should feel sun-bleached and woven, not sterile. Combat should feel *kinetic* — Lelua and Wai'Kenpō are dance-like martial arts, and the eventual sprite work should sell motion.

There is humor (Kailo's improvised kitchen-tool combat; Maika's flippancy; Tawiri's dry necromancy) but the world's stakes are real. People die. Faiths conflict. The Penyamun are dangerous. The game does not flinch from this, but it does not wallow either.

## Anti-goals

Things this game will deliberately *not* be.

- **Not** a roguelike. Hand-crafted dungeons, hand-written dialogue, deterministic story progression.
- **Not** an open-world sandbox. The maelstrom imposes a structure; the player follows the story around it.
- **Not** a class-customization game. The two-element pair is fixed per character; growth happens through abilities, equipment, and story, not respec.
- **Not** a real-time-with-pause game. Pure turn-based, in the JRPG tradition.
- **Not** a procedural-content game. Procedural generation is reserved for save-determinism (deterministic RNG seeds) and never for level layouts or characters.
- **Not** a multiplayer game. Single-player, single-save-per-slot, controller-friendly.

## When this document changes

This file changes only when the *core artistic vision* shifts. Mechanical changes go in [ROADMAP.md](ROADMAP.md). Code changes go in [ARCHITECTURE.md](ARCHITECTURE.md). New work goes in [TODO.md](TODO.md). If you find yourself updating this file casually, you are probably updating the wrong document.
