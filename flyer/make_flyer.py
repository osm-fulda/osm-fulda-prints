#!/usr/bin/env python3
"""OSM-Fulda-Flyer A5, immer zweiseitig: vorne wie der Aushang, hinten "So machst du mit".

Zum Mitnehmen / Weitergeben, auch Vorlage für einen späteren Profidruck.
  flyer-a4.pdf      – 2x A5 pro A4 quer, Duplex an kurzer Kante
  flyer-vorne/-hinten.png – Einzelseiten A5 zur Kontrolle

Vorne wie der Aushang, aber ohne QR-Codes (Hinweis zum Umdrehen) – alle Codes stehen hinten.

Vorderseite und Bausteine (Text, QR, Bogen) kommen aus ../aushang/make_aushang.py.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "aushang"))
from make_aushang import (ACCENT, BANNER, BANNER_RATIO, FRONT, GREY, H, HEAD_LEAD, M, TW, W,  # noqa: E402
                          a4_two_up, a5, cap, druck, headline_size, paragraph, qr, qr_row, render, text,
                          text_width, use_project_fonts, wrap)

TURN = "Dreh mich um – so machst du mit"
BODY, BODY_LEAD = 5.4, 1.45

def front(uid):
    """Vorderseite: Titelbild, Text mittig im Restplatz, unten Hinweis zum Umdrehen. Keine QR-Codes."""
    out = []
    bh = TW / BANNER_RATIO
    out.append(f'<clipPath id="{uid}-banner"><rect x="{M}" y="{M}" width="{TW}" height="{bh:.2f}" rx="3"/></clipPath>')
    out.append(f'<image href="{BANNER}" x="{M}" y="{M}" width="{TW}" height="{bh:.2f}" '
               f'preserveAspectRatio="xMidYMid slice" clip-path="url(#{uid}-banner)"/>')
    turn_y = H - M - 8                        # Mitte der Hinweiszeile
    hs = headline_size()
    heads = FRONT["headline"]
    lines = wrap(FRONT["body"].replace(" – ", "\u00a0– "), 400, BODY, TW)   # Strich nie am Zeilenanfang
    block = (cap(700, hs) + (len(heads) - 1) * hs * HEAD_LEAD + 6 + cap(500, 6.2) + 8 + cap(400, BODY)
             + (len(lines) - 1) * BODY * BODY_LEAD)
    top, bottom = M + bh, turn_y - 8
    y = top + (bottom - top - block) / 2 + cap(700, hs)
    for i, line in enumerate(heads):
        out.append(text(M, y + i * hs * HEAD_LEAD, line, hs, 700))
    y += (len(heads) - 1) * hs * HEAD_LEAD
    y += 6 + cap(500, 6.2)
    out.append(text(M, y, FRONT["sub"], 6.2, 500, ACCENT))
    y += 8 + cap(400, BODY)
    for i, line in enumerate(lines):
        out.append(text(M, y + i * BODY * BODY_LEAD, line, BODY, 400))
    out.extend(turn_hint(TURN, turn_y))
    return out


def turn_hint(s, cy, size=8.0):
    """Hinweis in Grün mit gezeichnetem Pfeil (Schrift hat keine Pfeilzeichen), mittig um cy."""
    gap, aw = 3.0, 9.0
    tw = text_width(s, 700, size)
    x = (W - tw - gap - aw) / 2
    ax = x + tw + gap
    return [text(x, cy + cap(700, size) / 2, s, size, 700, ACCENT),
            f'<path d="M{ax:.2f},{cy:.2f}h{aw - 2.5:.2f}" stroke="{ACCENT}" stroke-width="1.2"/>',
            f'<path d="M{ax + aw:.2f},{cy:.2f}l-3.2,-2.4v4.8z" fill="{ACCENT}"/>']


BACK = {
    "headline": "So machst du mit",
    "tools": [
        ("Fülle Lücken", f"StreetComplete-App für Android · {druck.SHOW_STREETCOMPLETE}", druck.URL_STREETCOMPLETE,
         "Die App stellt dir einfache Fragen zu deiner Umgebung: Ist der Weg beleuchtet? "
         "Hat das Café eine Rampe? Deine Antwort landet direkt in der Karte."),
        ("Finde Orte", f"OSMapp im Browser · {druck.SHOW_OSMAPP}", druck.URL_OSMAPP,
         "Orte suchen, Öffnungszeiten nachsehen und Fehler gleich melden oder korrigieren – "
         "direkt im Browser, ohne Installation."),
        ("Schau dich um", f"Panoramax · {druck.SHOW_PANORAMAX}", druck.URL_PANORAMAX,
         "Freie Straßenbilder aus Fulda – wie Street View, nur offen. "
         "Schau dich um oder trag eigene Fotos bei."),
    ],
    "group_head": "Wir in Fulda",
    "group_body": "Wir sind eine offene Gruppe von Mapper:innen aus Stadt und Landkreis "
                  "Fulda. Egal ob Neuling oder Profi: Schreib uns, stell Fragen "
                  "oder kartiere mit uns.",
    "codes": [
        ("Was ist OSM?", druck.SHOW_OSM, druck.URL_OSM),
        ("Mach mit!", druck.SHOW_WIKI, druck.URL_WIKI),
        ("Chatte mit uns", druck.SHOW_MATRIX, druck.URL_MATRIX),
    ],
    "footer": "Kartendaten © OpenStreetMap-Mitwirkende · openstreetmap.org/copyright",
}


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
    out.append(f'<line x1="{M}" y1="{y:.2f}" x2="{W - M}" y2="{y:.2f}" stroke="#999" stroke-width="0.25"/>')
    y += 6 + cap(700, 7)
    out.append(text(M, y, BACK["group_head"], 7, 700))
    y = paragraph(out, M, y + 3.5, BACK["group_body"], 4.2, TW)
    end = qr_row(out, BACK["codes"], y + 7, 26)
    assert end < H - M - 4, f"Rückseite zu voll ({end:.1f} mm)"
    out.append(text(W / 2, H - M, BACK["footer"], 3.0, 400, GREY, anchor="middle"))
    return out


def main():
    os.chdir(HERE)
    use_project_fonts()
    for name, make in (("vorne", front), ("hinten", back)):
        with open(f"flyer-{name}.svg", "w") as f:
            f.write(a5(make(name[0])))
        druck.png(f"flyer-{name}.svg", f"flyer-{name}.png", dpi=300)
    print("Rückseite (Bogen):")
    with open("bogen-vorne.svg", "w") as f:
        f.write(a4_two_up(front, guides=True))
    with open("bogen-hinten.svg", "w") as f:
        f.write(a4_two_up(back))
    render(["bogen-vorne.svg", "bogen-hinten.svg"], "flyer-a4.pdf")
    print("flyer-a4.pdf geschrieben")


if __name__ == "__main__":
    main()
