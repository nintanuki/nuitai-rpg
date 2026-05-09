"""Centralised text rendering.

One place in the codebase loads fonts, wraps text, and enforces the
ALL-CAPS in-game text rule. Gameplay code can hand any-case strings to
the renderer and trust that the player only ever sees them upper-cased.

The cache keys on (font path, point size) so callers can ask for the
same logical font-size repeatedly without paying the load cost.
"""

from __future__ import annotations

import pygame

from settings import ColorSettings, FontSettings


_FONT_CACHE: dict[tuple[str, int], pygame.font.Font] = {}


def get_font(size: int = FontSettings.SIZE_BODY) -> pygame.font.Font:
    """Return a cached pygame font at ``size`` points.

    Args:
        size: Point size; should come from ``FontSettings.SIZE_*``.

    Returns:
        The cached ``pygame.font.Font`` for that size.
    """
    key = (FontSettings.FONT, size)
    cached = _FONT_CACHE.get(key)
    if cached is None:
        cached = pygame.font.Font(FontSettings.FONT, size)
        _FONT_CACHE[key] = cached
    return cached


def wrap(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Greedy word-wrap ``text`` so each line fits within ``max_width`` pixels.

    Args:
        text: The text to wrap. May contain ``\\n`` for hard breaks.
        font: The font to measure with.
        max_width: The maximum allowed pixel width per line.

    Returns:
        A list of lines.
    """
    out: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            out.append("")
            continue
        words = paragraph.split(" ")
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    out.append(current)
                current = word
        if current:
            out.append(current)
    return out


def render_line(
    text: str,
    color: tuple[int, int, int] = ColorSettings.WHITE,
    size: int = FontSettings.SIZE_BODY,
) -> pygame.Surface:
    """Render one line of text to a fresh surface, ALL-CAPS enforced.

    Args:
        text: The text to render. Will be upper-cased.
        color: The text color.
        size: Point size; should come from ``FontSettings.SIZE_*``.

    Returns:
        A new surface containing the rendered glyphs.
    """
    font = get_font(size)
    return font.render(text.upper(), False, color)


def draw_text(
    surface: pygame.Surface,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int] = ColorSettings.WHITE,
    size: int = FontSettings.SIZE_BODY,
    max_width: int | None = None,
    line_spacing: int = 2,
) -> int:
    """Draw ``text`` onto ``surface``, wrapping if ``max_width`` is given.

    Args:
        surface: The surface to draw onto.
        text: The text to render. Will be upper-cased.
        position: Top-left in pixels.
        color: Text color.
        size: Point size.
        max_width: If set, word-wrap to this many pixels per line.
        line_spacing: Extra pixels between wrapped lines.

    Returns:
        The total height in pixels that was drawn (so callers can stack
        further content below it).
    """
    font = get_font(size)
    upper = text.upper()
    lines = wrap(upper, font, max_width) if max_width is not None else upper.split("\n")
    x, y = position
    line_height = font.get_linesize()
    drawn = 0
    for line in lines:
        rendered = font.render(line, False, color)
        surface.blit(rendered, (x, y + drawn))
        drawn += line_height + line_spacing
    return drawn
