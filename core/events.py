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
    """Emitted when a combatant declares an attack against a target."""

    attacker_id: str
    attacker_name: str
    target_id: str
    target_name: str
    element: Element


@dataclass(frozen=True)
class DamageEvent:
    """Emitted after damage is computed and applied."""

    target_id: str
    target_name: str
    amount: int
    element: Element
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
