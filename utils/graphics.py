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


# Cache of loaded element-icon surfaces keyed by element id.
# Each entry stores a Surface when the file was found, or ``None`` when
# the lookup confirmed there is no art for that element yet. Caching the
# negative result avoids re-stat'ing the filesystem on every frame for
# elements like ``lau`` / ``mana`` / ``ra`` / ``aku`` that don't have
# icons drawn yet.
_ELEMENT_ICON_CACHE: dict[str, pygame.Surface | None] = {}


def load_element_icon(element_id: str) -> pygame.Surface | None:
    """Return the affinity icon surface for ``element_id``, or ``None``.

    Looks up ``assets/graphics/icons/<element_id>.png``. If the file is
    missing the function returns ``None`` so callers can decide to fall
    back to the element word -- this keeps UI rendering tolerant of
    partial icon coverage while art for the remaining elements is in
    progress.

    Surfaces are cached (including the ``None`` outcome) so callers
    can invoke this in their render path without paying repeated disk
    or filesystem cost.

    Args:
        element_id: A lowercase element id, e.g. ``"ahi"`` or ``"wai"``.

    Returns:
        The icon ``pygame.Surface`` if the file exists, otherwise
        ``None``. The returned surface is shared -- callers must not
        mutate it.
    """
    if element_id in _ELEMENT_ICON_CACHE:
        return _ELEMENT_ICON_CACHE[element_id]
    candidate = os.path.join(AssetPaths.ICONS_DIR, f"{element_id}.png")
    if not os.path.exists(candidate):
        _ELEMENT_ICON_CACHE[element_id] = None
        return None
    surface = pygame.image.load(candidate)
    # ``convert_alpha`` needs an active display; callers run inside scene
    # render methods so the display is always up by then. Headless smoke
    # tests fall back to the unconverted surface, same as load_portrait.
    if pygame.display.get_surface() is not None:
        surface = surface.convert_alpha()
    _ELEMENT_ICON_CACHE[element_id] = surface
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
