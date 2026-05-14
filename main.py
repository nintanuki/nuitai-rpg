from __future__ import annotations

import pygame
import sys

from crt import CRT
from core.data_loader import DataLoader
from core.scene import SceneStack
from core.scenes.title_scene import TitleScene
from settings import ScreenSettings, InputSettings, ColorSettings
from systems.audio_manager import AudioManager
from systems.party import Party
from ui.layout import DebugOverlay


class GameManager:
    """Coordinate game state, flow, rendering phases, and input orchestration."""

    def __init__(self, start_fullscreen: bool = False):
        """Initialize pygame, the display, the input cache, and post-processing.

        Args:
            start_fullscreen: Whether to launch directly in fullscreen mode.
        """

        pygame.init()
        self._initialize_audio_mixer()
        self.screen = pygame.display.set_mode(ScreenSettings.RESOLUTION, pygame.SCALED)
        pygame.display.set_caption(ScreenSettings.WINDOW_TITLE)
        if start_fullscreen:
            pygame.display.toggle_fullscreen()
        self.clock = pygame.time.Clock()

        self.setup_controllers()

        # Audio is data-driven; see settings.AudioSettings for the registry.
        self.audio = AudioManager()

        # Post-processing: tracked separately because the CRT pass is skipped
        # when the player is already on a real CRT (i.e. fullscreen on the cabinet).
        self.full_screen = False
        self.crt = CRT(self.screen)

        # Content packs (characters, abilities, enemies, dungeons,
        # dialogue) are read from ``data/`` on demand and cached. Scenes
        # reach into this loader rather than re-reading JSON themselves.
        self.data = DataLoader()

        # Active gameplay state. ``party`` is overwritten by the title
        # screen when the player picks NEW GAME or CONTINUE; until then it
        # is an empty roster so save/load code can rely on it being
        # non-None.
        self.party: Party = Party()
        self.scene_stack = SceneStack(self)
        self.scene_stack.push(TitleScene(self))

    def _initialize_audio_mixer(self) -> None:
        """Initialize pygame's mixer once so AudioManager has a backing device."""
        if pygame.mixer.get_init():
            return
        try:
            pygame.mixer.init()
        except pygame.error as error:
            # Mixer failures are non-fatal; the game keeps running silently.
            # Logged via stderr so it never lands in gameplay output.
            sys.stderr.write(f"Audio mixer initialization failed: {error}\n")

    # -------------------------
    # BOOT / SETUP
    # -------------------------

    def setup_controllers(self) -> None:
        """Cache currently-connected controllers so quit-combo and event polling are cheap."""
        pygame.joystick.init()
        self.connected_joysticks = [
            pygame.joystick.Joystick(index)
            for index in range(pygame.joystick.get_count())
        ]

    def reset_game(self):
        """Restart the game by replacing the current GameManager with a fresh one.

        This is safer than resetting each subsystem by hand because it reuses
        the same startup path the game uses on first launch.
        """
        current_surface = pygame.display.get_surface()
        was_fullscreen = bool(current_surface and (current_surface.get_flags() & pygame.FULLSCREEN))

        new_game_manager = GameManager(start_fullscreen=was_fullscreen)
        new_game_manager.run()
        sys.exit()

    def close_game(self) -> None:
        """Close the game process cleanly."""
        pygame.quit()
        sys.exit()

    def quit_combo_pressed(self) -> bool:
        """Return True if START + SELECT + L1 + R1 are held on any controller."""
        required_buttons = InputSettings.JOY_BUTTON_QUIT_COMBO
        for joystick in self.connected_joysticks:
            if all(joystick.get_button(button) for button in required_buttons):
                return True
        return False
    
    # -------------------------
    # INPUT HANDLING
    # -------------------------

    def _handle_keydown(self, event) -> None:
        """Route one keyboard press to the appropriate UI/gameplay handler."""
        # Esc is the keyboard quit; useful while developing without a controller.
        if event.key == pygame.K_ESCAPE:
            self.close_game()

        # F11 fullscreen toggle is global and intentionally falls through so
        # other handlers still see the press.
        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
            self.full_screen = not self.full_screen

        # F1 toggles the UI debug overlay (see ui/layout.py). Off by
        # default; when on, every scene that registers debug rects /
        # points will outline them with labels so you can SEE the
        # layout coordinates instead of guessing. Falls through to
        # scenes intentionally.
        if event.key == pygame.K_F1:
            DebugOverlay.toggle()

    def _handle_joybuttondown(self, event) -> None:
        """Route one controller button press."""
        # Catch the multi-button quit chord on press for instant response;
        # the outer per-frame check covers held-state quits.
        if self.quit_combo_pressed():
            self.close_game()

        # BACK is the global fullscreen toggle and falls through.
        if event.button == InputSettings.JOY_BUTTON_BACK:
            pygame.display.toggle_fullscreen()
            self.full_screen = not self.full_screen

    def _handle_joyhatmotion(self, event) -> None:
        """Route a D-pad direction event."""
        pass

    def _handle_joyaxismotion(self, event) -> None:
        """Route a joystick or trigger motion event."""
        pass

    def _process_events(self) -> None:
        """Drain pygame's event queue and dispatch by event type.

        Global handlers (quit, fullscreen) run first; the same event is
        then forwarded to the active scene so it can react.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()
                continue
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.JOYBUTTONDOWN:
                self._handle_joybuttondown(event)
            elif event.type == pygame.JOYHATMOTION:
                self._handle_joyhatmotion(event)
            elif event.type == pygame.JOYAXISMOTION:
                self._handle_joyaxismotion(event)
            self.scene_stack.handle_event(event)

    # -------------------------
    # MAIN LOOP
    # -------------------------

    def _update_world(self, dt: float) -> None:
        """Advance the active scene by ``dt`` seconds."""
        self.scene_stack.update(dt)

    def _render_frame(self) -> None:
        """Compose one frame: clear, draw scenes, apply CRT pass."""
        self.screen.fill(ColorSettings.BG_COLOR)
        self.scene_stack.render_all(self.screen)

        # Apply CRT pass after world/UI rendering.
        if not self.full_screen:
            self.crt.draw()

    def run(self):
        """Run the main game loop until the player quits."""
        while True:
            if self.quit_combo_pressed():
                self.close_game()
            dt = self.clock.tick(ScreenSettings.FPS) / 1000.0
            self._process_events()
            self._update_world(dt)
            self._render_frame()
            pygame.display.flip()

if __name__ == "__main__":
    game_manager = GameManager()
    game_manager.run()
