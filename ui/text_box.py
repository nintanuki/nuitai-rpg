"""Bordered JRPG-style dialogue box.

The text box hugs the bottom of its host surface, draws a bordered
panel, and reveals queued lines with a typewriter effect. Callers
``push`` lines (optionally with a speaker tag); pressing confirm
fast-forwards to the end of the current page or advances to the next
page. When the queue empties, ``is_done`` returns True and the host
scene can pop the box.

The text box does not own any input mapping itself — the host scene
calls ``advance()`` when its confirm button is pressed.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

import pygame

from settings import ColorSettings, FontSettings, ScreenSettings, UISettings
from ui import text_renderer


class TextBox:
    """A bordered dialogue panel with paginated typewriter text."""

    def __init__(
        self,
        width: int = ScreenSettings.WIDTH,
        height: int = UISettings.TEXT_BOX_HEIGHT,
    ) -> None:
        """Construct a text box sized for the bottom of a ``width`` x ``H`` screen.

        Args:
            width: Panel width in pixels (defaults to full screen width).
            height: Panel height in pixels.
        """
        self.width = width
        self.height = height
        self._queue: deque[tuple[Optional[str], str]] = deque()

        # Currently displayed line state.
        self._current_speaker: Optional[str] = None
        self._current_lines: list[str] = []  # already wrapped to box width.
        self._chars_revealed: float = 0.0
        self._total_chars: int = 0

    # ------------------------------------------------------------------
    # QUEUE
    # ------------------------------------------------------------------

    def push(self, text: str, speaker: Optional[str] = None) -> None:
        """Append a line to the queue.

        Args:
            text: The line to display. Wrapping happens lazily when the
                line becomes the current one.
            speaker: Optional speaker label rendered above the line.
        """
        self._queue.append((speaker, text))
        if not self._current_lines:
            self._pull_next()

    def clear(self) -> None:
        """Drop any queued and currently-displayed text."""
        self._queue.clear()
        self._current_lines = []
        self._current_speaker = None
        self._chars_revealed = 0.0
        self._total_chars = 0

    def is_done(self) -> bool:
        """Return True when nothing is queued and nothing is displayed."""
        return not self._current_lines and not self._queue

    def is_page_complete(self) -> bool:
        """Return True if the current page has fully revealed its text."""
        return self._chars_revealed >= self._total_chars

    # ------------------------------------------------------------------
    # INPUT
    # ------------------------------------------------------------------

    def advance(self) -> None:
        """Advance presentation: fast-forward, or move to the next line."""
        if not self._current_lines:
            return
        if not self.is_page_complete():
            self._chars_revealed = self._total_chars
            return
        self._pull_next()

    # ------------------------------------------------------------------
    # FRAME
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance the typewriter reveal by ``dt`` seconds.

        Args:
            dt: Frame time in seconds.
        """
        if not self._current_lines:
            return
        if self._chars_revealed < self._total_chars:
            self._chars_revealed += UISettings.TYPEWRITER_CHARS_PER_SECOND * dt
            if self._chars_revealed > self._total_chars:
                self._chars_revealed = float(self._total_chars)

    def render(self, surface: pygame.Surface) -> None:
        """Draw the panel and the currently-revealed text onto ``surface``."""
        if not self._current_lines:
            return

        host_h = surface.get_height()
        rect = pygame.Rect(0, host_h - self.height, self.width, self.height)
        pygame.draw.rect(surface, ColorSettings.BLACK, rect)
        pygame.draw.rect(
            surface,
            ColorSettings.WHITE,
            rect,
            UISettings.TEXT_BOX_BORDER_THICKNESS,
        )

        pad = UISettings.TEXT_BOX_PADDING
        x = rect.left + pad
        y = rect.top + pad

        if self._current_speaker:
            y += text_renderer.draw_text(
                surface,
                self._current_speaker,
                (x, y),
                color=ColorSettings.WHITE,
                size=FontSettings.SIZE_HEADING,
            )

        # Reveal characters across the wrapped lines in order.
        revealed = int(self._chars_revealed)
        font = text_renderer.get_font(FontSettings.SIZE_BODY)
        line_height = font.get_linesize() + 2
        consumed = 0
        for line in self._current_lines:
            if revealed <= consumed:
                break
            chunk = line[: max(0, revealed - consumed)]
            text_renderer.draw_text(
                surface,
                chunk,
                (x, y),
                color=ColorSettings.WHITE,
                size=FontSettings.SIZE_BODY,
            )
            y += line_height
            consumed += len(line)

    # ------------------------------------------------------------------
    # INTERNALS
    # ------------------------------------------------------------------

    def _pull_next(self) -> None:
        """Advance to the next queued line, wrapping it for the panel width."""
        if not self._queue:
            self._current_lines = []
            self._current_speaker = None
            self._chars_revealed = 0.0
            self._total_chars = 0
            return
        speaker, text = self._queue.popleft()
        body_font = text_renderer.get_font(FontSettings.SIZE_BODY)
        max_width = self.width - 2 * UISettings.TEXT_BOX_PADDING
        upper = text.upper()
        wrapped = text_renderer.wrap(upper, body_font, max_width)
        self._current_speaker = speaker
        self._current_lines = wrapped
        self._chars_revealed = 0.0
        self._total_chars = sum(len(line) for line in wrapped)
