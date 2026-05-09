"""The scene system.

A ``Scene`` is one screenful of game state — title screen, overworld
room, battle, pause menu. Scenes are kept on a stack so transient
overlays (pause, dialogue, battle) can be pushed on top of the gameplay
beneath them and popped to return.

The top scene receives input and updates each frame. Rendering walks the
stack bottom-up so an overlay (e.g. a pause menu) draws on top of the
world it paused.

Persistence is built into the base class: every concrete scene
implements ``to_dict`` / ``from_dict`` so the save system can rebuild
the stack across sessions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import pygame

if TYPE_CHECKING:
    from main import GameManager


class Scene:
    """Abstract base for every screen in the game.

    Subclasses override the lifecycle hooks they need. Defaults are
    no-ops so a minimal scene only has to implement what it actually
    cares about.
    """

    # Scenes that don't pause the world below should set this False so
    # the renderer knows to draw the scene beneath them too. The base
    # default is True (an opaque scene) because most scenes own their
    # whole frame.
    OPAQUE: bool = True

    def __init__(self, gm: "GameManager") -> None:
        """Bind this scene to the running ``GameManager``.

        Args:
            gm: The host game manager. Scenes route audio, save, and
                cross-scene navigation through this reference.
        """
        self.gm = gm

    # ------------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        """Called when the scene becomes the top of the stack."""

    def on_exit(self) -> None:
        """Called when the scene leaves the stack (popped or replaced)."""

    # ------------------------------------------------------------------
    # INPUT / UPDATE / RENDER
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Receive one pygame event while this scene is on top."""

    def update(self, dt: float) -> None:
        """Advance scene logic by ``dt`` seconds.

        Args:
            dt: Elapsed wall time since the last frame, in seconds.
        """

    def render(self, surface: pygame.Surface) -> None:
        """Draw this scene onto ``surface``."""

    # ------------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise this scene's runtime state to a JSON-safe dict.

        Subclasses should call ``super().to_dict()`` and add their own
        keys. The default returns just the registry key so loaders can
        pick the right subclass.
        """
        return {"type": type(self).__name__}

    @classmethod
    def from_dict(cls, gm: "GameManager", data: dict[str, Any]) -> "Scene":
        """Rebuild a scene from a previously-saved dict."""
        return cls(gm)


class SceneStack:
    """Ordered stack of scenes. The top scene receives input and updates."""

    def __init__(self, gm: "GameManager") -> None:
        """Bind this stack to ``gm``; start empty.

        Args:
            gm: The host game manager passed to scenes that need it.
        """
        self.gm = gm
        self._stack: list[Scene] = []

    # ------------------------------------------------------------------
    # STACK OPERATIONS
    # ------------------------------------------------------------------

    @property
    def top(self) -> Optional[Scene]:
        """Return the topmost scene, or None if the stack is empty."""
        return self._stack[-1] if self._stack else None

    def push(self, scene: Scene) -> None:
        """Add ``scene`` to the top of the stack and notify it."""
        self._stack.append(scene)
        scene.on_enter()

    def pop(self) -> Optional[Scene]:
        """Remove and return the top scene; notify it of exit."""
        if not self._stack:
            return None
        scene = self._stack.pop()
        scene.on_exit()
        if self._stack:
            self._stack[-1].on_enter()
        return scene

    def replace(self, scene: Scene) -> None:
        """Pop the current top (if any) and push ``scene`` in its place."""
        if self._stack:
            top = self._stack.pop()
            top.on_exit()
        self._stack.append(scene)
        scene.on_enter()

    def clear(self) -> None:
        """Empty the stack, notifying each scene of exit (top first)."""
        while self._stack:
            self._stack.pop().on_exit()

    # ------------------------------------------------------------------
    # FRAME DISPATCH
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Forward ``event`` to the top scene if any."""
        if self._stack:
            self._stack[-1].handle_event(event)

    def update(self, dt: float) -> None:
        """Update the top scene if any."""
        if self._stack:
            self._stack[-1].update(dt)

    def render_all(self, surface: pygame.Surface) -> None:
        """Render the stack from the deepest opaque scene upward.

        A non-opaque overlay (e.g. a pause menu) leaves the world below
        it visible. We walk down until we find the deepest scene whose
        ``OPAQUE`` flag means everything below is hidden, then render
        from that scene up.
        """
        if not self._stack:
            return
        start = len(self._stack) - 1
        while start > 0 and not self._stack[start].OPAQUE:
            start -= 1
        for scene in self._stack[start:]:
            scene.render(surface)
