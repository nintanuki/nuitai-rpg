# Patterns lifted from Dungeon Digger / Adventure

> A concise reference for the code patterns we want to reuse from the
> two predecessor projects (`arcade-cabinet/.../dungeon-digger/` and
> `.../adventure/`). The point of this document is so we **never have
> to look at those repos again** — the patterns we care about live
> here in idiomatic Nuitai shape.

> Asset files (sprites, audio) are imported separately; Frankie copies
> them in by hand. Code patterns and idioms are what this document
> captures.

The patterns are grouped by what they're for. Each section has the
shape `Problem / Approach / Code sketch / Where it lands in Nuitai`.
The code sketches are illustrative, not literal — adapt to Nuitai's
conventions (`from __future__ import annotations`, type hints,
section banners, settings.py for tunables, ALL CAPS via text_renderer,
no magic numbers in code).

---

## 1. Sprite loading + scaling — load once, blit cheap

**Problem:** Each sprite needs to be loaded from disk, alpha-converted,
and scaled to `TILE_SIZE`. Doing this per frame is needlessly expensive.

**Approach:** Load all variants once at construction and cache them in
a dict keyed by their state axes. Per-frame "swap a sprite" is then a
dict lookup, not disk I/O.

```python
TILE = (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)
self.sprites: dict[tuple[str, str], pygame.Surface] = {}
for key, path in AssetPaths.PLAYER_SPRITES.items():
    surf = pygame.image.load(path).convert_alpha()
    self.sprites[key] = pygame.transform.scale(surf, TILE)
```

**Where it lands:** `OverworldPlayer.__init__` (Pass 3) replaces the
Pass-1 colored-rect placeholder with this load-and-cache. Same shape
for NPCs (one sprite per NPC id), doors (open / closed), shop
keepers, etc.

**Key axes for Nuitai's player:** `(facing,)` only — no helmet state
(Dungeon Digger's helmet axis is dungeon-crawler-specific), no peek
(optional polish — see §4 below).

---

## 2. Multi-variant sprite dict — keyed by gameplay state

**Problem:** A sprite has multiple visual states driven by orthogonal
gameplay axes (facing direction, action state, animation frame). Picking
the right one each frame should be a flat lookup.

**Approach:** Make the dict key the *combination* of axes that uniquely
identifies a frame. The lookup is then `self.sprites[(facing,
animation_frame)]` and the rendering code never branches on state.

```python
# Player: (facing,) for Layer 1 (no helmet, no peek).
self.sprites[("left",)]  = ...
self.sprites[("right",)] = ...
self.sprites[("up",)]    = ...
self.sprites[("down",)]  = ...

# Per-frame:
self.image = self.sprites[(self.facing,)]
```

**Where it lands:** Any sprite with state. The dungeon-digger pattern
generalises naturally — add another axis to the key tuple if a new
gameplay variable affects the sprite, no rendering-code changes
required.

**Caveat:** Don't include continuous fields (alpha, tint) in the key
— those go through `image.copy()` and `set_alpha` / blit-with-tint
applied to the looked-up surface.

---

## 3. Walk-cycle animation — target_pos lerp

**Problem:** The player commits to a tile, but the visual translation
needs to be smooth so it doesn't feel like Pokemon Red. (We already
ship this in `entities/overworld_player.py` from Pass 1; documenting
here for completeness so future sprite work re-uses the same shape.)

**Approach:** Logical position is `(col, row)` (tile coords); visual
position is interpolated per-frame from `start_pixel` to `end_pixel`
over `STEP_DURATION_MS`. When the lerp finishes, snap and clear the
moving flag.

The Nuitai version is in `OverworldPlayer.update`. The Dungeon Digger
version uses a Vector2 + scale_to_length variant; both are equivalent.
We pick the lerp-by-time form (Pass 1) over Dungeon Digger's
lerp-by-distance form (`anim_speed` pixels per frame) because
time-based lerp stays consistent across FPS variance.

**Where it lands:** Already shipped. The sprite-blit version (Pass 3)
will use the same `_step_active` / `_step_progress` state but blit a
sprite at the lerped pixel instead of a filled rect.

---

## 4. Idle "look-around" animation — optional polish

**Problem:** A sprite that stands perfectly still looks dead. Periodically
glancing in different directions is a tiny touch that animates the world.

**Approach:** A two-state machine — *waiting* (countdown until the next
peek cycle) and *cycling* (running through `IDLE_ANIMATION_SEQUENCE`
holding each frame for `IDLE_ANIMATION_FRAME_MS`). Movement or any
non-default sprite state cancels and resets.

```python
def update_idle_animation(self) -> None:
    now_ms = pygame.time.get_ticks()
    dt_ms = now_ms - self._idle_last_tick_ms
    self._idle_last_tick_ms = now_ms

    if self.is_moving or self.facing != "down":  # adapt cancel-conditions
        self._reset_idle()
        return

    if self.idle_frame_index == -1:
        self.idle_elapsed_ms += dt_ms
        if self.idle_elapsed_ms >= IDLE_ANIMATION_DELAY_MS:
            self.idle_frame_index = 0
            self.idle_frame_elapsed_ms = 0
            self.peek = SEQUENCE[0]
        return

    self.idle_frame_elapsed_ms += dt_ms
    if self.idle_frame_elapsed_ms >= IDLE_ANIMATION_FRAME_MS:
        self.idle_frame_elapsed_ms = 0
        self.idle_frame_index += 1
        if self.idle_frame_index >= len(SEQUENCE):
            self._reset_idle()
        else:
            self.peek = SEQUENCE[self.idle_frame_index]
```

**Where it lands:** Pass 3 stretch goal. Not required for Layer 1; if
the static-facing sprites feel lifeless the cycle takes maybe 30
minutes to drop in.

**Caveat:** Idle animation needs *idle frames* in the sprite sheet.
Dungeon Digger uses `peek_left` / `peek_right` variants for its
helmet-up sprite. If Nuitai's sprite sheet doesn't have peek frames,
the cycle becomes a blink (alpha pulse) or a one-frame "breathing"
overlay instead.

---

## 5. Asset directory iteration — pool + paired variants

**Problem:** A sprite category has many interchangeable members
(NPCs, monsters) that should be discoverable from a folder, with
some entries having `_left` / `_right` paired variants that count
as one creature.

**Approach:** Walk the directory, group by stem (filename minus
`_left` / `_right` suffix), and pick a random group. Each group is a
dict of `side → path`.

```python
IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp")
groups: dict[str, dict[str, str]] = {}
if os.path.isdir(directory):
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if not (os.path.isfile(path) and name.lower().endswith(IMG_EXTS)):
            continue
        stem, _ext = os.path.splitext(name)
        if stem.endswith("_left"):
            key, side = stem[:-5], "left"
        elif stem.endswith("_right"):
            key, side = stem[:-6], "right"
        else:
            key, side = stem, "static"
        groups.setdefault(key, {})[side] = path
chosen = random.choice(list(groups.values())) if groups else fallback
```

**Where it lands:** NPC spawning (Pass 7), if NPCs are placed by id
manually this isn't needed. Useful for any "pick a random one of
this kind" content — village idle bystanders, varied tree/rock
decorations, etc.

---

## 6. NPC sprite — interact then optionally fade

**Problem:** An NPC is a sprite that sits on a tile and reacts to the
player walking up to them. Some NPCs are temporary (give an item then
vanish); others are permanent.

**Approach:** A simple sprite class with `image` + `position`, with
optional fade-out state (`fade_pending` → `fading` → `fade_alpha`
ticks down to zero, then `kill()` the sprite).

```python
class NPC(pygame.sprite.Sprite):
    def __init__(self, ...):
        ...
        self.fade_pending = False
        self.fading = False
        self.fade_alpha = 255

    def animate(self) -> None:
        if self.fade_pending and not self.game.message_log.is_typing:
            self.fade_pending = False
            self.fading = True
        if self.fading:
            self.fade_alpha = max(0, self.fade_alpha - NPCSettings.FADE_SPEED)
            self.image.set_alpha(self.fade_alpha)
            if self.fade_alpha <= 0:
                self.kill()
```

**Where it lands:** Layer 1 NPCs (Pass 7). The fade behavior is
optional; Layer-1 NPCs are mostly permanent (village dwellers).
A Layer-1.5 quest NPC who "vanishes after giving you the key" would
use the full fade path.

**Adaptation:** Nuitai's NPCs are *not* sprite-group-managed — they're
keyed off the cell's `interactables` dict. So `kill()` in Nuitai
means "remove the entry from the cell's interactables and bump a
saved flag." A Layer-2 NPC system might switch to sprite groups for
moving NPCs (shopkeepers pacing, kids running around).

---

## 7. Door sprite — two-state visual

**Problem:** A door tile has two visual states (closed / open) with
the open state set in response to a gameplay event (key used, story
flag, etc.).

**Approach:** Load both surfaces at construction; swap the active one
on the state-change method.

```python
class Door(pygame.sprite.Sprite):
    def __init__(self, ...):
        super().__init__(groups)
        self.closed_image = ...load and scale...
        self.open_image = ...load and scale...
        self.image = self.closed_image
        self.is_open = False

    def open(self) -> None:
        self.image = self.open_image
        self.is_open = True
```

**Where it lands:** Layer 1 dungeon doors (Pass 7). The `is_open`
flag is what `OverworldPlayer.is_wall`-equivalent checks — a closed
door blocks; an open door is walkable.

The Layer-1 door interaction is one of:
- Key door: A-press while facing checks `Party.inventory["key"] >
  0`; if so consume one and call `door.open()`.
- Boss door: A-press blocked unless story flag set
  (`Party.flags["dungeon_cleared"]`).
- Plain door: A-press toggles open / closed (no key needed —
  cosmetic, common village fixtures).

---

## 8. Cardinal-only step normalisation

**Problem:** Diagonal movement on a grid causes 1.4× speed and breaks
the "1 step = 1 tile" invariant the encounter system relies on.

**Approach:** Clear one of the two non-zero components when both are
set, prioritising one axis consistently.

```python
def _normalize_cardinal_step(dx: int, dy: int) -> tuple[int, int]:
    if dx != 0 and dy != 0:
        # Pick a priority. Dungeon Digger picks vertical; we picked
        # "preserve current axis if walking, else horizontal" (see
        # OverworldPlayer._read_polled_direction).
        dx = 0
    return dx, dy
```

**Where it lands:** Already shipped in
`OverworldPlayer._read_polled_direction` (Pass 1). The pattern matters
for any other sprite that takes grid steps (NPCs that wander, ship
sprites on the world map, etc.).

---

## 9. Coords helper — stateless grid ↔ pixel conversion

**Problem:** Multiple subsystems need to convert between tile
coordinates `(col, row)` and screen pixels — the renderer, the player,
NPC code, the minimap (if we ever add one). Putting the math in
`GameManager` would force everyone through it.

**Approach:** Two pure functions in their own module that read the
relevant settings classes directly.

```python
# core/coords.py
from settings import GridSettings, OverworldSettings

def grid_to_pixel(col: int, row: int) -> tuple[int, int]:
    return (
        OverworldSettings.X + col * GridSettings.TILE_SIZE,
        OverworldSettings.Y + row * GridSettings.TILE_SIZE,
    )

def pixel_to_grid(x: float, y: float) -> tuple[int, int]:
    return (
        int((x - OverworldSettings.X) // GridSettings.TILE_SIZE),
        int((y - OverworldSettings.Y) // GridSettings.TILE_SIZE),
    )
```

**Where it lands:** Currently embedded in
`OverworldPlayer._logical_pixel`. When a second caller needs the
math (Pass 7 NPC placement, definitely), promote it to
`core/coords.py` and call from both. Not worth doing pre-emptively.

---

## 10. The cell-based world model (Adventure)

**Problem:** Screen-by-screen exploration where each "screen" is a
small tile grid and the world is a sparse 2D map of those screens.

**Approach:** Two static dicts and one stateful class.

```python
CELLS:          dict[name, list[list[char]]]
WORLD_LAYOUT:   dict[(cx, cy), name]
START_CELL_POS: tuple[int, int]

class World:
    def __init__(self) -> None:
        self.current_pos = START_CELL_POS
        self._refresh_active_cell()
    def is_wall(self, col, row) -> bool: ...
    def step_to_neighbor(self, dx_cells, dy_cells) -> bool: ...
```

**Where it lands:** Already shipped in `core/world.py` and
`core/overworld_cells.py` (Pass 1). The pattern generalises naturally
when interior layers (dungeon, house, ship cabin) come in — add a
`current_layer` field to `World` and an entrance-tile table that maps
`(cx, cy, layer) → (target_layer, target_cell, target_tile)`. The
renderer and player don't have to change.

---

## 11. Tile rendering — char grid → blits

**Problem:** Render a cell as a grid of tiles, color-coded or
sprite-coded by cell character.

**Approach:** Iterate the grid, look up each char's visual, blit.
Pass-1 ships colored rects; Pass 3 swaps for tile sprites.

```python
def _render_cell(self, surface: pygame.Surface) -> None:
    grid = self.world.current_grid
    for row in range(OverworldSettings.ROWS):
        for col in range(OverworldSettings.COLS):
            char = grid[row][col]
            x = OverworldSettings.X + col * GridSettings.TILE_SIZE
            y = OverworldSettings.Y + row * GridSettings.TILE_SIZE
            surface.blit(self._tile_sprites[char], (x, y))
            # (Pass 1: pygame.draw.rect(surface, _TILE_COLORS[char], ...))
```

**Where it lands:** Already shipped (rect form) in
`OverworldScene._render_cell`. Pass 3 swaps the rect call for the blit
above; the loop structure stays.

---

## 12. Color-with-alpha helper

**Problem:** Pygame's `Color` doesn't expose alpha as cleanly as you want; ad-hoc `pygame.Color(name); c.a = 200` litters the codebase.

**Approach:** A one-line helper in `ui/render_utils.py`:

```python
def color_with_alpha(color_name: str, alpha: int) -> pygame.Color:
    color = pygame.Color(color_name)
    color.a = alpha
    return color
```

**Where it lands:** Add to a new `utils/render_utils.py` (Pass 3 or whenever the first translucent overlay needs it). The `MenuScene._overlay` already does this inline; the helper just centralises the pattern.

---

## 13. Tutorial card system — pattern for any timed card overlay

**Problem:** A first-run player needs hints, but pushing them all at once is overwhelming and timing them by clock is brittle. The Dungeon Digger tutorial fires cards in response to **gameplay events** (`moved`, `dug`, `monster_spotted`, `item_used`, etc.) and uses two queues — burst (fire immediately) and flow (one per turn) — with anti-mash dismiss logic so the player can't skip past meaningful hints by holding a button.

**Approach:** A `TutorialManager` with three pieces:

```python
@dataclass(frozen=True)
class Card:
    id: str
    text: str
    queue: str   # "burst" or "flow"

CARDS: dict[str, Card] = {
    "first_step": Card("first_step", "PRESS A DIRECTION TO MOVE.", "burst"),
    ...
}

# Event id -> card ids to push.
TRIGGERS: dict[str, list[str]] = {
    "moved": [],          # already learned, no card
    "monster_spotted": ["combat_intro", "command_overview"],
    ...
}

class TutorialManager:
    def __init__(self): self.burst, self.flow = deque(), deque()
    def notify(self, event: str, **kwargs): ...
    def on_turn_end(self): ...   # advance flow queue one card per turn
    def update(self): ...        # tick anti-mash timer
    def is_blocking(self): ...   # paused while a card is showing
    def draw(self, surface): ...
```

**Where it lands:** Not in Layer 1's spec. Earmark as a Layer-1.5 polish pass if first-time players struggle with the controls. The pattern transfers cleanly: `gm.tutorial.notify("encounter_started")` from the encounter trigger, `gm.tutorial.notify("hp_low", member="kailo")` from the damage path, etc. Until then, leave it out — the code in Dungeon Digger is heavy and the demo doesn't need it.

---

## 14. Per-tile state dict — alternative to char grids

**Problem:** A char grid (`'.'` = floor, `'#'` = wall) is simple but caps at ~30 tile types and can't carry per-tile metadata (was-this-tile-dug, what-loot-is-here, has-this-trap-fired). Dungeon Digger uses a `dict[(col, row), {...}]` for richer per-tile state alongside the visual char.

**Approach:** Two parallel structures — the static grid for visuals and a sparse dict for runtime state.

```python
class DungeonLevel:
    def __init__(self):
        self.grid: list[list[str]] = ...  # char per tile, immutable
        self.tile_data: dict[(int, int), dict] = {}  # sparse, runtime state

    def is_walkable(self, col, row) -> bool:
        if not (0 <= row < ROWS and 0 <= col < COLS):
            return False
        char = self.grid[row][col]
        state = self.tile_data.get((col, row), {})
        return char != WALL_CHAR or state.get("is_dug", False)
```

**Where it lands:** When Nuitai's char grids hit their ceiling (probably during Layer 1 Pass 7 dungeon authoring, definitely by Layer 2). The cleanest migration is to keep the grid as the visual source of truth and add `tile_data` for any per-tile state that's runtime-mutable (door state, switch state, save-point-used flag). Cell JSON would also gain a `tile_data` field for content-time defaults.

---

## 15. Patterns we deliberately are NOT lifting

For the record, so future-me doesn't relitigate these decisions:

- **Dungeon Digger's `MessageLog` widget.** Nuitai uses the existing
  `TextBox` (already typewriter, paginated, ALL-CAPS, optional speaker
  tag, integrated with `text_renderer`). Two widgets doing the same
  job is worse than one.
- **Dungeon Digger's `DungeonLevel` + procedural level loader.**
  Nuitai's dungeon is hand-authored cells; no procedural rooms.
- **Dungeon Digger's fog-of-war / line-of-sight / light radius / dig
  / treasure / shop intermission.** All dungeon-crawler-specific.
- **Dungeon Digger's monster AI** (chase / hearing / repellent /
  cloak interactions). Nuitai uses random encounters, not visible
  overworld monsters.
- **Adventure's `DebugPlayer` smooth-motion AABB collision.** Nuitai
  is grid-stepped (see [overworld.md](overworld.md) §4). Adventure's
  movement model would be the right fit for a Zelda / Secret of
  Mana-style game; it isn't ours.
- **Dungeon Digger's `Score` / leaderboard / win-screen initials
  flow.** Nuitai is a story game; high scores aren't the loop.
