"""The PARTY status screen -- selectable roster with a stats panel.

Pushed by [core/scenes/menu_scene.py](menu_scene.py) when the player
picks PARTY. The left column lists each member's name, current /
max HP, and element pair; up/down moves the cursor between members
and the right column shows the highlighted member's full stat block.
Cancel (B / Backspace) pops it back to the system menu.

Pass-2 first cut keeps this strictly informational -- no equipment,
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
from ui.layout import DebugOverlay, RosterRowLayout
from utils.backgrounds import render_scene_background
from utils.graphics import load_element_icon, load_portrait

if TYPE_CHECKING:
    from main import GameManager
    from systems.party import PartyMember


_HEADING_POSITION = (40, 40)
_ROSTER_TOP_Y = 120
# Row pitch has to clear the SIZE_BODY name line plus a SIZE_SMALL /
# 16px icon line plus visual breathing room. 60 was tight for two text
# lines; 76 was too generous (icons floated low in the row, well below
# the portrait bottom). 64 keeps the name+icon block compact while
# still leaving 12 px between the icon's bottom and the next row.
_ROSTER_ROW_HEIGHT = 64
# Roster column anchored at the same X as the heading so the cursor
# triangle, portraits, and bottom prompt all read as a single left-aligned
# stack with the "PARTY" title above them.
_ROSTER_LEFT_X = 40
_PROMPT_BOTTOM_MARGIN = 30

# Stats panel layout (right column). The panel mirrors the area the
# player sees as the empty space to the right of the roster -- it shows
# the highlighted member's full stat block.
_STATS_PANEL_LEFT_X = 380
_STATS_PANEL_TOP_Y = 100
_STATS_PANEL_WIDTH = 380
_STATS_PANEL_HEIGHT = 440
_STATS_PANEL_BORDER = 2
_STATS_LABEL_X = _STATS_PANEL_LEFT_X + 20
_STATS_VALUE_X = _STATS_PANEL_LEFT_X + 220
# Stats-panel vertical rhythm. The header (member name) sits 16 px
# inside the panel; the element line lives below it; the divider line
# closes the header block off from the stat table. Original spacing was
# 28 px name->elements and 28 px elements->divider, which was sized
# for SIZE_SMALL text. The element line now renders 16x16 icons
# alongside SIZE_SMALL words (icon-plus-word) and was visually merging
# both with the name above and with the divider below. 40 px gaps give
# the icon clear breathing room top and bottom.
_STATS_HEADER_Y = _STATS_PANEL_TOP_Y + 16
_STATS_ELEMENTS_Y = _STATS_PANEL_TOP_Y + 56
_STATS_DIVIDER_Y = _STATS_PANEL_TOP_Y + 96
_STATS_ROW_TOP_Y = _STATS_DIVIDER_Y + 16
_STATS_ROW_HEIGHT = 28

# Stat rows displayed on the right panel.
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

_CURSOR_COLOR = ColorSettings.YELLOW


class PartyScene(Scene):
    """Selectable roster -- left list, right stat panel."""

    OPAQUE = True

    def __init__(self, gm: "GameManager") -> None:
        super().__init__(gm)
        self._cursor: int = 0

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
        if self.gm.party.members:
            selected = self.gm.party.members[self._cursor]
            self._render_stats_panel(surface, selected)
        text_renderer.draw_text(
            surface,
            "Up/Down: switch    Cancel: return",
            (_ROSTER_LEFT_X, ScreenSettings.HEIGHT - _PROMPT_BOTTOM_MARGIN),
            color=ColorSettings.GRAY,
            size=FontSettings.SIZE_SMALL,
        )

    def _render_member(
        self, surface: pygame.Surface, member: "PartyMember", index: int
    ) -> None:
        """Render one member's status block at the indexed row."""
        top_y = _ROSTER_TOP_Y + index * _ROSTER_ROW_HEIGHT
        layout = RosterRowLayout(left_x=_ROSTER_LEFT_X, top_y=top_y)

        if index == self._cursor:
            triangle = layout.selection_triangle()
            pygame.draw.polygon(surface, _CURSOR_COLOR, triangle)
            DebugOverlay.polygon(
                surface, triangle, "cursor", DebugOverlay.COLOR_CURSOR,
            )

        portrait = load_portrait(member.id)
        portrait_rect = layout.portrait_rect
        surface.blit(portrait, portrait_rect.topleft)
        DebugOverlay.rect(
            surface, portrait_rect, "portrait", DebugOverlay.COLOR_PORTRAIT,
        )

        # HP has moved to the stats panel; the left column is purely
        # identity (name + element icons). Dead members still flash red
        # so a wipe is visible at a glance.
        name_color = (
            ColorSettings.RED if member.current_hp <= 0 else ColorSettings.WHITE
        )
        text_renderer.draw_text(
            surface,
            member.name,
            layout.name_pos,
            color=name_color,
            size=FontSettings.SIZE_BODY,
        )
        DebugOverlay.point(
            surface, layout.name_pos, "name", DebugOverlay.COLOR_TEXT,
        )
        DebugOverlay.point(
            surface, layout.element_pos, "elements", DebugOverlay.COLOR_TEXT,
        )
        # Roster element row: icons only (no word) when an icon exists.
        # Stats panel is the place where icons sit *next to* words.
        self._render_element_line(
            surface, member.elements, layout.element_pos, show_word=False,
        )

    def _render_element_line(
        self,
        surface: pygame.Surface,
        element_ids: tuple,
        pos: tuple[int, int],
        *,
        show_word: bool = True,
    ) -> None:
        """Draw a multi-color element-pair line starting at ``pos``.

        For each element id the renderer prefers the per-element icon
        from ``assets/graphics/icons/<id>.png`` (loaded lazily by
        ``utils.graphics.load_element_icon``). When an icon exists and
        ``show_word`` is False, only the icon is drawn (used by the
        roster on the left of the party screen and by the battle
        roster). When ``show_word`` is True the word is drawn directly
        after the icon (used by the stats panel on the right). Elements
        without an icon yet fall back to the word so partial icon
        coverage degrades gracefully.

        Entries are separated by a gray " + " so the player can tell at
        a glance that a member has more than one affinity.
        """
        font = text_renderer.get_font(FontSettings.SIZE_SMALL)
        x, y = pos
        separator = " + "
        for i, element_id in enumerate(element_ids):
            style = ColorSettings.ELEMENT_TEXT_STYLES.get(
                element_id, {"color": ColorSettings.WHITE}
            )
            icon = load_element_icon(element_id)
            if icon is not None:
                surface.blit(
                    icon, (x, y + UISettings.ELEMENT_ICON_Y_OFFSET)
                )
                x += UISettings.ELEMENT_ICON_SIZE
                if show_word:
                    x += UISettings.ELEMENT_ICON_WORD_GAP
                    text_renderer.draw_text(
                        surface, element_id, (x, y),
                        size=FontSettings.SIZE_SMALL,
                        **style,
                    )
                    x += font.size(element_id.upper())[0]
            else:
                text_renderer.draw_text(
                    surface, element_id, (x, y),
                    size=FontSettings.SIZE_SMALL,
                    **style,
                )
                x += font.size(element_id.upper())[0]
            if i < len(element_ids) - 1:
                text_renderer.draw_text(
                    surface, separator, (x, y),
                    color=ColorSettings.GRAY, size=FontSettings.SIZE_SMALL,
                )
                x += font.size(separator.upper())[0]

    def _render_stats_panel(
        self, surface: pygame.Surface, member: "PartyMember"
    ) -> None:
        """Paint the right-side stat panel for ``member``."""
        panel_rect = pygame.Rect(
            _STATS_PANEL_LEFT_X,
            _STATS_PANEL_TOP_Y,
            _STATS_PANEL_WIDTH,
            _STATS_PANEL_HEIGHT,
        )
        pygame.draw.rect(
            surface, ColorSettings.GRAY, panel_rect, _STATS_PANEL_BORDER
        )
        DebugOverlay.rect(
            surface, panel_rect, "stats panel", DebugOverlay.COLOR_PANEL,
        )
        text_renderer.draw_text(
            surface,
            member.name,
            (_STATS_LABEL_X, _STATS_HEADER_Y),
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_BODY,
        )
        self._render_element_line(
            surface, member.elements, (_STATS_LABEL_X, _STATS_ELEMENTS_Y),
        )
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
