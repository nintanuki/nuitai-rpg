"""Turn-based battle simulation. Pure data; emits events; never draws.

A ``Battle`` holds two lists of combatants (party and enemies) and a
turn order. The scene drives the battle in two beats:

1. ``start_turn()`` advances to the next living combatant, emits a
   ``TurnStartEvent``, and — if the actor is an enemy — resolves the
   enemy's action inline. If the actor is a party member, the battle
   parks itself in *awaiting-command* mode (``is_awaiting_command()``)
   until the scene calls one of the ``submit_*`` methods.
2. ``submit_attack`` / ``submit_defend`` / ``submit_ability`` /
   ``submit_potion`` resolve the player's choice for the actor whose
   turn it is and return the resulting events.

Turn order is the dead-simple Layer-0 sequence ``party + enemies``,
rotated once per round. The eventual destination is an FFX-style
**Conditional Turn-Based** queue driven by per-combatant speed stats
and weighted by action cost; the command interface above is shaped so
that swap is internal to this module — scenes and views read the same
``current_actor`` / ``TurnStartEvent`` regardless of which scheduler
sits underneath.

Defending halves incoming damage (see ``BattleSettings``) until the
defender's *next* turn comes around; the flag clears at the top of
that turn so the buff is exactly one round long.
"""

from __future__ import annotations

from typing import Any

from core.elements import Element, damage_multiplier
from core.events import (
    AbilityUsedEvent,
    AttackEvent,
    BattleEndedEvent,
    CombatantDefeatedEvent,
    DamageEvent,
    DefendEvent,
    HealEvent,
    PotionUsedEvent,
    TurnStartEvent,
)
from settings import BattleSettings


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
        learnset: list[str] | None = None,
    ) -> None:
        """Construct a combatant.

        Args:
            combatant_id: Stable id, e.g. a party member or enemy id.
            name: Display name.
            hp: Starting and max HP.
            attack: Base attack stat (multiplied by element matchup).
            element: The combatant's primary element.
            is_party: True for party members, False for enemies.
            learnset: Optional list of ability ids this combatant
                knows. Resolved at command time through the battle's
                ability content pack.
        """
        self.id = combatant_id
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.attack = attack
        self.element = element
        self.is_party = is_party
        self.learnset = list(learnset) if learnset else []
        # Set by ``submit_defend``; cleared at the top of this
        # combatant's next ``start_turn``. While True, incoming damage
        # is divided by ``BattleSettings.DEFEND_DAMAGE_DIVISOR``.
        self.is_defending = False

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
        abilities: dict[str, dict[str, Any]] | None = None,
        potions: int | None = None,
    ) -> None:
        """Construct a battle from two combatant rosters.

        Args:
            party_combatants: The player's side.
            enemy_combatants: The opposing side.
            abilities: Ability data keyed by id, as produced by
                ``DataLoader.load("abilities")``. Each entry is a dict
                with at least ``name``, ``element``, ``kind``
                (``"damage"`` or ``"heal"``), and ``power``; ``target``
                is optional and currently honoured for healing only.
            potions: Starting potion count for the party's shared pool.
                Defaults to ``BattleSettings.STARTING_POTIONS``.
        """
        self.party = party_combatants
        self.enemies = enemy_combatants
        self._abilities = dict(abilities or {})
        self.potions = (
            BattleSettings.STARTING_POTIONS if potions is None else potions
        )
        self._order: list[Combatant] = self.party + self.enemies
        self._turn_index = 0
        self._ended = False
        self._outcome: str | None = None
        # The actor whose turn is currently active. Set by
        # ``start_turn`` and replaced on the next ``start_turn`` rather
        # than cleared, so views can keep highlighting the actor while
        # their resolution narration is still draining.
        self._current_actor: Combatant | None = None
        # True between a party member's ``TurnStartEvent`` and the
        # matching ``submit_*`` call. While True, ``start_turn`` is a
        # no-op so the scene can wait on player input.
        self._awaiting_command = False

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

    @property
    def current_actor(self) -> Combatant | None:
        """Return the combatant whose turn is active, if any."""
        return self._current_actor

    def is_awaiting_command(self) -> bool:
        """Return True while a party member's turn is waiting on input."""
        return self._awaiting_command

    def abilities_for(self, combatant: Combatant) -> list[dict[str, Any]]:
        """Return ability dicts available to ``combatant``.

        Looks up each id in the combatant's learnset against the
        ability content pack passed at construction. Missing ability
        ids are silently skipped so a content typo never crashes the
        scene mid-fight.
        """
        out: list[dict[str, Any]] = []
        for ability_id in combatant.learnset:
            entry = self._abilities.get(ability_id)
            if entry is not None:
                out.append(entry)
        return out

    def start_turn(self) -> list[Any]:
        """Advance to the next living combatant's turn.

        Returns:
            The events produced by this turn. For an enemy actor this
            includes the full resolution (``TurnStartEvent``,
            ``AttackEvent``, ``DamageEvent``, optional
            ``CombatantDefeatedEvent``, and a terminal
            ``BattleEndedEvent`` if the battle just ended). For a
            party actor this is just ``TurnStartEvent`` and the battle
            is parked in awaiting-command mode until a ``submit_*``
            call resolves it.
        """
        if self._ended or self._awaiting_command:
            return []
        actor = self._next_actor()
        if actor is None:
            return self._end()
        self._current_actor = actor
        # Defend lasts exactly one round; clear it at the top of the
        # defender's next turn so the buff window matches a JRPG's
        # standard expectation.
        actor.is_defending = False
        events: list[Any] = [TurnStartEvent(actor.id, actor.name)]
        if actor.is_party:
            self._awaiting_command = True
            return events
        # Enemy auto-resolution: Layer 0's enemies pick the first
        # living party member and swing. Layer 1's bestiary will read
        # action tables from JSON; the seam is right here.
        target = self._pick_target(actor)
        if target is None:
            events.extend(self._end())
            return events
        events.extend(self._resolve_attack(actor, target, actor.element, actor.attack))
        events.extend(self._check_terminal())
        return events

    def submit_attack(self, target_id: str | None = None) -> list[Any]:
        """Resolve the awaiting party member's basic attack.

        Args:
            target_id: Optional enemy id; defaults to the first living
                enemy.
        """
        actor = self._require_player_actor()
        target = self._find_enemy(target_id) or self._pick_target(actor)
        if target is None:
            return self._finish_player_turn([])
        events = self._resolve_attack(actor, target, actor.element, actor.attack)
        return self._finish_player_turn(events)

    def submit_defend(self) -> list[Any]:
        """Set the awaiting actor's defending flag and end their turn."""
        actor = self._require_player_actor()
        actor.is_defending = True
        return self._finish_player_turn([DefendEvent(actor.id, actor.name)])

    def submit_ability(
        self,
        ability_id: str,
        target_id: str | None = None,
    ) -> list[Any]:
        """Resolve the awaiting actor's chosen ability.

        Args:
            ability_id: The ability's content id.
            target_id: Optional override for the heal target or
                damage target; falls back to the ability's ``target``
                field, then to a sane default.
        """
        actor = self._require_player_actor()
        ability = self._abilities.get(ability_id) or {}
        name = ability.get("name", ability_id)
        events: list[Any] = [AbilityUsedEvent(actor.id, actor.name, ability_id, name)]
        kind = ability.get("kind", "damage")
        element = self._ability_element(ability, actor)
        if kind == "heal":
            target = (
                self._find_party_member(target_id)
                or self._find_party_member(ability.get("target"))
                or actor
            )
            amount = int(ability.get("power", 0))
            healed = self._restore_hp(target, amount)
            events.append(HealEvent(target.id, target.name, healed))
        else:
            target = self._find_enemy(target_id) or self._pick_target(actor)
            if target is not None:
                events.extend(
                    self._resolve_attack(actor, target, element, actor.attack)
                )
        return self._finish_player_turn(events)

    def submit_potion(self, target_id: str | None = None) -> list[Any]:
        """Spend one potion from the shared pool to heal a party member.

        With no potions left, this is a no-op that keeps the actor in
        awaiting-command state so the player can choose a different
        action.
        """
        actor = self._require_player_actor()
        if self.potions <= 0:
            # Don't consume the turn — let the player pick again.
            return []
        self.potions -= 1
        target = self._find_party_member(target_id) or actor
        healed = self._restore_hp(target, BattleSettings.POTION_HEAL_AMOUNT)
        events: list[Any] = [
            PotionUsedEvent(actor.id, actor.name, target.id, target.name, self.potions),
            HealEvent(target.id, target.name, healed),
        ]
        return self._finish_player_turn(events)

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

    def _find_enemy(self, target_id: str | None) -> Combatant | None:
        """Return the living enemy whose id is ``target_id`` (or None)."""
        if not target_id:
            return None
        for c in self.enemies:
            if c.id == target_id and c.alive:
                return c
        return None

    def _find_party_member(self, target_id: str | None) -> Combatant | None:
        """Return the party member whose id is ``target_id`` (or None)."""
        if not target_id:
            return None
        for c in self.party:
            if c.id == target_id:
                return c
        return None

    def _ability_element(
        self, ability: dict[str, Any], actor: Combatant
    ) -> Element:
        """Resolve an ability's element id; fall back to the actor's element."""
        raw = ability.get("element")
        if not raw:
            return actor.element
        try:
            return Element(raw)
        except ValueError:
            return actor.element

    def _resolve_attack(
        self,
        actor: Combatant,
        target: Combatant,
        element: Element,
        power: int,
    ) -> list[Any]:
        """Produce events for one strike and apply HP changes."""
        events: list[Any] = [
            AttackEvent(actor.id, actor.name, target.id, target.name, element)
        ]
        multiplier = damage_multiplier(element, target.element)
        raw = max(1, int(power * multiplier))
        amount = (
            max(1, raw // BattleSettings.DEFEND_DAMAGE_DIVISOR)
            if target.is_defending
            else raw
        )
        target.hp = max(0, target.hp - amount)
        events.append(
            DamageEvent(target.id, target.name, amount, element, multiplier)
        )
        if not target.alive:
            events.append(CombatantDefeatedEvent(target.id, target.name))
        return events

    def _restore_hp(self, target: Combatant, amount: int) -> int:
        """Restore up to ``amount`` HP on ``target``; return the actual amount."""
        before = target.hp
        target.hp = min(target.max_hp, target.hp + max(0, amount))
        return target.hp - before

    def _require_player_actor(self) -> Combatant:
        """Return the current actor or raise if no command is awaited."""
        if not self._awaiting_command or self._current_actor is None:
            raise RuntimeError("No party command is awaiting input")
        return self._current_actor

    def _finish_player_turn(self, events: list[Any]) -> list[Any]:
        """Clear the awaiting flag and append any terminal events."""
        self._awaiting_command = False
        events.extend(self._check_terminal())
        return events

    def _check_terminal(self) -> list[Any]:
        """Return a ``BattleEndedEvent`` list if one side is fully down."""
        if not any(c.alive for c in self.enemies):
            return self._end("victory")
        if not any(c.alive for c in self.party):
            return self._end("defeat")
        return []

    def _end(self, outcome: str | None = None) -> list[Any]:
        """Mark the battle ended and return a closing event list."""
        if self._ended:
            return []
        self._ended = True
        if outcome is None:
            outcome = "victory" if any(c.alive for c in self.party) else "defeat"
        self._outcome = outcome
        return [BattleEndedEvent(outcome)]
