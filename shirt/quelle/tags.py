#!/usr/bin/env python3
"""Generate the OSM tagging prints in the style of the iD feature editor.

Usage: python3 tags.py FONT_DIR
FONT_DIR must contain IBMPlexMono-Bold.ttf
(https://github.com/google/fonts/tree/main/ofl/ibmplexmono) and
BarlowCondensed-Bold.ttf.

Designs:
  tags-fulda-hell          the real Fulda place node (node/240088844) with its
                           tags and relations, from fulda-node-osm.json
                           (Overpass result of fulda-node.overpassql)
  tags-mapper-hell         the wearer as a mapper "object", with name=FIXME (a
                           strip of masking tape with the real name can cover it)
  tags-mapper-NAME-hell    the same with name=NAME, one file for each line of
                           mapper-namen.txt (optional, one OSM user name per line)

Each print is 28 cm wide, centred at the top of the print area.
"""
import json, os, re, sys
from common import HERE, PNG_OUT, AREA_MM, text_path, svg, export

FONTS = sys.argv[1]
MONO = os.path.join(FONTS, "IBMPlexMono-Bold.ttf")
BOLD = os.path.join(FONTS, "BarlowCondensed-Bold.ttf")

COL = dict(key="#2d3335", value="#2f6b2a", frame="#8a9499", text="#2d3335")
WIDTH_MM = 280  # print width; 1 SVG unit = 1 mm
TOP_MM = 20     # distance from the top of the print area
LINE = 1.4      # frame line width (DTF film needs >= 1 mm)
BIN_W = 26.0    # delete icon column width
PAD = 6.0       # text padding in a cell
MAX_EM = 20.0   # largest monospace font size; cap height ~0.7 em
CHAR = 0.6      # IBM Plex Mono advance width in em
NAME_CHARS = 16 # all mapper prints reserve space for user names up to this length


# --- content ---------------------------------------------------------------

def fulda():
    """The real Fulda place node: a selection of its tags and its relations."""
    els = json.load(open(os.path.join(HERE, "fulda-node-osm.json")))["elements"]
    node = next(e for e in els if e["type"] == "node")
    t = node["tags"]
    tags = [(k, t[k]) for k in ("place", "name", "name:prefix", "population", "wikipedia")]
    rels = []
    for e in els:
        if e["type"] == "relation":
            role = next(m["role"] for m in e["members"]
                        if m["type"] == "node" and m["ref"] == node["id"])
            rels.append((e["tags"]["name"], role))
    # Landkreis first (admin_level 6), then the town boundary (8)
    rels.sort(key=lambda r: r[0] != "Landkreis Fulda")
    return "Stadt", "node/%d" % node["id"], [("Tags", tags), ("Relationen", rels)], 0


def mapper(name=None):
    """The wearer as a mapper: only real OSM keys, read for a person.
    The preset header says MAPPER, so no extra main tag is needed."""
    tags = [("name", name or "FIXME"),         # FIXME: the classic OSM placeholder
            ("source", "survey"),              # mapped on site
            ("maxspeed", "walk"),              # walking speed: mappers survey on foot
            ("opening_hours", "24/7"),         # always on duty
            ("drinking_water", "yes"),         # equipment: water bottle
            ("power_supply", "yes"),           # equipment: power bank
            ("covered", "yes")]                # equipment: rain jacket
    return ("Mapper", None, [("Tags", tags), ("Relationen", [("OSM Fulda", "member")])],
            NAME_CHARS)


# --- drawing -----------------------------------------------------------------

def text(s, size, x, y, col):
    d, w = text_path(s, MONO, size)
    return '<path fill="%s" transform="translate(%.2f %.2f)" d="%s"/>' % (col, x, y, d)


def caps(s, cap, x, y, col, track=0.1):
    """Barlow Condensed Bold line with the given cap height, baseline at y."""
    d, w = text_path(s, BOLD, 100, track)
    sc = cap / 70.0
    return ('<path fill="%s" transform="translate(%.2f %.2f) scale(%s)" d="%s"/>'
            % (col, x, y, sc, d)), w * sc


def frame(x, y, w, h, r=4.0):
    return ('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%s" fill="none" '
            'stroke="%s" stroke-width="%s"/>' % (x, y, w, h, r, COL["frame"], LINE))


def hline(x0, x1, y):
    return '<path d="M%.2f %.2f H%.2f" stroke="%s" stroke-width="%s"/>' % (x0, y, x1, COL["frame"], LINE)


def vline(x, y0, y1):
    return '<path d="M%.2f %.2f V%.2f" stroke="%s" stroke-width="%s"/>' % (x, y0, y1, COL["frame"], LINE)


def bin_icon(cx, cy):
    """Trash can icon, 12 mm high, line art."""
    return ('<path fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
            'stroke-linejoin="round" transform="translate(%.2f %.2f)" '
            'd="M-6 -4 h12 M-2 -4 v-2 h4 v2 M-4 -4 l1 9 h6 l1 -9 M-1 -1.5 v5 M1 -1.5 v5"/>'
            % (COL["frame"], LINE, cx, cy))


def plus_button(y):
    return (frame(0, y, 24, 20, 3)
            + '<path d="M12 %.2f v10 M7 %.2f h10" stroke="%s" stroke-width="%s" '
              'stroke-linecap="round"/>' % (y + 5, y + 10, COL["frame"], LINE + 0.4))


def layout(sections, min_right):
    """Font size and left column width so that the longest texts fit.
    min_right: reserve the right column for at least this many characters."""
    left = max(len(a) for _, rows in sections for a, _ in rows)
    right = max([min_right] + [len(b) for _, rows in sections for _, b in rows])
    em = min(MAX_EM, (WIDTH_MM - BIN_W - 4 * PAD) / (CHAR * (left + right)))
    return em, left * CHAR * em + 2 * PAD


def editor(preset, ident, sections, min_right):
    em, left_w = layout(sections, min_right)
    row = em * 1.5
    cap = 0.7 * em
    o = []
    # preset header: preset name, object id on the right
    t, _ = caps(preset.upper(), 16, 0, 16, COL["text"], 0.08)
    o.append(t)
    if ident:
        d, w = text_path(ident, MONO, 11)
        o.append('<path fill="%s" transform="translate(%.2f 16)" d="%s"/>'
                 % (COL["frame"], WIDTH_MM - w, d))
    y = 24
    o.append(hline(0, WIDTH_MM, y))
    for title, rows in sections:
        # section heading: disclosure triangle + title (count)
        y += 12
        o.append('<path fill="%s" d="M0 %.2f h11 l-5.5 7z"/>' % (COL["text"], y))
        o.append(caps("%s (%d)" % (title.upper(), len(rows)), 11, 16, y + 7, COL["text"])[0])
        y += 15
        h = row * len(rows)
        o += [frame(0, y, WIDTH_MM, h), vline(left_w, y, y + h), vline(WIDTH_MM - BIN_W, y, y + h)]
        for i, (a, b) in enumerate(rows):
            top = y + i * row
            if i:
                o.append(hline(0, WIDTH_MM, top))
            base = top + row / 2 + cap / 2
            o.append(text(a, em, PAD, base, COL["key"]))
            o.append(text(b, em, left_w + PAD, base, COL["value"]))
            o.append(bin_icon(WIDTH_MM - BIN_W / 2, top + row / 2))
        y += h + 6
        o.append(plus_button(y))
        y += 20 + 4
    y += 12 + 8
    o.append(caps("OPENSTREETMAP FULDA", 8, 0, y, COL["text"], 0.12)[0])
    return "\n".join(o), y + 2


def write(name, design):
    body, h = editor(*design)
    # 2 mm margin so that frame lines on the edge are not cut
    w, h = WIDTH_MM + 4, round(h + 4, 2)
    svg_file = os.path.join(HERE, name + ".svg")
    open(svg_file, "w").write(svg("%smm" % w, "%smm" % h, body, "-2 -2 %s %s" % (w, h)))
    export(svg_file, os.path.join(PNG_OUT, name + ".png"), w, (AREA_MM[0] - w) / 2, TOP_MM)
    print("ok, %s %.0f x %.0f mm" % (name, w, h))


write("tags-fulda-hell", fulda())
write("tags-mapper-hell", mapper())
names = os.path.join(HERE, "mapper-namen.txt")
if os.path.exists(names):
    for user in filter(None, (l.strip() for l in open(names, encoding="utf-8"))):
        slug = re.sub(r"[^A-Za-z0-9_-]+", "_", user)
        write("tags-mapper-%s-hell" % slug, mapper(user))
