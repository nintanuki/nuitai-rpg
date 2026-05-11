"""Overworld player — grid-stepped, pixel-interpolated.

Logical position is ``(col, row)`` in cell-local tile coordinates.
The sprite's pixel position is interpolated each frame between the
previous tile and the destination tile over
``OverworldPlayerSettings.STEP_DURATION_MS``, so movement feels smooth
even though the underlying rules are tile-based.

This class is intentionally JRPG-traditional:

* Four-directional only; diagonals are never returned from the input
  layer for movement (the polled reader keeps the dominant axis when
  the player holds two directions at once).
* Held-input is read polled inside ``update`` rather than event-driven.
  Pygame's ``KEYDOWN`` repeat would have to be reconfigured per-scene
  to feel right, and that bleeds global state into the text box and
  menus. Polling stays local.
* Facing direction is the most recent attempted step (a wall bump
  still turns the sprite to face the wall).

Pass-1 rendering is a flat colored rectangle so the scaffolding can be
verified end-to-end before any sprite art exists. Pass-2 will swap in
real sprite frames; this file's only contract with the rest of the
code is the four facing directions, so adding frames is a local
change.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import pygame

from core.world import World
from settings import GridSettings, OverworldPlayerSettings, OverworldSettings
from ui import input_map

if TYPE_CHECKING:
    from main import GameManager


class OverworldPlayer:
    """Grid-stepped overworld leader with pixel-interpolation animation."""

    def __init__(self, gm: "GameManager", world: World) -> None:
        """Spawn the player at the configured starting tile.

        Args:
            gm: Active game manager. Used to reach the cached joystick
                list for polled direction reads.
            world: Active world model. Queried for wall collision and
                cell-edge transitions.
        """
        self.gm = gm
        self.world = world
        # Logical position in cell-local tile coordinates.
        self.col: int = OverworldPlayerSettings.SPAWN_COL
        self.row: int = OverworldPlayerSettings.SPAWN_ROW
        # Facing direction as a (dx, dy) cardinal unit vector. Default
        # south so the placeholder sprite has a stable facing on spawn.
        self.facing: tuple[int, int] = (0, 1)
        # Animation state. ``_step_progress`` walks 0.0 -> 1.0 over one
        # step duration; while ``_step_active`` is True the renderer
        # interpolates between ``_step_start`` and ``_step_target``.
        self._step_active: bool = False
        self._step_start: tuple[int, int] = (self.col, self.row)
        self._step_target: tuple[int, int] = (self.col, self.row)
        self._step_progress: float = 0.0
        # Monotonic count of completed step animations. The overworld
        # scene watches this to know when to roll for random
        # encounters — it increments once per successful tile-to-tile
        # walk, ignoring wall-bumps and cell transitions (the latter
        # snap instead of animating). Pass-1 saves do not persist this
        # value; a fresh load gets a fresh counter and benefits from
        # ``EncounterSettings.MIN_QUIET_STEPS`` as a natural grace
        # window.
        self.step_count: int = 0

    # ------------------------------------------------------------------
    # POSITION HELPERS
    # ------------------------------------------------------------------

    def _logical_pixel(self, col: int, row: int) -> tuple[int, int]:
        """Return the screen-space top-left for a tile in the active cell.

        Args:
            col: Cell-local column index.
            row: Cell-local row index.

        Returns:
            A ``(x, y)`` screen-space pixel coordinate suitable for
            blitting a TILE_SIZE square sprite at.
        """
        x = OverworldSettings.X + col * GridSettings.TILE_SIZE
        y = OverworldSettings.Y + row * GridSettings.TILE_SIZE
        return x, y

    def _snap_to_logical(self) -> None:
        """Force any in-flight animation to drop to the logical tile.

        Called after a cell transition or a save-load restore — the
        sprite snaps to the new logical position rather than animating
        across a discontinuity.
        """
        self._step_active = False
        self._step_start = (self.col, self.row)
        self._step_target = (self.col, self.row)
        self._step_progress = 0.0

    # ------------------------------------------------------------------
    # STEP CONTROL
    # ------------------------------------------------------------------

    def _begin_step(self, dx: int, dy: int) -> None:
        """Validate and start a step in a cardinal direction.

        Args:
            dx: ``-1`` west, ``+1`` east, ``0`` no horizontal step.
            dy: ``-1`` north, ``+1`` south, ``0`` no vertical step.
        """
        if dx == 0 and dy == 0:
            return
        # Always face the direction the player tried to move, even if
        # the step fails. That is how DQ-style "bumping" feels right.
        self.facing = (dx, dy)
        target_col = self.col + dx
        target_row = self.row + dy

        # Cell-edge crossing: ask the world to swap cells. The matching
        # entry tile in the new cell becomes the player's new logical
        # position; the sprite snaps to it rather than animating across
        # the seam.
        out_of_x = not (0 <= target_col < OverworldSettings.COLS)
        out_of_y = not (0 <= target_row < OverworldSettings.ROWS)
        if out_of_x or out_of_y:
            dx_cells = 1 if target_col >= OverworldSettings.COLS else (
                -1 if target_col < 0 else 0
            )
            dy_cells = 1 if target_row >= OverworldSettings.ROWS else (
                -1 if target_row < 0 else 0
            )
            if self.world.step_to_neighbor(dx_cells, dy_cells):
                self.col = target_col % OverworldSettings.COLS
                self.row = target_row % OverworldSettings.ROWS
                self._snap_to_logical()
            # On failure: bump (no animation, just the face-turn above).
            return

        # In-cell wall check.
        if self.world.is_wall(target_col, target_row):
            return  # bump

        # Begin animation.
        self._step_active = True
        self._step_start = (self.col, self.row)
        self._step_target = (target_col, target_row)
        self._step_progress = 0.0
        self.col = target_col
        self.row = target_row

    def _read_polled_direction(self) -> tuple[int, int]:
        """Read the currently-held cardinal direction, normalised to one axis.

        When the player holds two perpendicular directions, the
        existing facing axis wins — that makes corner-turning feel
        responsive instead of locking the sprite into a diagonal.

        Returns:
            A cardinal ``(dx, dy)`` with at most one component non-zero.
        """
        dx, dy = input_map.read_held_direction(self.gm.connected_joysticks)
        if dx == 0 and dy == 0:
            return 0, 0
        if dx != 0 and dy != 0:
            # Keep the axis already being walked; if neither, prefer
            # horizontal (matches most JRPG conventions).
            if self.facing[1] != 0 and self.facing[0] == 0:
                return 0, dy
            return dx, 0
        return dx, dy

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance the step animation and, at idle, start the next step.

        Args:
            dt: Frame time in seconds. Pulled straight from
                ``clock.tick(FPS) / 1000.0`` upstream.
        """
        if self._step_active:
            step_seconds = OverworldPlayerSettings.STEP_DURATION_MS / 1000.0
            self._step_progress += dt / step_seconds
            if self._step_progress >= 1.0:
                self._step_active = False
                self._step_progress = 0.0
                # Count only completed animated steps — wall-bumps
                # never started one, and cell transitions snap rather
                # than animate. This is exactly the "the player just
                # walked onto a new tile" signal the encounter system
                # needs.
                self.step_count += 1
            return
        dx, dy = self._read_polled_direction()
        if dx == 0 and dy == 0:
            return
        self._begin_step(dx, dy)

    def render(self, surface: pygame.Surface) -> None:
        """Draw the placeholder sprite at the current (interpolated) position.

        Args:
            surface: The screen surface to draw onto.
        """
        if self._step_active:
            start_x, start_y = self._logical_pixel(*self._step_start)
            end_x, end_y = self._logical_pixel(*self._step_target)
            t = max(0.0, min(1.0, self._step_progress))
            x = int(start_x + (end_x - start_x) * t)
            y = int(start_y + (end_y - start_y) * t)
        else:
            x, y = self._logical_pixel(self.col, self.row)
        rect = pygame.Rect(
            x, y, OverworldPlayerSettings.SIZE, OverworldPlayerSettings.SIZE
        )
        pygame.draw.rect(surface, OverworldPlayerSettings.COLOR, rect)

    # ------------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise logical position and facing to a JSON-safe dict."""
        return {
            "col": self.col,
            "row": self.row,
            "facing": list(self.facing),
        }

    def from_dict(self, data: dict) -> None:
        """Restore logical position and facing from a saved dict.

        Args:
            data: The dict previously returned by ``to_dict``. Missing
                or malformed fields are ignored, leaving the current
                value in place.
        """
        col = data.get("col")
        row = data.get("row")
        if isinstance(col, int):
            self.col = col
        if isinstance(row, int):
            self.row = row
        facing = data.get("facing")
        if isinstance(facing, list) and len(facing) == 2:
            try:
                self.facing = (int(facing[0]), int(facing[1]))
            except (TypeError, ValueError):
                pass
        self._snap_to_logical()
