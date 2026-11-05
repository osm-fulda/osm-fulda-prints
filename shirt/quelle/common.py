"""Shared helpers for the shirt print generators.

Needs fonttools, rsvg-convert and ImageMagick (magick).
"""
import os, subprocess
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
PNG_OUT = os.path.dirname(HERE)

# Supergeek configurator: PNG upload, print area 35 x 39.6 cm, no position
# control. Every upload is a transparent canvas of the full print area.
DPI = 300
AREA_MM = (350, 396)


def mm(v):
    """Millimetres to pixels at DPI."""
    return round(v / 25.4 * DPI)


def text_path(text, font, size, tracking=0.0):
    """Convert text to an SVG path. Return (d, width) in user units, baseline at y=0."""
    f = TTFont(font)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    sc = size / f["head"].unitsPerEm
    x = 0.0
    pen = SVGPathPen(gs)
    for i, ch in enumerate(text):
        g = cmap[ord(ch)]
        gs[g].draw(TransformPen(pen, (sc, 0, 0, -sc, x, 0)))
        x += gs[g].width * sc
        if i < len(text) - 1:
            x += tracking * size
    return pen.getCommands(), x


def svg(w, h, body, vb=None):
    vb = vb or "0 0 %s %s" % (w, h)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="%s" height="%s" viewBox="%s">\n%s\n</svg>\n' % (w, h, vb, body))


def export(svg_file, png_file, width_mm, x_mm, y_mm):
    """Render svg_file at width_mm and place it at (x_mm, y_mm) on the print area canvas."""
    subprocess.run(["rsvg-convert", "-w", str(mm(width_mm)), svg_file, "-o", png_file], check=True)
    subprocess.run(["magick", "-size", "%dx%d" % (mm(AREA_MM[0]), mm(AREA_MM[1])), "xc:none",
                    png_file, "-geometry", "+%d+%d" % (mm(x_mm), mm(y_mm)), "-composite",
                    png_file], check=True)


def render(svg_file, png_file, width_mm):
    """Render svg_file at width_mm without a print area canvas (for small prints
    such as the pocket print, where the configurator has its own small area)."""
    subprocess.run(["rsvg-convert", "-w", str(mm(width_mm)), svg_file, "-o", png_file], check=True)


def preview_tile(png_file, font):
    """ImageMagick arguments for one preview tile: upload on white, grey frame = print area."""
    return ["(", png_file, "-background", "#ffffff", "-flatten", "-resize", "400x",
            "-bordercolor", "#bbbbbb", "-border", "2",
            "-background", "#ffffff", "-gravity", "center", "-extent", "480x560",
            "-gravity", "south", "-splice", "0x50",
            "-font", font, "-pointsize", "26", "-fill", "#2d3335",
            "-annotate", "+0+12", os.path.basename(png_file), ")"]
