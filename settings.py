import os


class ColorSettings:
    """Class to hold all the color settings for the game."""
    BLACK = (0, 0, 0)
    NERO = (30, 30, 30)
    GRAY = (120, 120, 120)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 220, 0)

    BG_COLOR = NERO
    OVERLAY_BACKGROUND = BLACK

    # Overworld tile placeholder colors. Replaced by tile sprite blits
    # in Pass 2 once we have real art chosen for Nuitai's island
    # setting. Until then these are how the cell area visually
    # distinguishes one terrain type from another.
    OVERWORLD_FLOOR = (110, 160, 90)    # grass green; walkable
    OVERWORLD_WALL = (90, 70, 60)       # rocky brown; impassable
    OVERWORLD_WATER = (60, 130, 180)    # ocean blue; impassable
    OVERWORLD_SAND = (220, 200, 140)    # sandy beige; walkable

    # Per-element accent colors. Used by menus / UI labels to flag the
    # affinity of an ability or item at a glance. Tuned for readability
    # on the black command-panel background -- Ahi and Wai are *lighter*
    # than the pure RED/BLUE constants above. Aku's entry is the lore
    # color (black); rendering it readably is the job of
    # ``ELEMENT_TEXT_STYLES`` below, which pairs the black body with a
    # white halo so the glyph survives any backdrop.
    ELEMENT_COLORS: dict = {
        "ahi":  (255, 130, 130),  # light red
        "wai":  (130, 180, 255),  # light blue
        "lau":  (130, 220, 130),  # green
        "mana": (200, 140, 240),  # light purple
        "ra":   (255, 220, 0),    # yellow (matches the menu cursor for now)
        "aku":  (0, 0, 0),        # shadow black -- paired with white glow
    }

    # Per-element TEXT style. Anywhere the UI renders an element name
    # (element-pair lines on combatant cards, ability-row labels in the
    # battle command menu) reads its render kwargs from here and splats
    # them into ``text_renderer.draw_text``.
    #
    # SHIPPED RECIPE: every element gets the same white halo at radius
    # 3, alpha 90 -- the same recipe Aku originally needed so its lore-
    # black body would survive a dark background. Applying it to all
    # six keeps the screen visually balanced; without the halo the
    # other five read flat next to a halo'd Aku. Aku's body stays
    # black; everyone else keeps their accent fill.
    #
    # Alternatives we considered (preserved as runnable recipes in
    # ``visual_test_text.py``):
    #   universal soft white: glow=WHITE,  r=2, a=70  (toned down)
    #   self-color soft:      glow=fill,   r=2, a=60  (own-color bloom)
    #   self-color parity:    glow=fill,   r=3, a=90  (own-color at Aku intensity)
    #   brighter self-color:  glow=lighter, r=2, a=80 ("flame edge" -- per-element lighter halo)
    # Re-run ``python visual_test_text.py`` to compare again.
    _TEXT_HALO_WHITE = {
        "glow": (255, 255, 255),
        "glow_radius": 3,
        "glow_alpha": 90,
    }
    ELEMENT_TEXT_STYLES: dict = {
        "ahi":  {"color": (255, 130, 130), **_TEXT_HALO_WHITE},
        "wai":  {"color": (130, 180, 255), **_TEXT_HALO_WHITE},
        "lau":  {"color": (130, 220, 130), **_TEXT_HALO_WHITE},
        "mana": {"color": (200, 140, 240), **_TEXT_HALO_WHITE},
        "ra":   {"color": (255, 220, 0),   **_TEXT_HALO_WHITE},
        "aku":  {"color": (0, 0, 0),       **_TEXT_HALO_WHITE},
    }


class BackgroundSettings:
    """Named scene-background templates and per-scene assignments."""

    SOLID = "solid"
    GRADIENT = "gradient"

    TEMPLATES: dict = {
        "ocean": (GRADIENT, (60, 180, 210), (10, 30, 70)),
        "midnight": (GRADIENT, (20, 20, 60), (0, 0, 0)),
        "dusk": (GRADIENT, (120, 60, 100), (20, 10, 40)),
        "ember": (GRADIENT, (200, 80, 30), (60, 10, 10)),
        "nero": (SOLID, (30, 30, 30)),
        "black": (SOLID, (0, 0, 0)),
    }

    SCENE_BACKGROUNDS: dict = {
        "TitleScene": "ocean",
        "TestWorldScene": "nero",
        "BattleScene": "nero",
        "MenuScene": "nero",
        "OverworldScene": "nero",
    }

    DEFAULT_TEMPLATE: str = "nero"


class ScreenSettings:
    """Class to hold all the settings related to the screen."""
    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH, HEIGHT)
    FPS = 60
    CRT_ALPHA_RANGE = (75, 90)
    CRT_SCANLINE_HEIGHT = 3
    WINDOW_TITLE = "Nuitai RPG"
    TITLE_SCREEN_HEADING = "Nuitai"


class InputSettings:
    """Controller button and axis mappings used by gameplay and menus."""

    JOY_BUTTON_A = 0
    JOY_BUTTON_B = 1
    JOY_BUTTON_X = 2
    JOY_BUTTON_Y = 3
    JOY_BUTTON_L1 = 4
    JOY_BUTTON_R1 = 5
    JOY_BUTTON_BACK = 6
    JOY_BUTTON_START = 7
    JOY_BUTTON_QUIT_COMBO = (7, 6, 4, 5)

    JOY_AXIS_LEFT_X = 0
    JOY_AXIS_LEFT_Y = 1
    JOY_AXIS_L2 = 4
    JOY_AXIS_R2 = 5
    JOY_TRIGGER_THRESHOLD = 0.5


class FontSettings:
    """Font files, sizes, and text-color mappings for UI rendering."""

    FONT = os.path.join(
        os.path.dirname(__file__), 'assets', 'font', 'Pixeled.ttf'
    )

    SIZE_SMALL = 12
    SIZE_BODY = 16
    SIZE_HEADING = 24
    SIZE_TITLE_SCREEN_HEADING = 72


class AudioSettings:
    """Global audio toggles, mixer-level defaults, and the sound/music registry."""

    MUTE = False
    MUTE_MUSIC = False
    MUSIC_VOLUME = 1.0
    SFX_VOLUME = 1.0

    SOUND_EFFECTS: dict = {
        "menu_move": os.path.join(
            os.path.dirname(__file__), 'assets', 'audio', 'sound', 'sfx_menu_move2.ogg'
        ),
        "menu_select": os.path.join(
            os.path.dirname(__file__), 'assets', 'audio', 'sound', 'sfx_menu_select3.ogg'
        ),
    }

    SFX_FILE_VOLUMES: dict = {
        os.path.join(
            os.path.dirname(__file__), 'assets', 'audio', 'sound', 'sfx_menu_move2.ogg'
        ): 0.2,
        os.path.join(
            os.path.dirname(__file__), 'assets', 'audio', 'sound', 'sfx_menu_select3.ogg'
        ): 0.2,
    }

    MUSIC_TRACKS: list = []

    MUSIC_FILE_VOLUMES: dict = {
        os.path.join(
            os.path.dirname(__file__), 'assets', 'audio', 'sound', 'waves.ogg'
        ): 1.0,
    }


class AssetPaths:
    """Class to hold all the file paths for assets."""
    TV = os.path.join(
        os.path.dirname(__file__), 'assets', 'graphics', 'effects', 'tv.png'
    )
    WAVES_SOUND = os.path.join(
        os.path.dirname(__file__), 'assets', 'audio', 'sound', 'waves.ogg'
    )
    MENU_MOVE_SOUND = os.path.join(
        os.path.dirname(__file__), 'assets', 'audio', 'sound', 'sfx_menu_move2.ogg'
    )
    MENU_SELECT_SOUND = os.path.join(
        os.path.dirname(__file__), 'assets', 'audio', 'sound', 'sfx_menu_select3.ogg'
    )
    # Per-character portrait sprites used in the party / status screens.
    # Files are named ``<member_id>_portrait.png`` and live in
    # ``assets/graphics/portraits/``; ``unknown_portrait.png`` is the
    # placeholder used when a member-specific portrait hasn't been drawn
    # yet.
    PORTRAITS_DIR = os.path.join(
        os.path.dirname(__file__), 'assets', 'graphics', 'portraits'
    )
    UNKNOWN_PORTRAIT = os.path.join(
        os.path.dirname(__file__),
        'assets', 'graphics', 'portraits', 'unknown_portrait.png',
    )


class DebugSettings:
    """Settings related to debugging features."""


class SaveSettings:
    """Save-system tunables."""

    SAVES_DIR = os.path.join(os.path.dirname(__file__), 'saves')
    MAX_SAVE_SLOTS = 3
    AUTOSAVE_SLOT_ID = 0


class BattleSettings:
    """Gameplay tunables for battles."""

    STARTING_POTIONS = 5
    POTION_HEAL_AMOUNT = 15
    DEFEND_DAMAGE_DIVISOR = 2


class UISettings:
    """Tunables for in-game UI presentation."""

    TEXT_BOX_HEIGHT = 160
    TEXT_BOX_PADDING = 16
    TEXT_BOX_BORDER_THICKNESS = 3

    # Party-roster portrait sizing. Portraits are 44x44 PNGs blitted to
    # the left of each member's status block in the party / status
    # screens. ``PORTRAIT_GAP`` is the horizontal pixel margin between
    # the portrait right edge and the text column; it is kept equal to
    # the vertical gap between consecutive portrait sprites so all four
    # sides of each portrait have a uniform breathing room
    # (``_ROSTER_ROW_HEIGHT - PORTRAIT_SIZE`` on a 60px row = 16px).
    # ``PORTRAIT_Y_OFFSET`` nudges the portrait down a few pixels so the
    # top of the sprite lines up with the top of the glyphs in the name
    # beside it -- the Pixeled font has several pixels of internal leading
    # above its caps, so a portrait blitted at the raw row top sits
    # visibly higher than the text.
    PORTRAIT_SIZE = 44
    PORTRAIT_GAP = 16
    PORTRAIT_Y_OFFSET = 12
    # Vertical gap between the top of the name line and the top of the
    # element line. The old "44 = portrait bottom" math assumed the
    # font's visible glyph height matched its point size, but Pixeled
    # has several pixels of internal leading top and bottom, so 44 left
    # the element line drifting below the portrait. 32 keeps name and
    # element as a tight two-line block that fits within the portrait's
    # vertical span.
    ROSTER_ELEMENT_LINE_Y_OFFSET = 32

    # Width of the command panel on the left half of the bottom HUD
    # during a party member's turn. Sized so the divider clears the
    # widest line in the party roster ("TAWIRI 22/22") with a small
    # margin.
    COMMAND_PANEL_WIDTH = 200

    # Explicit pixel distance between rows in the battle command menu.
    # Sized for SIZE_BODY labels; SIZE_SMALL labels (auto-shrink, when
    # ability names overflow) sit a little airy in the same rows.
    COMMAND_MENU_ROW_HEIGHT = 28

    TYPEWRITER_CHARS_PER_SECOND = 60

    MENU_CURSOR_BLINK_HZ = 2.0
    MENU_ITEM_SPACING = 8
    TITLE_SCREEN_MENU_ITEM_SPACING = 4
    MENU_LABEL_OFFSET = 24

    TITLE_SCREEN_HEADING_X = 90
    TITLE_SCREEN_HEADING_Y = 90
    TITLE_SCREEN_MENU_X = 90
    TITLE_SCREEN_MENU_TOP_Y = 290


class GridSettings:
    """Tile dimensions for the overworld grid."""

    TILE_SIZE = 32  # Pixels per overworld tile.


class OverworldSettings:
    """Cell-area layout for the overworld scene.

    One cell is a fixed grid of tiles that fills the visible action
    window. Crossing the edge swaps to the matching neighbor cell in
    ``WORLD_LAYOUT`` and snaps the sprite to its entry tile. Screen-
    locked -- no scrolling camera at this layer.
    """

    COLS = 20  # Tiles wide per cell.
    ROWS = 12  # Tiles tall per cell.
    PIXEL_W = COLS * GridSettings.TILE_SIZE   # 640 px.
    PIXEL_H = ROWS * GridSettings.TILE_SIZE   # 384 px.
    X = (ScreenSettings.WIDTH - PIXEL_W) // 2  # Centered horizontally.
    Y = 40                                     # Top margin.

    # Wall character recognised by World.is_wall. Walls block the
    # player's step; the cell renderer paints them in OVERWORLD_WALL.
    WALL_CHAR = "#"
    # Walkable / impassable variants. Each one paints a distinct
    # placeholder color in the cell renderer. Pass 2 swaps these for
    # tile sprite blits.
    WATER_CHAR = "~"  # Impassable; visually distinct from rock walls.
    SAND_CHAR = "_"   # Walkable; alt-floor flavor for paths/beaches.
    FLOOR_CHAR = "."  # Walkable default.


class EncounterSettings:
    """Step-counted random-encounter parameters for the overworld.

    Pass-2 first cut uses one global rate; Pass-2 follow-up moves to
    per-cell tables (rate + min-quiet + enemy list) read from the cell
    data once cells migrate to JSON. The eligibility window (the first
    ``MIN_QUIET_STEPS`` steps after a fresh load or a finished battle)
    guarantees the player isn't immediately re-engaged.
    """

    # Probability per *eligible* step (after the quiet window) that an
    # encounter fires. 0.20 means ~5 steps on average past the quiet
    # window before a hit; the Layer-1 production value will be lower.
    RATE_PER_STEP = 0.20
    # Minimum number of steps after spawn / after the last battle
    # before any encounter can roll. Pure-quiet pacing window.
    MIN_QUIET_STEPS = 4


class OverworldPlayerSettings:
    """Tunable values for the overworld player sprite."""

    STEP_DURATION_MS = 150            # Walk animation duration per tile.
    COLOR = ColorSettings.YELLOW      # Pass-1 placeholder fill.
    SIZE = GridSettings.TILE_SIZE     # Visual size; matches tile size for Pass 1.
    SPAWN_COL = OverworldSettings.COLS // 2  # Center column on first spawn.
    SPAWN_ROW = OverworldSettings.ROWS // 2  # Center row on first spawn.
