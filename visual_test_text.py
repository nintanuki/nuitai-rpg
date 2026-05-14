"""Visual test harness for Aku text-style alternatives.

Standalone — run with ``python visual_test_text.py`` from the repo root.
Renders the six elements in their current accent colors as a reference
row, then a grid of Aku style variants (different fills + outlines +
glows) drawn on three representative backgrounds (nero, pure black,
overworld grass) so you can eyeball which combination reads best.

Press ESC or close the window to quit. F1 toggles a legend overlay
that names each row's recipe.

Nothing here is wired into the game; this file exists purely to pick a
direction for Aku's text style.
"""

from __future__ import annotations

import sys
import pygame

from settings import ColorSettings, FontSettings, ScreenSettings


# ---------------------------------------------------------------------------
# Outline / glow renderers
# ---------------------------------------------------------------------------

def render_outlined(
    text: str,
    font: pygame.font.Font,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
    thickness: int = 1,
) -> pygame.Surface:
    """Return ``text`` rendered in ``fill`` with a ``thickness`` outline.

    Implementation: render the outline-colored text 8 times around the
    center then blit the fill once on top. Antialiasing is off to keep
    the pixel-font edges crisp, matching the game's render pipeline.
    """
    body = font.render(text, False, fill)
    edge = font.render(text, False, outline)
    w, h = body.get_size()
    surf = pygame.Surface(
        (w + 2 * thickness, h + 2 * thickness), pygame.SRCALPHA
    )
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx == 0 and dy == 0:
                continue
            surf.blit(edge, (dx + thickness, dy + thickness))
    surf.blit(body, (thickness, thickness))
    return surf


def render_glow(
    text: str,
    font: pygame.font.Font,
    fill: tuple[int, int, int],
    glow: tuple[int, int, int],
    radius: int = 3,
    alpha: int = 110,
) -> pygame.Surface:
    """Return ``text`` with a soft halo in ``glow`` behind ``fill`` text.

    Multi-offset technique: blit the glow color in a ring of offsets at
    a low per-blit alpha so they accumulate into a soft cloud, then put
    the sharp text on top.
    """
    body = font.render(text, False, fill)
    halo = font.render(text, False, glow)
    halo.set_alpha(alpha)
    w, h = body.get_size()
    pad = radius + 1
    surf = pygame.Surface((w + 2 * pad, h + 2 * pad), pygame.SRCALPHA)
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            # Skip the very center; we'll draw the sharp text there.
            if dx == 0 and dy == 0:
                continue
            # Soft falloff — corners of the box get pushed past the
            # circular radius and dropped, keeping the halo round-ish.
            if dx * dx + dy * dy > radius * radius:
                continue
            surf.blit(halo, (dx + pad, dy + pad))
    surf.blit(body, (pad, pad))
    return surf


# ---------------------------------------------------------------------------
# Variant catalogue
# ---------------------------------------------------------------------------

# Reference: pull the current Aku color so the "current" row matches
# the live game exactly.
CURRENT_AKU = ColorSettings.ELEMENT_COLORS["aku"]  # placeholder orange


def _solid(color):
    """Variant factory: plain font.render with a single color."""
    def _render(font, text):
        return font.render(text, False, color)
    return _render


def _outline(fill, edge, thickness=1):
    def _render(font, text):
        return render_outlined(font=font, text=text,
                               fill=fill, outline=edge,
                               thickness=thickness)
    return _render


def _glow(fill, halo, radius=3, alpha=110):
    def _render(font, text):
        return render_glow(font=font, text=text,
                           fill=fill, glow=halo,
                           radius=radius, alpha=alpha)
    return _render


# Each row in the grid is one styling recipe for the word "AKU".
VARIANTS: list[tuple[str, callable]] = [
    ("current: solid orange (255,150,50)",
     _solid(CURRENT_AKU)),
    ("black fill + white outline",
     _outline(ColorSettings.BLACK, ColorSettings.WHITE)),
    ("black fill + violet outline (90,60,130)",
     _outline(ColorSettings.BLACK, (90, 60, 130))),
    ("black fill + dim red outline (120,30,30)",
     _outline(ColorSettings.BLACK, (120, 30, 30))),
    ("black fill + gray outline (120,120,120)",
     _outline(ColorSettings.BLACK, ColorSettings.GRAY)),
    ("dark violet solid (40,20,55), no outline",
     _solid((40, 20, 55))),
    ("black fill + violet GLOW (r=3)",
     _glow(ColorSettings.BLACK, (140, 90, 200), radius=3, alpha=90)),
    ("very dark gray solid (50,50,55), no outline",
     _solid((50, 50, 55))),
]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

# Three test backgrounds. We render each Aku variant on all three so
# you can see how it survives the worst-case contrast on every panel
# the player will actually encounter in-game.
PANEL_LABELS = ("nero (30,30,30)", "black (0,0,0)", "grass (110,160,90)")
PANEL_COLORS = (
    ColorSettings.NERO,
    ColorSettings.BLACK,
    ColorSettings.OVERWORLD_FLOOR,
)

TITLE = "AKU TEXT STYLE TEST  —  pick a row"
ESC_HINT = "ESC to quit  —  F1 toggles row labels"

WIDTH = ScreenSettings.WIDTH       # 800
HEIGHT = ScreenSettings.HEIGHT     # 600

LABEL_COL_W = 260      # left "row label" column
PANEL_GAP = 4
PANEL_COL_W = (WIDTH - LABEL_COL_W - 2 * PANEL_GAP) // 3   # ~178
ROW_H = 52
HEADER_H = 80          # title + reference row
PANEL_HDR_H = 18       # background-name strip above each panel column


def _draw_reference_row(screen: pygame.Surface, font: pygame.font.Font,
                        y: int) -> None:
    """Draw all six element accent colors in one strip for context."""
    pygame.draw.rect(screen, ColorSettings.NERO,
                     (0, y, WIDTH, ROW_H))
    label = font.render("ALL ELEMENTS (CURRENT)", False,
                        ColorSettings.GRAY)
    screen.blit(label, (12, y + 6))
    x = 12
    item_y = y + 24
    for elem_id, color in ColorSettings.ELEMENT_COLORS.items():
        glyph = font.render(elem_id.upper(), False, color)
        screen.blit(glyph, (x, item_y))
        x += glyph.get_width() + 18


def _draw_panel_headers(screen: pygame.Surface,
                        font_small: pygame.font.Font, y: int) -> None:
    """Label which column is which background."""
    x = LABEL_COL_W
    for label in PANEL_LABELS:
        text = font_small.render(label, False, ColorSettings.GRAY)
        screen.blit(text, (x + 4, y + 2))
        x += PANEL_COL_W + PANEL_GAP


def _draw_variant_row(screen: pygame.Surface,
                      font_body: pygame.font.Font,
                      font_small: pygame.font.Font,
                      y: int, label: str, recipe,
                      show_labels: bool) -> None:
    """Draw one row: text label + AKU rendered on each of three panels."""
    if show_labels:
        # Wrap long labels onto two lines manually so they stay inside
        # the label column without us pulling in the renderer's wrap().
        words = label.split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            cand = word if not current else f"{current} {word}"
            if font_small.size(cand)[0] <= LABEL_COL_W - 16:
                current = cand
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        for i, line in enumerate(lines[:2]):
            txt = font_small.render(line, False, ColorSettings.WHITE)
            screen.blit(txt, (8, y + 6 + i * 14))

    x = LABEL_COL_W
    for bg_color in PANEL_COLORS:
        pygame.draw.rect(screen, bg_color, (x, y, PANEL_COL_W, ROW_H))
        glyph = recipe(font_body, "AKU")
        gw, gh = glyph.get_size()
        screen.blit(
            glyph,
            (x + (PANEL_COL_W - gw) // 2, y + (ROW_H - gh) // 2),
        )
        x += PANEL_COL_W + PANEL_GAP


def _draw_frame(screen: pygame.Surface,
                font_body: pygame.font.Font,
                font_small: pygame.font.Font,
                show_labels: bool) -> None:
    screen.fill(ColorSettings.NERO)

    # Title strip.
    title = font_small.render(TITLE, False, ColorSettings.WHITE)
    screen.blit(title, (12, 8))
    hint = font_small.render(ESC_HINT, False, ColorSettings.GRAY)
    screen.blit(hint, (WIDTH - hint.get_width() - 12, 8))

    _draw_reference_row(screen, font_small, y=28)
    _draw_panel_headers(screen, font_small, y=HEADER_H)

    y = HEADER_H + PANEL_HDR_H
    for label, recipe in VARIANTS:
        _draw_variant_row(
            screen, font_body, font_small, y,
            label, recipe, show_labels,
        )
        y += ROW_H + PANEL_GAP


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    pygame.init()
    screen = pygame.display.set_mode(
        ScreenSettings.RESOLUTION, pygame.SCALED
    )
    pygame.display.set_caption("Aku text style visual test")
    clock = pygame.time.Clock()

    font_body = pygame.font.Font(FontSettings.FONT, FontSettings.SIZE_BODY)
    font_small = pygame.font.Font(FontSettings.FONT, FontSettings.SIZE_SMALL)

    show_labels = True
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F1:
                    show_labels = not show_labels

        _draw_frame(screen, font_body, font_small, show_labels)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
