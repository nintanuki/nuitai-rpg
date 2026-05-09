"""Load JSON content packs from ``data/``.

Content packs are directories of JSON files under ``data/<kind>/``.
Each file is one entity (e.g. ``data/characters/kailo.json``). Files
must have an ``id`` field; the loader uses it as the dict key so
gameplay code looks entities up by name rather than filesystem path.

Example:
    >>> loader = DataLoader()
    >>> chars = loader.load("characters")
    >>> chars["kailo"]["name"]
    'Kailo'

The directory ``data/`` itself does not need to exist for the engine to
boot — empty packs return ``{}``. This lets Layer 0 stand up before any
content is written.
"""

from __future__ import annotations

import json
import os
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")


class DataLoadError(ValueError):
    """Raised when a content pack file is malformed or missing required keys."""


class DataLoader:
    """Read JSON content packs from ``data/<kind>/``."""

    def __init__(self, data_dir: str = DATA_DIR) -> None:
        """Bind the loader to ``data_dir`` (defaults to repo-relative ``data/``).

        Args:
            data_dir: The directory to read content packs from.
        """
        self.data_dir = data_dir
        self._cache: dict[str, dict[str, dict[str, Any]]] = {}

    def load(self, kind: str) -> dict[str, dict[str, Any]]:
        """Return the pack for ``kind`` as a dict keyed by each entity's ``id``.

        Args:
            kind: The pack subdirectory name (e.g. ``"characters"``).

        Returns:
            A dict mapping entity id to its parsed JSON dict. Empty if
            the directory does not exist.

        Raises:
            DataLoadError: If a JSON file is malformed or lacks an ``id``.
        """
        if kind in self._cache:
            return self._cache[kind]

        pack_dir = os.path.join(self.data_dir, kind)
        pack: dict[str, dict[str, Any]] = {}
        if not os.path.isdir(pack_dir):
            self._cache[kind] = pack
            return pack

        for name in sorted(os.listdir(pack_dir)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(pack_dir, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
            except json.JSONDecodeError as error:
                raise DataLoadError(f"{path}: invalid JSON ({error})") from error
            if not isinstance(entry, dict) or "id" not in entry:
                raise DataLoadError(f"{path}: missing required 'id' field")
            pack[entry["id"]] = entry

        self._cache[kind] = pack
        return pack

    def reload(self, kind: str | None = None) -> None:
        """Drop cached packs so the next ``load`` reads from disk again.

        Args:
            kind: If given, drop only that pack; otherwise drop all.
        """
        if kind is None:
            self._cache.clear()
        else:
            self._cache.pop(kind, None)
