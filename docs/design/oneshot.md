# The One-Shot — Design

> The current Layer-1 plan, as agreed at the close of the Pass-2 session.
> The original [ROADMAP.md](../ROADMAP.md) had Layer 1 as a *text-only*
> demo with three party members and one dungeon. The plan has expanded:
> Layer 1 now ships as a complete one-shot — a single dungeon with
> NPCs, a shop, save points, heal points, and a final boss — rendered
> on top of the tile-based overworld engine that was kicked off in
> parallel during the Pass-1 / Pass-2 work.

> Layer 1 is the **playable cartridge**. When this milestone ships, the
> game stands on its own as a complete short JRPG; later layers add
> story, scope, and original art on top of it without rewriting the
> engine underneath.

This document is the canonical reference for everything Layer 1 commits
to. When something here is implemented, fold the current-systems
description into [ARCHITECTURE.md](../ARCHITECTURE.md) and leave the
"why we picked this" rationale here. When something here is dropped or
revised, update this file in place — never delete sections, edit them.

---

## 1. The pivot, in one paragraph

The original three-Layer ramp (text → text+portraits → tile-and-sprite)
was a way to de-risk the engine before committing to art. Pass 1 / Pass
2 of the overworld track de-risked the engine *and* shipped the tile
foundation, so the staged ramp lost most of its value. Layer 1 now
absorbs the overworld presentation, the stats / CTB systems that would
have been Layer 2, and the asset pipeline that would have been Layer
3 — but kept lightweight via temporary asset borrowing from Dungeon
Digger. The result is one milestone that ships a complete short
playable game, after which the project's bottleneck shifts from
engine work to **content** (story, dialogue, balance, and the original
art / music pass).

---

## 2. Asset import: temporary, from Dungeon Digger

The user is bringing in placeholder sprites from the existing Dungeon
Digger project. The short list, all 32×32 to match
`GridSettings.TILE_SIZE`:

- **Player sprite set.** The walking / facing variants. Dungeon
  Digger's player has a `(helmet_state, facing, peek)` triple keying
  every variant; for Layer 1 the `helmet_state` axis is dropped (no
  cloak/repellent in this game) and `peek` becomes optional. The
  facing axis (left / right; up / down can mirror or use new frames if
  any exist) maps directly onto `OverworldPlayer.facing`.
- **Walkable / non-walkable tiles.** Dirt, gravel, grass, stone wall —
  whatever Dungeon Digger has that fits a coastal / jungle / temple
  aesthetic for the one dungeon. The Pass-1 placeholder colored rects
  in `OverworldScene._render_cell` get swapped for blits of these
  tile sprites.
- **Doors.** Dungeon Digger has `closed_door.png` and `open_door.png`
  that can drive a Layer-1 door tile that opens with a key or after a
  story flag is set.
- **NPC sprites.** Dungeon Digger ships ~10 NPC tiles (`npcs/`); we
  reuse them for the village / shop NPCs we'll be writing.
- **NOT monsters.** Layer 1 uses random encounters, so there are no
  visible monsters on the overworld map. Dungeon Digger's monster
  sprites stay where they are.

All of these are **placeholders**. They get replaced one-for-one with
original Aseprite work as the art track catches up. The replacement is
a file-swap, not a code change — every sprite blit goes through the
asset-path constants in `settings.AssetPaths` (or the icon registry,
once that exists).

The user will copy the sprite files in manually; the code only needs to
know the paths. Once the files land:

- Add a new `assets/graphics/player/`, `assets/graphics/tiles/`,
  `assets/graphics/npcs/` directory tree mirroring Dungeon Digger's.
- Register the paths in `AssetPaths` (one constant per logical sprite
  for the player and door; one *directory* constant for the tile and
  NPC pools so the renderer can iterate).
- Replace `OverworldScene._TILE_COLORS` with a tile-sprite cache and
  swap the `pygame.draw.rect` call in `_render_cell` for a `blit`.
- Replace `OverworldPlayer.render`'s rect-fill with a blit of the
  player sprite keyed off `facing`.

---

## 3. Sprite + tile sizing

**Tile size: 32×32 pixels.** Already locked in via
`GridSettings.TILE_SIZE = 32`. Every overworld tile sprite must be
exactly this size.

**Overworld sprite size: 32×32 pixels.** Player, NPCs, and doors all
render at one tile. Multi-tile sprites (e.g. a ship spanning 2×1) are
out of scope for Layer 1.

**Element / item icons: 16×16 pixels.** A new size class for inline
glyphs that replace text in the UI — element icons in the PARTY
screen, item icons in INVENTORY, future ability tints in the battle
command panel.

**Character portraits: 32×32 pixels.** Used in the menu and (Layer 2+)
in dialogue boxes. Frankie's call: 32×32 keeps portraits readable at
scale-1 and matches the tile / sprite grain. This may grow to 48×48 or
64×64 later if it feels too small in the menu — design for a single
size constant in settings so the change is one number.

**Battle enemy sprites: TBD.** Layer 1 keeps battles text-narrated, so
no enemy sprites are required for the milestone. Layer 2 will introduce
them (likely 64×64 to support more detail since a battle has fewer
sprites visible at once).

A new `GridSettings.ICON_SIZE = 16` and `GridSettings.PORTRAIT_SIZE =
32` go in alongside `TILE_SIZE` so the values are referenced by name
from the renderer.

---

## 4. The icon system

A new `assets/graphics/icons/` directory holds all 16×16 element and
item icons. All original Aseprite art; the placeholder phase is the
elements rendered as their literal letter (`A`, `W`, `L`, etc.) using
the existing pixel font, drawn into a 16×16 surface so the icon
contract is the same shape on day one and after the Aseprite pass.

### 4.1. Element icons

Six icons, color-coded per `ColorSettings.ELEMENT_COLORS`:

| Element | Symbol      | Color (matches `ELEMENT_COLORS`) |
| ------- | ----------- | -------------------------------- |
| Ahi     | Flame       | Light red `(255, 130, 130)`      |
| Wai     | Wave        | Light blue `(130, 180, 255)`     |
| Lau     | Leaf        | Green `(130, 220, 130)`          |
| Ra      | Sun         | Yellow `(255, 220, 0)`           |
| Aku     | Skull       | Placeholder orange `(255, 150, 50)` (lore color is black; orange survives the panel background) |
| Mana    | Spiral      | Light purple `(200, 140, 240)`   |

Icons replace today's `text_renderer.draw_text(..., element_id, ...)`
in the PARTY screen. The same icons get used in:

- Battle command panel ability rows (next to or in place of the row
  color tint)
- Future: ability descriptions, equipment screens, status-effect
  badges

A single `ui/icons.py` module owns the loader and a `draw_icon(surface,
element_id, position)` helper. Loading happens once, cached by id.

### 4.2. Item icons

One icon per item id in the inventory, same 16×16 size. First entries:

- `potion` — flask
- `key` — key (for any locked door content)
- (Layer 2+) weapons, armor, scrolls, ingredients

The `INVENTORY` screen renders `<icon> NAME    x<count>` per row instead
of today's `name    x<count>` text-only.

### 4.3. Portraits

Per-character 32×32 portraits in `assets/graphics/portraits/`,
filename pattern `<id>.png` (e.g. `kailo.png`). Drawn next to the name
in the PARTY screen; later, drawn in dialogue boxes when an NPC or
party member is the speaker.

Three portraits required for Layer 1 (Kailo, Hina, Tawiri); a fourth
for Maika as he becomes recruitable in late Layer 1 / early Layer 2
content.

---

## 5. Controls

Existing input mapping is reshaped slightly so the system menu lands
on a JRPG-conventional button.

| Logical action  | Keyboard                     | Controller                          |
| --------------- | ---------------------------- | ----------------------------------- |
| Confirm         | Enter / Z / Space            | A                                   |
| Cancel          | Backspace / X                | B                                   |
| Up / Down / L/R | Arrow keys / WASD            | D-pad / left analog                 |
| Menu (open)     | Tab                          | **Y** (was START)                   |
| Menu (close)    | Backspace / X                | **B** (already cancel)              |
| Quit            | Esc                          | START + SELECT + L1 + R1 (combo)    |

`is_menu` in [ui/input_map.py](../../ui/input_map.py) currently fires
on `Tab` + `START`. Updating it to `Tab` + `Y` is a one-line change.
`is_cancel` already routes B to MenuScene's `on_cancel` callback, which
calls `_resume`, so closing the menu with B is already wired.

START and SELECT stay reserved for future "system" actions
(SELECT for a quick-action shortcut menu, START possibly for a
mini-map overlay later).

---

## 6. The seven-stat schema

Every party member and every enemy carries seven stats. Stored in
JSON content (`data/characters/`, `data/enemies/`) under a `stats`
dict; `PartyMember.stats` and `Combatant`'s constructor expand to
match.

| Stat   | Meaning                                                    |
| ------ | ---------------------------------------------------------- |
| HP     | Hit points. Persistent across battles via `current_hp` (already shipped). |
| MP     | Magic points. Spent on abilities. **Placeholder — see §6.1.** |
| ATK    | Physical attack power. Drives basic-attack damage.         |
| DEF    | Physical defense. Reduces incoming physical damage.        |
| MATK   | Magic attack power. Drives ability damage scaling.         |
| MDEF   | Magic defense. Reduces incoming ability damage.            |
| SPD    | Speed. Drives CTB turn-order frequency (see §7).           |

Damage formula sketch (refined during balance pass):

```
physical_damage = max(1, attacker.ATK - defender.DEF // 2)
magic_damage    = max(1, ability.power + attacker.MATK // 2 - defender.MDEF // 2)
```

Element multipliers from `core/elements.py` continue to gate on top:
multiply by `ADVANTAGE_MULTIPLIER` / `DISADVANTAGE_MULTIPLIER` /
`NEUTRAL_MULTIPLIER` after the base. The current Layer-0 formula
(`max(1, attacker.attack - defender.defense)` style) collapses into
this naturally — `ATK` is the existing `attack` stat renamed.

Migrations for existing JSON content packs:

- Add `mp`, `def`, `matk`, `mdef`, `spd` to every `data/characters/*.json`
  and every `data/enemies/*.json`.
- `Combatant.__init__` grows the same fields with sensible defaults
  (`max_mp = 0`, `defense = 0`, etc.) so legacy callers keep working.
- `PartyMember.current_hp` gets a sibling `current_mp` field with the
  same shape and the same backward-compat default.

### 6.1. MP is a placeholder for the lore-correct caster cost

The world bible says **magic is motion** (see [VISION.md](../VISION.md)
§2). A bound mage cannot cast. A dancer is a magician. That makes a
literal "magic point" pool feel out of register with the world.

The eventual cost system likely involves one or more of:

- **Stamina** — a per-turn or per-battle exertion budget that abilities
  drain and rest restores. Carries the "magic is movement" intuition
  more honestly than MP.
- **Rhythm-game inputs** — Sabin's blitzes / Auron's bushido. The
  ability fires at full strength only if the player nails a button
  combo or hits a timing window. Failing the input still casts but
  with reduced effect.
- **Cooldowns** — once-per-N-turns abilities, a la FFXIV battle craft.
  Cleanest from a balance standpoint, weakest narratively.

Layer 1 ships **MP** as the simplest possible stand-in. The
abilities-cost-MP, MP-restored-by-rest plumbing exists, the UI shows
an `MP <current> / <max>` line in PARTY, and the placeholder feel is
acknowledged in the lore — characters can think of it as "breath" or
"stride." Layer 2+ replaces the field's *meaning* (rename + new
mechanics) without the engine flinching, since the cost gate just
needs to be a "can this ability be cast right now" predicate.

---

## 7. CTB — Conditional Turn-Based, FFX-style

The current Layer-0 turn order is a flat `party + enemies` rotation
which the architecture doc already calls a placeholder. Layer 1
replaces it with the FFX scheduler.

### 7.1. The scheduler

Each combatant carries a `next_turn_time: float` field. The combatant
with the lowest next-turn-time is the active actor. After they act,
their next-turn-time advances by `action_cost / SPD`:

```
combatant.next_turn_time += action_cost / max(1, combatant.SPD)
```

Action costs (tunable, not final):

| Action          | Cost  |
| --------------- | ----- |
| Basic attack    | 1.0   |
| Defend          | 0.7   |
| Quick ability   | 0.8   |
| Standard ability| 1.0   |
| Heavy ability   | 1.5   |
| Use item        | 0.5   |

A character with twice the SPD of another acts twice as often. A
character who picks a heavy ability waits longer before their next
turn — the strategic core of FFX. A character who Defends gets back
into the queue *faster*, so chaining defense is a real choice when
hurt.

Implementation in `systems/battle.py`:

- `_order: list[Combatant]` (current sequential rotation) is replaced
  by the next-turn-time field on each combatant.
- `_next_actor` becomes "min by `next_turn_time` among living
  combatants."
- `start_turn` advances `next_turn_time` *before* picking the next
  actor (or, equivalently, on `_finish_player_turn` / after enemy auto
  resolution).
- A new `peek_upcoming(n)` method returns the next `n` actors in
  scheduled order, used by the view.

### 7.2. The upcoming-turns strip

Battle UI gets a horizontal strip across the top of the bottom HUD
showing the next ~6–8 upcoming actors in order. Each entry is a
small icon (using the icon system from §4): party portraits (32×32
scaled down to 24×24 strip-size) and enemy portraits (when battle
sprites land in Layer 2). For Layer 1 with no enemy sprites yet, the
enemy entries can be a colored block tinted with the enemy's element
color and labeled with the first letter or two of the enemy name.

A fast enemy that gets two turns in a row appears twice in the strip
back-to-back — the visualisation is just a peek into the schedule, no
special-casing required.

The strip is owned by `BattleScene._render_turn_strip` and updates
every frame from `self.battle.peek_upcoming(8)`.

### 7.3. Saved state

`Combatant.next_turn_time` is battle-local and doesn't need to persist
in saves — the field resets to 0 (or to its initial offset, see
§7.4) when a battle starts.

### 7.4. Initial offsets

Round-start randomisation: every combatant's `next_turn_time` starts
at `random.uniform(0, 1.0 / SPD)` rather than 0, so two characters
with identical SPD don't always go in the same order. Removes the
ordering exploit and adds variety without affecting balance.

---

## 8. Enemies: ability + basic attack each

Today's enemy `submit*` path resolves to a single basic attack. Layer 1
gives every enemy at least one **ability** alongside their basic
attack, with a per-enemy probability split (e.g. 70% basic, 30%
ability) — or driven by an enemy-side AI script later.

### 8.1. Enemy data shape

Each `data/enemies/<id>.json` grows an `abilities` list and an
`ability_chance` field:

```json
{
  "id": "shade",
  "name": "Shade",
  "element": "aku",
  "stats": { "hp": 50, "mp": 10, "atk": 10, "def": 4, "matk": 12, "mdef": 6, "spd": 8 },
  "abilities": ["curse"],
  "ability_chance": 0.35
}
```

`combatant_from_enemy_data` in `core/factories.py` carries the abilities
through; `Battle._enemy_action` rolls `ability_chance` and either picks
an ability at random from the list (favouring the one the AI is keenest
on) or falls back to the basic attack.

### 8.2. Ability decisions for Layer 1

Each ability gets a definition pinned down for the dungeon. First cut:

| Ability       | Element | Effect                                                             |
| ------------- | ------- | ------------------------------------------------------------------ |
| `curse`       | Aku     | Inflicts a 3-turn debuff lowering target's ATK and MATK by 30%.    |
| `firebolt`    | Ahi     | Single-target damage. Already exists.                              |
| `wave_fist`   | Wai     | Single-target damage with a 25% defend-pierce chance.              |
| `heal`        | Lau     | Single-target heal. Already exists.                                |
| `shakas_light`| Ra      | Aku-immunity buff. Already exists.                                 |
| `spirit_blast`| Mana    | Single-target damage that ignores element matchup (always 1.0×).   |
| `fire_punch`  | Ahi     | Single-target damage with 15% burn chance (3-turn DOT, Layer 1.5). |

The status-effect plumbing for `curse`'s ATK/MATK debuff is the same
shape as the existing Aku-immunity counter — a per-combatant
`statuses` dict, ticked at the top of the holder's own turn, queried
by the damage formula. The `Combatant.statuses` field is the
already-deferred Layer-0.5 item; promoting it now lets `curse` and
later debuffs share infrastructure.

### 8.3. Enemy variety for the dungeon

The dungeon needs ~5 distinct enemies plus the boss. Layer 1 enemies,
all with stat lines tuned for the battle balance pass (§11):

1. **Shade (Aku)** — Caster. Mid HP, low DEF, casts `curse`.
2. **Manogata (Wai)** — Tank. High HP and DEF, basic attack only.
3. **Fire Elemental (Ahi)** — Glass cannon. Low HP, high MATK, casts `firebolt`.
4. **Pohaku (Mana)** — Stone golem. Very high HP/DEF, very low SPD, hits hard but slow.
5. **Zealot (Ra)** — Buffer. Low offense, casts `shakas_light` on allies.
6. **Palm Dryad (Lau)** — Healer. Casts `heal` on allies, runs from the player.
7. **Boss (TBD)** — A two-element creature whose gimmick requires
   understanding the element triangle to defeat. Pinned down during
   the dungeon design pass (§9). Likely Aku + Mana so Hina's Ra and
   Tawiri's Aku are both relevant.

---

## 9. The dungeon — short-term goal

Layer 1 ships **one dungeon, end to end**. From cold boot the player
can: see the title, pick NEW GAME, learn who their party is via a
short cutscene, walk into the dungeon, fight ~5–8 random encounters,
talk to ~3–5 NPCs, buy items at one shop, save / heal at save points,
fight the boss, see an ending screen, and roll credits. ~30 minutes
on a first playthrough.

### 9.1. Structure

A small village hub (1 cell) feeding into a 4–6 room dungeon (4–6
cells). Rooms are connected by warps (door tiles or cell-edge walks).
The dungeon ends with a boss room that the player can only enter once
they've collected whatever the dungeon is gating (a key from an NPC,
a flag from a sub-quest, etc. — to be decided during dungeon design).

The cells live in `data/cells/*.json` once the data-driven cell
migration ships (open question in [overworld.md](overworld.md) §12).
Until then, they live in `core/overworld_cells.py`.

### 9.2. Save points + heal points

JRPG-conventional tile interactables:

- **Save tile** (recognisable visual, e.g. a glowing crystal or a
  shrine sprite): A-press while facing it writes to slot 1.
- **Heal tile** (a different visual, e.g. a spring or campfire):
  A-press while facing it restores all party members to full HP and
  full MP, with a confirmation message.

Both run through the existing `interactables` dispatch path (§7 of
the overworld design doc) and are content, not engine. The shape:

```python
'beach_west': {
    'grid': [...],
    'interactables': {
        (10, 6): {'kind': 'npc', 'dialogue': 'kailo_intro'},
        (12, 8): {'kind': 'save'},
        (4, 8):  {'kind': 'heal'},
        (15, 3): {'kind': 'sign', 'text': 'Lehua trail — keep west.'},
        (2, 4):  {'kind': 'shop', 'shop_id': 'lehua_general_store'},
    },
}
```

### 9.3. The shop

One shop in the village. Sells potions and (optionally) a single
gear upgrade per character. Push a `ShopScene` (new) on `kind: shop`
interaction. The shop UI is a vertical menu of items, each with a
price and a description; selecting an item opens a quantity prompt;
confirming spends `Party.gold` and adds to `Party.inventory`.

The `Party.gold` field already exists. Source of gold for Layer 1:
random encounters drop a small amount of gold per win (e.g. 1–10 per
enemy, set in enemy JSON), and the boss drops a chunk.

### 9.4. NPCs

3–5 named NPCs in the village. Each has a one-screen dialogue tree.
Layer 1 NPCs are flat — no quest-state branching beyond
"have-I-talked-to-them-once-yet?" Story-relevant NPCs (the friend who
sends the party into the dungeon, the boss's victim, the shopkeeper)
get more lines than the rest.

Names + roles to be pinned down in the writing pass; stand-in IDs:
`village_elder`, `shopkeeper`, `kid_with_hint`, `worried_villager`,
`drunk_who_knows_too_much`.

---

## 10. UI consistency: window-frame style

The current state of the game:

- **Battle text box**: full-width, sharp corners, white border, black fill.
- **Overworld text box**: same widget, but currently never visible
  (no message has been pushed on the overworld yet).
- **Action window** (overworld cell area): centered 640×384 with no
  visible border at all.
- **Pause menu / PARTY / INVENTORY**: scene-background fills the
  whole screen; menu items render on top with no panel chrome.
- **Dungeon Digger heritage**: rounded-corner borders on every
  window.

**Decision: rounded-corner borders everywhere.** Specifically:

- 2-pixel white border (`ColorSettings.WHITE`)
- 4-pixel corner radius (`UISettings.PANEL_BORDER_RADIUS`, new)
- Black fill (`ColorSettings.BLACK`)
- A small inner padding (`UISettings.PANEL_PADDING`, already exists for the text box)

This applies to:

- Text box (battle and overworld): same widget, full-width, anchored
  to the bottom of the screen, height `UISettings.TEXT_BOX_HEIGHT`
  (160 px), now with rounded corners.
- Overworld action window: same panel chrome drawn around the cell
  area.
- PARTY, INVENTORY, SHOP screens: panel chrome around each major
  region (member list, item list, etc.).
- Battle command panel: rounded as well; the divider stays as today.

Why rounded: matches the Dungeon Digger heritage Frankie's coming
from, reads as more SNES-JRPG-idiomatic (FF6 / Chrono Trigger used
1–2 px rounds), and softens the rectangular grid the rest of the
game leans hard into.

The overworld text box and the battle text box use **the same widget
and the same dimensions** so transitioning between them feels
continuous. The user will see the same panel slide in or stay in
place as they walk, talk, and fight.

### 10.1. Overworld message-box wiring

The text box already exists in `OverworldScene` (it's the same
`TextBox` widget the battle uses). It just doesn't have anything to
push into it during normal walking. Wire-ups:

- NPC interaction → dialogue lines pushed via `DialogueRunner` (§9.4)
- Sign tile interaction → static text pushed
- Save tile interaction → "GAME SAVED." pushed (also fixes the
  silent-save papercut from Pass 2's known-rough-edges list)
- Heal tile interaction → "YOUR PARTY HAS BEEN RESTORED." pushed
- Shop: handled by `ShopScene`, not the message box
- (Layer 1.5+) ambient flavor lines on entering certain cells, weather,
  etc.

### 10.2. The action-window border (overworld)

A rectangular panel with the rounded chrome, drawn around the cell
area before the cell tiles are blitted. Adds visible structure to the
exploration screen so the cell area reads as a "window into the
world" rather than as the world itself.

If the panel ever feels claustrophobic at 20×12 cells, options are:
shrink the chrome, drop the side margins, or grow the cell to 22×12
(loses 1 col of side margin). Defer that decision until the placeholder
sprite art lands and the screen has visual weight to evaluate.

---

## 11. Battle balance pass

Layer-0 enemies were target dummies — 24 HP each, attack 6, no real
strategy. Layer 1 raises the floor.

### 11.1. Enemy stat targets

| Tier         | HP    | ATK | DEF | SPD  |
| ------------ | ----- | --- | --- | ---- |
| Light enemy  | 35–50 | 8   | 4   | 8–10 |
| Medium enemy | 60–80 | 12  | 6   | 6–8  |
| Heavy enemy  | 90–110| 14  | 10  | 4–6  |
| Boss         | 250+  | 18  | 12  | 6–10 (multiple turns) |

These are starting points for the balance pass; expect revision as the
demo gets played. The dungeon's encounter table draws from light + medium
enemies; heavy enemies appear deeper and as mini-bosses.

### 11.2. Party stat starts

Layer-0 party stats (HP 30, ATK 8 etc.) are conservative for a
50-HP-enemy world. Bump baseline:

| Member | HP  | MP  | ATK | DEF | MATK | MDEF | SPD |
| ------ | --- | --- | --- | --- | ---- | ---- | --- |
| Kailo  | 50  | 15  | 12  | 8   | 8    | 6    | 8   |
| Hina   | 40  | 25  | 7   | 5   | 14   | 10   | 9   |
| Tawiri | 35  | 30  | 8   | 4   | 16   | 8    | 11  |

Roles: Kailo's the tank/striker, Hina's the support/healer, Tawiri's
the artillery / debuffer. Speeds split so Tawiri tends to act first
(fitting Aku's pre-emptive feel) and Kailo tends to act last (he's
the closer).

### 11.3. Per-encounter shape

The current single-enemy encounters get more variety:

- 60% — single enemy, picked by tier weighted to the dungeon depth
- 30% — two enemies, mixed tiers
- 10% — three enemies, all light tier

Multi-enemy encounters are the natural place where Hina's Ra abilities
(buff support) and Tawiri's AOE / debuff (tbd) start to matter
strategically.

### 11.4. The boss fight

Pinned down during the dungeon-design pass. Constraints:

- Two-element creature so the player has to think about elemental
  positioning (e.g. `aku` × `mana` so Ra purifies Aku and Mana
  transcends Ra — meaning Tawiri's Aku abilities are bait, but his
  Mana abilities are gold).
- A signature mechanic that telegraphs (e.g. casts `curse` on turn 3,
  or always heals when below 25% HP). Layer 1 doesn't need a phase
  system — one tier of cleverness is enough.
- HP and SPD tuned so the fight lasts ~6–8 rounds on a clean clear,
  ~3–4 rounds longer if the player misreads the element matchup.

---

## 12. What stays out of Layer 1

To keep the milestone shippable:

- **Music.** Existing waves track on the title; battles and the dungeon
  ship silent or with the existing placeholder battle track at most.
  Original music is Layer 4.
- **Animated battle sprites / animated walk cycles for the
  overworld.** Static sprite per facing is fine for Layer 1.
- **Character portraits in dialogue.** The PARTY screen uses portraits;
  dialogue does not yet. NPC + party speech stays text-only.
- **The maelstrom / ship system.** Layer 1 happens on one island;
  there's no sailing yet. Ship mechanics are Layer 4.
- **Stance / augment system.** Per-character ability augments and
  stances (the Layer-1+ thread the lore suggests) are deferred to
  Layer 2.
- **Status effects beyond two.** Layer 1 ships with Aku-immunity
  (already there) and `curse`'s ATK/MATK debuff. Poison, burn,
  drench, blind, weaken, silence are Layer 2.
- **Equipment.** Optional Layer-1 stretch goal: one weapon + one armor
  per character, bought at the shop. Otherwise: stats are flat.
- **Multi-cell scrolling rooms.** Cells stay screen-locked (one cell =
  one screenful). A scrolling camera is a Layer-3+ rework.
- **Dialogue branching beyond "first time / not first time."** Real
  branching dialogue waits on the writing pipeline.

---

## 13. Implementation order (the next passes)

A rough ordering for the work, not a contract. Each pass ships
independently testable so progress is visible.

### Pass 3 — Asset bones

- Drop the Dungeon Digger sprite files into the right directories.
- Add `AssetPaths` constants for player / tile / door / NPC.
- Replace `OverworldScene._TILE_COLORS` with a tile-sprite cache + blit
  loop in `_render_cell`.
- Replace `OverworldPlayer.render` rect-fill with a sprite blit keyed
  off `facing` (the four facings stay static per facing — no walk
  cycle yet).
- Add the rounded-corner panel chrome to the overworld action window
  and to the existing `TextBox`.
- Rebind `is_menu` from `START` to `Y`.
- Manual smoke: walk around, see real tiles, see the sprite face the
  way it last moved, see the bordered window chrome.

### Pass 4 — Stats expansion + CTB scheduler

- Add `mp`, `def`, `matk`, `mdef`, `spd` to PartyMember + Combatant +
  the JSON content packs (with backward-compat defaults).
- Add `current_mp` to PartyMember alongside `current_hp`.
- Replace `Battle._order` rotation with the next-turn-time scheduler.
- Add `peek_upcoming(n)`.
- Add the upcoming-turns strip to `BattleScene` rendering.
- Update damage formula to use the new defense / magic stats.
- Bump party + enemy stats per §11.

### Pass 5 — Icons + portraits + PARTY/INVENTORY polish

- Create `assets/graphics/icons/` and `assets/graphics/portraits/`
  directories; placeholder element icons render as letters in 16×16
  surfaces until Aseprite work lands.
- Add `ui/icons.py` with the loader + draw helpers.
- Replace text element labels in PARTY with icons.
- Add portrait blits to PARTY rows (and to ability list rows where
  the active actor is shown).
- Add item icons to INVENTORY rows.

### Pass 6 — Inventory navigation + use-outside-battle

- INVENTORY scene grows a cursor + per-item description panel.
- Confirm on `potion` outside battle opens a target submenu (party
  member); selecting one consumes the potion and heals the target.
- Confirm on a non-usable item shows its description and nothing else.

### Pass 7 — Dungeon content + interactables

- Author the village + 4–6 dungeon cells in the cell representation.
- Wire the `interactables` dispatch in `OverworldScene` for `npc`,
  `sign`, `warp`, `save`, `heal`, `shop`.
- Author 3–5 NPC dialogue trees.
- Author the shop content + `ShopScene`.
- Author the boss enemy + boss room + ending screen.

### Pass 8 — Balance + writing pass

- Tune enemy stats against actual play.
- Polish dialogue copy; replace the placeholder NPC names.
- Smoke playthrough end-to-end; iterate.

### Pass 9 — Layer-0.5 deferrals

The two scaffolding deferrals from earlier finally pay off:

- Persist the **scene stack** in saves (so Continue resumes the
  player's exact tile, not just the party).
- Promote the `statuses` field on `Combatant` if it isn't already
  there from §8's curse implementation.

---

## 14. Open decisions

Things deliberately left unfixed pending more data:

- **Whether MP rests outside battle or only at heal points.** Cleaner
  game feel if it auto-restores every turn-of-overworld; cleaner
  resource design if it requires a rest. Probably the latter, paired
  with cheap heal-tile placement.
- **Whether boss SPD lets it have an opening "free turn"** before
  the player gets to act — adds intimidation, can feel cheap. Decide
  during balance.
- **Whether the icon system gets per-element animated "pulse" frames**
  (a flame that flickers, a wave that rolls). One-frame static icons
  are fine for Layer 1; multi-frame is Layer 4 polish.
- **Whether portraits ship at 32×32 or 48×48.** Pick after the first
  Aseprite portrait lands and gets scrutinised in the menu.
- **Whether Maika joins by end of Layer 1 or stays an NPC** until
  Layer 2. Either is defensible; depends on the writing.
