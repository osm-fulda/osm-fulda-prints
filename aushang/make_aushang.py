#!/usr/bin/env python3
"""OSM-Fulda-Flyer A5 – Aushang (Scheibe) und Handzettel.

Eine Vorderseite für beides:
  aushang-a4.pdf                 – Vorderseite beidseitig (von außen und innen lesbar), 2x A5 pro A4
  aushang-mit-rueckseite-a4.pdf  – Vorderseite + Rückseite (Mitmachen), als Handzettel / Vorlage Profidruck
  aushang-vorne.svg/png, aushang-hinten.svg/png – Einzelseiten A5 zur Kontrolle

Schrift, Titelbild und URLs aus ../gemeinsam (druck.py).
"""
import base64
import os
import sys
import tempfile
import subprocess
from xml.sax.saxutils import escape

import qrcode
from fontTools.ttLib import TTFont
from qrcode.constants import ERROR_CORRECT_M

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gemeinsam"))
import druck  # noqa: E402
import make_a4  # noqa: E402

FONT_DIR = druck.FONT_DIR
# Titelbild eingebettet: librsvg lädt keine Dateien außerhalb des SVG-Ordners
with open(druck.BANNER, "rb") as _f:
    BANNER = "data:image/png;base64," + base64.b64encode(_f.read()).decode()
BANNER_RATIO = 2048 / 1280

W, H = 148, 210        # A5 in mm
M = 9                  # Rand (größer als nicht bedruckbarer Druckerrand)
TW = W - 2 * M         # Textbreite
INK = "#2d3335"
GREY = "#666"
ACCENT = "#3f7d32"     # Grün passend zur Karte im Banner

URL_OSM, URL_WIKI, URL_MATRIX = druck.URL_OSM, druck.URL_WIKI, druck.URL_MATRIX

FRONT = {
    "headline": "Du nutzt diese Karte vermutlich schon.",
    "sub": "Gemacht von Menschen wie dir – auch in Fulda.",
    "body": "OpenStreetMap ist die freie Weltkarte hinter vielen Apps und Websites – vom "
            "Fahrradnavi bis zur Wander-App. Jeder Weg, jede Parkbank und jeder Spielplatz darauf "
            "wurde von Freiwilligen eingetragen. Mach mit – oft reicht dein Handy.",
    "codes": [
        ("Was ist OSM?", "openstreetmap.de", URL_OSM),
        ("Mach mit!", "Wiki", URL_WIKI),
        ("Chatte mit uns", "Matrix", URL_MATRIX),
    ],
}

BACK = {
    "headline": "So machst du mit",
    "tools": [
        ("Fülle Lücken", "StreetComplete · App für Android", druck.URL_STREETCOMPLETE,
         "Die App stellt dir einfache Fragen zu deiner Umgebung: Ist der Weg beleuchtet? "
         "Hat das Café eine Rampe? Deine Antwort landet direkt in der Karte."),
        ("Finde Orte", "OSMapp · im Browser", druck.URL_OSMAPP,
         "Orte suchen, Öffnungszeiten nachsehen und Fehler gleich melden oder korrigieren – "
         "direkt im Browser, ohne Installation."),
        ("Schau dich um", "Panoramax · panorama.osm-fulda.de", druck.URL_PANORAMAX,
         "Freie Straßenbilder aus Fulda – wie Street View, nur offen. "
         "Schau dich um oder trag eigene Fotos bei."),
    ],
    "group_head": "Wir in Fulda",
    "group_body": "Wir sind eine offene Gruppe von Mapperinnen und Mappern aus Stadt und "
                  "Landkreis Fulda. Egal ob Neuling oder Profi: Schreib uns, stell Fragen "
                  "oder kartiere mit uns.",
    "codes": [
        ("Chatte mit uns", "Matrix", URL_MATRIX),
        ("Mach mit!", "Wiki", URL_WIKI),
    ],
    "footer": "Kartendaten © OpenStreetMap-Mitwirkende · openstreetmap.org/copyright",
}

# --- Schrift -----------------------------------------------------------------

WEIGHT_FILES = {700: "Bold", 600: "SemiBold", 500: "Medium", 400: "Regular"}
_fonts = {}


def font(weight):
    if weight not in _fonts:
        _fonts[weight] = TTFont(os.path.join(FONT_DIR, f"BarlowCondensed-{WEIGHT_FILES[weight]}.ttf"))
    return _fonts[weight]


def text_width(text, weight, size):
    f = font(weight)
    cmap, hmtx, upem = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap[ord(ch)]][0] for ch in text) / upem * size


def cap(weight, size):
    f = font(weight)
    return f["OS/2"].sCapHeight / f["head"].unitsPerEm * size


def wrap(text, weight, size, width):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and text_width(trial, weight, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur] if cur else lines


def text(x, y, s, size, weight=400, fill=INK, anchor="start"):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}">{escape(s)}</text>')


def paragraph(out, x, y, s, size, width, weight=400, fill=INK, lead=1.3):
    """Fließtext; y = Oberkante. Gibt Unterkante (letzte Grundlinie) zurück."""
    base = y + cap(weight, size)
    for i, line in enumerate(wrap(s, weight, size, width)):
        out.append(text(x, base + i * size * lead, line, size, weight, fill))
    return base + i * size * lead


# --- QR ----------------------------------------------------------------------

def qr(out, url, x0, y0, size):
    q = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=0)
    q.add_data(url)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    s = size / n
    parts = []
    for r, row in enumerate(m):
        c = 0
        while c < n:
            if row[c]:
                start = c
                while c < n and row[c]:
                    c += 1
                parts.append(f"M{x0 + start * s:.4f},{y0 + r * s:.4f}h{(c - start) * s:.4f}v{s:.4f}h{-(c - start) * s:.4f}z")
            else:
                c += 1
    out.append(f'<path d="{"".join(parts)}" fill="#000"/>')
    print(f"  {url[:45]:45} {size:.0f} mm, {s:.2f} mm/Modul")


def qr_row(out, codes, y, size, x0=M, width=TW, label=4.6, sub=3.4):
    cell = width / len(codes)
    for i, (lab, subt, url) in enumerate(codes):
        cx = x0 + cell * (i + 0.5)
        qr(out, url, cx - size / 2, y, size)
        ly = y + size + 1.2 + cap(600, label)
        out.append(text(cx, ly, lab, label, 600, anchor="middle"))
        out.append(text(cx, ly + 1.0 + cap(500, sub), subt, sub, 500, GREY, anchor="middle"))
    return y + size + 1.2 + cap(600, label) + 1.0 + cap(500, sub)


# --- Seiten ------------------------------------------------------------------

def front(uid):
    out = []
    bh = TW / BANNER_RATIO
    out.append(f'<clipPath id="{uid}-banner"><rect x="{M}" y="{M}" width="{TW}" height="{bh:.2f}" rx="3"/></clipPath>')
    out.append(f'<image href="{BANNER}" x="{M}" y="{M}" width="{TW}" height="{bh:.2f}" '
               f'preserveAspectRatio="xMidYMid slice" clip-path="url(#{uid}-banner)"/>')
    y = M + bh + 7
    hs = min(11.0, 11.0 * TW / text_width(FRONT["headline"], 700, 11.0))
    y += cap(700, hs)
    out.append(text(M, y, FRONT["headline"], hs, 700))
    y += 3.2 + cap(500, 6.2)
    out.append(text(M, y, FRONT["sub"], 6.2, 500, ACCENT))
    y = paragraph(out, M, y + 4.5, FRONT["body"], 4.3, TW)
    qs = 34
    row_h = qs + 1.2 + cap(600, 4.6) + 1.0 + cap(500, 3.4)
    top = (y + H - M - row_h) / 2 + 1.5      # Reihe mittig im Restplatz
    assert top >= y + 6, "Vorderseite zu voll"
    qr_row(out, FRONT["codes"], top, qs)
    return out


def back(uid):
    out = []
    y = M + cap(700, 9)
    out.append(text(M, y, BACK["headline"], 9, 700))
    y += 6
    qs = 26
    tx = M + qs + 6
    tw = W - M - tx
    for title, sub, url, desc in BACK["tools"]:
        qr(out, url, M, y, qs)
        ty = y + cap(600, 6)
        out.append(text(tx, ty, title, 6, 600))
        ty += 1.4 + cap(500, 3.6)
        out.append(text(tx, ty, sub, 3.6, 500, GREY))
        paragraph(out, tx, ty + 2.2, desc, 4.0, tw)
        y += qs + 6
    y += 0
    out.append(f'<line x1="{M}" y1="{y:.2f}" x2="{W - M}" y2="{y:.2f}" stroke="#999" stroke-width="0.25"/>')
    y += 6 + cap(700, 7)
    out.append(text(M, y, BACK["group_head"], 7, 700))
    y = paragraph(out, M, y + 3.5, BACK["group_body"], 4.2, TW)
    end = qr_row(out, BACK["codes"], y + 7, 26, x0=M + TW * 0.15, width=TW * 0.7)
    assert end < H - M - 4, f"Rückseite zu voll ({end:.1f} mm)"
    out.append(text(W / 2, H - M, BACK["footer"], 3.0, 400, GREY, anchor="middle"))
    return out


def a5(body):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="#fff"/>',
        f'<g font-family="Barlow Condensed">',
        *body,
        "</g></svg>",
    ])


def a4_two_up(make, guides=False):
    """A4 quer, 2x A5 nebeneinander. Ein Schnitt in der Mitte, Außenkanten = Papierkante.

    guides=True: durchgehende hellgraue Schnittlinie (nur Vorderseite, wegen Duplex-Versatz).
    """
    aw, ah = 297, 210
    x0 = (aw - 2 * W) / 2
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{aw}mm" height="{ah}mm" viewBox="0 0 {aw} {ah}">',
           f'<rect width="{aw}" height="{ah}" fill="#fff"/>']
    for i in range(2):
        out.append(f'<g transform="translate({x0 + i * W:.2f},0)" font-family="Barlow Condensed">')
        out.extend(make(f"p{i}"))
        out.append("</g>")
    mark = 'stroke="#000" stroke-width="0.15"'
    out.append(f'<line x1="{aw / 2}" y1="2" x2="{aw / 2}" y2="7" {mark}/>')
    out.append(f'<line x1="{aw / 2}" y1="{ah - 7}" x2="{aw / 2}" y2="{ah - 2}" {mark}/>')
    if guides:
        out.append(f'<line x1="{aw / 2}" y1="0" x2="{aw / 2}" y2="{ah}" stroke="#aaa" stroke-width="0.1"/>')
    out.append("</svg>")
    return "\n".join(out)


use_project_fonts = druck.use_project_fonts


def render(svg_files, out):
    """PDF rendern und mit Ghostscript komprimieren (Titelbild sonst je Kopie verlustfrei)."""
    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, "roh.pdf")
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", raw, *svg_files], check=True)
        make_a4.compress(raw, out)


def main():
    os.chdir(HERE)
    use_project_fonts()
    print("Vorderseite:")
    with open("aushang-vorne.svg", "w") as f:
        f.write(a5(front("v")))
    print("Rückseite:")
    with open("aushang-hinten.svg", "w") as f:
        f.write(a5(back("h")))
    for n in ("aushang-vorne", "aushang-hinten"):
        subprocess.run(["rsvg-convert", "-d", "300", "-p", "300", "-o", f"{n}.png", f"{n}.svg"], check=True)

    with open("bogen-vorne.svg", "w") as f:
        f.write(a4_two_up(front, guides=True))
    with open("bogen-vorne-ohne-linie.svg", "w") as f:
        f.write(a4_two_up(front))
    with open("bogen-hinten.svg", "w") as f:
        f.write(a4_two_up(back))
    render(["bogen-vorne.svg", "bogen-vorne-ohne-linie.svg"], "aushang-a4.pdf")
    render(["bogen-vorne.svg", "bogen-hinten.svg"], "aushang-mit-rueckseite-a4.pdf")
    print("aushang-a4.pdf, aushang-mit-rueckseite-a4.pdf geschrieben")


if __name__ == "__main__":
    main()
