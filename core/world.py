"""Active overworld state.

Owns which cell is currently loaded, exposes per-tile wall queries
against that cell, and handles cell-to-cell transitions when the player
crosses the action-window edge. Putting this in one place keeps the
renderer (which reads ``current_grid``) and the player (which calls
``is_wall`` / ``step_to_neighbor``) decoupled from how the cell layout
is stored.

When more than one layer exists (overworld + dungeons + house
interiors), this is the natural place to grow a ``current_layer`` field
plus an entrance-tile table. For Pass 1 there is only the overworld
layer, so it stays implicit.

The shape of this module — ``CELLS`` / ``WORLD_LAYOUT`` / ``current_pos``
+ ``step_to_neighbor`` — is lifted from the Adventure project; the
implementation is written fresh in Nuitai's conventions and routes wall
queries through ``OverworldSettings.WALL_CHAR`` so the tile alphabet
lives in one place (``settings.py``).
"""

from __future__ import annotations

from core.overworld_cells import CELLS, START_CELL_POS, WORLD_LAYOUT
from settings import OverworldSettings


class World:
    """Tracks the active cell and answers wall/transition questions about it."""

    def __init__(self) -> None:
        """Initialize the world at ``START_CELL_POS``."""
        self.cells = CELLS
        self.layout = WORLD_LAYOUT
        self.current_pos: tuple[int, int] = START_CELL_POS
        self._refresh_active_cell()

    # ------------------------------------------------------------------
    # ACTIVE CELL
    # ------------------------------------------------------------------

    def _refresh_active_cell(self) -> None:
        """Re-bind ``current_cell_name`` and ``current_grid`` from ``current_pos``."""
        cell_name = self.layout[self.current_pos]
        self.current_cell_name: str = cell_name
        self.current_grid: list[list[str]] = self.cells[cell_name]

    # ------------------------------------------------------------------
    # COLLISION QUERIES
    # ------------------------------------------------------------------

    def is_wall(self, col: int, row: int) -> bool:
        """Return whether the tile at ``(col, row)`` blocks movement.

        Tiles outside the cell's grid are reported as non-walls so the
        player can step into the cell-transition code in
        ``OverworldPlayer._begin_step`` rather than being clamped by
        collision.

        Args:
            col: Cell-local column index (0-based, east-positive).
            row: Cell-local row index (0-based, south-positive).

        Returns:
            ``True`` for wall tiles and impassable water; ``False`` for
            floor, sand, and out-of-bounds positions.
        """
        if not (0 <= row < OverworldSettings.ROWS and 0 <= col < OverworldSettings.COLS):
            return False
        tile = self.current_grid[row][col]
        return tile == OverworldSettings.WALL_CHAR or tile == OverworldSettings.WATER_CHAR

    # ------------------------------------------------------------------
    # CELL TRANSITIONS
    # ------------------------------------------------------------------

    def step_to_neighbor(self, dx_cells: int, dy_cells: int) -> bool:
        """Try to swap to the neighbor cell at the given world offset.

        Args:
            dx_cells: ``-1`` west, ``+1`` east, ``0`` no horizontal step.
            dy_cells: ``-1`` north, ``+1`` south, ``0`` no vertical step.

        Returns:
            ``True`` if the neighbor cell exists and was swapped in;
            ``False`` if no cell sits at that world coordinate (caller
            should treat the step as a bump).
        """
        cx, cy = self.current_pos
        new_pos = (cx + dx_cells, cy + dy_cells)
        if new_pos in self.layout:
            self.current_pos = new_pos
            self._refresh_active_cell()
            return True
        return False

    # ------------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise just the active-cell pointer; cells themselves are static."""
        return {"current_pos": list(self.current_pos)}

    def from_dict(self, data: dict) -> None:
        """Restore the active-cell pointer from a saved dict."""
        pos = data.get("current_pos")
        if isinstance(pos, list) and len(pos) == 2:
            candidate = (int(pos[0]), int(pos[1]))
            if candidate in self.layout:
                self.current_pos = candidate
                self._refresh_active_cell()
