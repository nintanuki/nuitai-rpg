"""Battle scene — hosts a ``Battle`` and a ``BattleView``.

Layer 0 wires up the simulation -> view seam **and** the player's
command interface. The encounter is loaded from ``data/enemies/`` via
``core.factories`` so the JSON -> runtime path is demonstrated end to
end.

Each frame:

* If the text box still has narration, confirm advances it.
* Otherwise, if the battle is awaiting a command from the active
  party member, the scene shows a four-option command panel on the
  left half of the bottom HUD (Attack / Defend / Ability / Potion).
  Choosing Attack, a damage / heal ability, or Potion enters a
  *target-selection* state — a blinking yellow cursor appears next
  to the candidate combatant on the roster, up / down cycle through
  valid targets, confirm submits the command, cancel returns to the
  previous menu. Defend skips targeting because it acts on the
  defender themselves.
* Otherwise, ``battle.start_turn()`` is called to advance the queue;
  for enemies that resolves the action inline.

The active actor's name is highlighted yellow in the roster so the
player always knows whose turn it is.
"""

from __future__ import annotations

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
from settings import ColorSettings, FontSettings, ScreenSettings, UISettings
from systems.battle import Battle, Combatant
from ui import input_map, text_renderer
from ui.battle_view import BattleView
from ui.menu import Menu, MenuItem
from ui.text_box import TextBox
from utils.backgrounds import render_scene_background

if TYPE_CHECKING:
    from main import GameManager


# Layer-0 default opponent id. Layer 1 will pick encounters from a
# dungeon's encounter table; this constant just keeps the test world
# fightable while the engine is the only thing being exercised.
_DEFAULT_ENEMY_ID = "shade"

# Pixel offsets for the party / enemy roster columns at the top of the
# battle HUD. Kept here (not in settings) because they describe the
# layout of one specific scene; the moment two scenes share them, they
# graduate to UISettings.
_ROSTER_TOP_Y = 100
_ROSTER_ROW_HEIGHT = 28
_PARTY_X = 40
_ENEMY_X = ScreenSettings.WIDTH - 240
# Horizontal offset of the blinking target cursor from a roster line's
# left edge. Negative so the cursor sits to the left of the name.
_TARGET_CURSOR_OFFSET = -24


def _build_party_combatants(party) -> list[Combatant]:
    """Map party members to combatants via the shared factory."""
    return [combatant_from_party_member(m) for m in party.members]


def _build_enemies(gm: "GameManager") -> list[Combatant]:
    """Load the Layer-0 placeholder encounter from content data."""
    enemies = gm.data.load("enemies")
    data = enemies.get(_DEFAULT_ENEMY_ID)
    if data is not None:
        return [combatant_from_enemy_data(data)]
    # Hard fallback so the engine still boots if content is missing.
    return [
        Combatant(
            _DEFAULT_ENEMY_ID, "Shade",
            hp=24, attack=6, element=Element.AKU, is_party=False,
        ),
    ]


class BattleScene(Scene):
    """A turn-based encounter scene."""

    OPAQUE = True

    def __init__(self, gm: "GameManager") -> None:
        """Build the battle and its presentation pipeline."""
        super().__init__(gm)
        self.abilities = self.gm.data.load("abilities")
        self.battle = Battle(
            party_combatants=_build_party_combatants(self.gm.party),
            enemy_combatants=_build_enemies(self.gm),
            abilities=self.abilities,
        )
        self.text_box = TextBox()
        self.view = BattleView(self.text_box)
        self._battle_finished = False
        # Top-level command menu — labels are rewritten each frame to
        # reflect the current potion count.
        self.command_menu = Menu(
            items=[
                MenuItem("Attack", self._on_attack),
                MenuItem("Defend", self._on_defend),
                MenuItem("Ability", self._on_open_abilities),
                MenuItem("Potion", self._on_potion),
            ],
        )
        # Ability submenu — rebuilt every time it opens so the rows
        # match the active actor's learnset.
        self.ability_menu: Menu | None = None
        # Target-selection state. ``_pending_command`` describes what
        # the player chose ("attack" / "ability" / "potion" plus an
        # optional ability id); ``_target_pool`` lists the candidate
        # combatants; ``_target_cursor`` indexes the currently
        # highlighted one. All three are None / empty when the scene
        # is not in targeting mode.
        self._pending_command: dict[str, Any] | None = None
        self._target_pool: list[Combatant] = []
        self._target_cursor: int = 0

    # ------------------------------------------------------------------
    # COMMAND HANDLERS
    # ------------------------------------------------------------------

    def _on_attack(self) -> None:
        """Top-level Attack — pick a target enemy before resolving."""
        self._begin_targeting({"kind": "attack"}, pool="enemy")

    def _on_defend(self) -> None:
        """Submit defend immediately — defend acts on the actor itself."""
        self._dispatch(self.battle.submit_defend())

    def _on_open_abilities(self) -> None:
        """Replace the command panel with the active actor's ability list."""
        actor = self.battle.current_actor
        if actor is None:
            return
        abilities = self.battle.abilities_for(actor)
        items = [
            MenuItem(
                a.get("name", a.get("id", "?")),
                lambda ability_id=a["id"]: self._on_ability_chosen(ability_id),
            )
            for a in abilities
        ]
        if not items:
            # Nothing to pick; silently keep the top-level menu open.
            return
        self.ability_menu = Menu(items=items, on_cancel=self._close_ability_menu)

    def _on_ability_chosen(self, ability_id: str) -> None:
        """Close the ability submenu and step into target selection."""
        self.ability_menu = None
        ability = self.abilities.get(ability_id, {})
        pool = "party" if ability.get("kind") == "heal" else "enemy"
        self._begin_targeting(
            {"kind": "ability", "ability_id": ability_id},
            pool=pool,
        )

    def _close_ability_menu(self) -> None:
        """Drop back to the top-level command menu without spending a turn."""
        self.ability_menu = None

    def _on_potion(self) -> None:
        """Spend a potion if any remain; pick the recipient first."""
        if self.battle.potions <= 0:
            return
        self._begin_targeting({"kind": "potion"}, pool="party")

    def _dispatch(self, events: list[Any]) -> None:
        """Feed a turn's events into the view and capture battle-end flags."""
        for ev in events:
            self.view.consume(ev)
            if isinstance(ev, BattleEndedEvent):
                self._battle_finished = True

    # ------------------------------------------------------------------
    # TARGETING
    # ------------------------------------------------------------------

    def _begin_targeting(self, pending: dict[str, Any], pool: str) -> None:
        """Enter target-selection mode for ``pending``.

        Args:
            pending: Description of the command awaiting a target. Must
                include a ``kind`` of ``"attack"``, ``"ability"``, or
                ``"potion"``; ability commands also carry
                ``ability_id``.
            pool: ``"enemy"`` to pick from the living enemy roster,
                ``"party"`` for living party members.
        """
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
        """Submit the pending command against the highlighted target."""
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
        """Drop targeting state and return to the menu the player came from."""
        cmd = self._pending_command
        self._pending_command = None
        self._target_pool = []
        self._target_cursor = 0
        # Ability targeting was reached through the ability submenu —
        # rebuild that submenu so cancel feels like back-one-step.
        if cmd is not None and cmd.get("kind") == "ability":
            self._on_open_abilities()

    def _move_target_cursor(self, direction: int) -> None:
        """Cycle the targeting cursor through the candidate pool."""
        if not self._target_pool:
            return
        self._target_cursor = (
            self._target_cursor + direction
        ) % len(self._target_pool)

    # ------------------------------------------------------------------
    # INPUT / UPDATE
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route input through the appropriate layer for the current state."""
        # While narration is draining, confirm fast-forwards it; that
        # takes priority over menu input so the player always sees the
        # last line of feedback.
        if not self.text_box.is_done():
            if input_map.is_confirm(event):
                self.text_box.advance()
            return
        if self._battle_finished:
            return
        # Target-selection state takes precedence over the menus.
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
        # Cancel during a player turn either closes the ability submenu
        # or attempts to flee from the top-level menu.
        if input_map.is_cancel(event):
            if self.ability_menu is not None:
                self.ability_menu.cancel()
                self.gm.audio.play("menu_move")
            else:
                self._dispatch(self.battle.flee())
            return
        if not self.battle.is_awaiting_command():
            return
        active_menu = self.ability_menu or self.command_menu
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
        """Advance narration, then advance the queue when text drains."""
        self.text_box.update(dt)
        if (
            not self._battle_finished
            and self.text_box.is_done()
            and not self.battle.is_over
            and not self.battle.is_awaiting_command()
        ):
            self._dispatch(self.battle.start_turn())
        # When the battle is over and all narration has drained, return
        # to the world.
        if self._battle_finished and self.text_box.is_done():
            self.gm.scene_stack.pop()

    # ------------------------------------------------------------------
    # RENDER
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        """Draw the battle HUD plus either the command panel or the text box."""
        render_scene_background(self, surface)
        text_renderer.draw_text(
            surface,
            "Battle",
            (40, 40),
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_HEADING,
        )

        self._render_rosters(surface)

        # The command panel and the text box never coexist visually:
        # the panel only shows while a party turn is waiting on input
        # and no narration is left to read; otherwise the dialogue
        # spans the whole bottom bar.
        if (
            not self._battle_finished
            and self.battle.is_awaiting_command()
            and self.text_box.is_done()
        ):
            self._render_command_panel(surface)
        else:
            self.text_box.render(surface)

    def _render_rosters(self, surface: pygame.Surface) -> None:
        """Draw party + enemy HP columns and any active-turn / target cursors."""
        active_id = (
            self.battle.current_actor.id
            if self.battle.current_actor is not None
            else None
        )
        # The blinking target cursor reuses the menu cursor's cadence
        # so the two reads as one visual language.
        target_cursor_visible = (
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
                current_target, target_cursor_visible,
            )
        for index, c in enumerate(self.battle.enemies):
            self._render_roster_line(
                surface, c, _ENEMY_X, index, active_id,
                current_target, target_cursor_visible,
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
        """Draw one roster line plus any cursors that point at it."""
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
        """Draw the split command-and-prompt bar at the bottom of the screen."""
        host_h = surface.get_height()
        rect = pygame.Rect(
            0,
            host_h - UISettings.TEXT_BOX_HEIGHT,
            ScreenSettings.WIDTH,
            UISettings.TEXT_BOX_HEIGHT,
        )
        pygame.draw.rect(surface, ColorSettings.BLACK, rect)
        pygame.draw.rect(
            surface,
            ColorSettings.WHITE,
            rect,
            UISettings.TEXT_BOX_BORDER_THICKNESS,
        )
        # Vertical divider between command list (left) and prompt (right).
        divider_x = rect.left + UISettings.COMMAND_PANEL_WIDTH
        pygame.draw.line(
            surface,
            ColorSettings.WHITE,
            (divider_x, rect.top),
            (divider_x, rect.bottom),
            UISettings.TEXT_BOX_BORDER_THICKNESS,
        )

        pad = UISettings.TEXT_BOX_PADDING
        # Refresh the potion label every frame so the x{N} indicator
        # stays in sync with the shared pool as it drains.
        self._refresh_command_labels()
        active_menu = self.ability_menu or self.command_menu
        menu_anchor = (
            rect.left + pad + UISettings.MENU_LABEL_OFFSET,
            rect.top + pad,
        )
        # SIZE_SMALL + tight spacing so all four commands fit inside
        # the bottom HUD without enlarging the panel.
        active_menu.render(
            surface,
            menu_anchor,
            item_spacing=UISettings.COMMAND_MENU_ITEM_SPACING,
            font_size=FontSettings.SIZE_SMALL,
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
        """Return the right-side prompt that matches the current state."""
        actor = self.battle.current_actor
        if self._pending_command is not None:
            return "Choose a target."
        if self.ability_menu is not None:
            return "Choose an ability."
        if actor is not None:
            return f"What will {actor.name} do?"
        return ""

    def _refresh_command_labels(self) -> None:
        """Update mutable command rows (potion count, disabled states)."""
        # The four rows are constructed in a fixed order in __init__:
        # 0 Attack, 1 Defend, 2 Ability, 3 Potion.
        potion_item = self.command_menu.items[3]
        potion_item.label = f"Potion x{self.battle.potions}"
        potion_item.enabled = self.battle.potions > 0
        actor = self.battle.current_actor
        ability_item = self.command_menu.items[2]
        ability_item.enabled = bool(
            actor is not None and self.battle.abilities_for(actor)
        )
