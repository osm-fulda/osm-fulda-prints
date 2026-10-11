"""Gemeinsame Bausteine für die OSM-Fulda-Drucksachen.

Schrift Barlow Condensed (OFL, ./fonts), Logo und Titelbild (./assets), QR-Codes als Vektor,
Text-Messung für Zeilenumbruch und Ausrichtung. Alle Maße in mm.
"""
import base64
import os
import subprocess

import qrcode
from fontTools.ttLib import TTFont
from qrcode.constants import ERROR_CORRECT_M

DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(DIR, "fonts")
LOGO = os.path.join(DIR, "assets", "osm-fulda-logo.svg")
BANNER = os.path.join(DIR, "assets", "titelbild.png")
BANNER_RATIO = 2048 / 1280

FONT = "Barlow Condensed"
INK = "#2d3335"        # Textfarbe wie im Titelbild (QR-Codes bleiben reinschwarz)
GREY = "#666"
ACCENT = "#3f7d32"     # Grün passend zur Karte im Titelbild

W, H = 85, 55          # Kartenformat
BLEED = 3              # Beschnitt rundum

URL_OSM = "https://openstreetmap.de/osm/"
URL_WIKI = "https://wiki.openstreetmap.org/wiki/Fulda"
URL_MATRIX = "https://matrix.to/#/#osm-fulda-space:shivering-isles.com"
URL_STREETCOMPLETE = "https://streetcomplete.app/"
URL_OSMAPP = "https://osmapp.org/de"
URL_PANORAMAX = "https://panorama.osm-fulda.de/"

# --- Schrift -----------------------------------------------------------------

WEIGHT_FILES = {700: "Bold", 600: "SemiBold", 500: "Medium", 400: "Regular"}
_fonts = {}


def font(weight):
    if weight not in _fonts:
        _fonts[weight] = TTFont(os.path.join(FONT_DIR, f"BarlowCondensed-{WEIGHT_FILES[weight]}.ttf"))
    return _fonts[weight]


def text_width(text, weight, size, spacing=0.0):
    """Breite in mm (ohne Kerning), Laufweite nur zwischen den Zeichen."""
    f = font(weight)
    cmap, hmtx, upem = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    adv = sum(hmtx[cmap[ord(ch)]][0] for ch in text)
    return adv / upem * size + spacing * (len(text) - 1)


def cap_height(weight, size):
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


def use_project_fonts():
    """Schriften aus ./fonts für rsvg-convert verfügbar machen, ohne sie zu installieren."""
    conf = os.path.join(FONT_DIR, "fonts.conf")
    with open(conf, "w") as f:
        f.write(f'<?xml version="1.0"?>\n<fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
                f'<dir>{FONT_DIR}</dir></fontconfig>\n')
    os.environ["FONTCONFIG_FILE"] = conf


# --- Grafik ------------------------------------------------------------------

def qr_path(data, x0, y0, size):
    """QR-Code als SVG-Pfad (Fehlerkorrektur M, ohne Ruhezone). -> (d, version, module, mm/modul)"""
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=0)
    qr.add_data(data)
    qr.make(fit=True)
    m = qr.get_matrix()
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
    return "".join(parts), qr.version, n, s


def logo_svg(x, y, size, dpi=1200):
    """Logo als opakes PNG auf Weiß einbetten.

    Das Logo hat weichgezeichnete Schatten und halbtransparente Verläufe. Als Vektor landen die
    im PDF als Soft-Masks, die viele Druckertreiber als grauen Kasten ums Logo drucken.
    Vorab gerendert ohne Transparenz gibt es das Problem nicht (Karten sind weiß hinterlegt).
    """
    px = round(size / 25.4 * dpi)
    data = subprocess.run(["rsvg-convert", "-b", "white", "-w", str(px), "-h", str(px), LOGO],
                          check=True, capture_output=True).stdout
    href = "data:image/png;base64," + base64.b64encode(data).decode()
    return f'<image x="{x:.2f}" y="{y:.2f}" width="{size}" height="{size}" href="{href}"/>'


def card_page(body):
    """Karten-SVG 85x55 mm + Beschnitt; body in Kartenkoordinaten (0,0 = Endformat-Ecke)."""
    pw, ph = W + 2 * BLEED, H + 2 * BLEED
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{pw}mm" height="{ph}mm" viewBox="0 0 {pw} {ph}">',
        f'<rect width="{pw}" height="{ph}" fill="#fff"/>',
        f'<g transform="translate({BLEED},{BLEED})" font-family="{FONT}" fill="{INK}">',
        *body,
        "</g></svg>",
    ])


def png(svg, out, dpi=600):
    subprocess.run(["rsvg-convert", "-d", str(dpi), "-p", str(dpi), "-o", out, svg], check=True)


def pdf(svgs, out):
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", out, *svgs], check=True)
