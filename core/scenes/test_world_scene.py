"""A single placeholder room — proves the engine seams hold together.

Layer 0's job is not to feel like a game; it is to demonstrate that
the title -> world -> battle -> save -> load round-trip works. This
scene presents a small command menu (TALK, FIGHT, SAVE, QUIT) and
hands off to the appropriate sub-scene. Layer 1 will replace it with
the real opening dungeon.

All flavor text here is intentionally barebones — placeholders for the
writer to overwrite.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from core import save
from core.events import DialogueLineEvent
from core.scene import Scene
from settings import ColorSettings, FontSettings, ScreenSettings
from systems.dialogue import DialogueRunner
from ui import input_map, text_renderer
from ui.menu import Menu, MenuItem
from ui.text_box import TextBox
from utils.backgrounds import render_scene_background

if TYPE_CHECKING:
    from main import GameManager


class TestWorldScene(Scene):
    """A one-room placeholder world for proving engine plumbing."""

    OPAQUE = True

    def __init__(self, gm: "GameManager") -> None:
        """Construct the test-world menu and dialogue box."""
        super().__init__(gm)
        self.menu = Menu(
            items=[
                MenuItem("Talk", self._talk),
                MenuItem("Fight", self._fight),
                MenuItem("Save", self._save),
                MenuItem("Quit to Title", self._quit_to_title),
            ],
        )
        self.text_box = TextBox()
        self._save_message_pending = False

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def _talk(self) -> None:
        """Run the placeholder dialogue tree through the text box.

        This wires the full content path: ``DataLoader`` reads the
        dialogue JSON, ``DialogueRunner`` walks the tree and emits
        ``DialogueLineEvent``s, and the text box consumes them. Layer 1
        replaces the tree id with whatever NPC the player interacted
        with.
        """
        tree = self.gm.data.load("dialogue").get("opening")
        if tree is None:
            # Barebones fallback if content is missing.
            self.text_box.push("There is no one here yet.")
            return
        runner = DialogueRunner(tree)
        while not runner.is_done:
            for event in runner.advance():
                if isinstance(event, DialogueLineEvent):
                    self.text_box.push(event.text, speaker=event.speaker)

    def _fight(self) -> None:
        """Push a battle scene on top of this one."""
        from core.scenes.battle_scene import BattleScene  # local: cycle.

        self.gm.scene_stack.push(BattleScene(self.gm))

    def _save(self) -> None:
        """Write the current party to slot 1."""
        save.save(1, {"party": self.gm.party.to_dict()})
        self._save_message_pending = True
        self.text_box.push("Saved.")

    def _quit_to_title(self) -> None:
        """Replace the stack with the title screen."""
        from core.scenes.title_scene import TitleScene  # local: cycle.

        self.gm.scene_stack.replace(TitleScene(self.gm))

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """If the text box has content, advance it; otherwise drive the menu."""
        if not self.text_box.is_done():
            if input_map.is_confirm(event):
                self.text_box.advance()
            return
        if input_map.is_up(event):
            self.menu.move_up()
        elif input_map.is_down(event):
            self.menu.move_down()
        elif input_map.is_confirm(event):
            self.menu.confirm()

    def update(self, dt: float) -> None:
        """Tick the typewriter effect."""
        self.text_box.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """Draw the room label, party roster, command menu, and text box."""
        render_scene_background(self, surface)
        text_renderer.draw_text(
            surface,
            "Test Room",
            (40, 40),
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_HEADING,
        )
        # Party roster on the right; serves as the "this layer is wired up"
        # smoke check for save/load.
        roster_x = ScreenSettings.WIDTH - 240
        text_renderer.draw_text(
            surface,
            "Party",
            (roster_x, 40),
            color=ColorSettings.WHITE,
            size=FontSettings.SIZE_BODY,
        )
        for index, member in enumerate(self.gm.party.members):
            text_renderer.draw_text(
                surface,
                member.name,
                (roster_x, 70 + index * 24),
                color=ColorSettings.WHITE,
            )
        # Command menu on the left.
        self.menu.render(surface, (60, 120))
        # Text box always last so it sits above the menu.
        self.text_box.render(surface)
