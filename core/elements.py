"""The element system — single source of truth.

The world of Nuitai runs on six elements arranged in two interlocking
triangles, each with a clockwise "beats" relationship:

    Material triangle:  Ahi -> Lau -> Wai -> Ahi
    Spiritual triangle: Ra -> Aku -> Mana -> Ra

If A beats B, an A-aligned attack hits B for ``ADVANTAGE_MULTIPLIER``
damage and a B-aligned attack hits A for ``DISADVANTAGE_MULTIPLIER``.
Same-element and cross-triangle pairings are neutral
(``NEUTRAL_MULTIPLIER``). Per-combatant resistances or immunities to
specific elements (e.g. "this Aku enemy is immune to Aku status
effects") will be authored case-by-case in content data, not imposed
as a global rule here.

Element math only fires for attacks that *carry* an element. Basic
attacks from party members are non-elemental and bypass the table
entirely (see ``docs/ARCHITECTURE.md`` for the rules). Enemy basic
attacks currently keep their element until the upcoming
physical/special split lands.

Every other module that needs element math imports from this file.
Do not duplicate the table.
"""

from __future__ import annotations

from enum import Enum


class Element(Enum):
    """The six elements of Nuitai.

    Names use the in-world Polynesian-derived terms; English glosses are
    documentation-only and never shown to the player.
    """

    AHI = "ahi"     # Fire. Material.
    LAU = "lau"     # Nature / leaf. Material.
    WAI = "wai"     # Water. Material.
    RA = "ra"       # Light / sun. Spiritual.
    AKU = "aku"     # Shadow / decay. Spiritual.
    MANA = "mana"   # Spirit / breath. Spiritual.


# Damage multipliers. Living in this module means a designer tweaking
# combat feel changes one number, not five.
ADVANTAGE_MULTIPLIER = 2.0
DISADVANTAGE_MULTIPLIER = 0.5
NEUTRAL_MULTIPLIER = 1.0


# attacker -> defender it beats. Two closed triangles.
_BEATS: dict[Element, Element] = {
    Element.AHI: Element.LAU,
    Element.LAU: Element.WAI,
    Element.WAI: Element.AHI,
    Element.RA: Element.AKU,
    Element.AKU: Element.MANA,
    Element.MANA: Element.RA,
}


def beats(attacker: Element, defender: Element) -> bool:
    """Return True if ``attacker``'s element strongly beats ``defender``'s.

    Args:
        attacker: The element of the incoming attack.
        defender: The element of the receiving combatant.

    Returns:
        True for an advantageous matchup, False otherwise (including
        neutral matchups across triangles).
    """
    return _BEATS.get(attacker) is defender


def damage_multiplier(attacker: Element, defender: Element) -> float:
    """Return the damage scalar for an ``attacker`` element vs a ``defender``.

    Args:
        attacker: The element of the incoming attack.
        defender: The element of the receiving combatant.

    Returns:
        ``ADVANTAGE_MULTIPLIER`` if attacker beats defender,
        ``DISADVANTAGE_MULTIPLIER`` if defender beats attacker, otherwise
        ``NEUTRAL_MULTIPLIER`` (including same-element pairings).
    """
    if beats(attacker, defender):
        return ADVANTAGE_MULTIPLIER
    if beats(defender, attacker):
        return DISADVANTAGE_MULTIPLIER
    return NEUTRAL_MULTIPLIER
