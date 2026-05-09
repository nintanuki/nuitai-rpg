"""Save / load with schema versioning.

A save is a JSON file under ``SaveSettings.SAVES_DIR``, one file per
slot. The file always contains a ``version`` key. The loader runs the
data through ``migrate`` before handing it to gameplay code so older
saves continue to load after schema changes.

Slots are integer ids:
- ``SaveSettings.AUTOSAVE_SLOT_ID`` (0): the autosave.
- 1..``SaveSettings.MAX_SAVE_SLOTS``: player-driven slots.
"""

from __future__ import annotations

import json
import os
from typing import Any

from settings import SaveSettings


# Bump when the on-disk shape of a save changes. Add a migration step
# in ``migrate`` for every increment so older saves keep loading.
SAVE_SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

def slot_path(slot_id: int) -> str:
    """Return the absolute path of the save file for ``slot_id``."""
    return os.path.join(SaveSettings.SAVES_DIR, f"slot_{slot_id}.json")


def slot_exists(slot_id: int) -> bool:
    """Return True if a save file exists for ``slot_id``."""
    return os.path.isfile(slot_path(slot_id))


# ---------------------------------------------------------------------------
# READ / WRITE
# ---------------------------------------------------------------------------

def save(slot_id: int, payload: dict[str, Any]) -> None:
    """Write ``payload`` to ``slot_id``, stamping the current schema version.

    Args:
        slot_id: The save slot to write.
        payload: The gameplay state to persist. Must be JSON-serialisable.
    """
    os.makedirs(SaveSettings.SAVES_DIR, exist_ok=True)
    record = {"version": SAVE_SCHEMA_VERSION, "data": payload}
    with open(slot_path(slot_id), "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)


def load(slot_id: int) -> dict[str, Any]:
    """Load the save at ``slot_id``, applying any migrations.

    Args:
        slot_id: The save slot to read.

    Returns:
        The migrated ``data`` payload (the inner dict, not the wrapper).

    Raises:
        FileNotFoundError: If the slot does not exist.
        ValueError: If the file is malformed or fails to migrate.
    """
    path = slot_path(slot_id)
    with open(path, "r", encoding="utf-8") as f:
        record = json.load(f)
    if not isinstance(record, dict) or "version" not in record:
        raise ValueError(f"save {path} is missing a version stamp")
    return migrate(record)


# ---------------------------------------------------------------------------
# MIGRATIONS
# ---------------------------------------------------------------------------

def migrate(record: dict[str, Any]) -> dict[str, Any]:
    """Walk a save record forward to ``SAVE_SCHEMA_VERSION``.

    Each schema bump appends a step here. The function returns the
    inner ``data`` payload at the current version. Unknown future
    versions raise ``ValueError`` rather than silently corrupting state.

    Args:
        record: The full ``{"version": N, "data": ...}`` wrapper read
            from disk.

    Returns:
        The migrated ``data`` dict at ``SAVE_SCHEMA_VERSION``.
    """
    version = record.get("version", 0)
    data = record.get("data", {})
    if version > SAVE_SCHEMA_VERSION:
        raise ValueError(
            f"save was written with version {version}, "
            f"this build only understands up to {SAVE_SCHEMA_VERSION}"
        )
    # No migrations yet — this is the first version. Future steps go
    # here as ``if version < N: data = _migrate_to_N(data); version = N``.
    return data
