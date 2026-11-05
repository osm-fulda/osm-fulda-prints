"""Shapes of the OSM Fulda logo, read from ../../gemeinsam/assets/osm-fulda-logo.svg.

All paths are in the 256x256 coordinate system of the source logo.
"""
import os, re
from common import HERE

SRC = os.path.join(HERE, "..", "..", "gemeinsam", "assets", "osm-fulda-logo.svg")
s = open(SRC).read()


def elem(id_):
    """Return the full source of the element with the given id."""
    a = s.find('id="%s"' % id_)
    st = s.rfind('<', 0, a)
    tag = re.match(r'<(\w+)', s[st:]).group(1)
    # self-closing?
    end_self = s.find('/>', a)
    end_open = s.find('>', a)
    if end_self != -1 and end_self < end_open + 1 and s[end_open - 1] == '/':
        return s[st:end_open + 1]
    depth, i = 0, st
    pat = re.compile(r'<(/?)%s\b[^>]*?(/?)>' % tag)
    for m in pat.finditer(s, st):
        if m.group(1):
            depth -= 1
        elif not m.group(2):
            depth += 1
        if depth == 0:
            return s[st:m.end()]


def d_of(id_):
    return re.search(r'\sd="([^"]*)"', elem(id_)).group(1)


MAP_TF = "translate(0 -10)"
OUTLINE = d_of("path294")
GREEN = d_of("path296")  # forest areas
RIVER = d_of("path300")
# contour lines, split into single lines (path310 holds five)
CONTOURS = ["M" + x for i in ("path302", "path304", "path306", "path308", "path310")
            for x in d_of(i).split("M") if x.strip()]
BORDERS = [d_of("path314"), d_of("path316")]
SHADOWS = [d_of("path%d" % i) for i in range(340, 356, 2)]  # dark fold panels
RING = d_of("path386")
GLASS = d_of("path390")
NECK = d_of("path396")
COLLAR = d_of("path394")
HANDLE = d_of("path400")
BAND1 = d_of("path398")
BAND2 = d_of("path362")
WAPPEN = elem("g905")
LENS_C, LENS_R = (174.27, 85.47), 69.8


def lens(ring, handle, band, ring_extra=0.0):
    """Return SVG markup of the magnifier (handle and ring, no glass) in logo units."""
    o = ['<path fill="%s" d="%s"/>' % (band, BAND2)]
    # same paint order as the source: gold bands under the dark handle body
    for d in (COLLAR, NECK):
        o.append('<path fill="%s" d="%s"/>' % (handle, d))
    o.append('<path fill="%s" d="%s"/>' % (band, BAND1))
    o.append('<path fill="%s" d="%s"/>' % (handle, HANDLE))
    if ring_extra:  # a stroke on both ring edges makes the ring thicker
        o.append('<path fill="%s" stroke="%s" stroke-width="%s" d="%s"/>'
                 % (ring, ring, ring_extra, RING))
    else:
        o.append('<path fill="%s" d="%s"/>' % (ring, RING))
    return "\n".join(o)
