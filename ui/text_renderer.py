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
        text: The text to wrap. May contain ``\n`` for hard breaks.
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


def _render_glow(
    text: str,
    font: pygame.font.Font,
    fill: tuple[int, int, int],
    glow: tuple[int, int, int],
    radius: int,
    alpha: int,
) -> tuple[pygame.Surface, int]:
    """Render ``text`` in ``fill`` with a soft ``glow`` halo behind it.

    The halo is drawn by blitting the glow-colored text at every offset
    inside a filled circle of ``radius`` pixels with a single per-blit
    ``alpha`` so the offsets accumulate into a soft cloud rather than a
    hard edge. Returned alongside the surface is the pad amount, which
    callers use to offset the blit so the glyph's natural baseline still
    lands at the requested ``position`` (glow bleeds *outward* from the
    text and shouldn't shift layout).
    """
    body = font.render(text, False, fill)
    halo = font.render(text, False, glow)
    halo.set_alpha(alpha)
    w, h = body.get_size()
    pad = radius + 1
    surf = pygame.Surface((w + 2 * pad, h + 2 * pad), pygame.SRCALPHA)
    r_sq = radius * radius
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                continue
            # Drop the box corners so the halo reads round, not square.
            if dx * dx + dy * dy > r_sq:
                continue
            surf.blit(halo, (dx + pad, dy + pad))
    surf.blit(body, (pad, pad))
    return surf, pad


def render_line(
    text: str,
    color: tuple[int, int, int] = ColorSettings.WHITE,
    size: int = FontSettings.SIZE_BODY,
    glow: tuple[int, int, int] | None = None,
    glow_radius: int = 3,
    glow_alpha: int = 110,
) -> pygame.Surface:
    """Render one line of text to a fresh surface, ALL-CAPS enforced.

    Args:
        text: The text to render. Will be upper-cased.
        color: The text color (the sharp body of the glyph).
        size: Point size; should come from ``FontSettings.SIZE_*``.
        glow: Optional halo color. When set, the returned surface is
            ``2 * (glow_radius + 1)`` pixels wider and taller than the
            raw glyph box; callers blitting it should account for the
            pad (or use ``draw_text`` which handles the offset itself).
        glow_radius: Pixel radius of the halo.
        glow_alpha: Per-blit alpha of the halo passes. Lower values
            make the halo softer.

    Returns:
        A new surface containing the rendered glyphs.
    """
    font = get_font(size)
    upper = text.upper()
    if glow is None:
        return font.render(upper, False, color)
    surf, _pad = _render_glow(
        upper, font, color, glow, glow_radius, glow_alpha,
    )
    return surf


def draw_text(
    surface: pygame.Surface,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int] = ColorSettings.WHITE,
    size: int = FontSettings.SIZE_BODY,
    max_width: int | None = None,
    line_spacing: int = 2,
    glow: tuple[int, int, int] | None = None,
    glow_radius: int = 3,
    glow_alpha: int = 110,
) -> int:
    """Draw ``text`` onto ``surface``, wrapping if ``max_width`` is given.

    Args:
        surface: The surface to draw onto.
        text: The text to render. Will be upper-cased.
        position: Top-left in pixels (of the natural glyph box — the
            glow halo, if any, bleeds *outside* this box symmetrically
            and does not shift the visible baseline).
        color: Text color (sharp body).
        size: Point size.
        max_width: If set, word-wrap to this many pixels per line.
        line_spacing: Extra pixels between wrapped lines.
        glow: Optional halo color. Used by Aku-element labels so the
            lore-black body remains readable against the black command
            panel and any other dark background.
        glow_radius: Pixel radius of the halo.
        glow_alpha: Per-blit alpha of the halo passes.

    Returns:
        The total height in pixels that was drawn (so callers can stack
        further content below it). Halo bleed is NOT counted toward this
        height -- vertical layout treats glow as a free overhang.
    """
    font = get_font(size)
    upper = text.upper()
    lines = wrap(upper, font, max_width) if max_width is not None else upper.split("\n")
    x, y = position
    line_height = font.get_linesize()
    drawn = 0
    for line in lines:
        if glow is None:
            rendered = font.render(line, False, color)
            surface.blit(rendered, (x, y + drawn))
        else:
            rendered, pad = _render_glow(
                line, font, color, glow, glow_radius, glow_alpha,
            )
            # Offset by -pad so the glyph body lines up with where the
            # plain-text render would have placed it.
            surface.blit(rendered, (x - pad, y + drawn - pad))
        drawn += line_height + line_spacing
    return drawn
