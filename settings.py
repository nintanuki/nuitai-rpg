import os

class ColorSettings:
    """Class to hold all the color settings for the game."""
    BLACK = (0, 0, 0)
    NERO = (30, 30, 30)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    BG_COLOR = NERO
    OVERLAY_BACKGROUND = WHITE

class ScreenSettings:
    """Class to hold all the settings related to the screen."""
    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH, HEIGHT)
    FPS = 60
    CRT_ALPHA_RANGE = (75, 90)
    CRT_SCANLINE_HEIGHT = 3
    TITLE = "Nuitai RPG"

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
    # ``AudioManager.play(name)``. Empty by default; populate per-project.
    SOUND_EFFECTS: dict[str, str] = {}

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

class DebugSettings:
    """Settings related to debugging features."""