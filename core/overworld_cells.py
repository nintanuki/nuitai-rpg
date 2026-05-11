"""Static overworld cell content.

Pass-1 placeholder cells used to verify the `World` + `OverworldPlayer`
+ `OverworldScene` plumbing. Two cells sit side by side, joined by a
single one-tile opening at row 6 that lines up on both their inner
edges. When Pass 2 brings real cells, this module migrates to
``data/cells/*.json`` and the ``DataLoader`` reads them like every
other content pack.

Tile alphabet — keep in sync with ``OverworldSettings.*_CHAR`` in
[settings.py](../settings.py):

* ``'.'`` — walkable floor (grass placeholder color).
* ``'#'`` — wall (rocky brown placeholder color).
* ``'~'`` — impassable water (ocean blue placeholder color).
* ``'_'`` — walkable sand (sandy beige placeholder color).

``CELLS`` maps a cell name to its 12 × 20 char grid.
``WORLD_LAYOUT`` maps a world-space cell coordinate (cx, cy) — cx
grows east, cy grows south — to the cell name that lives there. The
player crosses cell edges by stepping past the action-window border;
``World.step_to_neighbor`` resolves the new coordinate against this
table.
"""

from __future__ import annotations


# The two Pass-1 test cells. Each row is exactly OverworldSettings.COLS
# characters wide; the module contains a smoke check at import time that
# enforces this so authoring typos fail loudly rather than silently
# misaligning the grid.

CELLS: dict[str, list[list[str]]] = {
    "beach_west": [
        list("####################"),
        list("#..................#"),
        list("#.......~~.........#"),
        list("#......~~~~........#"),
        list("#.......~~.........#"),
        list("#..................#"),
        list("#..................."),   # East edge opens at col 19, row 6.
        list("#..................#"),
        list("#.._...............#"),
        list("#..__..............#"),
        list("#..................#"),
        list("####################"),
    ],
    "beach_east": [
        list("####################"),
        list("#..................#"),
        list("#.........~~.......#"),
        list("#........~~~~......#"),
        list("#.........~~.......#"),
        list("#..................#"),
        list("...................#"),   # West edge opens at col 0, row 6.
        list("#..................#"),
        list("#...........__.....#"),
        list("#............__....#"),
        list("#..................#"),
        list("####################"),
    ],
}


# Cell-coordinate layout. cx grows east, cy grows south.
WORLD_LAYOUT: dict[tuple[int, int], str] = {
    (0, 0): "beach_west",
    (1, 0): "beach_east",
}


# Cell the player spawns into on a new game. ``OverworldPlayer.__init__``
# uses ``OverworldPlayerSettings.SPAWN_COL`` / ``SPAWN_ROW`` for the
# within-cell tile.
START_CELL_POS: tuple[int, int] = (0, 0)


def _validate_cells() -> None:
    """Fail loudly at import time if any cell is misshaped.

    Catches the easy authoring mistake of dropping or adding one
    character on a row, which would otherwise misalign the grid
    diagonally as soon as the player steps into that row.
    """
    # Local import: settings is the source of truth for the grid
    # dimensions, but we keep the import lazy so this module can be
    # introspected without forcing a settings import order.
    from settings import OverworldSettings

    for name, grid in CELLS.items():
        if len(grid) != OverworldSettings.ROWS:
            raise ValueError(
                f"Cell {name!r} has {len(grid)} rows; expected {OverworldSettings.ROWS}."
            )
        for row_index, row in enumerate(grid):
            if len(row) != OverworldSettings.COLS:
                raise ValueError(
                    f"Cell {name!r} row {row_index} has {len(row)} cols; "
                    f"expected {OverworldSettings.COLS}."
                )


_validate_cells()
