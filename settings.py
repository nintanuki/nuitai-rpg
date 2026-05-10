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

class BackgroundSettings:
    """Named scene-background templates and per-scene assignments.

    A *template* describes how a scene's empty backdrop is drawn — usually
    a solid fill or a vertical gradient. Scenes look up their template
    through ``SCENE_BACKGROUNDS`` (keyed by the scene class name) and fall
    back to ``DEFAULT_TEMPLATE`` when unmapped.

    To re-skin a scene, edit ``SCENE_BACKGROUNDS`` only — no scene code
    has to change. To add a new look across the project, add a new entry
    to ``TEMPLATES``.

    Template shapes:
        ("solid", (r, g, b))                       — flat color fill.
        ("gradient", (r, g, b), (r, g, b))         — vertical gradient
            interpolated top → bottom.
    """

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
    """Controller button and axis mappings used by gameplay and menus.

    Constants are named after the physical button on the controller, not the
    action it performs. The only exception is JOY_BUTTON_QUIT_COMBO, which is
    a special multi-button chord rather than a single button.
    """

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

class DebugSettings:
    """Settings related to debugging features."""


class SaveSettings:
    """Save-system tunables."""

    SAVES_DIR = os.path.join(os.path.dirname(__file__), 'saves')
    MAX_SAVE_SLOTS = 3
    AUTOSAVE_SLOT_ID = 0


class BattleSettings:
    """Gameplay tunables for battles.

    Damage multipliers live in ``core/elements.py`` (single source of
    truth for element math). Everything here is content-feel: how many
    potions the party starts an encounter with, how much a potion heals,
    how much defending reduces incoming damage.
    """

    # Encounter starting inventory. Layer 1 will move this into the
    # party's shared inventory; for the Layer-0 test fight a flat pool
    # on the Battle object is enough.
    STARTING_POTIONS = 5

    # Flat heal applied to one party member per potion used. Calibrated
    # against Combatant HP (Kailo 30, Hina 25, Tawiri 22) so a potion
    # meaningfully restores roughly half a bar.
    POTION_HEAL_AMOUNT = 15

    # Integer divisor applied to incoming damage when the target spent
    # its last turn defending. Tweak here to soften / sharpen defend.
    DEFEND_DAMAGE_DIVISOR = 2


class UISettings:
    """Tunables for in-game UI presentation."""

    TEXT_BOX_HEIGHT = 160
    TEXT_BOX_PADDING = 16
    TEXT_BOX_BORDER_THICKNESS = 3

    # Width of the command panel on the left half of the bottom HUD
    # during a party member's turn. The remaining horizontal space
    # hosts the dialogue prompt to the right of the divider.
    # Sized so the divider clears the widest line in the party roster
    # ("TAWIRI 22/22") with a small margin.
    COMMAND_PANEL_WIDTH = 200

    # Per-row gap (in pixels) for the battle command menu. Tighter than
    # the default menu spacing so all four commands fit in the bottom
    # HUD without the panel having to grow.
    COMMAND_MENU_ITEM_SPACING = 4

    TYPEWRITER_CHARS_PER_SECOND = 60

    MENU_CURSOR_BLINK_HZ = 2.0
    MENU_ITEM_SPACING = 8
    TITLE_SCREEN_MENU_ITEM_SPACING = 4
    MENU_LABEL_OFFSET = 24

    TITLE_SCREEN_HEADING_X = 90
    TITLE_SCREEN_HEADING_Y = 90
    TITLE_SCREEN_MENU_X = 90
    TITLE_SCREEN_MENU_TOP_Y = 290
