"""Build runtime gameplay objects from JSON content data.

This module is the single seam between content packs (the JSON dicts
returned by ``core.data_loader.DataLoader``) and the runtime objects
the simulation operates on (``PartyMember``, ``Combatant``).

Every "load X from data" path in the engine should land here so the
JSON-to-runtime mapping is never duplicated across scenes. When a new
kind of content needs a runtime form, add a factory here rather than
constructing the object inline in a scene.
"""

from __future__ import annotations

from typing import Any

from core.elements import Element
from systems.battle import Combatant
from systems.party import PartyMember


def party_member_from_data(data: dict[str, Any]) -> PartyMember:
    """Construct a ``PartyMember`` from a character JSON dict.

    Args:
        data: A dict from ``data/characters/<id>.json`` with at least
            ``id``, ``name``, and a two-element ``elements`` list. The
            optional ``learnset`` array carries ability ids that the
            member knows; battle-time lookup happens through
            ``Battle.abilities_for``.

    Returns:
        A fresh ``PartyMember`` ready to be added to a ``Party``.
    """
    elements = data["elements"]
    return PartyMember(
        member_id=data["id"],
        name=data["name"],
        elements=(elements[0], elements[1]),
        stats=dict(data.get("stats", {})),
        learnset=list(data.get("learnset", [])),
    )


def combatant_from_party_member(member: PartyMember) -> Combatant:
    """Build the battle-time combatant for a party member.

    Args:
        member: The party member to drop into a battle.

    Returns:
        A ``Combatant`` whose element is the member's primary (first)
        element and whose learnset carries the member's ability ids.
        Layer 1 will extend this to honour an active stance.
    """
    primary = Element(member.elements[0])
    return Combatant(
        combatant_id=member.id,
        name=member.name,
        hp=member.stats.get("hp", 20),
        attack=member.stats.get("attack", 6),
        element=primary,
        is_party=True,
        learnset=list(member.learnset),
    )


def combatant_from_enemy_data(data: dict[str, Any]) -> Combatant:
    """Build a battle-time combatant from an enemy JSON dict.

    Args:
        data: A dict from ``data/enemies/<id>.json`` with at least
            ``id``, ``name``, ``element``, and ``stats``.

    Returns:
        A ``Combatant`` ready to drop into a ``Battle`` as an opponent.
    """
    stats = data.get("stats", {})
    return Combatant(
        combatant_id=data["id"],
        name=data["name"],
        hp=stats.get("hp", 20),
        attack=stats.get("attack", 6),
        element=Element(data["element"]),
        is_party=False,
    )
