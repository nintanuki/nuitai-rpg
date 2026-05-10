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

    # SOLID is the discriminator string for flat-fill templates;
    # GRADIENT for top-to-bottom interpolated templates. Kept as
    # constants so call sites never type the literal.
    SOLID = "solid"
    GRADIENT = "gradient"

    # Built-in templates. Add freely; each name is a stable handle that
    # ``SCENE_BACKGROUNDS`` and any future settings UI can reference.
    # Color tuples are RGB in 0..255.
    TEMPLATES: dict = {
        # Sunlit aqua surface fading to deep-ocean navy — the Ms. Fishy
        # backdrop reused here for any underwater / open-sea feel.
        "ocean": (GRADIENT, (60, 180, 210), (10, 30, 70)),
        # Indigo night fading to true black; good for somber title cards
        # and pre-dawn world rooms.
        "midnight": (GRADIENT, (20, 20, 60), (0, 0, 0)),
        # Plum dusk fading to deep violet; warmer alternative to
        # midnight for menus that want some color.
        "dusk": (GRADIENT, (120, 60, 100), (20, 10, 40)),
        # Volcanic top fading to ember bottom — for fire-island and
        # battle scenes that want heat without changing the layout.
        "ember": (GRADIENT, (200, 80, 30), (60, 10, 10)),
        # Flat fills — keep these around so the system can express the
        # game's pre-template look without special-casing scenes.
        "nero": (SOLID, (30, 30, 30)),
        "black": (SOLID, (0, 0, 0)),
    }

    # Which template each scene uses. Keys are scene class names so the
    # renderer can look up by ``type(scene).__name__`` without scenes
    # having to declare anything. Unlisted scenes use ``DEFAULT_TEMPLATE``.
    SCENE_BACKGROUNDS: dict = {
        "TitleScene": "ocean",
        "TestWorldScene": "nero",
        "BattleScene": "nero",
        # ``MenuScene`` is a translucent overlay (``OPAQUE = False``) and
        # does not paint its own background, so this entry is advisory
        # for future opaque variants only.
        "MenuScene": "nero",
    }

    # Fallback template name when a scene has no entry above. Must be a
    # key in ``TEMPLATES``.
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

    # Pixel-font point sizes. The Pixeled font reads cleanly only at these
    # ladder rungs; intermediate sizes blur because the glyphs are not
    # vector-grid-aligned. Add new sizes only by powers-of-two-ish steps.
    SIZE_SMALL = 12   # Subtle UI like menu hints, status strips.
    SIZE_BODY = 16    # Default in-game prose (text box, menus).
    SIZE_HEADING = 24 # Scene titles, character names above text boxes.
    SIZE_TITLE_SCREEN_HEADING = 72  # Main title text on the title screen.

class AudioSettings:
    """Global audio toggles, mixer-level defaults, and the sound/music registry.

    The AudioManager is fully data-driven: it loads every entry from
    ``SOUND_EFFECTS`` on startup and rotates through ``MUSIC_TRACKS`` for
    background music. Add new audio cues by editing those two collections —
    the manager itself never has to change.
    """

    MUTE = False
    MUTE_MUSIC = False  # Keep music disabled while retaining sound effects.
    MUSIC_VOLUME = 1.0  # Background music volume in the range [0.0, 1.0].
    SFX_VOLUME = 1.0  # Sound effect volume in the range [0.0, 1.0].

    # Logical name -> filesystem path. Keys are what gameplay code passes to
    # ``AudioManager.play(name)``.
    SOUND_EFFECTS: dict[str, str] = {
        "menu_move": os.path.join(
            os.path.dirname(__file__), 'assets', 'audio', 'sound', 'sfx_menu_move2.ogg'
        ),
        "menu_select": os.path.join(
            os.path.dirname(__file__), 'assets', 'audio', 'sound', 'sfx_menu_select3.ogg'
        ),
    }

    # Background tracks; one is chosen at random each time music starts,
    # avoiding back-to-back repeats. Empty by default.
    MUSIC_TRACKS: list[str] = []

class AssetPaths:
    """Class to hold all the file paths for assets."""
    # __file__-relative so the project runs no matter the working directory
    # (e.g. when launched from the arcade cabinet launcher).
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
    """Save-system tunables.

    Saves are JSON files written under ``SAVES_DIR``, one file per slot
    (``slot_<id>.json``). Slot 0 is reserved for autosaves; slots
    1..MAX_SAVE_SLOTS are player-driven.
    """

    # __file__-relative so saves live next to the running game regardless
    # of the working directory the launcher used.
    SAVES_DIR = os.path.join(os.path.dirname(__file__), 'saves')

    # Player-facing slot count. Slot 0 is reserved for the autosave on top
    # of this number; the UI will render 1..N + an autosave row.
    MAX_SAVE_SLOTS = 3

    # Autosave slot id. Must be 0 (reserved); kept as a constant so code
    # never types the literal.
    AUTOSAVE_SLOT_ID = 0


class UISettings:
    """Tunables for in-game UI presentation.

    All measurements are in screen pixels unless noted otherwise. Time
    values are in seconds. Speeds (``*_PER_SECOND``) are rates so they
    work regardless of frame rate.
    """

    # Text-box geometry. The dialogue box hugs the bottom of the screen at
    # this height with this much inner padding before text begins. Border
    # is the thickness of the rectangle drawn around it.
    TEXT_BOX_HEIGHT = 160
    TEXT_BOX_PADDING = 16
    TEXT_BOX_BORDER_THICKNESS = 3

    # Typewriter rendering speed. Characters are revealed at this rate
    # while the box is paginating; pressing confirm fast-forwards to the
    # end of the current page.
    TYPEWRITER_CHARS_PER_SECOND = 60

    # Menu cursor blink. Two phases per second feels alert without being
    # distracting; lower for a more sedate cursor.
    MENU_CURSOR_BLINK_HZ = 2.0

    # Vertical spacing between menu items. Calibrated so SIZE_BODY text
    # has comfortable headroom without wasting screen real estate.
    MENU_ITEM_SPACING = 8

    # Title menu uses a tighter gap so the first item clears the heading
    # while the bottom row stays anchored visually.
    TITLE_SCREEN_MENU_ITEM_SPACING = 4

    # Horizontal gap in pixels between the menu cursor and label text.
    MENU_LABEL_OFFSET = 24

    # Title-screen layout anchors in pixels from the top-left corner.
    TITLE_SCREEN_HEADING_X = 90
    TITLE_SCREEN_HEADING_Y = 90
    TITLE_SCREEN_MENU_X = 90
    TITLE_SCREEN_MENU_TOP_Y = 290