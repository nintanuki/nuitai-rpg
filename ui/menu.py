"""Cursor-driven vertical menu.

A menu is a list of labelled items, each with a callback. The cursor
moves up/down with arrow keys or D-pad/analog input. Confirm fires the
selected item's callback. Cancel fires the menu's optional cancel
callback.

Drawing draws a blinking ``>`` next to the selected row. The menu is
deliberately simple — battle command menus and pause menus can both be
built on top of it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

import pygame

from settings import ColorSettings, FontSettings, UISettings
from ui import text_renderer


@dataclass
class MenuItem:
    """One row of a menu."""

    label: str
    on_select: Callable[[], None]
    enabled: bool = True


class Menu:
    """Cursor-driven vertical menu, controller and keyboard friendly."""

    def __init__(
        self,
        items: list[MenuItem],
        on_cancel: Optional[Callable[[], None]] = None,
    ) -> None:
        """Build a menu over ``items``.

        Args:
            items: The menu rows (must contain at least one enabled item).
            on_cancel: Optional callback fired by ``cancel()``.
        """
        self.items = items
        self.on_cancel = on_cancel
        self.cursor = self._first_enabled()

    # ------------------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------------------

    def move_up(self) -> None:
        """Move the cursor to the previous enabled row, wrapping."""
        self._step(-1)

    def move_down(self) -> None:
        """Move the cursor to the next enabled row, wrapping."""
        self._step(1)

    def confirm(self) -> None:
        """Fire the currently-selected row's callback if it's enabled."""
        if 0 <= self.cursor < len(self.items):
            item = self.items[self.cursor]
            if item.enabled:
                item.on_select()

    def cancel(self) -> None:
        """Fire ``on_cancel`` if one was provided."""
        if self.on_cancel is not None:
            self.on_cancel()

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def render(
        self,
        surface: pygame.Surface,
        position: tuple[int, int],
        centered: bool = False,
        item_spacing: int | None = None,
    ) -> None:
        """Draw the menu starting at ``position``.

        Args:
            surface: The target render surface.
            position: Anchor position in pixels.
            centered: If True, each row label is centered on ``position[0]``.
            item_spacing: Optional per-render row gap in pixels.
        """
        font = text_renderer.get_font(FontSettings.SIZE_BODY)
        spacing = UISettings.MENU_ITEM_SPACING if item_spacing is None else item_spacing
        line_height = font.get_linesize() + spacing
        x, y = position

        # Cursor blink derived from wall time so the menu doesn't have to
        # be ticked from update() to animate.
        cursor_visible = (
            int(time.monotonic() * UISettings.MENU_CURSOR_BLINK_HZ * 2) % 2 == 0
        )

        for index, item in enumerate(self.items):
            color = ColorSettings.WHITE if item.enabled else ColorSettings.GRAY
            row_y = y + index * line_height
            text_x = x
            if centered:
                label_width = font.size(item.label.upper())[0]
                text_x = x - (label_width // 2)
            if index == self.cursor and cursor_visible:
                text_renderer.draw_text(
                    surface,
                    ">",
                    (text_x - UISettings.MENU_LABEL_OFFSET, row_y),
                    color,
                )
            text_renderer.draw_text(surface, item.label, (text_x, row_y), color)

    # ------------------------------------------------------------------
    # INTERNALS
    # ------------------------------------------------------------------

    def _first_enabled(self) -> int:
        """Return the index of the first enabled item, or 0 if none."""
        for index, item in enumerate(self.items):
            if item.enabled:
                return index
        return 0

    def _step(self, direction: int) -> None:
        """Move the cursor by ``direction`` rows, skipping disabled items."""
        if not self.items:
            return
        n = len(self.items)
        for _ in range(n):
            self.cursor = (self.cursor + direction) % n
            if self.items[self.cursor].enabled:
                return
