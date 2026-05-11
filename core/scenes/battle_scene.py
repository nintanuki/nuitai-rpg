"""Battle scene — hosts a ``Battle`` and a ``BattleView``.

Layer 0 wires up the simulation -> view seam **and** the player's
command interface. The encounter is loaded from ``data/enemies/`` via
``core.factories`` so the JSON -> runtime path is demonstrated end to
end. The opponent is picked at random from a small pool until the
encounter-table system arrives in Layer 1.

Each frame:

* If the text box still has narration, confirm advances it.
* Otherwise, if the battle is awaiting a command from the active
  party member, the scene shows a four-option command panel on the
  left half of the bottom HUD (Attack / Defend / Ability / Item).
  Choosing Ability or Item swaps the panel for a submenu; choosing
  Attack, a damage / heal / buff ability, or a usable item enters a
  *target-selection* state with a blinking yellow cursor on the
  roster.
* Otherwise, ``battle.start_turn()`` is called to advance the queue;
  for enemies that resolves the action inline.

Menu sizing auto-shrinks per submenu: the panel prefers SIZE_BODY,
but if any label in the active menu would overflow the column width
at that size, the whole menu drops to SIZE_SMALL together so rows
stay aligned with each other. Ability rows are tinted by element via
``ColorSettings.ELEMENT_COLORS``.

The active actor's name is highlighted yellow in the roster so the
player always knows whose turn it is.
"""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Any

import pygame

from core.elements import Element
from core.events import BattleEndedEvent
from core.factories import (
    combatant_from_enemy_data,
    combatant_from_party_member,
)
from core.scene import Scene
from settings import BattleSettings, ColorSettings, FontSettings, ScreenSettings, UISettings
from systems.battle import Battle, Combatant
from ui import input_map, text_renderer
from ui.battle_view import BattleView
from ui.menu import Menu, MenuItem
from ui.text_box import TextBox
from utils.backgrounds import render_scene_background

if TYPE_CHECKING:
    from main import GameManager


_DEMO_ENEMY_IDS: tuple[str, ...] = (
    "shade",
    "manogata",
    "fire_elemental",
    "pohaku",
    "zealot",
    "palm_dryad",
)

_ROSTER_TOP_Y = 100
_ROSTER_ROW_HEIGHT = 28
_PARTY_X = 40
_ENEMY_X = ScreenSettings.WIDTH - 240
_TARGET_CURSOR_OFFSET = -24


def _build_party_combatants(
    party, characters: dict[str, dict[str, Any]]
) -> list[Combatant]:
    """Map party members to combatants, healing missing learnsets from content."""
    combatants: list[Combatant] = []
    for m in party.members:
        if not m.learnset:
            content = characters.get(m.id, {})
            m.learnset = list(content.get("learnset", []))
        combatants.append(combatant_from_party_member(m))
    return combatants


def _build_enemies(gm: "GameManager") -> list[Combatant]:
    """Load a random Layer-0 placeholder encounter from content data."""
    enemies = gm.data.load("enemies")
    available = [eid for eid in _DEMO_ENEMY_IDS if eid in enemies]
    if not available:
        return [
            Combatant(
                "shade", "Shade",
                hp=24, attack=6, element=Element.AKU, is_party=False,
            ),
        ]
    return [combatant_from_enemy_data(enemies[random.choice(available)])]


class BattleScene(Scene):
    """A turn-based encounter scene."""

    OPAQUE = True

    def __init__(self, gm: "GameManager") -> None:
        super().__init__(gm)
        self.abilities = self.gm.data.load("abilities")
        characters = self.gm.data.load("characters")
        # Potions are a Party-level resource that persists across
        # battles. Read the current count from ``Party.inventory``; if
        # the inventory entry is missing entirely (old save format,
        # never been to a battle), fall back to the new-game starter
        # count so the player isn't silently emptied out. Once a battle
        # runs and the survivor count is written back, the inventory
        # value is authoritative on every subsequent fight.
        starting_potions = gm.party.inventory.get(
            "potion", BattleSettings.STARTING_POTIONS
        )
        self.battle = Battle(
            party_combatants=_build_party_combatants(self.gm.party, characters),
            enemy_combatants=_build_enemies(self.gm),
            abilities=self.abilities,
            potions=starting_potions,
        )
        self.text_box = TextBox()
        self.view = BattleView(self.text_box)
        self._battle_finished = False
        self.command_menu = Menu(
            items=[
                MenuItem("Attack", self._on_attack),
                MenuItem("Defend", self._on_defend),
                MenuItem("Ability", self._on_open_abilities),
                MenuItem("Item", self._on_open_items),
            ],
        )
        self.ability_menu: Menu | None = None
        self.item_menu: Menu | None = None
        self._pending_command: dict[str, Any] | None = None
        self._target_pool: list[Combatant] = []
        self._target_cursor: int = 0

    # ------------------------------------------------------------------
    # COMMAND HANDLERS
    # ------------------------------------------------------------------

    def _on_attack(self) -> None:
        self._begin_targeting({"kind": "attack"}, pool="enemy")

    def _on_defend(self) -> None:
        self._dispatch(self.battle.submit_defend())

    def _on_open_abilities(self) -> None:
        actor = self.battle.current_actor
        if actor is None:
            return
        abilities = self.battle.abilities_for(actor)
        items: list[MenuItem] = []
        for a in abilities:
            element_id = a.get("element")
            color = (
                ColorSettings.ELEMENT_COLORS.get(element_id)
                if element_id else None
            )
            items.append(
                MenuItem(
                    a.get("name", a.get("id", "?")),
                    lambda ability_id=a["id"]: self._on_ability_chosen(ability_id),
                    color=color,
                )
            )
        if not items:
            return
        self.ability_menu = Menu(items=items, on_cancel=self._close_ability_menu)

    def _on_ability_chosen(self, ability_id: str) -> None:
        self.ability_menu = None
        ability = self.abilities.get(ability_id, {})
        kind = ability.get("kind", "damage")
        pool = "party" if kind in ("heal", "buff") else "enemy"
        self._begin_targeting(
            {"kind": "ability", "ability_id": ability_id},
            pool=pool,
        )

    def _close_ability_menu(self) -> None:
        self.ability_menu = None

    def _on_open_items(self) -> None:
        items: list[MenuItem] = []
        if self.battle.potions > 0:
            items.append(
                MenuItem(
                    f"Potion x{self.battle.potions}",
                    self._on_potion_chosen,
                )
            )
        if not items:
            return
        self.item_menu = Menu(items=items, on_cancel=self._close_item_menu)

    def _on_potion_chosen(self) -> None:
        self.item_menu = None
        self._begin_targeting({"kind": "potion"}, pool="party")

    def _close_item_menu(self) -> None:
        self.item_menu = None

    def _dispatch(self, events: list[Any]) -> None:
        for ev in events:
            self.view.consume(ev)
            if isinstance(ev, BattleEndedEvent):
                self._battle_finished = True
                self._sync_party_state_back()

    def _sync_party_state_back(self) -> None:
        """Write battle-mutated state back onto the persistent ``Party``.

        Called exactly once, the moment the battle emits its
        ``BattleEndedEvent``. Pushes each surviving party combatant's
        current HP back onto the matching ``PartyMember`` so damage
        carries into the overworld and into the next save. Also writes
        the surviving potion count back onto ``Party.inventory`` so
        consumables persist across battles instead of resetting every
        fight.
        """
        for combatant in self.battle.party:
            member = self.gm.party.find(combatant.id)
            if member is None:
                continue
            # Clamp to the member's max so a buggy heal-overflow
            # never widens the persistent ceiling silently.
            capped = max(0, min(combatant.hp, member.max_hp))
            member.current_hp = capped
        self.gm.party.inventory["potion"] = max(0, int(self.battle.potions))

    # ------------------------------------------------------------------
    # TARGETING
    # ------------------------------------------------------------------

    def _begin_targeting(self, pending: dict[str, Any], pool: str) -> None:
        if pool == "enemy":
            candidates = [c for c in self.battle.enemies if c.alive]
        else:
            candidates = [c for c in self.battle.party if c.alive]
        if not candidates:
            return
        self._pending_command = pending
        self._target_pool = candidates
        self._target_cursor = 0

    def _on_target_confirmed(self) -> None:
        if not self._pending_command or not self._target_pool:
            return
        target = self._target_pool[self._target_cursor]
        cmd = self._pending_command
        self._pending_command = None
        self._target_pool = []
        self._target_cursor = 0
        kind = cmd["kind"]
        if kind == "attack":
            self._dispatch(self.battle.submit_attack(target.id))
        elif kind == "ability":
            self._dispatch(
                self.battle.submit_ability(cmd["ability_id"], target.id)
            )
        elif kind == "potion":
            self._dispatch(self.battle.submit_potion(target.id))

    def _cancel_targeting(self) -> None:
        cmd = self._pending_command
        self._pending_command = None
        self._target_pool = []
        self._target_cursor = 0
        if cmd is None:
            return
        kind = cmd.get("kind")
        if kind == "ability":
            self._on_open_abilities()
        elif kind == "potion":
            self._on_open_items()

    def _move_target_cursor(self, direction: int) -> None:
        if not self._target_pool:
            return
        self._target_cursor = (
            self._target_cursor + direction
        ) % len(self._target_pool)

    # ------------------------------------------------------------------
    # INPUT / UPDATE
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.text_box.is_done():
            if input_map.is_confirm(event):
                self.text_box.advance()
            return
        if self._battle_finished:
            return
        if self._pending_command is not None:
            if input_map.is_cancel(event):
                self._cancel_targeting()
                self.gm.audio.play("menu_move")
            elif input_map.is_up(event):
                self._move_target_cursor(-1)
                self.gm.audio.play("menu_move")
            elif input_map.is_down(event):
                self._move_target_cursor(1)
                self.gm.audio.play("menu_move")
            elif input_map.is_confirm(event):
                self.gm.audio.play("menu_select")
                self._on_target_confirmed()
            return
        if input_map.is_cancel(event):
            if self.item_menu is not None:
                self.item_menu.cancel()
                self.gm.audio.play("menu_move")
            elif self.ability_menu is not None:
                self.ability_menu.cancel()
                self.gm.audio.play("menu_move")
            else:
                self._dispatch(self.battle.flee())
            return
        if not self.battle.is_awaiting_command():
            return
        active_menu = self.item_menu or self.ability_menu or self.command_menu
        if input_map.is_up(event):
            if active_menu.move_up():
                self.gm.audio.play("menu_move")
        elif input_map.is_down(event):
            if active_menu.move_down():
                self.gm.audio.play("menu_move")
        elif input_map.is_confirm(event):
            if active_menu.confirm():
                self.gm.audio.play("menu_select")

    def update(self, dt: float) -> None:
        self.text_box.update(dt)
        if (
            not self._battle_finished
            and self.text_box.is_done()
            and not self.battle.is_over
            and not self.battle.is_awaiting_command()
        ):
            self._dispatch(self.battle.start_turn())
        if self._battle_finished and self.text_box.is_done():
            self.gm.scene_stack.pop()

    # ------------------------------------------------------------------
    # RENDER
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        render_scene_background(self, surface)
        text_renderer.draw_text(
            surface,
            "Battle",
            (40, 40),
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_HEADING,
        )
        self._render_rosters(surface)
        if (
            not self._battle_finished
            and self.battle.is_awaiting_command()
            and self.text_box.is_done()
        ):
            self._render_command_panel(surface)
        else:
            self.text_box.render(surface)

    def _render_rosters(self, surface: pygame.Surface) -> None:
        active_id = (
            self.battle.current_actor.id
            if self.battle.current_actor is not None
            else None
        )
        cursor_visible = (
            int(time.monotonic() * UISettings.MENU_CURSOR_BLINK_HZ * 2) % 2 == 0
        )
        current_target = (
            self._target_pool[self._target_cursor]
            if self._pending_command is not None and self._target_pool
            else None
        )
        for index, c in enumerate(self.battle.party):
            self._render_roster_line(
                surface, c, _PARTY_X, index, active_id,
                current_target, cursor_visible,
            )
        for index, c in enumerate(self.battle.enemies):
            self._render_roster_line(
                surface, c, _ENEMY_X, index, active_id,
                current_target, cursor_visible,
            )

    def _render_roster_line(
        self,
        surface: pygame.Surface,
        combatant: Combatant,
        x: int,
        index: int,
        active_id: str | None,
        target: Combatant | None,
        cursor_visible: bool,
    ) -> None:
        row_y = _ROSTER_TOP_Y + index * _ROSTER_ROW_HEIGHT
        color = (
            ColorSettings.YELLOW if combatant.id == active_id
            else ColorSettings.WHITE
        )
        if combatant is target and cursor_visible:
            text_renderer.draw_text(
                surface, ">", (x + _TARGET_CURSOR_OFFSET, row_y),
                color=ColorSettings.YELLOW,
            )
        text_renderer.draw_text(
            surface,
            f"{combatant.name}  {combatant.hp}/{combatant.max_hp}",
            (x, row_y),
            color=color,
        )

    def _render_command_panel(self, surface: pygame.Surface) -> None:
        host_h = surface.get_height()
        rect = pygame.Rect(
            0,
            host_h - UISettings.TEXT_BOX_HEIGHT,
            ScreenSettings.WIDTH,
            UISettings.TEXT_BOX_HEIGHT,
        )
        pygame.draw.rect(surface, ColorSettings.BLACK, rect)
        pygame.draw.rect(
            surface, ColorSettings.WHITE, rect,
            UISettings.TEXT_BOX_BORDER_THICKNESS,
        )
        divider_x = rect.left + UISettings.COMMAND_PANEL_WIDTH
        pygame.draw.line(
            surface, ColorSettings.WHITE,
            (divider_x, rect.top), (divider_x, rect.bottom),
            UISettings.TEXT_BOX_BORDER_THICKNESS,
        )

        pad = UISettings.TEXT_BOX_PADDING
        self._refresh_command_labels()
        active_menu = self.item_menu or self.ability_menu or self.command_menu
        menu_anchor = (
            rect.left + pad + UISettings.MENU_LABEL_OFFSET,
            rect.top + pad,
        )
        # Auto-shrink: prefer SIZE_BODY; drop the whole menu to
        # SIZE_SMALL together if any label would overflow at the
        # larger size.
        label_max_width = (
            UISettings.COMMAND_PANEL_WIDTH - 2 * pad - UISettings.MENU_LABEL_OFFSET
        )
        font_size = self._fit_font_size(active_menu, label_max_width)
        active_menu.render(
            surface,
            menu_anchor,
            font_size=font_size,
            row_height=UISettings.COMMAND_MENU_ROW_HEIGHT,
        )

        prompt = self._command_prompt()
        if prompt:
            text_renderer.draw_text(
                surface,
                prompt,
                (divider_x + pad, rect.top + pad),
                color=ColorSettings.WHITE,
                size=FontSettings.SIZE_BODY,
                max_width=rect.right - divider_x - 2 * pad,
            )

    def _command_prompt(self) -> str:
        actor = self.battle.current_actor
        if self._pending_command is not None:
            return "Choose a target."
        if self.item_menu is not None:
            return "Choose an item."
        if self.ability_menu is not None:
            return "Choose an ability."
        if actor is not None:
            return f"What will {actor.name} do?"
        return ""

    def _refresh_command_labels(self) -> None:
        actor = self.battle.current_actor
        ability_item = self.command_menu.items[2]
        ability_item.enabled = bool(
            actor is not None and self.battle.abilities_for(actor)
        )
        item_item = self.command_menu.items[3]
        item_item.enabled = self.battle.potions > 0

    def _fit_font_size(self, menu: Menu, max_width: int) -> int:
        """Pick the largest ladder size whose labels all fit ``max_width``.

        The whole menu uses one size so the rows stay aligned with each
        other; the moment one label would overflow at the larger size,
        every row drops to the smaller size together. The size ladder
        is the Pixeled font's clean rungs (SIZE_BODY then SIZE_SMALL);
        intermediate sizes blur and are not used.
        """
        for size in (FontSettings.SIZE_BODY, FontSettings.SIZE_SMALL):
            font = text_renderer.get_font(size)
            if all(
                font.size(item.label.upper())[0] <= max_width
                for item in menu.items
            ):
                return size
        return FontSettings.SIZE_SMALL
