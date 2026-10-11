#!/usr/bin/env python3
"""OSM-Fulda-Aushang A5 – für Pinnwand, Schwarzes Brett und Schaufenster.

Nur eine Seite. Pinnwand/Brett: einseitig drucken (Seite 1). Glasscheibe: beidseitig, dann ist
die Vorderseite von innen und außen lesbar.
  aushang-a4.pdf                 – 2x A5 pro A4 quer; Seite 1 mit Schnittlinie, Seite 2 = Rückseite für Duplex
  aushang-vorne.svg/png          – Einzelseite A5 zur Kontrolle

Der Flyer (../flyer) nutzt dieselbe Vorderseite und die Bausteine hier, hat aber eine eigene Rückseite.
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
SHIFT = 2.5            # Bogen: beide A5 so weit nach außen. Viele Drucker verkleinern trotz "100 %"
                       # leicht zur Blattmitte (gemessen ~97 %) -> innen/außen sonst ungleich.
                       # Ergebnis innen/außen: 11,5/7 mm bei 100 %, je ~11 mm bei 97 %.
TW = W - 2 * M         # Textbreite
INK = "#2d3335"
GREY = "#666"
ACCENT = "#3f7d32"     # Grün passend zur Karte im Banner

URL_OSM, URL_WIKI, URL_MATRIX = druck.URL_OSM, druck.URL_WIKI, druck.URL_MATRIX

FRONT = {
    "headline": ["Du nutzt diese Karte jeden Tag.", "Ohne es zu wissen."],   # Zeilen
    "sub": "Gemacht von Menschen wie dir – auch in Fulda.",
    "body": "OpenStreetMap ist die freie Weltkarte hinter vielen Apps und Websites – vom "
            "Fahrradnavi bis zur Wander-App. Jeder Weg, jede Parkbank und jeder Spielplatz darauf "
            "wurde von Freiwilligen eingetragen. Mach mit – oft reicht dein Handy.",
    "codes": [
        ("Was ist OSM?", druck.SHOW_OSM, URL_OSM),
        ("Mach mit!", druck.SHOW_WIKI, URL_WIKI),
        ("Chatte mit uns", druck.SHOW_MATRIX, URL_MATRIX),
    ],
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
    for word in text.split(" "):   # nur normale Leerzeichen – \u00a0 hält zusammen
        if not word:
            continue
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

HEAD_MAX, HEAD_LEAD = 11.0, 1.1


def headline_size():
    """Größte Schrift bis HEAD_MAX, bei der jede Zeile der Überschrift in die Breite passt."""
    return min(HEAD_MAX, *(HEAD_MAX * TW / text_width(l, 700, HEAD_MAX) for l in FRONT["headline"]))


def front(uid):
    out = []
    bh = TW / BANNER_RATIO
    out.append(f'<clipPath id="{uid}-banner"><rect x="{M}" y="{M}" width="{TW}" height="{bh:.2f}" rx="3"/></clipPath>')
    out.append(f'<image href="{BANNER}" x="{M}" y="{M}" width="{TW}" height="{bh:.2f}" '
               f'preserveAspectRatio="xMidYMid slice" clip-path="url(#{uid}-banner)"/>')
    y = M + bh + 7
    hs = headline_size()
    y += cap(700, hs)
    for i, line in enumerate(FRONT["headline"]):
        out.append(text(M, y + i * hs * HEAD_LEAD, line, hs, 700))
    y += (len(FRONT["headline"]) - 1) * hs * HEAD_LEAD
    y += 4.5 + cap(500, 6.2)
    out.append(text(M, y, FRONT["sub"], 6.2, 500, ACCENT))
    y = paragraph(out, M, y + 4.5, FRONT["body"], 4.3, TW)
    qs = 34
    row_h = qs + 1.2 + cap(600, 4.6) + 1.0 + cap(500, 3.4)
    top = (y + H - M - row_h) / 2 + 1.5      # Reihe mittig im Restplatz
    assert top >= y + 6, "Vorderseite zu voll"
    qr_row(out, FRONT["codes"], top, qs)
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
        shift = SHIFT if i else -SHIFT
        out.append(f'<g transform="translate({x0 + i * W + shift:.2f},0)" font-family="Barlow Condensed">')
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
    subprocess.run(["rsvg-convert", "-d", "300", "-p", "300", "-o", "aushang-vorne.png", "aushang-vorne.svg"],
                   check=True)
    with open("bogen-vorne.svg", "w") as f:
        f.write(a4_two_up(front, guides=True))
    with open("bogen-vorne-ohne-linie.svg", "w") as f:
        f.write(a4_two_up(front))
    render(["bogen-vorne.svg", "bogen-vorne-ohne-linie.svg"], "aushang-a4.pdf")
    print("aushang-a4.pdf geschrieben")


if __name__ == "__main__":
    main()
