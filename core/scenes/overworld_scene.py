"""The overworld — sprite walks a tile grid, message box at the bottom.

The Layer-3 destination scene, kicked off early so it can advance in
parallel with the Layer-1 text demo / battle polish. Owns three
collaborators: a ``World`` (cell layout + active-cell pointer), an
``OverworldPlayer`` (logical position + sprite animation + held-input
polling), and a ``TextBox`` (the existing widget, reused unchanged for
the bottom message panel).

What is and is not here in Pass 1:

* **Walking, cell transitions, save/load round-trip** — yes.
* **System-menu push on Tab / START** — yes (re-uses ``MenuScene``).
* **NPCs, dialogue triggers, signs, warp tiles, encounters** — Pass 2.
* **Animated walk cycle, real sprite art** — Pass 2.

The cell area renders as one filled rect per tile, keyed off the cell
char (``OverworldSettings.*_CHAR``). Pass 2 swaps the per-tile rect for
a sprite blit when real placeholder tile art is available; this scene
already isolates the tile-rendering loop in ``_render_cell`` so the
swap is local.

See [docs/design/overworld.md](../../docs/design/overworld.md) for the
full design rationale.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from core.scene import Scene
from core.world import World
from entities.overworld_player import OverworldPlayer
from settings import (
    ColorSettings,
    EncounterSettings,
    GridSettings,
    OverworldSettings,
)
from ui import input_map
from ui.text_box import TextBox
from utils.backgrounds import render_scene_background

if TYPE_CHECKING:
    from main import GameManager


# Mapping from cell char to placeholder tile color. Kept local to this
# module because it is purely a Pass-1 rendering concern; once real
# tile sprites land in Pass 2, this dict is replaced by a lookup of
# tile surfaces by char.
_TILE_COLORS: dict[str, tuple[int, int, int]] = {
    OverworldSettings.FLOOR_CHAR: ColorSettings.OVERWORLD_FLOOR,
    OverworldSettings.WALL_CHAR: ColorSettings.OVERWORLD_WALL,
    OverworldSettings.WATER_CHAR: ColorSettings.OVERWORLD_WATER,
    OverworldSettings.SAND_CHAR: ColorSettings.OVERWORLD_SAND,
}


class OverworldScene(Scene):
    """The screen-locked, cell-based overworld."""

    OPAQUE = True

    def __init__(self, gm: "GameManager") -> None:
        """Construct the overworld with its world, player, and text box.

        Args:
            gm: The host game manager. Provides audio, save, and
                cross-scene navigation routing.
        """
        super().__init__(gm)
        self.world = World()
        self.player = OverworldPlayer(gm, self.world)
        # Cell area is narrower than the screen, so size the text box
        # to the full screen width but keep the existing 160-px height.
        self.text_box = TextBox()
        # Encounter pacing. ``_last_seen_step_count`` tracks how many
        # of the player's steps we've already rolled against; the
        # difference between it and ``player.step_count`` each frame
        # is "new steps this update". ``_quiet_steps`` is the running
        # count of consecutive non-encounter steps — it reaches the
        # eligibility threshold and then every subsequent step is a
        # random check against ``EncounterSettings.RATE_PER_STEP``.
        # Reset to zero whenever an encounter pushes a battle so the
        # player gets a guaranteed quiet window when they return.
        self._last_seen_step_count: int = 0
        self._quiet_steps: int = 0

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route one event.

        When the text box has content, confirm advances it and other
        keys fall through silently (so a held direction won't queue
        steps that fire the instant the player closes a dialogue).
        Otherwise, Tab / START pushes the system menu; movement is
        polled inside ``player.update`` and does not go through this
        handler.

        Args:
            event: The pygame event to route.
        """
        if not self.text_box.is_done():
            if input_map.is_confirm(event):
                self.text_box.advance()
            return
        if input_map.is_menu(event):
            self._open_menu()

    def update(self, dt: float) -> None:
        """Tick the text box, then advance the player if no text is showing.

        After advancing the player, any newly-completed steps roll for
        a random encounter; on a hit a ``BattleScene`` is pushed on
        top of this scene. The overworld resumes automatically when
        the battle pops, since this scene was never destroyed.

        Args:
            dt: Frame time in seconds.
        """
        self.text_box.update(dt)
        if not self.text_box.is_done():
            return
        self.player.update(dt)
        self._update_encounter_rolls()

    def _update_encounter_rolls(self) -> None:
        """Roll a random encounter once per newly-completed step.

        The player exposes a monotonic ``step_count`` that increments
        each time a step animation finishes; subtracting our last-seen
        value gives the number of new steps to roll against this
        frame. Each new step adds one to ``_quiet_steps``; once the
        running quiet count meets ``EncounterSettings.MIN_QUIET_STEPS``,
        every subsequent step is a Bernoulli trial against
        ``RATE_PER_STEP``. On the first hit, the encounter pushes a
        battle and the quiet counter resets so the player gets a fresh
        eligibility window after the fight.
        """
        new_steps = self.player.step_count - self._last_seen_step_count
        if new_steps <= 0:
            return
        self._last_seen_step_count = self.player.step_count
        for _ in range(new_steps):
            self._quiet_steps += 1
            if self._quiet_steps < EncounterSettings.MIN_QUIET_STEPS:
                continue
            if random.random() < EncounterSettings.RATE_PER_STEP:
                self._trigger_encounter()
                return

    def _trigger_encounter(self) -> None:
        """Push a ``BattleScene`` on top of this scene and reset pacing.

        Pass-2 first cut uses ``BattleScene``'s own random enemy roll
        (the ``_DEMO_ENEMY_IDS`` pool). The encounter table will move
        to per-cell data once cell content migrates to JSON.
        """
        # Local import: ``BattleScene`` lives in a sibling scene file
        # and importing it at the top would risk a cycle the moment a
        # battle ever needs to read overworld state on the way out.
        from core.scenes.battle_scene import BattleScene

        self._quiet_steps = 0
        self.gm.scene_stack.push(BattleScene(self.gm))

    def render(self, surface: pygame.Surface) -> None:
        """Paint background, cell tiles, player, and message box in that order.

        Args:
            surface: The screen surface to draw onto.
        """
        render_scene_background(self, surface)
        self._render_cell(surface)
        self.player.render(surface)
        self.text_box.render(surface)

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    def _render_cell(self, surface: pygame.Surface) -> None:
        """Draw the active cell's tile grid as one filled rect per tile.

        Args:
            surface: The screen surface to draw onto.
        """
        grid = self.world.current_grid
        tile_size = GridSettings.TILE_SIZE
        default_color = ColorSettings.OVERWORLD_FLOOR
        for row in range(OverworldSettings.ROWS):
            row_cells = grid[row]
            for col in range(OverworldSettings.COLS):
                char = row_cells[col]
                color = _TILE_COLORS.get(char, default_color)
                rect = pygame.Rect(
                    OverworldSettings.X + col * tile_size,
                    OverworldSettings.Y + row * tile_size,
                    tile_size,
                    tile_size,
                )
                pygame.draw.rect(surface, color, rect)

    def _open_menu(self) -> None:
        """Push the translucent system menu on top of this scene."""
        # Local import: ``MenuScene`` lives in a sibling scene module
        # and importing it at top of file would risk a cycle if the
        # menu ever pushes overworld-aware actions later.
        from core.scenes.menu_scene import MenuScene

        self.gm.scene_stack.push(MenuScene(self.gm))

    # ------------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise the active cell pointer and the player's tile state."""
        base = super().to_dict()
        base["world"] = self.world.to_dict()
        base["player"] = self.player.to_dict()
        return base

    @classmethod
    def from_dict(cls, gm: "GameManager", data: dict) -> "OverworldScene":
        """Rebuild a scene from a previously-saved dict.

        Args:
            gm: The host game manager.
            data: The dict previously returned by ``to_dict``.

        Returns:
            A fully-restored ``OverworldScene``.
        """
        scene = cls(gm)
        if isinstance(data, dict):
            world_data = data.get("world")
            if isinstance(world_data, dict):
                scene.world.from_dict(world_data)
            player_data = data.get("player")
            if isinstance(player_data, dict):
                scene.player.from_dict(player_data)
        return scene
