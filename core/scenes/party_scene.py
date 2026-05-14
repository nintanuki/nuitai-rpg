"""The PARTY status screen — selectable roster with a stats panel.

Pushed by [core/scenes/menu_scene.py](menu_scene.py) when the player
picks PARTY. The left column lists each member's name, current /
max HP, and element pair; up/down moves the cursor between members
and the right column shows the highlighted member's full stat block.
Cancel (B / Backspace) pops it back to the system menu.

Pass-2 first cut keeps this strictly informational — no equipment,
no ability lists, no per-stat sub-cursor. The numbers in the right
panel are sourced from each character's content JSON so updating
``data/characters/<id>.json`` is enough to change what the player
sees here; the stats themselves are not yet wired into combat
beyond ``hp`` and ``attack``.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pygame

from core.scene import Scene
from settings import ColorSettings, FontSettings, ScreenSettings, UISettings
from ui import input_map, text_renderer
from utils.backgrounds import render_scene_background
from utils.graphics import load_portrait

if TYPE_CHECKING:
    from main import GameManager
    from systems.party import PartyMember


_HEADING_POSITION = (40, 40)
_ROSTER_TOP_Y = 120
_ROSTER_ROW_HEIGHT = 60
# Roster column anchored at the same X as the heading so the cursor
# triangle, portraits, and bottom prompt all read as a single left-aligned
# stack with the "PARTY" title above them.
_ROSTER_LEFT_X = 40
_PROMPT_BOTTOM_MARGIN = 30
# Horizontal start of the text column for each roster row. Sits just
# right of the portrait so the name / HP / element line lines up cleanly
# regardless of whether the member has a real portrait or the unknown
# placeholder.
_ROSTER_TEXT_X = _ROSTER_LEFT_X + UISettings.PORTRAIT_SIZE + UISettings.PORTRAIT_GAP

# Stats panel layout (right column). The panel mirrors the area the
# player sees as the empty space to the right of the roster — it shows
# the highlighted member's full stat block.
_STATS_PANEL_LEFT_X = 380
_STATS_PANEL_TOP_Y = 100
_STATS_PANEL_WIDTH = 380
_STATS_PANEL_HEIGHT = 440
_STATS_PANEL_BORDER = 2
_STATS_LABEL_X = _STATS_PANEL_LEFT_X + 20
_STATS_VALUE_X = _STATS_PANEL_LEFT_X + 220
_STATS_HEADER_Y = _STATS_PANEL_TOP_Y + 16
_STATS_ELEMENTS_Y = _STATS_PANEL_TOP_Y + 44
_STATS_DIVIDER_Y = _STATS_PANEL_TOP_Y + 72
_STATS_ROW_TOP_Y = _STATS_DIVIDER_Y + 16
_STATS_ROW_HEIGHT = 28

# Stat rows displayed on the right panel. Each tuple is
# ``(stats_key, display_label)``. ``hp`` is special-cased in
# ``_render_stats_panel`` to show ``current / max`` instead of a single
# number; everything else reads straight out of ``member.stats``.
_STAT_ROWS: tuple[tuple[str, str], ...] = (
    ("level", "Level"),
    ("hp", "HP"),
    ("attack", "Attack"),
    ("defense", "Defense"),
    ("magic", "Magic"),
    ("resist", "Resist"),
    ("speed", "Speed"),
    ("luck", "Luck"),
)

# Cursor triangle drawn left of the currently-highlighted roster row.
# Same accent color as the menu cursor elsewhere in the UI so the
# selection feels consistent across screens.
_CURSOR_COLOR = ColorSettings.YELLOW


class PartyScene(Scene):
    """Selectable roster — left list, right stat panel."""

    OPAQUE = True

    def __init__(self, gm: "GameManager") -> None:
        """Bind this scene to the host game manager.

        Args:
            gm: The host game manager. ``gm.party`` is the data source.
        """
        super().__init__(gm)
        # Which roster row the cursor is on. Persists for the lifetime
        # of the scene; reset to 0 every time the screen is reopened
        # because the scene is freshly constructed by ``MenuScene``.
        self._cursor: int = 0

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Up/down moves the selector; cancel pops back to the menu."""
        if input_map.is_cancel(event):
            self.gm.audio.play("menu_select")
            self.gm.scene_stack.pop()
            return
        members = self.gm.party.members
        if not members:
            return
        if input_map.is_up(event):
            self._cursor = (self._cursor - 1) % len(members)
            self.gm.audio.play("menu_move")
        elif input_map.is_down(event):
            self._cursor = (self._cursor + 1) % len(members)
            self.gm.audio.play("menu_move")

    def render(self, surface: pygame.Surface) -> None:
        """Paint heading + roster rows + the selected member's stat panel.

        Args:
            surface: The screen surface to draw onto.
        """
        render_scene_background(self, surface)
        text_renderer.draw_text(
            surface,
            "Party",
            _HEADING_POSITION,
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_HEADING,
        )
        for index, member in enumerate(self.gm.party.members):
            self._render_member(surface, member, index)
        # Stats panel for the currently-highlighted member. Skipped if
        # the party is empty so the screen still renders cleanly during
        # bring-up or after a hypothetical full-wipe.
        if self.gm.party.members:
            selected = self.gm.party.members[self._cursor]
            self._render_stats_panel(surface, selected)
        # Bottom-of-screen hint so the player knows what to press.
        text_renderer.draw_text(
            surface,
            "Up/Down: switch    Cancel: return",
            (_ROSTER_LEFT_X, ScreenSettings.HEIGHT - _PROMPT_BOTTOM_MARGIN),
            color=ColorSettings.GRAY,
            size=FontSettings.SIZE_SMALL,
        )

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    def _render_member(
        self, surface: pygame.Surface, member: "PartyMember", index: int
    ) -> None:
        """Render one member's status block at the indexed row.

        Each row leads with a 32x32 portrait sprite; the name / HP and
        element line sit in the text column to the right of it. Members
        without a member-specific portrait fall back to
        ``unknown_portrait.png`` so the layout stays visually consistent
        even before custom art has been drawn. The currently-selected
        row gets a small yellow cursor triangle drawn to its left.

        Args:
            surface: The screen surface to draw onto.
            member: The party member being rendered.
            index: Zero-based row index.
        """
        top_y = _ROSTER_TOP_Y + index * _ROSTER_ROW_HEIGHT
        # Cursor triangle on the active row. Drawn before the portrait
        # so it sits flush against the left edge of the row rather than
        # bleeding into the portrait pixels.
        if index == self._cursor:
            # Center the triangle on the portrait's vertical midpoint
            # rather than the raw row top, so the cursor sits in the
            # middle of the portrait's left edge regardless of how the
            # portrait offset is tuned.
            portrait_center_y = (
                top_y
                + UISettings.PORTRAIT_Y_OFFSET
                + UISettings.PORTRAIT_SIZE // 2
            )
            triangle = [
                (_ROSTER_LEFT_X - 22, portrait_center_y - 8),
                (_ROSTER_LEFT_X - 22, portrait_center_y + 8),
                (_ROSTER_LEFT_X - 8, portrait_center_y),
            ]
            pygame.draw.polygon(surface, _CURSOR_COLOR, triangle)
        # Portrait on the left edge of the row. Loaded through
        # ``load_portrait`` so the file lookup and ``convert_alpha`` only
        # happen once per member id across the session. The vertical
        # offset compensates for the Pixeled font's leading so the top
        # of the portrait sits roughly level with the top of the name
        # glyphs to its right.
        portrait = load_portrait(member.id)
        surface.blit(
            portrait,
            (_ROSTER_LEFT_X, top_y + UISettings.PORTRAIT_Y_OFFSET),
        )
        # First line: name + current/max HP. Tinted red when HP is
        # at zero so a save loaded into "KO'd" state is visually
        # obvious; otherwise plain white.
        hp_color = (
            ColorSettings.RED if member.current_hp <= 0 else ColorSettings.WHITE
        )
        text_renderer.draw_text(
            surface,
            f"{member.name}    HP {member.current_hp} / {member.max_hp}",
            (_ROSTER_TEXT_X, top_y),
            color=hp_color,
            size=FontSettings.SIZE_BODY,
        )
        # Second line: element pair, each tinted by its accent. We
        # render them side by side using ``font.size`` to advance the
        # cursor so the per-element color survives without manual
        # string concatenation. The accent colors match the battle
        # command panel's ability rows so the screen reads consistent
        # with combat.
        font = text_renderer.get_font(FontSettings.SIZE_SMALL)
        element_y = top_y + UISettings.ROSTER_ELEMENT_LINE_Y_OFFSET
        cursor_x = _ROSTER_TEXT_X
        separator = " + "
        for i, element_id in enumerate(member.elements):
            element_color = ColorSettings.ELEMENT_COLORS.get(
                element_id, ColorSettings.WHITE
            )
            text_renderer.draw_text(
                surface,
                element_id,
                (cursor_x, element_y),
                color=element_color,
                size=FontSettings.SIZE_SMALL,
            )
            cursor_x += font.size(element_id.upper())[0]
            if i < len(member.elements) - 1:
                text_renderer.draw_text(
                    surface,
                    separator,
                    (cursor_x, element_y),
                    color=ColorSettings.GRAY,
                    size=FontSettings.SIZE_SMALL,
                )
                cursor_x += font.size(separator.upper())[0]

    def _render_stats_panel(
        self, surface: pygame.Surface, member: "PartyMember"
    ) -> None:
        """Paint the right-side stat panel for ``member``.

        The panel is a bordered rectangle with the member's name and
        element pair at the top, a divider line, and one labelled row
        per stat in ``_STAT_ROWS``. ``hp`` is special-cased to show
        the ``current / max`` pair so the panel agrees with the roster
        line on the left.

        Args:
            surface: The screen surface to draw onto.
            member: The party member whose stats are being shown.
        """
        # Frame. Drawn as a 2px gray outline so the panel reads as a
        # discrete sub-region without competing with the bottom HUD
        # styling in battle.
        panel_rect = pygame.Rect(
            _STATS_PANEL_LEFT_X,
            _STATS_PANEL_TOP_Y,
            _STATS_PANEL_WIDTH,
            _STATS_PANEL_HEIGHT,
        )
        pygame.draw.rect(
            surface, ColorSettings.GRAY, panel_rect, _STATS_PANEL_BORDER
        )
        # Member name as the panel header.
        text_renderer.draw_text(
            surface,
            member.name,
            (_STATS_LABEL_X, _STATS_HEADER_Y),
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_BODY,
        )
        # Element pair below the name, using the same per-element accent
        # tinting as the roster row so the player can confirm the panel
        # is pointing at the highlighted member.
        font_small = text_renderer.get_font(FontSettings.SIZE_SMALL)
        cursor_x = _STATS_LABEL_X
        separator = " + "
        for i, element_id in enumerate(member.elements):
            element_color = ColorSettings.ELEMENT_COLORS.get(
                element_id, ColorSettings.WHITE
            )
            text_renderer.draw_text(
                surface,
                element_id,
                (cursor_x, _STATS_ELEMENTS_Y),
                color=element_color,
                size=FontSettings.SIZE_SMALL,
            )
            cursor_x += font_small.size(element_id.upper())[0]
            if i < len(member.elements) - 1:
                text_renderer.draw_text(
                    surface,
                    separator,
                    (cursor_x, _STATS_ELEMENTS_Y),
                    color=ColorSettings.GRAY,
                    size=FontSettings.SIZE_SMALL,
                )
                cursor_x += font_small.size(separator.upper())[0]
        # Divider line under the header so the stat rows feel grouped.
        pygame.draw.line(
            surface,
            ColorSettings.GRAY,
            (_STATS_PANEL_LEFT_X + 10, _STATS_DIVIDER_Y),
            (
                _STATS_PANEL_LEFT_X + _STATS_PANEL_WIDTH - 10,
                _STATS_DIVIDER_Y,
            ),
            1,
        )
        # Stat rows. Labels in gray, values in white so the numbers pop.
        for row_index, (key, label) in enumerate(_STAT_ROWS):
            y = _STATS_ROW_TOP_Y + row_index * _STATS_ROW_HEIGHT
            text_renderer.draw_text(
                surface,
                label,
                (_STATS_LABEL_X, y),
                color=ColorSettings.GRAY,
                size=FontSettings.SIZE_BODY,
            )
            if key == "hp":
                value_text = f"{member.current_hp} / {member.max_hp}"
            else:
                value_text = str(member.stats.get(key, 0))
            text_renderer.draw_text(
                surface,
                value_text,
                (_STATS_VALUE_X, y),
                color=ColorSettings.WHITE,
                size=FontSettings.SIZE_BODY,
            )
