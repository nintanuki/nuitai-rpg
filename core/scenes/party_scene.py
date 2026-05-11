"""The PARTY status screen — read-only roster.

Pushed by [core/scenes/menu_scene.py](menu_scene.py) when the player
picks PARTY. Shows each member's name, current HP / max HP, and
element pair. Cancel (B / Backspace) pops it back to the system menu.

Pass-2 first cut keeps this strictly informational — no equipment,
no ability lists, no per-member sub-cursor. The intent is to give
Frankie's save / load round-trip a place to *see* that HP actually
persisted across a battle and a session. The richer party screen
(equipment, learnset, status effects, swap order) is a Layer-1+
deliverable that this file's renderer will extend in place.
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
_ROSTER_TOP_Y = 120
_ROSTER_ROW_HEIGHT = 60
_ROSTER_LEFT_X = 60
_PROMPT_BOTTOM_MARGIN = 30


class PartyScene(Scene):
    """Read-only roster screen — name, HP/maxHP, elements."""

    OPAQUE = True

    def __init__(self, gm: "GameManager") -> None:
        """Bind this scene to the host game manager.

        Args:
            gm: The host game manager. ``gm.party`` is the data source.
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
        """Paint heading + each member's status line + the cancel prompt.

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
        # Bottom-of-screen hint so the player knows what to press.
        text_renderer.draw_text(
            surface,
            "Press cancel to return.",
            (_ROSTER_LEFT_X, ScreenSettings.HEIGHT - _PROMPT_BOTTOM_MARGIN),
            color=ColorSettings.GRAY,
            size=FontSettings.SIZE_SMALL,
        )

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    def _render_member(
        self, surface: pygame.Surface, member, index: int
    ) -> None:
        """Render one member's status block at the indexed row.

        Args:
            surface: The screen surface to draw onto.
            member: The party member being rendered.
            index: Zero-based row index.
        """
        top_y = _ROSTER_TOP_Y + index * _ROSTER_ROW_HEIGHT
        # First line: name + current/max HP. Tinted yellow when HP is
        # at zero so a save loaded into "KO'd" state is visually
        # obvious; otherwise plain white.
        hp_color = (
            ColorSettings.RED if member.current_hp <= 0 else ColorSettings.WHITE
        )
        text_renderer.draw_text(
            surface,
            f"{member.name}    HP {member.current_hp} / {member.max_hp}",
            (_ROSTER_LEFT_X, top_y),
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
        element_y = top_y + 24
        cursor_x = _ROSTER_LEFT_X
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
