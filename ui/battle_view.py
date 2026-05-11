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
    AbilityUsedEvent,
    AttackEvent,
    BattleEndedEvent,
    CombatantDefeatedEvent,
    DamageEvent,
    DefendEvent,
    HealEvent,
    PotionUsedEvent,
    StatusAppliedEvent,
    TurnStartEvent,
)
from ui.text_box import TextBox


class BattleView:
    """Push narration lines for battle events into a text box."""

    def __init__(self, text_box: TextBox) -> None:
        self.text_box = text_box

    def consume(self, event: object) -> None:
        """Phrase one battle event into the text box."""
        if isinstance(event, TurnStartEvent):
            self.text_box.push(f"{event.combatant_name}'s turn.")
        elif isinstance(event, AttackEvent):
            self.text_box.push(
                f"{event.attacker_name} attacks {event.target_name}."
            )
        elif isinstance(event, DamageEvent):
            # Multiplier 0.0 is the immunity sentinel — the strike
            # connected mechanically but did nothing.
            if event.multiplier == 0.0:
                self.text_box.push(
                    f"It had no effect on {event.target_name}!"
                )
                return
            self.text_box.push(
                f"{event.target_name} takes {event.amount} damage."
            )
            # Pokemon-style placeholder effectiveness dialogue. Non-
            # elemental hits (multiplier == 1.0) skip the tag entirely.
            if event.multiplier > 1.0:
                self.text_box.push("It's super effective!")
            elif event.multiplier < 1.0:
                self.text_box.push("It's not very effective...")
        elif isinstance(event, DefendEvent):
            self.text_box.push(f"{event.combatant_name} braces for the blow.")
        elif isinstance(event, AbilityUsedEvent):
            self.text_box.push(
                f"{event.user_name} uses {event.ability_name}!"
            )
        elif isinstance(event, HealEvent):
            self.text_box.push(
                f"{event.target_name} recovers {event.amount} HP."
            )
        elif isinstance(event, PotionUsedEvent):
            # Self-use vs giving the potion to another character — the
            # narration has to line up with who actually gets the HP
            # back on the accompanying HealEvent.
            if event.user_id == event.target_id:
                self.text_box.push(f"{event.user_name} drinks a potion.")
            else:
                self.text_box.push(
                    f"{event.user_name} gives {event.target_name} a potion."
                )
        elif isinstance(event, StatusAppliedEvent):
            # Aku immunity is the only status that actually fires
            # today; phrase it warmly so it reads as a blessing rather
            # than an affliction. Anything else still falls back to
            # the older afflict / shake-off pair.
            if event.status == "aku immune":
                if event.applied:
                    self.text_box.push(
                        f"{event.target_name} is wrapped in Shaka's Light."
                    )
                else:
                    self.text_box.push(
                        f"Shaka's Light fades from {event.target_name}."
                    )
            else:
                verb = "is afflicted by" if event.applied else "shakes off"
                self.text_box.push(
                    f"{event.target_name} {verb} {event.status}."
                )
        elif isinstance(event, CombatantDefeatedEvent):
            self.text_box.push(f"{event.combatant_name} falls.")
        elif isinstance(event, BattleEndedEvent):
            outcome = {
                "victory": "Victory.",
                "defeat": "Defeat.",
                "flee": "Escaped.",
            }.get(event.outcome, event.outcome)
            self.text_box.push(outcome)
