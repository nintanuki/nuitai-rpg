"""Pause / system menu — a translucent overlay over the scene below.

Lists the core out-of-world commands: party status (placeholder),
inventory (placeholder), save, settings (placeholder), and quit to
title. Pushed by gameplay scenes; drawn over them because ``OPAQUE``
is False.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from core import save
from core.scene import Scene
from settings import ColorSettings, FontSettings, ScreenSettings
from ui import input_map, text_renderer
from ui.menu import Menu, MenuItem

if TYPE_CHECKING:
    from main import GameManager


_OVERLAY_ALPHA = 200  # Out of 255; high enough to dim the world clearly.


class MenuScene(Scene):
    """A translucent overlay menu."""

    OPAQUE = False  # Render the scene below us first; we sit on top.

    def __init__(self, gm: "GameManager") -> None:
        """Build the system menu options."""
        super().__init__(gm)
        self.menu = Menu(
            items=[
                MenuItem("Party", self._noop, enabled=False),
                MenuItem("Inventory", self._noop, enabled=False),
                MenuItem("Save", self._save),
                MenuItem("Settings", self._noop, enabled=False),
                MenuItem("Quit to Title", self._quit_to_title),
                MenuItem("Resume", self._resume),
            ],
            on_cancel=self._resume,
        )
        # Cached overlay surface so we don't allocate every frame.
        self._overlay = pygame.Surface(ScreenSettings.RESOLUTION).convert_alpha()
        self._overlay.fill((0, 0, 0, _OVERLAY_ALPHA))

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def _noop(self) -> None:
        """Placeholder for unimplemented commands."""

    def _save(self) -> None:
        """Persist the current party to slot 1."""
        save.save(1, {"party": self.gm.party.to_dict()})

    def _resume(self) -> None:
        """Pop this overlay so the underlying scene resumes."""
        self.gm.scene_stack.pop()

    def _quit_to_title(self) -> None:
        """Throw away the whole stack and go back to the title screen."""
        from core.scenes.title_scene import TitleScene  # local: cycle.

        self.gm.scene_stack.clear()
        self.gm.scene_stack.push(TitleScene(self.gm))

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Standard menu navigation."""
        if input_map.is_up(event):
            self.menu.move_up()
        elif input_map.is_down(event):
            self.menu.move_down()
        elif input_map.is_confirm(event):
            self.menu.confirm()
        elif input_map.is_cancel(event):
            self.menu.cancel()

    def render(self, surface: pygame.Surface) -> None:
        """Dim the underlying world, then draw the menu over it."""
        surface.blit(self._overlay, (0, 0))
        text_renderer.draw_text(
            surface,
            "Menu",
            (40, 40),
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_HEADING,
        )
        self.menu.render(surface, (60, 120))
