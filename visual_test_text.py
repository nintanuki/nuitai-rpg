"""Visual test for element-line glow strategies.

Aku's style is settled (black fill + white halo); this revision shifts
the focus to lifting the OTHER five elements so the screen doesn't read
as "Aku is a god, everyone else is a placeholder."

Top row: the settled Aku recipe alone, in a larger font, for reference.

Grid below: the full in-game element pair line
``AHI + WAI + LAU + MANA + RA + AKU`` rendered several ways, each on
the two in-game backgrounds the player will actually see it over
(nero -- 99% of scenes -- and pure black for the command panel and
overlays). Aku is always rendered with its settled white halo
regardless of approach; the approaches only affect the other five.

All six approach recipes stay defined in this file even after one of
them ships, so the comparison can be re-run later if we want to retune.

Run with ``python visual_test_text.py`` from the repo root.
ESC quits, F11 toggles fullscreen, F1 toggles the row labels.
"""

from __future__ import annotations

import sys
import pygame

from settings import ColorSettings, FontSettings


# ---------------------------------------------------------------------------
# Renderer (kept in sync with ui/text_renderer._render_glow so what you see
# here matches what the live game produces).
# ---------------------------------------------------------------------------

def _render_glow(text, font, fill, glow, radius, alpha):
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
            if dx * dx + dy * dy > r_sq:
                continue
            surf.blit(halo, (dx + pad, dy + pad))
    surf.blit(body, (pad, pad))
    return surf, pad


def render_with_kwargs(font, text, color, glow=None, glow_radius=3,
                       glow_alpha=90):
    """Render ``text`` using the same kwargs ``draw_text`` accepts.

    Returns ``(surface, pad)``; pad is the symmetric overhang produced
    by the halo (0 when there's no glow). The caller should blit at
    ``(x - pad, y - pad)`` so the glyph body lines up with the natural
    layout position regardless of whether a halo is present.
    """
    if glow is None:
        return font.render(text, False, color), 0
    return _render_glow(text, font, color, glow, glow_radius, glow_alpha)


# ---------------------------------------------------------------------------
# Element data
# ---------------------------------------------------------------------------

ELEMENTS = ("ahi", "wai", "lau", "mana", "ra", "aku")

FILL = {
    "ahi":  (255, 130, 130),
    "wai":  (130, 180, 255),
    "lau":  (130, 220, 130),
    "mana": (200, 140, 240),
    "ra":   (255, 220, 0),
    "aku":  (0, 0, 0),
}

# Lighter variant of each element's fill -- used by the "brighter
# self-color" approach so the halo extends past the body in a pale
# version of the element's own hue (like the outer edge of a flame).
BRIGHT_HALO = {
    "ahi":  (255, 200, 200),  # coral / salmon-white
    "wai":  (200, 220, 255),  # ice / sky-white
    "lau":  (200, 250, 200),  # mint / leaf-white
    "mana": (230, 200, 250),  # lavender-white
    "ra":   (255, 250, 180),  # butter / sun-white
}

# Aku's settled recipe always overrides any approach. Mirrors the
# entry in ``ColorSettings.ELEMENT_TEXT_STYLES``.
SETTLED_AKU = {
    "color": (0, 0, 0),
    "glow": (255, 255, 255),
    "glow_radius": 3,
    "glow_alpha": 90,
}


def _approach_flat(elem):
    """Baseline -- no halo, just the accent fill."""
    return {"color": FILL[elem]}


def _approach_universal_white(elem):
    """Apply Aku's exact recipe (white halo at r=3, a=90) to everyone.

    THIS IS THE SHIPPED RECIPE. Kept in this file alongside the other
    approaches so we can re-run the comparison if we ever want to retune.
    """
    return {"color": FILL[elem], "glow": (255, 255, 255),
            "glow_radius": 3, "glow_alpha": 90}


def _approach_soft_white(elem):
    """Toned-down universal white -- smaller radius, lower alpha."""
    return {"color": FILL[elem], "glow": (255, 255, 255),
            "glow_radius": 2, "glow_alpha": 70}


def _approach_self_soft(elem):
    """Each element blooms in its own color, gently."""
    return {"color": FILL[elem], "glow": FILL[elem],
            "glow_radius": 2, "glow_alpha": 60}


def _approach_self_parity(elem):
    """Each element blooms in its own color at the same intensity as Aku."""
    return {"color": FILL[elem], "glow": FILL[elem],
            "glow_radius": 3, "glow_alpha": 90}


def _approach_brighter(elem):
    """Halo is a lighter version of the body color -- 'flame edge' look."""
    return {"color": FILL[elem], "glow": BRIGHT_HALO[elem],
            "glow_radius": 2, "glow_alpha": 80}


APPROACHES = [
    ("flat (current state)",                            _approach_flat),
    ("universal white glow  (Aku recipe r=3 a=90) ** SHIPPED **",
                                                        _approach_universal_white),
    ("universal soft white  (r=2 a=70)",                _approach_soft_white),
    ("self-color soft       (own color r=2 a=60)",      _approach_self_soft),
    ("self-color parity     (own color r=3 a=90)",      _approach_self_parity),
    ("brighter self-color   (lighter halo r=2 a=80)",   _approach_brighter),
]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

# Two background columns (down from three) gives each panel almost
# 2x the width, which is what lets the element line render at
# SIZE_BODY without clipping. Grass dropped because the in-game
# element label only ever lands over nero or pure black.
WIDTH = 1100
HEIGHT = 650

PANEL_LABELS = ("nero (30,30,30) -- typical scene bg",
                "black (0,0,0) -- command panel / overlay")
PANEL_COLORS = (
    ColorSettings.NERO,
    ColorSettings.BLACK,
)
PANEL_COUNT = len(PANEL_COLORS)

LABEL_COL_W = 250
PANEL_GAP = 8
PANEL_COL_W = (WIDTH - LABEL_COL_W - (PANEL_COUNT - 1) * PANEL_GAP) // PANEL_COUNT

TOP_TITLE_H = 28
SHOWCASE_LABEL_H = 18
SHOWCASE_ROW_H = 72
GAP_H = 12
GRID_HDR_H = 20
PANEL_HDR_H = 18
APPROACH_ROW_H = 64

SEPARATOR = " + "


def _wrap_label(font, label, max_width):
    """Greedy two-line wrap so long approach labels fit the label column."""
    words = label.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        cand = word if not current else f"{current} {word}"
        if font.size(cand)[0] <= max_width:
            current = cand
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:2]


def _draw_element_line(surface, font, top_x, top_y, panel_w, panel_h,
                       approach_fn):
    """Draw 'AHI + WAI + LAU + MANA + RA + AKU' centered in the panel.

    Aku always uses ``SETTLED_AKU``. Every other element gets
    ``approach_fn(element_id)`` as its render kwargs. The line is
    centered horizontally inside the panel using body widths only;
    halo padding extends symmetrically and is not counted toward width.
    """
    sep_w = font.size(SEPARATOR.upper())[0]
    total_w = 0
    for i, elem in enumerate(ELEMENTS):
        total_w += font.size(elem.upper())[0]
        if i < len(ELEMENTS) - 1:
            total_w += sep_w

    x = top_x + max(0, (panel_w - total_w) // 2)
    y = top_y + (panel_h - font.get_linesize()) // 2
    for i, elem in enumerate(ELEMENTS):
        kwargs = SETTLED_AKU if elem == "aku" else approach_fn(elem)
        glyph, pad = render_with_kwargs(font, elem.upper(), **kwargs)
        surface.blit(glyph, (x - pad, y - pad))
        x += font.size(elem.upper())[0]
        if i < len(ELEMENTS) - 1:
            sep = font.render(SEPARATOR.upper(), False, ColorSettings.GRAY)
            surface.blit(sep, (x, y))
            x += sep_w


def _draw_approach_row(surface, font_body, font_small, top_y, label,
                       approach_fn, show_labels):
    """One grid row: label column + element line on each background."""
    if show_labels:
        for i, line in enumerate(_wrap_label(font_small, label,
                                             LABEL_COL_W - 12)):
            txt = font_small.render(line, False, ColorSettings.WHITE)
            surface.blit(txt, (8, top_y + 10 + i * 14))

    x = LABEL_COL_W
    for bg in PANEL_COLORS:
        pygame.draw.rect(surface, bg,
                         (x, top_y, PANEL_COL_W, APPROACH_ROW_H))
        # Element line renders at SIZE_BODY so the comparison reads
        # clearly even on a small monitor. The live game uses SIZE_SMALL
        # for these labels; resizing won't change which recipe wins.
        _draw_element_line(surface, font_body, x, top_y,
                           PANEL_COL_W, APPROACH_ROW_H, approach_fn)
        x += PANEL_COL_W + PANEL_GAP


def _draw_panel_headers(surface, font_small, y):
    """Label which column is which background, above the first grid row."""
    x = LABEL_COL_W
    for label in PANEL_LABELS:
        txt = font_small.render(label, False, ColorSettings.GRAY)
        surface.blit(txt, (x + 4, y + 2))
        x += PANEL_COL_W + PANEL_GAP


def _draw_showcase_aku(surface, font_body, font_small, top_y):
    """Top reference row: the settled Aku alone on each background.

    Rendered at SIZE_BODY (16pt). The grid below uses the same size so
    the comparison reads at the same scale, but the showcase keeps a
    distinct background-header strip to anchor the eye.
    """
    txt = font_small.render(
        "SETTLED AKU (reference) -- this is what we're matching",
        False, ColorSettings.WHITE,
    )
    surface.blit(txt, (8, top_y))

    y = top_y + SHOWCASE_LABEL_H
    x = LABEL_COL_W
    for bg in PANEL_COLORS:
        pygame.draw.rect(surface, bg, (x, y, PANEL_COL_W, SHOWCASE_ROW_H))
        glyph, pad = render_with_kwargs(font_body, "AKU", **SETTLED_AKU)
        gw, gh = glyph.get_size()
        surface.blit(
            glyph,
            (x + (PANEL_COL_W - gw) // 2,
             y + (SHOWCASE_ROW_H - gh) // 2),
        )
        x += PANEL_COL_W + PANEL_GAP


def _draw_frame(surface, font_body, font_small, show_labels):
    surface.fill(ColorSettings.NERO)

    # Title strip.
    title = font_small.render(
        "ELEMENT GLOW TEST  --  pick a row",
        False, ColorSettings.WHITE,
    )
    surface.blit(title, (12, 6))
    hint = font_small.render(
        "ESC quits  --  F11 fullscreen  --  F1 toggles row labels",
        False, ColorSettings.GRAY,
    )
    surface.blit(hint, (WIDTH - hint.get_width() - 12, 6))

    # Top reference: settled Aku, alone, on each background.
    showcase_y = TOP_TITLE_H
    _draw_showcase_aku(surface, font_body, font_small, showcase_y)

    # Section header for the comparison grid.
    grid_y = showcase_y + SHOWCASE_LABEL_H + SHOWCASE_ROW_H + GAP_H
    section_label = font_small.render(
        "Approaches for the other five (Aku stays on the settled white)",
        False, ColorSettings.WHITE,
    )
    surface.blit(section_label, (8, grid_y))
    _draw_panel_headers(surface, font_small, grid_y + GRID_HDR_H)

    # One row per approach.
    row_y = grid_y + GRID_HDR_H + PANEL_HDR_H
    for label, fn in APPROACHES:
        _draw_approach_row(surface, font_body, font_small, row_y, label, fn,
                           show_labels)
        row_y += APPROACH_ROW_H + PANEL_GAP


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    pygame.display.set_caption("Element glow visual test")
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
                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif event.key == pygame.K_F1:
                    show_labels = not show_labels
        _draw_frame(screen, font_body, font_small, show_labels)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
