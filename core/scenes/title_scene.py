"""The title screen — the first scene the player sees.

Offers NEW GAME, CONTINUE, LOAD GAME, and QUIT.
Picking NEW GAME builds a default party and replaces the stack with
the test world. Picking CONTINUE loads slot 1 and does the same.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from core import save
from core.factories import party_member_from_data
from core.scene import Scene
from settings import ColorSettings, FontSettings, SaveSettings, ScreenSettings, UISettings
from systems.party import Party
from ui import input_map, text_renderer
from ui.menu import Menu, MenuItem

if TYPE_CHECKING:
    from main import GameManager


# Order in which the Layer-0 default party is built. The ids are
# resolved against ``data/characters/`` so adding a member is a
# data-only change once Layer 1's roster is settled.
_DEFAULT_PARTY_IDS: tuple[str, ...] = ("kailo", "hina", "tawiri")


def build_default_party(gm: "GameManager") -> Party:
    """Construct a fresh party from ``data/characters/`` content.

    Args:
        gm: The host game manager (provides the shared ``DataLoader``).

    Returns:
        A populated ``Party``. Missing character files are skipped
        rather than crashing so a partial content pack still boots.
    """
    characters = gm.data.load("characters")
    party = Party()
    for member_id in _DEFAULT_PARTY_IDS:
        data = characters.get(member_id)
        if data is None:
            continue
        party.add(party_member_from_data(data))
    return party


class TitleScene(Scene):
    """The opening menu."""

    OPAQUE = True

    def __init__(self, gm: "GameManager") -> None:
        """Construct the title screen menu."""
        super().__init__(gm)
        from core.scenes.test_world_scene import TestWorldScene  # local: cycle.

        any_save_exists = any(
            save.slot_exists(slot_id)
            for slot_id in range(
                SaveSettings.AUTOSAVE_SLOT_ID,
                SaveSettings.MAX_SAVE_SLOTS + 1,
            )
        )
        self.menu = Menu(
            items=[
                MenuItem("New Game", self._new_game),
                MenuItem("Continue", self._continue, enabled=any_save_exists),
                MenuItem("Load Game", self._load_game, enabled=any_save_exists),
                MenuItem("Quit", self.gm.close_game),
            ],
        )
        self._test_world_cls = TestWorldScene

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def _continue(self) -> None:
        """Load slot 1 and replace the stack with the test world."""
        try:
            data = save.load(1)
        except (FileNotFoundError, ValueError):
            return
        self.gm.party = Party.from_dict(data.get("party", {}))
        self.gm.scene_stack.replace(self._test_world_cls(self.gm))
    
    def _new_game(self) -> None:
        """Replace the stack with a fresh test world and a default party."""
        self.gm.party = build_default_party(self.gm)
        self.gm.scene_stack.replace(self._test_world_cls(self.gm))

    def _load_game(self) -> None:
        """Load game entry point (currently mirrors CONTINUE behavior)."""
        self._continue()

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Translate input into menu navigation.
        
        Args:
            event: The pygame event to handle.
        """
        if input_map.is_up(event):
            self.menu.move_up()
        elif input_map.is_down(event):
            self.menu.move_down()
        elif input_map.is_confirm(event):
            self.menu.confirm()

    def render(self, surface: pygame.Surface) -> None:
        """
        Draw the title text and the menu.
        
        Args:
            surface: The screen surface to draw on.
        """
        surface.fill(ColorSettings.BG_COLOR)

        text_renderer.draw_text(
            surface,
            ScreenSettings.TITLE_SCREEN_HEADING,
            (UISettings.TITLE_SCREEN_HEADING_X, UISettings.TITLE_SCREEN_HEADING_Y),
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_TITLE_SCREEN_HEADING,
        )

        self.menu.render(
            surface,
            (UISettings.TITLE_SCREEN_MENU_X, UISettings.TITLE_SCREEN_MENU_TOP_Y),
            centered=False,
            item_spacing=UISettings.TITLE_SCREEN_MENU_ITEM_SPACING,
        )
