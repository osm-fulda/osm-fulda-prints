#!/usr/bin/env python3
"""OSM-Fulda-Aushang, der klassische – für Pinnwand, Schwarzes Brett und Schaufenster.

Ein QR-Code zum Einstieg (StreetComplete), die Community dezent in der Fußzeile.
Gestaltet auf A5 (148 x 210), gedruckt im Endformat 137 x 194 mm wie die anderen Aushänge
(../gemeinsam/make_a4.py: a5_two_up, zwei pro A4-Bogen, Schnittmarken).

Nur eine Seite. Pinnwand/Brett: einseitig drucken (Seite 1). Glasscheibe: beidseitig, dann ist
die Vorderseite von innen und außen lesbar.
  aushang-klassisch-a4.pdf       – Seite 1 mit Schnittlinien, Seite 2 = dieselbe Seite ohne Linien für Duplex
  aushang-klassisch.svg/png      – Einzelseite zur Kontrolle

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


FRONT = {
    "headline": ["Du nutzt diese Karte jeden Tag.", "Ohne es zu wissen."],   # Zeilen
    "sub": "Gemacht von Menschen wie dir – auch in Fulda.",
    "body": "OpenStreetMap ist die freie Datenbank hinter vielen Karten, Apps und Websites – vom "
            "Fahrradnavi bis zur Wander-App. Jeder Weg, jede Parkbank und jeder Spielplatz darin "
            "wurde von Freiwilligen eingetragen.",
    # Ein QR-Code, und zwar zum Einstieg: StreetComplete (wie die Aushänge in ../aushang-schule).
    # Die Community steht dezent in der Fußzeile, als Text.
    "cta": ["Fehlt was? Trag es ein."],                 # feste Zeilen
    "cta_body": "Die App StreetComplete stellt dir unterwegs kurze Fragen. Ein Fingertipp genügt.",
    "rule": "Einzige Regel: Nur eintragen, was es wirklich gibt.",
    # Absender: Name dunkel, Adressen grün – so groß und auffällig wie bei den anderen Aushängen
    "footer": ("OpenStreetMap-Community Fulda", f"{druck.SHOW_WIKI} · {druck.SHOW_MATRIX}"),
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


# --- Seiten ------------------------------------------------------------------

HEAD_MAX, HEAD_LEAD = 11.0, 1.1


def headline_size():
    """Größte Schrift bis HEAD_MAX, bei der jede Zeile der Überschrift in die Breite passt."""
    return min(HEAD_MAX, *(HEAD_MAX * TW / text_width(l, 700, HEAD_MAX) for l in FRONT["headline"]))


def qr_cta(out, y_bottom):
    """StreetComplete-QR links, Aufforderung rechts daneben; Unterkante des QR-Codes bei y_bottom.

    Ruhezone 4 Module (ISO/IEC 18004): Der Grund ist weiß, links reicht der Seitenrand M dafür,
    darum steht der Code bündig an der Satzkante. Gibt die Oberkante der Ruhezone zurück.
    """
    qs = 36
    module = druck.qr_path(druck.go("a/klassisch"), 0, 0, qs)[3]
    pad = 4 * module
    assert M >= pad, "Seitenrand kleiner als die Ruhezone"
    qx, qy = M, y_bottom - qs
    qr(out, druck.go("a/klassisch"), qx, qy, qs)
    tx = qx + qs + pad + 2
    tw = W - M - tx
    s1, s2 = 7.0, 4.3
    y = qy + cap(700, s1)
    for i, line in enumerate(FRONT["cta"]):
        assert text_width(line, 700, s1) <= tw, line
        out.append(text(tx, y + i * s1 * 1.15, line, s1, 700))
    y += (len(FRONT["cta"]) - 1) * s1 * 1.15
    y = paragraph(out, tx, y + 3, FRONT["cta_body"], s2, tw)
    y = paragraph(out, tx, y + 2.2, FRONT["rule"], s2, tw, 600)
    out.append(text(tx, qy + qs, druck.SHOW_STREETCOMPLETE, 5.4, 700, ACCENT))
    assert y < qy + qs - 5.4 - 2, ("Text am QR-Code zu lang", round(y, 1))
    return qy - pad


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

    foot = H - M
    name, links = FRONT["footer"]
    fs = 3.9                                   # gedruckt (Maßstab 137/148) gut 3,5 mm
    out.append(f'<text x="{M}" y="{foot:.2f}" font-size="{fs}" font-weight="700" fill="{INK}">'
               f'{escape(name)} · <tspan fill="{ACCENT}">{escape(links)}</tspan></text>')
    assert text_width(f"{name} · {links}", 700, fs) <= TW, "Fußzeile zu lang"
    top = qr_cta(out, foot - 8)
    assert top >= y + 6, ("Vorderseite zu voll", round(y, 1), round(top, 1))
    return out


def a5(body):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="#fff"/>',
        f'<g font-family="Barlow Condensed">',
        *body,
        "</g></svg>",
    ])


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
    with open("aushang-klassisch.svg", "w") as f:
        f.write(a5(front("v")))
    subprocess.run(["rsvg-convert", "-d", "300", "-p", "300", "-o", "aushang-klassisch.png", "aushang-klassisch.svg"],
                   check=True)
    with open("bogen-klassisch.svg", "w") as f:
        f.write(make_a4.a5_two_up(front, guides=True))
    with open("bogen-klassisch-ohne-linie.svg", "w") as f:
        f.write(make_a4.a5_two_up(front))
    render(["bogen-klassisch.svg", "bogen-klassisch-ohne-linie.svg"], "aushang-klassisch-a4.pdf")
    print("aushang-klassisch-a4.pdf geschrieben")


if __name__ == "__main__":
    main()
