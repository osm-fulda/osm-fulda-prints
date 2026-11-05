#!/usr/bin/env python3
"""Generate the shirt logos from ../../gemeinsam/assets/osm-fulda-logo.svg.

Usage: python3 logo.py FONT_DIR
FONT_DIR must contain BarlowCondensed-Bold.ttf
(https://github.com/google/fonts/tree/main/ofl/barlowcondensed).
The logo is redrawn as flat line art (no gradients, shadows or glass) for DTF
printing.

Variants:
  grosslogo-linie-hell   27.8 cm wide (full print height), on the full print area
  pocketlogo-linie-hell    pocket print, lines designed for 8 cm width, without a
                           print area canvas
  pocketlogo-flaeche-dunkel  the same with the filled map for dark shirts, with a
                           light keyline around the logo
"""
import os, sys
from common import HERE, PNG_OUT, AREA_MM, text_path, svg, export, render
from osmlogo import (MAP_TF, OUTLINE, GREEN, RIVER, CONTOURS, BORDERS, SHADOWS, RING, GLASS,
                     NECK, COLLAR, HANDLE, BAND1, BAND2, WAPPEN, LENS_C, LENS_R, lens)

FONTS = sys.argv[1]
BOLD = os.path.join(FONTS, "BarlowCondensed-Bold.ttf")

# DTF film with lines thinner than ~1 mm can lift in the wash. 256 units = logo width.
# name -> (palette, print width mm, contour lines, contour width,
#          border/outline factor, extra ring width, extra river width)
# grosslogo:  1 mm = 0.9 units: original line widths, all details
# pocketlogo: 1 mm = 3.2 units: four main contour lines at ~1.3 mm, thicker
#             borders, outline, lens ring and river ends
SIZES = {
    "grosslogo-linie-hell": ("linie-hell", 278, CONTOURS, 1.6, 1.0, 0.0, 0.0),
    "pocketlogo-linie-hell": ("linie-hell", 80, [CONTOURS[i] for i in (3, 5, 7, 9)],
                              4.1, 1.9, 1.6, 2.8),
    "pocketlogo-flaeche-dunkel": ("flaeche-dunkel", 80, [CONTOURS[i] for i in (3, 5, 7, 9)],
                                  4.1, 1.9, 1.6, 2.8),
}
# None = not drawn
PALETTES = {
    # line art for light shirts
    "linie-hell": dict(base=None, fold=None, green=None, glass=None, keyline=None,
                       river="#3f7fd0", contour="#4f8a3a", border="#c04848",
                       outline="#2f6b2a", ring="#2d3335", handle="#2d3335", band="#e0a800",
                       text="#2d3335", sub="#2f6b2a"),
    # filled map like the original logo, for dark shirts: a light keyline
    # around the logo keeps the dark ring and handle visible
    "flaeche-dunkel": dict(base="#ceeeab", fold="#bfe59d", green="#a6dd8b", glass="#e6f3f8",
                           keyline="#e9eef0", river="#8fb3e3", contour="#93ad6c",
                           border="#d06b6b", outline=None, ring="#2d3335", handle="#2d3335",
                           band="#f2c230", text="#ffffff", sub="#ceeeab"),
}
KEYLINE = 7.5  # keyline stroke width in logo units (half of it shows: ~1.2 mm at 8 cm)
COL = None     # palette of the variant that is drawn


def logo(contours, contour_w, sw, ring_extra, river_extra):
    """Logo in the 256x256 source coordinate system, in the palette COL."""
    line = ('<path fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
            'stroke-linejoin="round" d="%s"/>')
    o = ['<defs><clipPath id="mapclip"><path d="%s"/></clipPath>'
         '<mask id="lensmask" maskUnits="userSpaceOnUse" x="-50" y="-50" width="400" height="400">'
         '<rect x="-50" y="-50" width="400" height="400" fill="#fff"/>'
         '<circle cx="%s" cy="%s" r="%s" fill="#000"/></mask></defs>'
         % (OUTLINE, LENS_C[0], LENS_C[1], LENS_R)]
    if COL["keyline"]:
        # silhouette of map, lens and handle with a wide stroke, under everything
        k = ('fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"'
             % (COL["keyline"], COL["keyline"], KEYLINE))
        o.append('<path %s transform="%s" d="%s"/>' % (k, MAP_TF, OUTLINE))
        for d in (RING, GLASS, NECK, COLLAR, HANDLE, BAND1, BAND2):
            o.append('<path %s d="%s"/>' % (k, d))
    o += ['<g mask="url(#lensmask)"><g transform="%s">' % MAP_TF]
    if COL["base"]:
        o.append('<path fill="%s" d="%s"/>' % (COL["base"], OUTLINE))
    o.append('<g clip-path="url(#mapclip)">')
    if COL["fold"]:
        for d in SHADOWS:
            o.append('<path fill="%s" transform="translate(0 192)" d="%s"/>' % (COL["fold"], d))
    if COL["green"]:
        o.append('<path fill="%s" d="%s"/>' % (COL["green"], GREEN))
    if river_extra:  # a stroke makes the thin river ends thicker
        o.append('<path fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" d="%s"/>'
                 % (COL["river"], COL["river"], river_extra, RIVER))
    else:
        o.append('<path fill="%s" d="%s"/>' % (COL["river"], RIVER))
    o += [line % (COL["contour"], contour_w, d) for d in contours]
    o += [line % (COL["border"], 2.6 * sw, d) for d in BORDERS]
    o.append('</g>')
    if COL["outline"]:
        o.append('<path fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" d="%s"/>'
                 % (COL["outline"], 3.2 * sw, OUTLINE))
    o.append('</g></g>')
    if COL["glass"]:
        o.append('<path fill="%s" d="%s"/>' % (COL["glass"], GLASS))
    o.append(lens(COL["ring"], COL["handle"], COL["band"], ring_extra))
    o.append(WAPPEN)
    return "\n".join(o)


def lettering(x, y_top, cap_big):
    """OPENSTREETMAP / FULDA, both lines of the same width. Return (svg, width, height)."""
    d_big, w_big = text_path("FULDA", BOLD, 100, 0.06)
    d_small, w_small = text_path("OPENSTREETMAP", BOLD, 30, 0.1)
    sb = cap_big / 70.0
    tw = w_big * sb
    ss = tw / w_small
    y_s = y_top + 0.70 * 30 * ss
    y_b = y_s + 0.16 * cap_big + cap_big
    out = ('<path fill="%s" transform="translate(%s %s) scale(%s)" d="%s"/>'
           % (COL["sub"], x, y_s, ss, d_small)
           + '<path fill="%s" transform="translate(%s %s) scale(%s)" d="%s"/>'
           % (COL["text"], x, y_b, sb, d_big))
    return out, tw, y_b - y_top


for name, (palette, width_mm, *style) in SIZES.items():
    COL = PALETTES[palette]
    # lettering under the logo, same width as the map (236 of 256 units)
    _, tw, _ = lettering(0, 0, 64.0)
    txt, tw, th = lettering(10, 262, 64.0 * 236.0 / tw)
    svg_file = os.path.join(HERE, name + ".svg")
    # margin so that the keyline at the image edge is not cut
    m = KEYLINE / 2 + 1 if COL["keyline"] else 0
    w, h = 256 + 2 * m, round(262 + th + 4 + 2 * m, 2)
    open(svg_file, "w").write(svg(w, h, logo(*style) + txt, "%s %s %s %s" % (-m, -m, w, h)))
    png_file = os.path.join(PNG_OUT, name + ".png")
    if name.startswith("pocket"):
        # pixels for 12 cm at 300 dpi, so the file stays sharp if the
        # configurator makes the pocket print bigger than designed
        render(svg_file, png_file, 120)
    else:
        export(svg_file, png_file, width_mm, (AREA_MM[0] - width_mm) / 2, 0)
print("ok")
