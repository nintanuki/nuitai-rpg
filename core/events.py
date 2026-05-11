"""Typed event records emitted by gameplay systems.

Gameplay systems (`systems/battle.py`, `systems/dialogue.py`, future world
events) **emit** these records. View modules (`ui/battle_view.py`,
`ui/text_box.py`, future overworld renderer) **consume** them. The
producer never knows which view, if any, is listening; the view never
calls back into the producer.

This separation is what allows the same gameplay engine to drive Layer
1's text-only presentation, Layer 3's Dragon-Quest-style sprites, and
Layer 5's full-art combat without rewrites.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.elements import Element


# ---------------------------------------------------------------------------
# BATTLE EVENTS
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TurnStartEvent:
    """Emitted at the top of a combatant's turn."""

    combatant_id: str
    combatant_name: str


@dataclass(frozen=True)
class AttackEvent:
    """Emitted when a combatant declares an attack against a target.

    ``element`` is ``None`` for non-elemental swings — party members'
    basic attacks always sit here. Abilities and (for now) enemy basic
    attacks carry the element they were authored with.
    """

    attacker_id: str
    attacker_name: str
    target_id: str
    target_name: str
    element: Element | None


@dataclass(frozen=True)
class DamageEvent:
    """Emitted after damage is computed and applied.

    ``element`` is ``None`` for non-elemental damage. ``multiplier`` is
    the element-matchup scalar applied (1.0 for non-elemental or
    cross-triangle) — views key the "super effective" / "not very
    effective" narration off of this number rather than recomputing
    matchups themselves.
    """

    target_id: str
    target_name: str
    amount: int
    element: Element | None
    multiplier: float  # 2.0 / 1.0 / 0.5 — lets views narrate effectiveness.


@dataclass(frozen=True)
class StatusAppliedEvent:
    """Emitted when a combatant gains or loses a status condition."""

    target_id: str
    target_name: str
    status: str
    applied: bool  # True = gained, False = removed.


@dataclass(frozen=True)
class CombatantDefeatedEvent:
    """Emitted when a combatant's HP drops to zero."""

    combatant_id: str
    combatant_name: str


@dataclass(frozen=True)
class DefendEvent:
    """Emitted when a combatant chooses to defend.

    Defending halves incoming damage until the combatant's next turn.
    The status itself lives on ``Combatant.is_defending``; this event is
    the narration hook.
    """

    combatant_id: str
    combatant_name: str


@dataclass(frozen=True)
class AbilityUsedEvent:
    """Emitted when a combatant invokes a named ability.

    Damage / heal numbers still ride on ``DamageEvent`` / ``HealEvent``;
    this event is the narration hook that names the move.
    """

    user_id: str
    user_name: str
    ability_id: str
    ability_name: str


@dataclass(frozen=True)
class HealEvent:
    """Emitted after HP is restored on a combatant."""

    target_id: str
    target_name: str
    amount: int


@dataclass(frozen=True)
class PotionUsedEvent:
    """Emitted when a party member spends a potion to heal.

    The accompanying ``HealEvent`` carries the actual HP restored.
    ``potions_remaining`` is included so the view can refresh its
    on-screen ``x{N}`` indicator from the same stream.
    """

    user_id: str
    user_name: str
    target_id: str
    target_name: str
    potions_remaining: int


@dataclass(frozen=True)
class BattleEndedEvent:
    """Emitted once the battle is fully resolved."""

    # "victory", "defeat", or "flee".
    outcome: str


# ---------------------------------------------------------------------------
# DIALOGUE / WORLD EVENTS
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DialogueLineEvent:
    """One line of dialogue ready to be displayed."""

    speaker: Optional[str]   # None = narrator / no speaker tag.
    text: str


@dataclass(frozen=True)
class DialogueEndedEvent:
    """Emitted when a dialogue tree finishes."""

    dialogue_id: str
