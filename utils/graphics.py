"""Graphics helpers shared across scenes.

The functions here build pygame ``Surface`` objects that scenes
pre-render once and blit each frame, rather than allocating or
recomputing per-frame pixel work.
"""

from __future__ import annotations

import os

import pygame

from settings import AssetPaths


# Cache of loaded portrait surfaces keyed by ``PartyMember.id``.
# Portraits are tiny (32x32) but ``pygame.image.load`` still hits disk
# and ``convert_alpha`` is non-trivial; cache them so the party screen
# can re-render every frame without thrashing.
_PORTRAIT_CACHE: dict[str, pygame.Surface] = {}


def load_portrait(member_id: str) -> pygame.Surface:
    """Return the portrait surface for ``member_id``, or the unknown fallback.

    The portrait is looked up at ``assets/graphics/portraits/<id>_portrait.png``.
    If that file does not exist, ``unknown_portrait.png`` is used instead
    so newly-added party members still get a placeholder face. Surfaces
    are cached by member id (including the fallback case, keyed by the
    requested id) so the second and later calls are O(1).

    The display must already be initialised before this is called; in
    practice all callers are inside scene ``render`` / ``__init__``
    methods, which run after ``GameManager`` opens the window.

    Args:
        member_id: The ``PartyMember.id`` whose portrait to load (e.g.
            ``"kailo"``).

    Returns:
        A ``pygame.Surface`` containing the portrait. Returned surface
        is shared — callers must not mutate it.
    """
    cached = _PORTRAIT_CACHE.get(member_id)
    if cached is not None:
        return cached
    candidate = os.path.join(
        AssetPaths.PORTRAITS_DIR, f"{member_id}_portrait.png"
    )
    path = candidate if os.path.exists(candidate) else AssetPaths.UNKNOWN_PORTRAIT
    surface = pygame.image.load(path)
    # ``convert_alpha`` requires an active display surface; the call
    # site already ran after ``GameManager`` set the display mode, so
    # this is safe. We fall back to a plain ``convert`` in the rare
    # case there's no display (e.g. headless smoke tests).
    if pygame.display.get_surface() is not None:
        surface = surface.convert_alpha()
    _PORTRAIT_CACHE[member_id] = surface
    return surface


def build_gradient_surface(
    width: int,
    height: int,
    color_top: tuple[int, int, int],
    color_bottom: tuple[int, int, int],
) -> pygame.Surface:
    """Pre-render a vertical gradient surface for scene backgrounds.

    The gradient is linearly interpolated row-by-row, top to bottom,
    so callers cache the returned surface and blit it each frame
    instead of recomputing.

    Args:
        width: Surface width in pixels.
        height: Surface height in pixels.
        color_top: RGB color at ``y = 0`` (top of the surface).
        color_bottom: RGB color at ``y = height - 1`` (bottom of the
            surface).

    Returns:
        The rendered gradient surface.
    """
    surface = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * t)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * t)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width - 1, y))
    return surface
