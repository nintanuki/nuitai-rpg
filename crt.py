import pygame
import random

from settings import ScreenSettings, ColorSettings, AssetPaths

class CRT:
    """Creates a CRT monitor effect"""
    def __init__(self, screen):
        """
        Initializes the CRT effect by loading a TV overlay image,
        scaling it to fit the screen,
        and storing a reference to the screen for drawing.

        Args:
            screen: Display surface to render the CRT effect onto.
        """
        self.screen = screen
        self.base_tv = pygame.image.load(AssetPaths.TV).convert_alpha()
        self.base_tv = pygame.transform.scale(self.base_tv, ScreenSettings.RESOLUTION)

    def create_crt_lines(self, surf):
        """Draw horizontal scan lines across a surface to mimic CRT artifacts.

        Args:
            surf: Surface receiving the scanline overlay.
        """
        line_height = ScreenSettings.CRT_SCANLINE_HEIGHT
        for y in range(0, ScreenSettings.HEIGHT, line_height):
            pygame.draw.line(surf, ColorSettings.OVERLAY_BACKGROUND, (0, y), (ScreenSettings.WIDTH, y), 1)

    def draw(self):
        """Draws the CRT effect by copying the base TV image, applying a random alpha for flickering,
        adding scan lines, and blitting it on top of the current screen."""
        # Copy per frame so the overlay effect does not accumulate between frames.
        tv = self.base_tv.copy()

        tv.set_alpha(random.randint(*ScreenSettings.CRT_ALPHA_RANGE))
        self.create_crt_lines(tv)

        self.screen.blit(tv, (0, 0))