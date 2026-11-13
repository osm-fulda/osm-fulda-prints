#!/usr/bin/env python3
"""Mitmachkarte 55x85 mm hochkant, doppelseitig – für Leute, die schon angebissen haben und mehr wollen.

Vorderseite: Logo, Frage und Antwort („Wir haben dich angefixt? Jetzt kommst du da nicht wieder raus.“) – im Stil der Motivkarten.
Rückseite:   6 QR-Codes in drei Gruppen, geordnet nach dem nächsten Schritt:
             Loslegen (App, Orte) · Mehr machen (am PC, Fotos) · Mitreden (Chat, Wiki).

Erzeugt mitmachkarte-vorne/-hinten.svg + .png (hochkant), mitmachkarte.pdf (2 Seiten, mit Beschnitt,
für Druckereien) und den Druckbogen mitmachkarte-a4.pdf (gewohntes Raster 2x5, Karten darin gedreht,
beidseitig, an langer Kante spiegeln – siehe druck.card_page_rotated).

ACHTUNG: überschreibt die SVGs. Nach Handarbeit in Inkscape an den Hochkant-SVGs müssen die gedrehten
Bogen-SVGs (bogen-vorne/-hinten.svg) neu erzeugt werden – am einfachsten die Änderung hier im Skript machen.
"""
import os
import sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gemeinsam"))
import druck  # noqa: E402
import make_a4  # noqa: E402
from druck import cap_height, logo_svg, qr_path, text_width  # noqa: E402

W, H = druck.H, druck.W      # hochkant: 55 x 85
SAFE = 3.5                   # Sicherheitsabstand innen
INK, GREY, ACCENT = druck.INK, druck.GREY, druck.ACCENT

FRONT = {
    "kicker": "OPENSTREETMAP FULDA",
    "head": ["Wir haben dich", "angefixt?"],
    "head2": ["Jetzt kommst du da", "nicht wieder raus."],     # Antwort auf die Frage, wie am Aufsteller
    "sub": ["Hinten findest du alles,", "was du zum Loslegen brauchst."],
}

GROUPS = [  # (Überschrift, [(Label, Adresse zum Abtippen, URL), …]) – je zwei Codes nebeneinander
    ("LOSLEGEN", [("Lücken füllen", druck.SHOW_STREETCOMPLETE, druck.go("m/streetcomplete")),
                  ("Orte finden", druck.SHOW_OSMAPP, druck.go("m/osmapp"))]),
    ("MEHR MACHEN", [("Am PC bearbeiten", druck.SHOW_OSM_ORG, druck.go("m/osm")),
                     ("Fotos beitragen", druck.SHOW_PANORAMAX, druck.go("m/panoramax"))]),
    ("MITREDEN", [("Chatte mit uns", druck.SHOW_MATRIX, druck.go("m/chat")),
                  ("Fulda im Wiki", druck.SHOW_WIKI, druck.go("m/wiki"))]),
]

QR_SIZE = 14.5
HEAD_SIZE = 2.3              # Gruppenüberschrift, gesperrt
HEAD_SPACING = 0.6
LABEL_SIZE = 2.7
SUB_SIZE = 2.1
GROUP_GAP = 3.6              # zwischen den Gruppen


def text(x, y, s, size, weight=400, fill=INK, anchor="start", spacing=None):
    sp = f' letter-spacing="{spacing:.3f}"' if spacing else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size:.3f}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{sp}>{escape(s)}</text>')


def fit(lines, weight, max_size, width):
    return min(max_size, *(max_size * width / text_width(l, weight, max_size) for l in lines))


def centered_lines(out, y, lines, size, weight, fill=INK, lead=1.12):
    """Feste Zeilen mittig; y = Oberkante. Gibt die letzte Grundlinie zurück."""
    y += cap_height(weight, size)
    for i, l in enumerate(lines):
        assert text_width(l, weight, size) <= W - 2 * SAFE + 0.01, ("zu breit", l)
        out.append(text(W / 2, y + i * size * lead, l, size, weight, fill, "middle"))
    return y + (len(lines) - 1) * size * lead


def front():
    """Wie die klassische Motivkarte: Logo, Schriftzug, Satz – nur mit Frage und Antwort statt Aufhänger."""
    out = []
    ls = 24
    y = 7
    out.append(logo_svg((W - ls) / 2, y, ls))
    y += ls + 3 + cap_height(500, 2.6)
    out.append(text(W / 2 + 0.55 / 2, y, FRONT["kicker"], 2.6, 500, GREY, "middle", spacing=0.55))
    hs = fit(FRONT["head"] + FRONT["head2"], 700, 8.0, W - 2 * SAFE)
    y = centered_lines(out, y + 4.5, FRONT["head"], hs, 700, lead=1.1)
    y = centered_lines(out, y + 5.0, FRONT["head2"], hs, 700, lead=1.1)
    y = centered_lines(out, y + 3.4, FRONT["sub"], 3.4, 500, ACCENT, lead=1.25)
    assert y < H - SAFE - 2, ("Vorderseite zu voll", round(y, 1))
    return "#fff", out


def group_height():
    return (cap_height(600, HEAD_SIZE) + 2.2 + QR_SIZE + 1.0 + cap_height(600, LABEL_SIZE)
            + 0.9 + cap_height(500, SUB_SIZE))


def back():
    """Drei Gruppen untereinander, je Überschrift mit Linien links und rechts, darunter zwei Codes."""
    out = []
    gh = group_height()
    total = len(GROUPS) * gh + (len(GROUPS) - 1) * GROUP_GAP
    assert total <= H - 2 * SAFE, ("Rückseite zu hoch", round(total, 1))
    y = (H - total) / 2
    cell = (W - 2 * SAFE) / 2
    line = 'stroke="#bbb" stroke-width="0.2"'
    for head, codes in GROUPS:
        hy = y + cap_height(600, HEAD_SIZE)
        out.append(text(W / 2 + HEAD_SPACING / 2, hy, head, HEAD_SIZE, 600, GREY, "middle", spacing=HEAD_SPACING))
        half = text_width(head, 600, HEAD_SIZE, HEAD_SPACING) / 2 + 1.8
        ly = hy - cap_height(600, HEAD_SIZE) / 2
        out.append(f'<line x1="{SAFE + 1}" y1="{ly:.2f}" x2="{W / 2 - half:.2f}" y2="{ly:.2f}" {line}/>')
        out.append(f'<line x1="{W / 2 + half:.2f}" y1="{ly:.2f}" x2="{W - SAFE - 1}" y2="{ly:.2f}" {line}/>')
        qy = hy + 2.2
        for i, (label, show, url) in enumerate(codes):
            cx = SAFE + cell * (i + 0.5)
            d, ver, n, module = qr_path(url, cx - QR_SIZE / 2, qy, QR_SIZE)
            print(f"  {label:17} v{ver:<2} {n}x{n} Module, {module:.2f} mm/Modul")
            out.append(f'<path d="{d}" fill="#000"/>')
            # Ruhezone 4 Module: zwischen den Codes und zum Rand frei
            assert cell - QR_SIZE >= 2 * 4 * module - 0.01, "Codes stehen zu eng"
            lyb = qy + QR_SIZE + 1.0 + cap_height(600, LABEL_SIZE)
            out.append(text(cx, lyb, label, LABEL_SIZE, 600, INK, "middle"))
            out.append(text(cx, lyb + 0.9 + cap_height(500, SUB_SIZE), show, SUB_SIZE, 500, GREY, "middle"))
            for s, wgt, size in [(label, 600, LABEL_SIZE), (show, 500, SUB_SIZE)]:
                assert text_width(s, wgt, size) <= cell - 0.6, ("Text zu breit", s)
        y += gh + GROUP_GAP
    return "#fff", out


def main():
    os.chdir(HERE)
    druck.use_project_fonts()
    print("Rückseite:")
    sides = {"vorne": front(), "hinten": back()}
    for side, (bg, body) in sides.items():
        with open(f"mitmachkarte-{side}.svg", "w") as f:
            f.write(druck.card_page_upright(bg, body))
        with open(f"bogen-{side}.svg", "w") as f:
            f.write(druck.card_page_rotated(bg, body, side))
        druck.png(f"mitmachkarte-{side}.svg", f"mitmachkarte-{side}.png")
    druck.pdf(["mitmachkarte-vorne.svg", "mitmachkarte-hinten.svg"], "mitmachkarte.pdf")
    make_a4.build("bogen-vorne.svg", "bogen-hinten.svg", "mitmachkarte-a4.pdf")


if __name__ == "__main__":
    main()
