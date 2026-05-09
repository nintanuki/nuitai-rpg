"""Turn-based battle simulation. Pure data; emits events; never draws.

A ``Battle`` holds two lists of combatants (party and enemies) and a
turn order. Each call to ``step()`` advances one combatant's turn,
emits the resulting events, and returns them. The outer scene
dispatches those events to ``BattleView`` (or any other consumer).

This Layer-0 implementation is intentionally minimal: each turn picks
the first living opponent and attacks. Layer 1 will plug in command
selection, ability data, status effects, and boss scripting on top of
the same event stream.
"""

from __future__ import annotations

from typing import Any

from core.elements import Element, damage_multiplier
from core.events import (
    AttackEvent,
    BattleEndedEvent,
    CombatantDefeatedEvent,
    DamageEvent,
    TurnStartEvent,
)


class Combatant:
    """One participant in a battle."""

    def __init__(
        self,
        combatant_id: str,
        name: str,
        hp: int,
        attack: int,
        element: Element,
        is_party: bool,
    ) -> None:
        """Construct a combatant.

        Args:
            combatant_id: Stable id, e.g. a party member or enemy id.
            name: Display name.
            hp: Starting and max HP.
            attack: Base attack stat (multiplied by element matchup).
            element: The combatant's primary element.
            is_party: True for party members, False for enemies.
        """
        self.id = combatant_id
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.attack = attack
        self.element = element
        self.is_party = is_party

    @property
    def alive(self) -> bool:
        """Return True while HP is above zero."""
        return self.hp > 0


class Battle:
    """A turn-based encounter that emits events as it resolves."""

    def __init__(
        self,
        party_combatants: list[Combatant],
        enemy_combatants: list[Combatant],
    ) -> None:
        """Construct a battle from two combatant rosters.

        Args:
            party_combatants: The player's side.
            enemy_combatants: The opposing side.
        """
        self.party = party_combatants
        self.enemies = enemy_combatants
        self._order: list[Combatant] = self.party + self.enemies
        self._turn_index = 0
        self._ended = False
        self._outcome: str | None = None

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    @property
    def is_over(self) -> bool:
        """Return True once the battle has emitted its end event."""
        return self._ended

    @property
    def outcome(self) -> str | None:
        """Return ``"victory"``, ``"defeat"``, or None until the battle ends."""
        return self._outcome

    def step(self) -> list[Any]:
        """Resolve one turn and return the events it produced."""
        if self._ended:
            return []
        actor = self._next_actor()
        if actor is None:
            return self._end()

        events: list[Any] = [TurnStartEvent(actor.id, actor.name)]
        target = self._pick_target(actor)
        if target is None:
            return self._end()

        events.append(
            AttackEvent(actor.id, actor.name, target.id, target.name, actor.element)
        )
        multiplier = damage_multiplier(actor.element, target.element)
        amount = max(1, int(actor.attack * multiplier))
        target.hp = max(0, target.hp - amount)
        events.append(
            DamageEvent(target.id, target.name, amount, actor.element, multiplier)
        )
        if not target.alive:
            events.append(CombatantDefeatedEvent(target.id, target.name))

        # Check terminal state after this strike.
        if not any(c.alive for c in self.enemies):
            events.extend(self._end("victory"))
        elif not any(c.alive for c in self.party):
            events.extend(self._end("defeat"))
        return events

    def flee(self) -> list[Any]:
        """End the battle immediately with a flee outcome."""
        return self._end("flee")

    # ------------------------------------------------------------------
    # INTERNALS
    # ------------------------------------------------------------------

    def _next_actor(self) -> Combatant | None:
        """Return the next living combatant in turn order, advancing the index."""
        for _ in range(len(self._order)):
            actor = self._order[self._turn_index % len(self._order)]
            self._turn_index += 1
            if actor.alive:
                return actor
        return None

    def _pick_target(self, actor: Combatant) -> Combatant | None:
        """Pick the first living opponent for ``actor``."""
        pool = self.enemies if actor.is_party else self.party
        for c in pool:
            if c.alive:
                return c
        return None

    def _end(self, outcome: str | None = None) -> list[Any]:
        """Mark the battle ended and return a closing event list."""
        if self._ended:
            return []
        self._ended = True
        if outcome is None:
            outcome = "victory" if any(c.alive for c in self.party) else "defeat"
        self._outcome = outcome
        return [BattleEndedEvent(outcome)]
