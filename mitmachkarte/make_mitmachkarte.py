#!/usr/bin/env python3
"""Mitmachkarte 85x55 mm, doppelseitig – für Leute, die schon Interesse haben.

Vorderseite: Titelbild (Banner) mit Rahmen + Quellenhinweis.
Rückseite:   6 QR-Codes – oben Info & Kontakt, unten Tools.

Erzeugt mitmachkarte-vorne/-hinten.svg + .png, mitmachkarte.pdf (2 Seiten, mit Beschnitt)
und den Druckbogen mitmachkarte-a4.pdf (2x5, beidseitig, an langer Kante spiegeln).

ACHTUNG: überschreibt die SVGs. Nach Handarbeit in Inkscape nur noch
`python3 ../gemeinsam/make_a4.py mitmachkarte-vorne.svg mitmachkarte-hinten.svg -o mitmachkarte-a4.pdf`.
"""
import base64
import os
import sys
from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gemeinsam"))
import druck  # noqa: E402
import make_a4  # noqa: E402
from druck import H, W, cap_height, logo_svg, qr_path, text_width  # noqa: E402

FRONT_STYLE = "banner"  # "banner" = Titelbild mit Rahmen, "logo" = Logo + Schriftzug (frühere Fassung)
BANNER_DPI = 450        # Auflösung des eingebetteten Bildes
BANNER_CROP = 0.05      # unteren Bildrand abschneiden (enthält winzigen Quellenhinweis)
ATTRIBUTION = "Kartendaten © OpenStreetMap-Mitwirkende"

CODES = [  # (Label, Untertitel, URL)
    # Reihe 1: Info & Kontakt
    ("Was ist OSM?", "openstreetmap.de", druck.URL_OSM),
    ("Mach mit!", "Wiki", druck.URL_WIKI),
    ("Chatte mit uns", "Matrix", druck.URL_MATRIX),
    # Reihe 2: Tools
    ("Fülle Lücken", "StreetComplete", druck.URL_STREETCOMPLETE),
    ("Finde Orte", "OSMapp", druck.URL_OSMAPP),
    ("Schau dich um", "Panoramax", druck.URL_PANORAMAX),
]

SAFE = 3             # Sicherheitsabstand innen
COLS, ROWS = 3, 2
QR_SIZE = 16.0
LABEL_SIZE = 2.7
LABEL_GAP = 0.8      # QR -> Label
ROW_GAP = 5.0        # Label -> nächster QR (Ruhezone + Trenner)
SEP_LABEL = "TOOLS"  # Trenner vor Reihe 2
SEP_SIZE = 2.2
SEP_COLOR = "#777"
SUB_SIZE = 2.0
SUB_GAP = 0.4        # Label -> Untertitel

# nur für FRONT_STYLE = "logo"
LOGO_SIZE = 40.0
FRONT_LEFT = 6.0
TITLE_W = 33.0
SMALL_RATIO = 0.3
TITLE_GAP = 1.4


def front_banner():
    """Titelbild mit weißem Rand und runden Ecken, lesbarer Quellenhinweis darunter.

    Bild wird verkleinert und als data-URI eingebettet -> SVG ist eigenständig
    (Inkscape, make_a4.py; librsvg lädt keine Dateien außerhalb des SVG-Ordners).
    """
    attr_size = 1.7
    bh = H - 2 * SAFE - 1.0 - attr_size          # sichtbare Bildhöhe
    full_h = bh / (1 - BANNER_CROP)
    bw = full_h * druck.BANNER_RATIO
    x, y = (W - bw) / 2, SAFE
    im = Image.open(druck.BANNER).convert("RGB")
    px = round(bw / 25.4 * BANNER_DPI)
    im = im.resize((px, round(px / druck.BANNER_RATIO)), Image.LANCZOS)
    buf = BytesIO()
    im.save(buf, "JPEG", quality=92, subsampling=0)
    data = base64.b64encode(buf.getvalue()).decode()
    return [
        f'<clipPath id="banner-clip"><rect x="{x:.2f}" y="{y:.2f}" width="{bw:.2f}" height="{bh:.2f}" rx="2"/></clipPath>',
        f'<image href="data:image/jpeg;base64,{data}" x="{x:.2f}" y="{y:.2f}" width="{bw:.2f}" height="{full_h:.2f}" '
        f'clip-path="url(#banner-clip)"/>',
        f'<text x="{W / 2}" y="{H - SAFE:.2f}" font-size="{attr_size}" font-weight="500" fill="{druck.GREY}" '
        f'text-anchor="middle">{escape(ATTRIBUTION)}</text>',
    ]


def front_logo():
    big = TITLE_W / text_width("FULDA", 700, 1)
    small = big * SMALL_RATIO
    sp = (TITLE_W - text_width("OPENSTREETMAP", 500, small)) / 12
    cap_b, cap_s = cap_height(700, big), cap_height(500, small)
    y_small = (H - (cap_s + TITLE_GAP + cap_b)) / 2 + cap_s
    y_big = y_small + TITLE_GAP + cap_b
    logo_x = W - SAFE - LOGO_SIZE
    return [
        f'<text x="{FRONT_LEFT}" y="{y_small:.2f}" font-size="{small:.3f}" font-weight="500" letter-spacing="{sp:.3f}">OPENSTREETMAP</text>',
        f'<text x="{FRONT_LEFT}" y="{y_big:.2f}" font-size="{big:.3f}" font-weight="700">FULDA</text>',
        logo_svg(logo_x, (H - LOGO_SIZE) / 2, LOGO_SIZE),
    ]


def back():
    cell_w = (W - 2 * SAFE) / COLS
    label_h = LABEL_GAP + LABEL_SIZE
    sub_h = SUB_GAP + SUB_SIZE
    rows = [CODES[r * COLS:(r + 1) * COLS] for r in range(ROWS)]
    row_hs = [QR_SIZE + label_h + (sub_h if any(c[1] for c in r) else 0) for r in rows]
    grid_h = sum(row_hs) + ROW_GAP * (ROWS - 1)
    assert grid_h <= H - 2 * SAFE, "Raster zu hoch"
    top = (H - grid_h) / 2
    out = []
    y = top
    for row, codes in enumerate(rows):
        for col, (label, sub, url) in enumerate(codes):
            cx = SAFE + cell_w * (col + 0.5)
            d, ver, n, s = qr_path(url, cx - QR_SIZE / 2, y, QR_SIZE)
            print(f"  {label:16} v{ver:<2} {n}x{n} Module, {s:.2f} mm/Modul")
            out.append(f'<path d="{d}" fill="#000"/>')
            ly = y + QR_SIZE + LABEL_GAP + LABEL_SIZE * 0.8
            out.append(f'<text x="{cx:.2f}" y="{ly:.2f}" font-size="{LABEL_SIZE}" font-weight="600" text-anchor="middle">{escape(label)}</text>')
            if sub:
                out.append(f'<text x="{cx:.2f}" y="{ly + SUB_GAP + SUB_SIZE * 0.85:.2f}" font-size="{SUB_SIZE}" font-weight="500" '
                           f'fill="{druck.GREY}" text-anchor="middle">{escape(sub)}</text>')
        y += row_hs[row] + ROW_GAP
    # Trennlinie zwischen den Reihen, mittig unterbrochen für das Label
    sy = top + row_hs[0] + ROW_GAP / 2
    sep_sp = 0.6
    half_txt = text_width(SEP_LABEL, 600, SEP_SIZE, sep_sp) / 2 + 1.5
    x0, x1 = SAFE + 2, W - SAFE - 2
    line = f'stroke="{SEP_COLOR}" stroke-width="0.2"'
    out.append(f'<line x1="{x0}" y1="{sy:.2f}" x2="{W / 2 - half_txt:.2f}" y2="{sy:.2f}" {line}/>')
    out.append(f'<line x1="{W / 2 + half_txt:.2f}" y1="{sy:.2f}" x2="{x1}" y2="{sy:.2f}" {line}/>')
    out.append(f'<text x="{W / 2}" y="{sy + SEP_SIZE * 0.36:.2f}" font-size="{SEP_SIZE}" fill="{SEP_COLOR}" '
               f'letter-spacing="{sep_sp}" font-weight="600" text-anchor="middle">{escape(SEP_LABEL)}</text>')
    return out


def main():
    os.chdir(HERE)
    druck.use_project_fonts()
    front = front_banner() if FRONT_STYLE == "banner" else front_logo()
    print("Rückseite:")
    for name, body in (("mitmachkarte-vorne", front), ("mitmachkarte-hinten", back())):
        with open(f"{name}.svg", "w") as f:
            f.write(druck.card_page(body))
        druck.png(f"{name}.svg", f"{name}.png")
    druck.pdf(["mitmachkarte-vorne.svg", "mitmachkarte-hinten.svg"], "mitmachkarte.pdf")
    make_a4.build("mitmachkarte-vorne.svg", "mitmachkarte-hinten.svg", "mitmachkarte-a4.pdf")


if __name__ == "__main__":
    main()
