#!/usr/bin/env python3
"""Generate the Fulda street map print from OpenStreetMap data.

Usage: python3 stadtplan.py FONT_DIR
Reads stadtplan-osm.json, lupe-osm.json and detail-osm.json (Overpass results
of stadtplan.overpassql, lupe.overpassql and detail.overpassql). To refresh
the data, run for each query:
  curl --data-urlencode data@stadtplan.overpassql \\
       https://overpass-api.de/api/interpreter -o stadtplan-osm.json
Map data (c) OpenStreetMap contributors, ODbL. The print shows the attribution.

The street map has a magnifier over Dom and Schloss with 2x zoom inside the lens:
  stadtplan-lupe-detail-hell   detailed map: gardens, paths, trees, fountains;
                               Dom, Paulustor, Hexenturm, Heertor dark, Schloss lighter
"""
import math, os, sys
from common import HERE, PNG_OUT, AREA_MM, text_path, svg, export
from osmlogo import LENS_C, LENS_R, lens
import karte

FONTS = sys.argv[1]
BOLD = os.path.join(FONTS, "BarlowCondensed-Bold.ttf")

CENTER = (50.5530, 9.6750)  # lat, lon: Altstadt between Dom and Stadtpfarrkirche
RADIUS_M = 1500             # map radius in metres
DIAMETER_MM = 250           # printed map diameter
WIDTH_MM = 270              # printed width of the full motif

# line widths in mm at print size; DTF film needs >= 1 mm
ROAD_MM = 1.1   # residential road; main roads are wider (karte.ROAD_CLASSES)
RIVER_MM = 4.0

LENS_MM = 42.0  # outer radius of the magnifier ring
ZOOM = 2.0      # magnification inside the lens

COL = dict(road="#2d3335", river="#3f7fd0", landmark="#c04848", park="#4f8a3a",
           building="#9aa3a7", text="#2d3335", sub="#2f6b2a", ring="#2d3335",
           handle="#2d3335", band="#e0a800")
# detail lens: colours of a detailed OSM map (flat colours only)
DCOL = dict(land="#ede7dc", grass="#a9d98a", wood="#7fbf62", flowerbed="#e58fb0",
            water="#7fb0e8", fountain="#3f7fd0", street="#ffffff", path="#ffffff",
            building="#c7b8a8", dom="#8b5a2b", schloss="#a8743f", hedge="#7fbf62", tree="#3f7a2e")

R = DIAMETER_MM / 2.0
P = karte.Proj(CENTER, DIAMETER_MM / (2.0 * RADIUS_M))

base = karte.load("stadtplan-osm.json")
ROADS = karte.roads_svg(base, P, ROAD_MM, COL["road"])
river = [P.d(g) for g in karte.rivers(base)]
park = [P.d(g, True) for g in karte.parks(base)]
dom, schloss, sights, buildings = karte.landmarks()
print("Schloss: %d buildings" % len(schloss))
landmarks = dom + schloss + sights


def base_map():
    o = []
    for d in park:
        o.append('<path fill="%s" d="%s"/>' % (COL["park"], d))
    for d in river:
        o.append('<path fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
                 'stroke-linejoin="round" d="%s"/>' % (COL["river"], RIVER_MM, d))
    o.append(ROADS)
    o.append('<path fill="%s" stroke="%s" stroke-width="1" stroke-linejoin="round" d="%s"/>'
             % (COL["landmark"], COL["landmark"], " ".join(P.d(g, True) for g in landmarks)))
    return "\n".join(o)


detail = karte.detail()
STREETS = [P.d(e["geometry"]) for e in karte.load("lupe-osm.json")
           if e.get("geometry") and e.get("tags", {}).get("area") != "yes"
           and e.get("tags", {}).get("highway") in karte.ROAD_CLASSES]
STREETS += [P.d(e["geometry"]) for e in karte.load("detail-osm.json")
            if e.get("tags", {}).get("highway") == "service" and e.get("geometry")]


TREE_R = 0.8    # tree dot radius in mm at print size (dot = 1.6 mm)
SIGHT_GROW = 2.4  # outline of small landmarks in mm at print size
TREE_GAP = 1.0  # smallest gap between two tree dots in mm at print size


def trees(gap):
    """Tree dots in map units: single trees plus points along tree rows.
    Drop a tree if it is nearer than one dot plus gap to a kept tree, so that
    dense avenues stay single dots and do not merge into a band."""
    pts = [P.xy(*p) for p in detail["tree"]]
    step = 2 * TREE_R / ZOOM + gap
    for g in detail["tree_row"]:
        q = [P.xy(p["lat"], p["lon"]) for p in g]
        for (x0, y0), (x1, y1) in zip(q, q[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
            pts += [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n)]
    kept = []
    for x, y in pts:
        if all(math.hypot(x - a, y - b) >= step for a, b in kept):
            kept.append((x, y))
    return kept


def detail_map():
    """Detailed OSM map for the lens: streets, paths, gardens, trees, fountains.
    Widths in map units; the lens shows them ZOOM times bigger (1 mm print = 1/ZOOM)."""
    u = 1.0 / ZOOM  # 1 mm at print size
    def fill(col, geoms):
        return '<path fill="%s" d="%s"/>' % (col, " ".join(P.d(g, True) for g in geoms)) if geoms else ""
    def line(col, w, geoms):
        return ('<path fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
                'stroke-linejoin="round" d="%s"/>' % (col, w, " ".join(P.d(g) for g in geoms))
                if geoms else "")
    def dots(col, r, pts):
        return '<g fill="%s">%s</g>' % (col, "".join(
            '<circle cx="%.2f" cy="%.2f" r="%s"/>' % (x, y, r) for x, y in pts))
    o = ['<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (LC[0], LC[1], GLASS_R, DCOL["land"])]
    o.append('<path fill="%s" d="%s"/>' % (DCOL["grass"], " ".join(park)))
    o.append(fill(DCOL["grass"], detail["grass"]))
    o.append(fill(DCOL["wood"], detail["wood"]))
    o.append(fill(DCOL["flowerbed"], detail["flowerbed"]))
    o.append(fill(DCOL["water"], detail["water"]))
    o.append('<path fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
             'stroke-linejoin="round" d="%s"/>' % (COL["river"], RIVER_MM / ZOOM, " ".join(river)))
    o.append('<path fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
             'stroke-linejoin="round" d="%s"/>' % (DCOL["street"], 2.4 * u, " ".join(STREETS)))
    o.append(line(DCOL["path"], 1.0 * u, detail["path"]))
    o.append(fill(DCOL["building"], buildings))
    o.append(fill(DCOL["dom"], dom))
    o.append(fill(DCOL["schloss"], schloss))
    # Paulustor and Hexenturm are small: a wide outline in the same colour
    # makes them bigger than in reality, so that they stay visible
    o.append('<path fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" d="%s"/>'
             % (DCOL["dom"], DCOL["dom"], SIGHT_GROW * u,
                " ".join(P.d(g, True) for g in sights)))
    o.append(line(DCOL["hedge"], 1.4 * u, detail["hedge"]))
    o.append(dots(DCOL["tree"], TREE_R * u, trees(TREE_GAP * u)))
    o.append(dots(DCOL["fountain"], 1.5 * u, [P.xy(*p) for p in detail["fountain"]]))
    return "\n".join(o)


# lens centre: midway between Dom and Schloss
pts = [P.xy(*karte.centroid(g)) for g in (dom[0], max(schloss, key=len))]
LC = ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
K = LENS_MM / LENS_R       # logo units -> mm
GLASS_R = 67.6 * K         # inner radius of the ring + overlap


def map_with_lens(inner):
    """The base map with a magnifier at LC and the zoomed map inside the lens."""
    o = ['<defs><clipPath id="c"><circle cx="0" cy="0" r="%s"/></clipPath>' % R,
         '<clipPath id="g"><circle cx="%s" cy="%s" r="%s"/></clipPath>' % (LC[0], LC[1], GLASS_R),
         '<mask id="m" maskUnits="userSpaceOnUse" x="-200" y="-200" width="400" height="400">'
         '<rect x="-200" y="-200" width="400" height="400" fill="#fff"/>'
         '<circle cx="%s" cy="%s" r="%s" fill="#000"/></mask></defs>' % (LC[0], LC[1], LENS_MM)]
    o.append('<g clip-path="url(#c)" mask="url(#m)">%s</g>' % base_map())
    o.append('<g clip-path="url(#g)"><g transform="translate(%s %s) scale(%s) translate(%s %s)">'
             '%s</g></g>' % (LC[0], LC[1], ZOOM, -LC[0], -LC[1], inner()))
    o.append('<g transform="translate(%s %s) scale(%s) translate(%s %s)">%s</g>'
             % (LC[0], LC[1], K, -LENS_C[0], -LENS_C[1],
                lens(COL["ring"], COL["handle"], COL["band"])))
    return "\n".join(o)


def lettering(y):
    """OPENSTREETMAP / FULDA / coordinates / attribution, centred. Return (svg, new y)."""
    o = []
    for text, cap, track, col, gap in (
            ("OPENSTREETMAP", 9, 0.12, COL["sub"], 4),
            ("FULDA", 40, 0.06, COL["text"], 7),
            ("50.5530° N · 9.6750° E", 7, 0.08, COL["sub"], 5),
            (karte.ATTRIBUTION, 5.5, 0.04, COL["text"], 0)):
        d, w = text_path(text, BOLD, 100, track)
        sc = cap / 70.0
        y += cap
        o.append('<path fill="%s" transform="translate(%s %s) scale(%s)" d="%s"/>'
                 % (col, (WIDTH_MM - w * sc) / 2, y, sc, d))
        y += gap
    return "\n".join(o), y


txt, y = lettering(DIAMETER_MM + 14)
H = round(y + 1, 2)
for name, inner in (("stadtplan-lupe-detail-hell", detail_map),):
    body = '<g transform="translate(%s %s)">%s</g>\n%s' % (WIDTH_MM / 2, R, map_with_lens(inner), txt)
    svg_file = os.path.join(HERE, name + ".svg")
    open(svg_file, "w").write(svg("%smm" % WIDTH_MM, "%smm" % H, body, "0 0 %s %s" % (WIDTH_MM, H)))
    export(svg_file, os.path.join(PNG_OUT, name + ".png"), WIDTH_MM, (AREA_MM[0] - WIDTH_MM) / 2, 0)
    print("ok, %s height %.0f mm" % (name, H))
