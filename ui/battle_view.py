"""Translate battle events into text-box narration.

The battle simulation emits typed events (see ``core/events.py``); the
view subscribes to them and pushes phrased lines into a ``TextBox``.
This is the seam that lets the same battle logic drive a text-only
Layer 1 demo and a sprite-and-animation Layer 3 / 5 presentation.

Phrasing here is intentionally barebones; future passes will expand it
with proper VO-style writing per character and per element.
"""

from __future__ import annotations

from core.events import (
    AttackEvent,
    BattleEndedEvent,
    CombatantDefeatedEvent,
    DamageEvent,
    StatusAppliedEvent,
    TurnStartEvent,
)
from ui.text_box import TextBox


class BattleView:
    """Push narration lines for battle events into a text box."""

    def __init__(self, text_box: TextBox) -> None:
        """Bind the view to ``text_box``.

        Args:
            text_box: The text box to push lines into.
        """
        self.text_box = text_box

    def consume(self, event: object) -> None:
        """Phrase one battle event into the text box.

        Args:
            event: A record from ``core/events.py``. Unknown event types
                are ignored so producers can introduce new events
                without breaking older views.
        """
        if isinstance(event, TurnStartEvent):
            self.text_box.push(f"{event.combatant_name}'s turn.")
        elif isinstance(event, AttackEvent):
            self.text_box.push(
                f"{event.attacker_name} attacks {event.target_name}."
            )
        elif isinstance(event, DamageEvent):
            tag = ""
            if event.multiplier > 1.0:
                tag = " A telling blow!"
            elif event.multiplier < 1.0:
                tag = " It barely lands."
            self.text_box.push(
                f"{event.target_name} takes {event.amount} damage.{tag}"
            )
        elif isinstance(event, StatusAppliedEvent):
            verb = "is afflicted by" if event.applied else "shakes off"
            self.text_box.push(f"{event.target_name} {verb} {event.status}.")
        elif isinstance(event, CombatantDefeatedEvent):
            self.text_box.push(f"{event.combatant_name} falls.")
        elif isinstance(event, BattleEndedEvent):
            outcome = {
                "victory": "Victory.",
                "defeat": "Defeat.",
                "flee": "Escaped.",
            }.get(event.outcome, event.outcome)
            self.text_box.push(outcome)
