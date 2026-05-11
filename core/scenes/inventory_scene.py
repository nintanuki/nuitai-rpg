"""The INVENTORY status screen — read-only item list.

Pushed by [core/scenes/menu_scene.py](menu_scene.py) when the player
picks INVENTORY. Lists each item in ``Party.inventory`` with its count.
Cancel (B / Backspace) pops it back to the system menu.

Pass-2 first cut is strictly informational — no using items from this
screen, no equipping, no sorting. Items are *used* from inside a
battle's Item submenu today (potions only). The screen exists so
Frankie's save / load round-trip has a place to *see* that the potion
count actually persisted across battles and across sessions; richer
inventory interaction lands in Layer 1+ once item content exists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from core.scene import Scene
from settings import ColorSettings, FontSettings, ScreenSettings
from ui import input_map, text_renderer
from utils.backgrounds import render_scene_background

if TYPE_CHECKING:
    from main import GameManager


_HEADING_POSITION = (40, 40)
_LIST_TOP_Y = 120
_LIST_LEFT_X = 60
_LIST_ROW_HEIGHT = 28
_PROMPT_BOTTOM_MARGIN = 30


class InventoryScene(Scene):
    """Read-only inventory list — one row per item, with the count."""

    OPAQUE = True

    def __init__(self, gm: "GameManager") -> None:
        """Bind this scene to the host game manager.

        Args:
            gm: The host game manager. ``gm.party.inventory`` is the
                data source.
        """
        super().__init__(gm)

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Cancel pops back to the system menu."""
        if input_map.is_cancel(event):
            self.gm.audio.play("menu_select")
            self.gm.scene_stack.pop()

    def render(self, surface: pygame.Surface) -> None:
        """Paint heading + each inventory row + the cancel prompt.

        Args:
            surface: The screen surface to draw onto.
        """
        render_scene_background(self, surface)
        text_renderer.draw_text(
            surface,
            "Inventory",
            _HEADING_POSITION,
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_HEADING,
        )
        inventory = self.gm.party.inventory
        # Stable display order: sorted by item id so repeated visits
        # do not reshuffle rows. Dict iteration in Python 3.7+ is
        # insertion-ordered, but inventory adds happen in many places
        # so we normalise here.
        rows = sorted(inventory.items())
        if not rows:
            text_renderer.draw_text(
                surface,
                "Empty.",
                (_LIST_LEFT_X, _LIST_TOP_Y),
                color=ColorSettings.GRAY,
                size=FontSettings.SIZE_BODY,
            )
        for index, (item_id, count) in enumerate(rows):
            y = _LIST_TOP_Y + index * _LIST_ROW_HEIGHT
            text_renderer.draw_text(
                surface,
                f"{item_id}    x{count}",
                (_LIST_LEFT_X, y),
                color=ColorSettings.WHITE,
                size=FontSettings.SIZE_BODY,
            )
        text_renderer.draw_text(
            surface,
            "Press cancel to return.",
            (_LIST_LEFT_X, ScreenSettings.HEIGHT - _PROMPT_BOTTOM_MARGIN),
            color=ColorSettings.GRAY,
            size=FontSettings.SIZE_SMALL,
        )
