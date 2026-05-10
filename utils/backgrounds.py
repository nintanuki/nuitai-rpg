"""Scene-background renderer driven by ``BackgroundSettings``.

Each scene calls :func:`render_scene_background` from its own ``render``
method instead of issuing a raw ``surface.fill``. The renderer reads
``BackgroundSettings.SCENE_BACKGROUNDS`` to pick the right template by
scene class name, then either fills a solid color or blits a cached
gradient surface.

Gradient surfaces are expensive to build (one ``draw.line`` per pixel
row) so they are cached on first use, keyed by ``(template_name, width,
height)``. The cache is invalidated automatically when the screen size
changes or when ``BackgroundSettings.TEMPLATES`` is reloaded between
runs; tests can call :func:`clear_cache` to drop entries by hand.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from settings import BackgroundSettings
from utils.graphics import build_gradient_surface

if TYPE_CHECKING:
    from core.scene import Scene


# Cached gradient surfaces keyed by (template name, width, height). Solid
# fills are cheap and intentionally skip the cache.
_GRADIENT_CACHE: dict[tuple[str, int, int], pygame.Surface] = {}


# ----------------------------------------------------------------------
# PUBLIC API
# ----------------------------------------------------------------------


def template_name_for_scene(scene: "Scene") -> str:
    """Return the template name configured for ``scene``.

    Falls back to ``BackgroundSettings.DEFAULT_TEMPLATE`` when the scene's
    class name is not in ``SCENE_BACKGROUNDS``.

    Args:
        scene: The scene instance currently being rendered.

    Returns:
        A key into ``BackgroundSettings.TEMPLATES``.
    """
    scene_class_name = type(scene).__name__
    return BackgroundSettings.SCENE_BACKGROUNDS.get(
        scene_class_name, BackgroundSettings.DEFAULT_TEMPLATE
    )


def render_scene_background(scene: "Scene", surface: pygame.Surface) -> None:
    """Paint ``surface`` with the background template configured for ``scene``.

    Drop-in replacement for ``surface.fill(ColorSettings.BG_COLOR)`` at
    the top of a scene's ``render``. Unknown template names degrade to
    a flat fill in the default background color so a typo never crashes
    a frame.

    Args:
        scene: The scene being rendered (used to look up its template).
        surface: The pygame surface to paint.
    """
    render_template(template_name_for_scene(scene), surface)


def render_template(template_name: str, surface: pygame.Surface) -> None:
    """Paint ``surface`` with a specific named template.

    Useful when a scene wants to pick its background dynamically rather
    than via the static class-name mapping (e.g. a world room that swaps
    skies between day and night).

    Args:
        template_name: A key in ``BackgroundSettings.TEMPLATES``.
        surface: The pygame surface to paint.
    """
    template = BackgroundSettings.TEMPLATES.get(template_name)
    if template is None:
        # Fall back to the default rather than crashing: a missing template
        # is a configuration bug, not a reason to drop a frame.
        template = BackgroundSettings.TEMPLATES.get(
            BackgroundSettings.DEFAULT_TEMPLATE
        )
    if template is None:
        return

    kind = template[0]
    if kind == BackgroundSettings.SOLID:
        _, color = template
        surface.fill(color)
        return

    if kind == BackgroundSettings.GRADIENT:
        _, color_top, color_bottom = template
        width, height = surface.get_size()
        cache_key = (template_name, width, height)
        cached = _GRADIENT_CACHE.get(cache_key)
        if cached is None:
            cached = build_gradient_surface(width, height, color_top, color_bottom)
            _GRADIENT_CACHE[cache_key] = cached
        surface.blit(cached, (0, 0))


def clear_cache() -> None:
    """Drop every cached gradient surface.

    Call this when ``BackgroundSettings.TEMPLATES`` has been edited at
    runtime (e.g. by a future settings menu) so the next render rebuilds
    from the new values.
    """
    _GRADIENT_CACHE.clear()
