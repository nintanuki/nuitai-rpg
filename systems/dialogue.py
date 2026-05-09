"""Run a dialogue tree, emitting one ``DialogueLineEvent`` per advance.

A dialogue tree is a JSON dict shaped roughly:

    {
        "id": "intro",
        "lines": [
            {"speaker": "Hina", "text": "..."},
            {"text": "..."}
        ]
    }

Layer 0 supports plain linear sequences; branching (choices, flags) is
a Layer 1 extension that will read additional fields from the same
shape. The runner emits ``DialogueLineEvent`` for each line and a
trailing ``DialogueEndedEvent`` once the tree is done.
"""

from __future__ import annotations

from typing import Any

from core.events import DialogueEndedEvent, DialogueLineEvent


class DialogueRunner:
    """Iterate the lines of a dialogue tree, emitting events."""

    def __init__(self, tree: dict[str, Any]) -> None:
        """Bind the runner to a parsed dialogue tree.

        Args:
            tree: A dict with at minimum an ``id`` and a ``lines`` list.
        """
        self.tree = tree
        self._lines: list[dict[str, Any]] = list(tree.get("lines", []))
        self._index = 0
        self._ended = False

    @property
    def is_done(self) -> bool:
        """Return True once the trailing end event has been emitted."""
        return self._ended

    def advance(self) -> list[Any]:
        """Emit the next line's event, or the end event if the tree is done.

        Returns:
            A list of event records (zero or one) for the caller to
            dispatch into views.
        """
        if self._ended:
            return []
        if self._index < len(self._lines):
            line = self._lines[self._index]
            self._index += 1
            return [
                DialogueLineEvent(
                    speaker=line.get("speaker"),
                    text=line.get("text", ""),
                )
            ]
        self._ended = True
        return [DialogueEndedEvent(self.tree.get("id", ""))]
