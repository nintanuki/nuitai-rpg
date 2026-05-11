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

Aku-immunity (granted by abilities like Shaka's Light) is a per-
combatant turn counter that drops by one at the top of the holder's
own turn and is consumed against any incoming Aku-element strike.
While active, Aku damage on the holder is fully nullified — the strike
still emits a DamageEvent so the view can narrate the no-effect line,
but the multiplier is zero and HP is unchanged.
"""

from __future__ import annotations

from typing import Any

from core.elements import Element, NEUTRAL_MULTIPLIER, damage_multiplier
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
        # Remaining turns of Aku immunity (granted by Shaka's Light).
        # Decrements at the top of this combatant's own turn; an
        # incoming Aku-element strike is fully nullified while the
        # counter is positive.
        self.aku_immune_turns = 0

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
        """Construct a battle from two combatant rosters."""
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
        self._current_actor: Combatant | None = None
        self._awaiting_command = False

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    @property
    def is_over(self) -> bool:
        return self._ended

    @property
    def outcome(self) -> str | None:
        return self._outcome

    @property
    def current_actor(self) -> Combatant | None:
        return self._current_actor

    def is_awaiting_command(self) -> bool:
        return self._awaiting_command

    def abilities_for(self, combatant: Combatant) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for ability_id in combatant.learnset:
            entry = self._abilities.get(ability_id)
            if entry is not None:
                out.append(entry)
        return out

    def start_turn(self) -> list[Any]:
        """Advance to the next living combatant's turn."""
        if self._ended or self._awaiting_command:
            return []
        actor = self._next_actor()
        if actor is None:
            return self._end()
        self._current_actor = actor
        actor.is_defending = False
        events: list[Any] = [TurnStartEvent(actor.id, actor.name)]
        # Tick down Aku immunity at the start of the holder's own
        # turn; emit a "wears off" StatusAppliedEvent when it drops
        # to zero so the view can narrate the fade.
        if actor.aku_immune_turns > 0:
            actor.aku_immune_turns -= 1
            if actor.aku_immune_turns == 0:
                events.append(
                    StatusAppliedEvent(actor.id, actor.name, "aku immune", False)
                )
        if actor.is_party:
            self._awaiting_command = True
            return events
        # Enemy auto-resolution. Enemy basic attacks keep their
        # element until the upcoming physical/special split lands.
        target = self._pick_target(actor)
        if target is None:
            events.extend(self._end())
            return events
        events.extend(self._resolve_attack(actor, target, actor.element, actor.attack))
        events.extend(self._check_terminal())
        return events

    def submit_attack(self, target_id: str | None = None) -> list[Any]:
        """Resolve the awaiting party member's basic attack.

        Basic attacks have no elemental affinity — the element table is
        bypassed and the swing always lands at NEUTRAL_MULTIPLIER.
        Layer 1+ will introduce augments (Ahi / Mana only) that imbue
        a basic attack with an element.
        """
        actor = self._require_player_actor()
        target = self._find_enemy(target_id) or self._pick_target(actor)
        if target is None:
            return self._finish_player_turn([])
        events = self._resolve_attack(actor, target, None, actor.attack)
        return self._finish_player_turn(events)

    def submit_defend(self) -> list[Any]:
        actor = self._require_player_actor()
        actor.is_defending = True
        return self._finish_player_turn([DefendEvent(actor.id, actor.name)])

    def submit_ability(
        self,
        ability_id: str,
        target_id: str | None = None,
    ) -> list[Any]:
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
        elif kind == "buff":
            target = self._find_party_member(target_id) or actor
            status = ability.get("status")
            duration = int(ability.get("duration", 0))
            if status == "aku_immune":
                target.aku_immune_turns = duration
                events.append(
                    StatusAppliedEvent(target.id, target.name, "aku immune", True)
                )
        else:  # damage (default)
            target = self._find_enemy(target_id) or self._pick_target(actor)
            if target is not None:
                events.extend(
                    self._resolve_attack(actor, target, element, actor.attack)
                )
        return self._finish_player_turn(events)

    def submit_potion(self, target_id: str | None = None) -> list[Any]:
        actor = self._require_player_actor()
        if self.potions <= 0:
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
        return self._end("flee")

    # ------------------------------------------------------------------
    # INTERNALS
    # ------------------------------------------------------------------

    def _next_actor(self) -> Combatant | None:
        for _ in range(len(self._order)):
            actor = self._order[self._turn_index % len(self._order)]
            self._turn_index += 1
            if actor.alive:
                return actor
        return None

    def _pick_target(self, actor: Combatant) -> Combatant | None:
        pool = self.enemies if actor.is_party else self.party
        for c in pool:
            if c.alive:
                return c
        return None

    def _find_enemy(self, target_id: str | None) -> Combatant | None:
        if not target_id:
            return None
        for c in self.enemies:
            if c.id == target_id and c.alive:
                return c
        return None

    def _find_party_member(self, target_id: str | None) -> Combatant | None:
        if not target_id:
            return None
        for c in self.party:
            if c.id == target_id:
                return c
        return None

    def _ability_element(
        self, ability: dict[str, Any], actor: Combatant
    ) -> Element:
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
        element: Element | None,
        power: int,
    ) -> list[Any]:
        """Produce events for one strike and apply HP changes.

        ``element`` is ``None`` for non-elemental swings (party basic
        attacks). The element table is consulted only when an element
        is present; otherwise the multiplier stays at NEUTRAL_MULTIPLIER.

        If the target carries an active Aku-immunity counter and the
        incoming element is Aku, the strike is fully nullified — a
        DamageEvent with amount=0 and multiplier=0 is emitted so the
        view can narrate the no-effect line.
        """
        events: list[Any] = [
            AttackEvent(actor.id, actor.name, target.id, target.name, element)
        ]
        if element is Element.AKU and target.aku_immune_turns > 0:
            events.append(DamageEvent(target.id, target.name, 0, element, 0.0))
            return events
        multiplier = (
            damage_multiplier(element, target.element)
            if element is not None
            else NEUTRAL_MULTIPLIER
        )
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
        before = target.hp
        target.hp = min(target.max_hp, target.hp + max(0, amount))
        return target.hp - before

    def _require_player_actor(self) -> Combatant:
        if not self._awaiting_command or self._current_actor is None:
            raise RuntimeError("No party command is awaiting input")
        return self._current_actor

    def _finish_player_turn(self, events: list[Any]) -> list[Any]:
        self._awaiting_command = False
        events.extend(self._check_terminal())
        return events

    def _check_terminal(self) -> list[Any]:
        if not any(c.alive for c in self.enemies):
            return self._end("victory")
        if not any(c.alive for c in self.party):
            return self._end("defeat")
        return []

    def _end(self, outcome: str | None = None) -> list[Any]:
        if self._ended:
            return []
        self._ended = True
        if outcome is None:
            outcome = "victory" if any(c.alive for c in self.party) else "defeat"
        self._outcome = outcome
        return [BattleEndedEvent(outcome)]
