"""OpenStreetMap data helpers for the map prints.

Map data (c) OpenStreetMap contributors, ODbL. Every print with map data must
show the attribution "Kartendaten © OpenStreetMap-Mitwirkende".
"""
import json, math, os
from common import HERE

ATTRIBUTION = "Kartendaten © OpenStreetMap-Mitwirkende"

# highway class -> line width factor (1.0 = residential)
ROAD_CLASSES = {
    "motorway": 2.2, "trunk": 2.2, "primary": 2.2,
    "secondary": 1.65, "tertiary": 1.65,
    "motorway_link": 1.3, "trunk_link": 1.3, "primary_link": 1.3,
    "secondary_link": 1.3, "tertiary_link": 1.3,
    "unclassified": 1.0, "residential": 1.0, "living_street": 1.0, "pedestrian": 1.0,
}


def load(name):
    """Return the elements of an Overpass JSON file next to this module."""
    return json.load(open(os.path.join(HERE, name)))["elements"]


class Proj:
    """Equirectangular projection to mm on the print, origin at center."""

    def __init__(self, center, mm_per_m):
        self.center, self.s = center, mm_per_m

    def xy(self, lat, lon):
        dx = (lon - self.center[1]) * 111320.0 * math.cos(math.radians(self.center[0]))
        dy = (lat - self.center[0]) * 110540.0
        return dx * self.s, -dy * self.s

    def d(self, geom, close=False):
        pts = [self.xy(p["lat"], p["lon"]) for p in geom]
        return "M" + " L".join("%.2f %.2f" % p for p in pts) + ("Z" if close else "")


def roads_svg(elements, proj, base_mm, col):
    """Road lines; base_mm = width of a residential road. Thin roads first."""
    roads = {}
    for e in elements:
        t, g = e.get("tags", {}), e.get("geometry")
        f = ROAD_CLASSES.get(t.get("highway"))
        if g and f and t.get("area") != "yes":
            roads.setdefault(f, []).append(proj.d(g))
    return "\n".join('<path fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round" '
                     'stroke-linejoin="round" d="%s"/>' % (col, f * base_mm, " ".join(ds))
                     for f, ds in sorted(roads.items()))


def rivers(elements):
    return [e["geometry"] for e in elements
            if e.get("geometry") and e.get("tags", {}).get("waterway") == "river"]


def parks(elements):
    return [e["geometry"] for e in elements
            if e.get("geometry") and e.get("tags", {}).get("leisure") == "park"]


def centroid(geom):
    return (sum(p["lat"] for p in geom) / len(geom), sum(p["lon"] for p in geom) / len(geom))


def inside(pt, geom):
    """Ray casting point-in-polygon test in lat/lon."""
    lat, lon = pt
    res = False
    for i in range(len(geom)):
        a, b = geom[i], geom[i - 1]
        if (a["lat"] > lat) != (b["lat"] > lat):
            x = a["lon"] + (lat - a["lat"]) * (b["lon"] - a["lon"]) / (b["lat"] - a["lat"])
            if lon < x:
                res = not res
    return res


# Dom: building=cathedral. Schloss: all buildings inside the castle area
# way/1202607461, except the Schlosstheater (way/206908089).
SCHLOSS_AREA = 1202607461
SCHLOSS_EXCLUDE = {206908089}
# other landmarks: Paulustor, Hexenturm, Heertor (a ruin, not a building)
SIGHTS = {46716972, 206897910, 1574239510}


def landmarks():
    """Return (dom, schloss, sights, other_buildings) geometries from lupe-osm.json."""
    detail = load("lupe-osm.json")
    area = next(e["geometry"] for e in detail if e["id"] == SCHLOSS_AREA)
    dom, schloss, sights, other = [], [], [], []
    for e in detail:
        t, g = e.get("tags", {}), e.get("geometry")
        if g and e["id"] in SIGHTS:
            sights.append(g)
            continue
        if not g or "building" not in t:
            continue
        if t["building"] == "cathedral":
            dom.append(g)
        elif e["id"] not in SCHLOSS_EXCLUDE and inside(centroid(g), area):
            schloss.append(g)
        else:
            other.append(g)
    return dom, schloss, sights, other


def detail():
    """Small map features for the detail lens, from detail-osm.json.
    Return a dict: kind -> list of geometries (trees and node fountains: (lat, lon))."""
    out = {k: [] for k in ("grass", "wood", "flowerbed", "water", "fountain",
                           "path", "hedge", "tree_row", "tree")}
    for e in load("detail-osm.json"):
        t, g = e.get("tags", {}), e.get("geometry")
        if e["type"] == "node":
            if t.get("natural") == "tree":
                out["tree"].append((e["lat"], e["lon"]))
            elif t.get("amenity") == "fountain":
                out["fountain"].append((e["lat"], e["lon"]))
            continue
        if not g:
            continue
        if t.get("amenity") == "fountain" or t.get("natural") == "water" or "water" in t:
            out["water"].append(g)
        elif t.get("landuse") == "flowerbed":
            out["flowerbed"].append(g)
        elif t.get("natural") in ("wood", "scrub") or t.get("landuse") == "orchard":
            out["wood"].append(g)
        elif (t.get("leisure") in ("garden", "playground", "pitch")
              or t.get("landuse") in ("grass", "meadow")):
            out["grass"].append(g)
        elif t.get("barrier") == "hedge":
            out["hedge"].append(g)
        elif t.get("natural") == "tree_row":
            out["tree_row"].append(g)
        elif t.get("highway") in ("footway", "path", "pedestrian", "steps", "cycleway", "track"):
            out["path"].append(g)
    return out
