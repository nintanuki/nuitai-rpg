"""Geometry helpers for UI layout.

Why this module exists
----------------------
Scenes used to compute element positions inline with raw arithmetic:

    portrait_x = _ROSTER_LEFT_X
    portrait_y = top_y + UISettings.PORTRAIT_Y_OFFSET
    name_x    = _ROSTER_LEFT_X + PORTRAIT_SIZE + PORTRAIT_GAP
    name_y    = top_y
    cursor_y  = top_y + UISettings.PORTRAIT_Y_OFFSET + UISettings.PORTRAIT_SIZE // 2

That style has three problems:

1. The *relationship* between elements ("the cursor sits at the vertical
   middle of the portrait") is lost in the arithmetic. A human (or an AI
   agent) reading the code has to mentally re-derive it every time.
2. Tweaking one shared value (say ``PORTRAIT_Y_OFFSET``) silently
   misaligns every dependent element across multiple scenes, and the
   only way to know is to launch the game and squint.
3. Two scenes that draw the same logical layout (party screen + battle
   roster) drift apart over time because the math is copy-pasted.

This module fixes (1) by expressing positions as *named anchors* on a
``pygame.Rect`` ("portrait_rect.centery"), fixes (2) by giving you a
single class to edit, and fixes (3) by letting both scenes import the
same helper instead of duplicating arithmetic.

The general pattern: one **anchor rectangle** per logical region, every
other position is derived from it via Rect properties (``centery``,
``midright``, ``bottom``, etc.). pygame.Rect already exposes nine
anchor points, which is conceptually equivalent to CSS flexbox
alignment for UI mockups.

When in doubt: add a Rect-returning property here, don't add another
constant in settings.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pygame

from settings import ColorSettings, FontSettings, UISettings
from ui import text_renderer


# ---------------------------------------------------------------------
# ROSTER ROW LAYOUT
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RosterRowLayout:
    """One roster row's geometry, derived from a single (left_x, top_y).

    A "roster row" is the visual unit you see in both the party screen
    and the battle HUD: an optional portrait on the left, a name + HP
    line to its right, and an element-affinity line directly below the
    name. The cursor / target glyph sits to the left of the portrait
    (or of the text column, for portrait-less rows).

    All values flow from two anchors:

    * ``left_x`` — the leftmost X of the row's content area. For rows
      with a portrait, this is the portrait's left edge; for portrait-
      less rows (enemies in battle), this is the text column's left.
    * ``top_y`` — the row's top in screen pixels. Name text is drawn
      from this Y; the portrait sprite is nudged down by
      ``PORTRAIT_Y_OFFSET`` so its visible top lines up with the
      visible top of the glyphs (the Pixeled font has internal leading
      that means raw-Y text appears a few pixels below raw-Y blits).

    The ``has_portrait`` flag toggles between the party-style row (with
    a portrait sprite) and the enemy-style row (text only). The text
    column auto-adjusts: portrait rows offset their text by
    ``PORTRAIT_SIZE + PORTRAIT_GAP``; portrait-less rows put text at
    ``left_x`` directly.

    Anything derived from these anchors lives as a ``@property`` below.
    If you need another anchor (say, "the bottom-right corner of the
    portrait" for some new badge), add a property here — don't compute
    it inline in a scene.
    """

    left_x: int
    top_y: int
    has_portrait: bool = True

    # --- core rectangles ---------------------------------------------

    @property
    def portrait_rect(self) -> pygame.Rect | None:
        """Pixel rectangle the portrait sprite occupies.

        Returns ``None`` for portrait-less rows (enemies). Callers must
        check ``has_portrait`` (or for None) before blitting.
        """
        if not self.has_portrait:
            return None
        return pygame.Rect(
            self.left_x,
            self.top_y + UISettings.PORTRAIT_Y_OFFSET,
            UISettings.PORTRAIT_SIZE,
            UISettings.PORTRAIT_SIZE,
        )

    @property
    def text_column_x(self) -> int:
        """Leftmost X of the name / element text column.

        For portrait rows, this sits one ``PORTRAIT_GAP`` past the
        portrait's right edge. For portrait-less rows, it's just
        ``left_x`` — the row leads with text directly.
        """
        if self.has_portrait:
            return self.left_x + UISettings.PORTRAIT_SIZE + UISettings.PORTRAIT_GAP
        return self.left_x

    # --- text anchors ------------------------------------------------

    @property
    def name_pos(self) -> tuple[int, int]:
        """Top-left of the name + HP text line (the first row line)."""
        return (self.text_column_x, self.top_y)

    @property
    def element_pos(self) -> tuple[int, int]:
        """Top-left of the element-affinity line (under the name).

        Vertical offset is read from
        ``UISettings.ROSTER_ELEMENT_LINE_Y_OFFSET`` so the gap between
        name and element is tuned in exactly one place.
        """
        return (
            self.text_column_x,
            self.top_y + UISettings.ROSTER_ELEMENT_LINE_Y_OFFSET,
        )

    # --- cursor / target glyph anchors --------------------------------

    @property
    def cursor_focal_y(self) -> int:
        """The Y to vertically-center selection cursors on.

        For portrait rows, this is the portrait's vertical midpoint —
        so a "look here" triangle sits centered on the left edge of
        the portrait. For portrait-less rows, fall back to the
        name-line Y plus a half-line of fudge so the cursor still
        feels attached to the row.
        """
        portrait = self.portrait_rect
        if portrait is not None:
            return portrait.centery
        # Roughly the visual center of a one-line name label. The
        # ``+ 10`` is half the SIZE_BODY pixel height; tweak in
        # UISettings if Pixeled gets swapped.
        return self.top_y + 10

    def selection_triangle(
        self, half_height: int = 8, width: int = 14
    ) -> list[tuple[int, int]]:
        """Vertices for the yellow selection triangle (party screen).

        Triangle points right, with its tip flush to (or just left of)
        the portrait's left edge and its body extending ``width`` px
        further left. ``half_height`` controls the triangle's vertical
        extent above and below the cursor's focal Y.
        """
        focal_y = self.cursor_focal_y
        # Tip sits 8px left of the portrait's left edge so it doesn't
        # touch the sprite pixels. If there's no portrait we still
        # offset 8px so the cursor reads as separate from the text.
        tip_x = self.left_x - 8
        back_x = tip_x - width
        return [
            (back_x, focal_y - half_height),
            (back_x, focal_y + half_height),
            (tip_x, focal_y),
        ]

    @property
    def target_glyph_pos(self) -> tuple[int, int]:
        """Position for the battle ">" target cursor.

        Drawn left of the row, vertically aligned with the name line.
        Battle's target cursor blinks rather than animating, so the
        position is just a static anchor.
        """
        return (self.left_x - 24, self.top_y)


# ---------------------------------------------------------------------
# DEBUG OVERLAY
# ---------------------------------------------------------------------


class DebugOverlay:
    """Toggleable visual overlay for UI layout debugging.

    Why this exists
    ---------------
    When something is "off by a few pixels", the fastest way to debug
    is to *see* the bounding rectangles the layout code is computing.
    Without this, you launch the game, squint, change a number, relaunch,
    squint again, repeat. With this, you press F1 in-game and every
    registered element shows up as a colored outline with its semantic
    name floating above it. Misalignments become obvious in one frame.

    How to use it
    -------------
    1. Press ``F1`` in-game to toggle. Wired in ``main.py``.
    2. In your scene's render path, call ``DebugOverlay.rect(surface,
       rect, "portrait")`` or ``DebugOverlay.point(surface, pos,
       "name")`` at the moment you've computed a position you'd like
       to be able to see. The call is a no-op when the overlay is off,
       so leave them in.
    3. Pick a color per category if you want — e.g. magenta for
       portraits, cyan for text anchors, yellow for cursors — so you
       can tell categories apart at a glance.

    Why a class with classmethods instead of an instance? The overlay
    is one global on/off; threading it through every scene as an
    instance is more ceremony than the feature deserves. ``classmethod``
    keeps the call sites short (``DebugOverlay.rect(...)``).
    """

    # Master switch. Flipped by main.py's F1 handler.
    enabled: bool = False

    # Default colors for common categories. Use these so the same kind
    # of element always shows up in the same color across scenes.
    COLOR_PORTRAIT = (255, 0, 255)   # magenta
    COLOR_TEXT = (0, 255, 255)       # cyan
    COLOR_CURSOR = (255, 220, 0)     # yellow
    COLOR_PANEL = (0, 255, 0)        # green
    COLOR_REGION = (255, 120, 0)     # orange

    @classmethod
    def toggle(cls) -> None:
        """Flip the overlay on/off. Called by the F1 key handler."""
        cls.enabled = not cls.enabled

    @classmethod
    def rect(
        cls,
        surface: pygame.Surface,
        rect: pygame.Rect | tuple[int, int, int, int],
        label: str,
        color: tuple[int, int, int] = COLOR_PORTRAIT,
    ) -> None:
        """Draw a 1px outline + label for one rectangle.

        No-op when ``enabled`` is False so call sites are free.

        Args:
            surface: The screen surface (same one the scene is
                rendering to).
            rect: A pygame.Rect or 4-tuple ``(x, y, w, h)``.
            label: Short semantic name shown above the rectangle.
                The label is rendered ALL-CAPS by the text renderer
                so keep it terse.
            color: RGB stroke color. Defaults to the portrait magenta;
                pass ``DebugOverlay.COLOR_TEXT`` etc. for other
                categories.
        """
        if not cls.enabled:
            return
        rect = rect if isinstance(rect, pygame.Rect) else pygame.Rect(rect)
        pygame.draw.rect(surface, color, rect, 1)
        cls._label(surface, (rect.left, rect.top - 12), label, color)

    @classmethod
    def point(
        cls,
        surface: pygame.Surface,
        pos: tuple[int, int],
        label: str,
        color: tuple[int, int, int] = COLOR_TEXT,
    ) -> None:
        """Draw a small crosshair + label at a single anchor position.

        Use this for things that aren't rectangles — text anchors,
        cursor tips, alignment points. No-op when the overlay is off.
        """
        if not cls.enabled:
            return
        x, y = pos
        # 5px crosshair so the anchor's exact pixel is identifiable.
        pygame.draw.line(surface, color, (x - 4, y), (x + 4, y), 1)
        pygame.draw.line(surface, color, (x, y - 4), (x, y + 4), 1)
        cls._label(surface, (x + 6, y - 6), label, color)

    @classmethod
    def polygon(
        cls,
        surface: pygame.Surface,
        points: Iterable[tuple[int, int]],
        label: str,
        color: tuple[int, int, int] = COLOR_CURSOR,
    ) -> None:
        """Outline an arbitrary polygon (e.g. the selection triangle)."""
        if not cls.enabled:
            return
        pts = list(points)
        if len(pts) < 2:
            return
        pygame.draw.polygon(surface, color, pts, 1)
        cls._label(surface, (pts[0][0], pts[0][1] - 12), label, color)

    # -----------------------------------------------------------------
    # INTERNALS
    # -----------------------------------------------------------------

    @classmethod
    def _label(
        cls,
        surface: pygame.Surface,
        pos: tuple[int, int],
        text: str,
        color: tuple[int, int, int],
    ) -> None:
        """Render a small debug label at ``pos``.

        Uses the smallest font in the renderer so labels don't
        smother the UI they're annotating. The text_renderer
        upper-cases everything automatically.
        """
        font = text_renderer.get_font(FontSettings.SIZE_SMALL)
        surf = font.render(text.upper(), False, color)
        surface.blit(surf, pos)
