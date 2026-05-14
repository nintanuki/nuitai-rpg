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
    # Optional override for the row's label color. When ``None`` the
    # menu uses ``ColorSettings.WHITE`` (or ``GRAY`` if disabled). When
    # set, the override applies to enabled rows; disabled rows still
    # render gray so the "you can't pick this" affordance survives.
    # Used to tint ability rows by their element.
    color: tuple[int, int, int] | None = None
    # Optional halo for the row's label, paired with ``color``. Used by
    # Aku-element abilities so the lore-black body stays visible on the
    # black command panel. ``None`` skips the glow render path entirely.
    glow: tuple[int, int, int] | None = None
    glow_radius: int = 3
    glow_alpha: int = 90


class Menu:
    """Cursor-driven vertical menu, controller and keyboard friendly."""

    def __init__(
        self,
        items: list[MenuItem],
        on_cancel: Optional[Callable[[], None]] = None,
    ) -> None:
        """Build a menu over ``items``."""
        self.items = items
        self.on_cancel = on_cancel
        self.cursor = self._first_enabled()

    # ------------------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------------------

    def move_up(self) -> bool:
        return self._step(-1)

    def move_down(self) -> bool:
        return self._step(1)

    def confirm(self) -> bool:
        if 0 <= self.cursor < len(self.items):
            item = self.items[self.cursor]
            if item.enabled:
                item.on_select()
                return True
        return False

    def cancel(self) -> bool:
        if self.on_cancel is not None:
            self.on_cancel()
            return True
        return False

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def render(
        self,
        surface: pygame.Surface,
        position: tuple[int, int],
        centered: bool = False,
        item_spacing: int | None = None,
        font_size: int | None = None,
        row_height: int | None = None,
    ) -> None:
        """Draw the menu starting at ``position``.

        Args:
            surface: The target render surface.
            position: Anchor position in pixels.
            centered: If True, each row label is centered on ``position[0]``.
            item_spacing: Optional per-render row gap in pixels (added
                to the font's natural line size).
            font_size: Optional override for the row font size; defaults
                to ``FontSettings.SIZE_BODY``. Use ``SIZE_SMALL`` for
                compact in-HUD menus like the battle command panel.
            row_height: Optional **explicit** pixel distance between
                rows. Overrides ``item_spacing`` + font metrics.
        """
        size = FontSettings.SIZE_BODY if font_size is None else font_size
        font = text_renderer.get_font(size)
        if row_height is not None:
            line_height = row_height
        else:
            spacing = (
                UISettings.MENU_ITEM_SPACING if item_spacing is None
                else item_spacing
            )
            line_height = font.get_linesize() + spacing
        x, y = position

        cursor_visible = (
            int(time.monotonic() * UISettings.MENU_CURSOR_BLINK_HZ * 2) % 2 == 0
        )

        for index, item in enumerate(self.items):
            # Disabled rows always render gray so the player can tell
            # they're locked out. Enabled rows use the row's own
            # ``color`` override (e.g. an ability's element accent)
            # when set, falling back to plain white. Disabled rows
            # always skip the glow path too — a halo on a "locked"
            # row would over-sell its availability.
            if not item.enabled:
                color = ColorSettings.GRAY
                glow = None
            elif item.color is not None:
                color = item.color
                glow = item.glow
            else:
                color = ColorSettings.WHITE
                glow = None
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
                    ColorSettings.YELLOW,
                    size=size,
                )
            text_renderer.draw_text(
                surface, item.label, (text_x, row_y), color, size=size,
                glow=glow,
                glow_radius=item.glow_radius,
                glow_alpha=item.glow_alpha,
            )

    # ------------------------------------------------------------------
    # INTERNALS
    # ------------------------------------------------------------------

    def _first_enabled(self) -> int:
        for index, item in enumerate(self.items):
            if item.enabled:
                return index
        return 0

    def _step(self, direction: int) -> bool:
        if not self.items:
            return False
        original_cursor = self.cursor
        n = len(self.items)
        for _ in range(n):
            self.cursor = (self.cursor + direction) % n
            if self.items[self.cursor].enabled:
                return self.cursor != original_cursor
        return False
