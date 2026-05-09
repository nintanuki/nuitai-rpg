"""Battle scene — hosts a ``Battle`` and a ``BattleView``.

Layer 0 wires up the simulation -> view seam without yet exposing
command selection. The encounter is loaded from ``data/enemies/`` via
``core.factories`` so the JSON -> runtime path is demonstrated end to
end. Each frame, while the text box is empty, the scene advances the
battle by one turn and feeds the resulting events into the view. When
the battle ends and the text box drains, the scene pops itself.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from core.elements import Element
from core.events import BattleEndedEvent
from core.factories import (
    combatant_from_enemy_data,
    combatant_from_party_member,
)
from core.scene import Scene
from settings import ColorSettings, FontSettings, ScreenSettings
from systems.battle import Battle, Combatant
from ui import input_map, text_renderer
from ui.battle_view import BattleView
from ui.text_box import TextBox

if TYPE_CHECKING:
    from main import GameManager


# Layer-0 default opponent id. Layer 1 will pick encounters from a
# dungeon's encounter table; this constant just keeps the test world
# fightable while the engine is the only thing being exercised.
_DEFAULT_ENEMY_ID = "shade"


def _build_party_combatants(party) -> list[Combatant]:
    """Map party members to combatants via the shared factory."""
    return [combatant_from_party_member(m) for m in party.members]


def _build_enemies(gm: "GameManager") -> list[Combatant]:
    """Load the Layer-0 placeholder encounter from content data."""
    enemies = gm.data.load("enemies")
    data = enemies.get(_DEFAULT_ENEMY_ID)
    if data is not None:
        return [combatant_from_enemy_data(data)]
    # Hard fallback so the engine still boots if content is missing.
    return [
        Combatant(
            _DEFAULT_ENEMY_ID, "Shade",
            hp=24, attack=6, element=Element.AKU, is_party=False,
        ),
    ]


class BattleScene(Scene):
    """A turn-based encounter scene."""

    OPAQUE = True

    def __init__(self, gm: "GameManager") -> None:
        """Build the battle and its presentation pipeline."""
        super().__init__(gm)
        self.battle = Battle(
            party_combatants=_build_party_combatants(self.gm.party),
            enemy_combatants=_build_enemies(self.gm),
        )
        self.text_box = TextBox()
        self.view = BattleView(self.text_box)
        self._battle_finished = False

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Confirm advances the text box; cancel attempts to flee."""
        if input_map.is_confirm(event):
            self.text_box.advance()
        elif input_map.is_cancel(event) and not self._battle_finished:
            for ev in self.battle.flee():
                self.view.consume(ev)
                if isinstance(ev, BattleEndedEvent):
                    self._battle_finished = True

    def update(self, dt: float) -> None:
        """Advance the simulation while the box is empty; tick typewriter."""
        self.text_box.update(dt)
        if (
            not self._battle_finished
            and self.text_box.is_done()
            and not self.battle.is_over
        ):
            for ev in self.battle.step():
                self.view.consume(ev)
                if isinstance(ev, BattleEndedEvent):
                    self._battle_finished = True
        # When the battle is over and all narration has drained, return to
        # the world.
        if self._battle_finished and self.text_box.is_done():
            self.gm.scene_stack.pop()

    def render(self, surface: pygame.Surface) -> None:
        """Draw a barebones combat HUD plus the text box."""
        surface.fill(ColorSettings.BG_COLOR)
        text_renderer.draw_text(
            surface,
            "Battle",
            (40, 40),
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_HEADING,
        )

        # Party HP column on the left.
        for index, c in enumerate(self.battle.party):
            text_renderer.draw_text(
                surface,
                f"{c.name}  {c.hp}/{c.max_hp}",
                (40, 100 + index * 28),
            )
        # Enemy HP column on the right.
        right_x = ScreenSettings.WIDTH - 240
        for index, c in enumerate(self.battle.enemies):
            text_renderer.draw_text(
                surface,
                f"{c.name}  {c.hp}/{c.max_hp}",
                (right_x, 100 + index * 28),
            )
        self.text_box.render(surface)
