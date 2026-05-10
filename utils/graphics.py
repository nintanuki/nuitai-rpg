"""Graphics helpers shared across scenes.

The functions here build pygame ``Surface`` objects that scenes
pre-render once and blit each frame, rather than allocating or
recomputing per-frame pixel work.
"""

from __future__ import annotations

import pygame


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
