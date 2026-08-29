#!/usr/bin/env python3
"""Şəbəkə, generated.

The imagery on this site is not photography. It is the window the house is named
after, built the way the window is built: a wooden lattice with coloured glass in
the gaps. Drawing it instead of shooting it keeps the repository licence-clean,
gives every room a picture that is unmistakably its own, and costs about a
kilobyte a room -- which is itself part of what we are selling.

Four lattice families, all real constructions rather than decoration:

    ulduz8      eight-pointed star and cross -- the pattern on the Xan Sarayı
    sekkizguse  octagons meeting edge to edge, squares in the gaps
    carpaz      45-degree lattice, diamonds
    altibucaq   hexagons and triangles

The glass follows one rule, the same for every room: three tones of the room's own
colour carry the pattern and a constant amber picks out the smallest pieces --
a workshop keeps one stock of amber and varies only the coloured sheet. There is
no clear glass: at the size these panels are actually seen, pale pieces stopped
reading as glass and started reading as specks.

    python3 tools/sebeke.py          # writes every SVG and a contact sheet
"""

from __future__ import annotations

import colorsys
import math
from pathlib import Path

import hotel

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/img/sebeke"

WOOD = "#2D2320"          # walnut: the lattice itself
WOOD_LIT = "#4A3A31"      # the edge of a bar catching light
AMBER = "#D9A441"         # the constant amber stock


# --- Colour -----------------------------------------------------------------

def _hex_to_hls(h: str):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)


def _hls_to_hex(h, l, s) -> str:
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


MIN_ON_WOOD = 1.9         # a sheet darker than this disappears into the bar


def _lift(hex_colour: str) -> str:
    """Raise a tone until it separates from the wood it sits in.

    Amber and olive deepen into something very close to walnut, and a hexagon in
    that colour reads as a hole rather than as glass. Rather than hand-picking
    around it per room, every tone is checked against the bar face and lightened
    until it is visible -- which is the same thing a glazier does when a sheet
    turns out too dark for the frame.
    """
    h, l, s = _hex_to_hls(hex_colour)
    for _ in range(40):
        if hotel.contrast(_hls_to_hex(h, l, s), WOOD_LIT) >= MIN_ON_WOOD:
            break
        l += 0.025
    return _hls_to_hex(h, min(l, 0.92), s)


def glass_tones(base_hex: str) -> list:
    """Four sheets: the room's colour deep, light and mid, then the house amber."""
    h, l, s = _hex_to_hls(base_hex)
    deep = _hls_to_hex(h, max(0.18, l - 0.09), min(1.0, s + 0.06))
    light = _hls_to_hex(h, min(0.70, l + 0.23), max(0.30, s - 0.10))
    mid = _hls_to_hex(h, min(0.58, l + 0.10), max(0.34, s - 0.04))
    return [_lift(deep), _lift(light), AMBER, _lift(mid)]


# --- Geometry ---------------------------------------------------------------
# Each family returns (tile_size, [(points, tone_index), ...]) in tile space.
# Shapes may run past the tile edge; the pattern clips and the neighbour
# completes them, which is how the lattice keeps going.

def _poly(pts) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def _star8(cx, cy, r):
    """Two squares laid over each other -- the eight-pointed star."""
    inner = r * math.cos(math.radians(45)) / math.cos(math.radians(22.5))
    pts = []
    for k in range(8):
        a = math.radians(45 * k)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        b = math.radians(45 * k + 22.5)
        pts.append((cx + inner * math.cos(b), cy + inner * math.sin(b)))
    return pts


def _cross(cx, cy, arm, half):
    """A Greek cross: the shape the gaps between four stars actually make."""
    a, w = arm, half
    return [(cx - w, cy - a), (cx + w, cy - a), (cx + w, cy - w), (cx + a, cy - w),
            (cx + a, cy + w), (cx + w, cy + w), (cx + w, cy + a), (cx - w, cy + a),
            (cx - w, cy + w), (cx - a, cy + w), (cx - a, cy - w), (cx - w, cy - w)]


def _regular(cx, cy, r, n, phase=0.0):
    return [(cx + r * math.cos(math.radians(phase + 360 * k / n)),
             cy + r * math.sin(math.radians(phase + 360 * k / n))) for k in range(n)]


def tile_ulduz8(s: float):
    r = s * 0.295
    shapes = [(_star8(s / 2, s / 2, r), 0)]
    arm, half = s * 0.215, s * 0.078
    for cx, cy in ((0, 0), (s, 0), (0, s), (s, s)):
        shapes.append((_cross(cx, cy, arm, half), 1))
    for cx, cy in ((s / 2, 0), (s / 2, s), (0, s / 2), (s, s / 2)):
        shapes.append((_regular(cx, cy, s * 0.095, 4, 45), 2))
    return shapes


def tile_sekkizguse(s: float):
    """Octagons edge to edge; the gap between four of them is a square."""
    shapes = [(_regular(s / 2, s / 2, s * 0.40, 8, 22.5), 0)]
    for cx, cy in ((0, 0), (s, 0), (0, s), (s, s)):
        shapes.append((_regular(cx, cy, s * 0.165, 4, 45), 1))
    for cx, cy in ((s / 2, 0), (s / 2, s), (0, s / 2), (s, s / 2)):
        shapes.append((_regular(cx, cy, s * 0.125, 4, 0), 2))
    return shapes


def tile_carpaz(s: float):
    """A lattice turned 45 degrees. Diamonds, and a small square where they meet."""
    h = s / 2
    shapes = []
    for cx, cy in ((h, h), (0, 0), (s, 0), (0, s), (s, s)):
        outer, inner = h * 0.78, h * 0.40
        tone = 0 if (cx, cy) == (h, h) else 1
        shapes.append(([(cx, cy - outer), (cx + outer, cy),
                        (cx, cy + outer), (cx - outer, cy)], tone))
        shapes.append(([(cx, cy - inner), (cx + inner, cy),
                        (cx, cy + inner), (cx - inner, cy)], 3 if tone == 0 else 0))
    for cx, cy in ((h, 0), (0, h), (s, h), (h, s)):
        shapes.append((_regular(cx, cy, s * 0.115, 4, 0), 2))
    return shapes


def tile_altibucaq(s: float):
    """Hexagons in a staggered grid, triangles filling what is left."""
    r = s * 0.245                     # 2r must stay under the 0.5s centre spacing
    shapes = []
    for cx, cy, tone in ((s * 0.25, s * 0.25, 0), (s * 0.75, s * 0.75, 3),
                         (s * 0.75, s * 0.25, 1), (s * 0.25, s * 0.75, 1)):
        shapes.append((_regular(cx, cy, r, 6, 0), tone))
    for cx, cy in ((s * 0.5, 0), (s * 0.5, s), (0, s * 0.5), (s, s * 0.5)):
        shapes.append((_regular(cx, cy, s * 0.10, 3, 90), 2))
    for cx, cy in ((0, 0), (s, 0), (0, s), (s, s)):
        shapes.append((_regular(cx, cy, s * 0.105, 4, 45), 2))
    return shapes


FAMILIES = {
    "ulduz8": tile_ulduz8,
    "sekkizguse": tile_sekkizguse,
    "carpaz": tile_carpaz,
    "altibucaq": tile_altibucaq,
}


# --- Rendering --------------------------------------------------------------

def panel(family: str, base_hex: str, density: int, w: int, h: int,
          pid: str, frame: bool = True) -> str:
    """One şəbəkə panel as an <svg> element, drawn as a repeating pattern."""
    tones = glass_tones(base_hex)
    s = w / density
    shapes = FAMILIES[family](s)
    bars = max(2.6, s * 0.095)

    cells = "".join(
        f'<polygon points="{_poly(pts)}" fill="{tones[t]}"/>' for pts, t in shapes)
    # The bar edges are drawn as a stroke on the same shapes: in a real şəbəkə the
    # wood is what you see first and the glass sits behind it.
    edges = "".join(
        f'<polygon points="{_poly(pts)}" fill="none" stroke="{WOOD}" '
        f'stroke-width="{bars:.2f}" stroke-linejoin="round"/>' for pts, t in shapes)

    f = (f'<rect x="{bars:.1f}" y="{bars:.1f}" width="{w - 2 * bars:.1f}" '
         f'height="{h - 2 * bars:.1f}" fill="none" stroke="{WOOD}" '
         f'stroke-width="{bars * 2:.1f}"/>') if frame else ""

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="presentation">'
        f'<defs><pattern id="{pid}" width="{s:.3f}" height="{s:.3f}" '
        f'patternUnits="userSpaceOnUse">'
        f'<rect width="{s:.3f}" height="{s:.3f}" fill="{WOOD_LIT}"/>'
        f'{cells}{edges}</pattern></defs>'
        f'<rect width="{w}" height="{h}" fill="url(#{pid})"/>{f}</svg>')


def favicon() -> str:
    """One star, one cross, the house colours. Legible at 16px."""
    tones = glass_tones(hotel.ROOMS[5].hex_light)     # Yaqut, the ruby room
    star = _poly(_star8(16, 16, 11))
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        f'<rect width="32" height="32" rx="5" fill="{WOOD}"/>'
        f'<polygon points="{star}" fill="{tones[0]}" stroke="{AMBER}" '
        'stroke-width="1.6" stroke-linejoin="round"/>'
        f'<circle cx="16" cy="16" r="3.1" fill="{AMBER}"/></svg>')


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for r in hotel.ROOMS:                       # the rule, enforced not assumed
        for tone in glass_tones(r.hex_light):
            assert hotel.contrast(tone, WOOD_LIT) >= MIN_ON_WOOD - 0.01, \
                f"{r.name}: {tone} vanishes into the lattice"
    total = 0
    for r in hotel.ROOMS:
        svg = panel(r.pattern, r.hex_light, r.density, 720, 480, f"s-{r.slug}")
        p = OUT / f"{r.slug}.svg"
        p.write_text(svg, encoding="utf-8")
        total += p.stat().st_size
    # A wide one for the front page, built on the ruby room's stock.
    hero = panel("ulduz8", hotel.ROOM_BY_SLUG["yaqut"].hex_light, 9, 1440, 560,
                 "s-hero", frame=False)
    (OUT / "hero.svg").write_text(hero, encoding="utf-8")
    total += (OUT / "hero.svg").stat().st_size
    # A narrow band for section rules.
    band = panel("carpaz", hotel.ROOM_BY_SLUG["lacivard"].hex_light, 24, 1440, 72,
                 "s-band", frame=False)
    (OUT / "band.svg").write_text(band, encoding="utf-8")
    total += (OUT / "band.svg").stat().st_size

    fav = ROOT / "assets/img/favicon.svg"
    fav.write_text(favicon(), encoding="utf-8")
    print(f"{len(hotel.ROOMS) + 2} panels + favicon, {total / 1024:.1f} KB total")


def contact_sheet() -> Path:
    """Everything on one page, so the shapes get looked at instead of assumed."""
    cards = "".join(
        f'<figure><img src="sebeke/{r.slug}.svg" alt="{r.name}" width="720" '
        f'height="480"><figcaption>{r.name} — {r.pattern}, sıxlıq {r.density}, '
        f'{r.hex_light}</figcaption></figure>' for r in hotel.ROOMS)
    html = (
        '<!doctype html><meta charset="utf-8"><title>şəbəkə</title><style>'
        'body{background:#EDEEEA;font:13px system-ui;margin:16px;width:1180px}'
        '.g{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}'
        'figure{margin:0}img{width:100%;height:auto;display:block}'
        'figcaption{padding:5px 2px;color:#333}'
        '.wide img{width:100%}</style>'
        f'<div class="wide"><img src="sebeke/hero.svg" alt="hero">'
        f'<img src="sebeke/band.svg" alt="band"></div>'
        f'<div class="g">{cards}</div>')
    p = ROOT / "assets/img/_contact.html"
    p.write_text(html, encoding="utf-8")
    return p


if __name__ == "__main__":
    build()
    print("contact sheet:", contact_sheet())
