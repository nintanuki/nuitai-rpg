"""The party — characters, inventory, gold, story flags.

This module owns the runtime state that survives across scenes and is
the primary thing saves persist. Everything is plain Python types so
``to_dict`` / ``from_dict`` round-trip cleanly through JSON.

Combat statistics for individual party members are stored as a flat
dict; the schema is deliberately loose at Layer 0 so content can grow
into it. Layer 1 will pin the schema once character data files exist.
"""

from __future__ import annotations

from typing import Any


class PartyMember:
    """One member of the party."""

    def __init__(
        self,
        member_id: str,
        name: str,
        elements: tuple[str, str],
        stats: dict[str, int] | None = None,
    ) -> None:
        """Construct a party member.

        Args:
            member_id: Stable id used for save/load and content lookup
                (e.g. ``"kailo"``).
            name: Display name.
            elements: The member's two element ids (e.g. ``("ahi", "wai")``).
            stats: Optional initial stat dict. Missing keys default to 0.
        """
        self.id = member_id
        self.name = name
        self.elements = elements
        self.stats = dict(stats) if stats else {}

    def to_dict(self) -> dict[str, Any]:
        """Serialise this member to a JSON-safe dict."""
        return {
            "id": self.id,
            "name": self.name,
            "elements": list(self.elements),
            "stats": dict(self.stats),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PartyMember":
        """Reconstruct a ``PartyMember`` from a dict produced by ``to_dict``."""
        return cls(
            member_id=data["id"],
            name=data["name"],
            elements=tuple(data["elements"]),
            stats=dict(data.get("stats", {})),
        )


class Party:
    """The whole adventuring party plus shared inventory and flags."""

    def __init__(self) -> None:
        """Construct an empty party."""
        self.members: list[PartyMember] = []
        self.inventory: dict[str, int] = {}
        self.gold: int = 0
        self.flags: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # ROSTER
    # ------------------------------------------------------------------

    def add(self, member: PartyMember) -> None:
        """Append ``member`` to the roster if not already present."""
        if any(m.id == member.id for m in self.members):
            return
        self.members.append(member)

    def remove(self, member_id: str) -> None:
        """Remove the member with ``member_id`` if present."""
        self.members = [m for m in self.members if m.id != member_id]

    def find(self, member_id: str) -> PartyMember | None:
        """Return the member with ``member_id`` or None if absent."""
        for m in self.members:
            if m.id == member_id:
                return m
        return None

    # ------------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise the whole party to a JSON-safe dict."""
        return {
            "members": [m.to_dict() for m in self.members],
            "inventory": dict(self.inventory),
            "gold": self.gold,
            "flags": dict(self.flags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Party":
        """Reconstruct a ``Party`` from a dict produced by ``to_dict``."""
        party = cls()
        party.members = [PartyMember.from_dict(m) for m in data.get("members", [])]
        party.inventory = dict(data.get("inventory", {}))
        party.gold = int(data.get("gold", 0))
        party.flags = dict(data.get("flags", {}))
        return party
