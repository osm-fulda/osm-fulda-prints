#!/usr/bin/env python3
"""Infokarte 85x55 mm, einseitig – zum Liegenlassen (Wartezimmer, Café ...).

Anders als die Visitenkarte richtet sie sich an Leute, die OSM noch nicht kennen:
Wiedererkennung (Logo + Titel), ein Satz als Aufhänger, kurze Erklärung, 2 QR-Codes.

Erzeugt infokarte.svg / .png / .pdf und den A4-Bogen infokarte-a4.pdf (einseitig).
ACHTUNG: überschreibt infokarte.svg – nach Handarbeit nur noch
`python3 ../gemeinsam/make_a4.py infokarte.svg -o infokarte-a4.pdf` laufen lassen.
"""
import os
import sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gemeinsam"))
import druck  # noqa: E402
import make_a4  # noqa: E402
from druck import GREY, H, INK, W, cap_height, logo_svg, qr_path, text_width, wrap  # noqa: E402

SAFE = 3.5
HEADLINE = ["Du nutzt diese Karte", "vermutlich schon."]   # Zeilen des Aufhängers
KICKER = "OPENSTREETMAP FULDA"   # kleine Zeile darüber
BODY = ("OpenStreetMap gehört keinem Konzern, sondern uns allen – niemand verdient "
        "an deinen Daten. Sie steckt in vielen Apps. Was fehlt, trägst du selbst ein.")
CODES = [  # (Label, Untertitel, URL)
    ("Was ist OSM?", "openstreetmap.de", druck.URL_OSM),
    ("Mach mit!", "Wiki Fulda", druck.URL_WIKI),
]

LOGO = 25.0          # Logo oben links, groß
KICKER_SIZE = 2.4    # Schriftgröße Kickerzeile
KICKER_SPACING = 0.45
HEAD_MAX = 6.4       # max. Schriftgröße Aufhänger
HEAD_LEAD = 1.12
BODY_SIZE = 3.2
BODY_LEAD = 1.3
QR = 17.0
QR_GAP = 4.0         # Abstand zwischen den beiden Codes
LABEL = 2.9
SUB = 2.2


def text(x, y, s, size, weight, fill=INK, anchor="start", spacing=None):
    sp = f' letter-spacing="{spacing:.3f}"' if spacing else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size:.3f}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{sp}>{escape(s)}</text>')


def card():
    out = []
    # Kopf: großes Logo links; rechts kleine Kickerzeile + Aufhänger (zweizeilig) als Hauptelement
    lx = lgy = SAFE - 1.0                 # Logo-SVG hat etwas Luft am Rand
    out.append(logo_svg(lx, lgy, LOGO))
    tx = lx + LOGO + 1.5
    tw = W - SAFE - tx
    hs = min(HEAD_MAX, *(HEAD_MAX * tw / text_width(l, 700, HEAD_MAX) for l in HEADLINE))
    ck, ch = cap_height(500, KICKER_SIZE), cap_height(700, hs)
    block = ck + 2.2 + ch + (len(HEADLINE) - 1) * hs * HEAD_LEAD
    yk = lgy + (LOGO - block) / 2 + ck    # Block vertikal mittig zum Logo
    out.append(text(tx, yk, KICKER, KICKER_SIZE, 500, GREY, spacing=KICKER_SPACING))
    yh = yk + 2.2 + ch
    for i, line in enumerate(HEADLINE):
        out.append(text(tx, yh + i * hs * HEAD_LEAD, line, hs, 700))
    yh += (len(HEADLINE) - 1) * hs * HEAD_LEAD

    # QR-Codes unten rechts
    label_h = 0.8 + cap_height(600, LABEL) + 0.9 + cap_height(500, SUB)
    qy = H - SAFE - label_h - QR
    xr = W - SAFE - QR
    xs = [xr - QR - QR_GAP, xr]
    for x, (lab, sub, url) in zip(xs, CODES):
        d, ver, n, s = qr_path(url, x, qy, QR)
        print(f"  {lab:14} v{ver} {n}x{n}, {s:.2f} mm/Modul")
        out.append(f'<path d="{d}" fill="#000"/>')
        cx = x + QR / 2
        ly = qy + QR + 0.8 + cap_height(600, LABEL)
        out.append(text(cx, ly, lab, LABEL, 600, anchor="middle"))
        out.append(text(cx, ly + 0.9 + cap_height(500, SUB), sub, SUB, 500, GREY, anchor="middle"))

    # Fließtext links neben den Codes
    bw = xs[0] - 3.0 - SAFE
    lines = wrap(BODY, 400, BODY_SIZE, bw)
    y = max(yh + 3.2, lgy + LOGO + 0.5) + cap_height(400, BODY_SIZE)
    for i, line in enumerate(lines):
        out.append(text(SAFE, y + i * BODY_SIZE * BODY_LEAD, line, BODY_SIZE, 400))
    bottom = y + (len(lines) - 1) * BODY_SIZE * BODY_LEAD
    assert bottom <= H - SAFE, f"Text zu lang ({bottom:.1f} mm)"
    assert qy >= yh + 2.5, "QR-Codes stoßen an den Aufhänger"
    return out


def main():
    os.chdir(HERE)
    druck.use_project_fonts()
    with open("infokarte.svg", "w") as f:
        f.write(druck.card_page(card()))
    druck.png("infokarte.svg", "infokarte.png")
    druck.pdf(["infokarte.svg"], "infokarte.pdf")
    make_a4.build("infokarte.svg", None, "infokarte-a4.pdf")


if __name__ == "__main__":
    main()
