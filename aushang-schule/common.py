#!/usr/bin/env python3
"""Gemeinsame Bausteine der Schul-Aushänge (A4 hoch): Text, QR-Feld unten, Seite, Bauen.

Schrift, Farben und QR-Codes kommen aus ../gemeinsam (druck.py). Alle Maße in mm.
"""
import os
import sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gemeinsam"))
import druck  # noqa: E402
import make_a4  # noqa: E402

W, H, M = 210, 297, 16
TW = W - 2 * M
INK, GREY = druck.INK, druck.GREY


def text(x, y, s, size, weight=400, fill=INK, anchor="start"):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}">{escape(s)}</text>')


def paragraph(out, x, y, s, size, width, weight=400, fill=INK, lead=1.3):
    """y = Oberkante. Gibt die letzte Grundlinie zurück."""
    base = y + druck.cap_height(weight, size)
    lines = druck.wrap(s, weight, size, width)
    for i, line in enumerate(lines):
        out.append(text(x, base + i * size * lead, line, size, weight, fill))
    return base + (len(lines) - 1) * size * lead


def cap(weight, size):
    return druck.cap_height(weight, size)


def fit(lines, weight, max_size, width=TW):
    return min(max_size, *(max_size * width / druck.text_width(l, weight, max_size) for l in lines))


def qr_block(out, x, y, size, bg="#fff"):
    """QR-Code mit weißer Ruhezone von 4 Modulen (ISO/IEC 18004). Gibt die Ruhezone in mm zurück."""
    d, _, _, module = druck.qr_path(druck.URL_STREETCOMPLETE, x, y, size)
    pad = 4 * module
    out.append(f'<rect x="{x - pad:.2f}" y="{y - pad:.2f}" width="{size + 2 * pad:.2f}" '
               f'height="{size + 2 * pad:.2f}" rx="2" fill="{bg}"/>')
    out.append(f'<path d="{d}" fill="#000"/>')
    return pad


def bottom(out, fg, sub, accent, line1, line2, qs=36, s1=6.2, s2=4.8, w1=600, rule_in_text=False, qr_right=False, url_label=None):
    """QR-Code unten mit Text daneben und Fußzeile. Ruhezone bündig am Rand.

    qr_right=True: Text links an der Satzkante wie der Rest des Blatts, QR-Code rechts unten –
    dort endet die Leserichtung (Z-Muster), also genau da, wo man handeln soll.
    """
    foot = H - M + 3
    qy = foot - 11 - qs
    module = druck.qr_path(druck.URL_STREETCOMPLETE, 0, 0, qs)[3]
    if qr_right:
        pad = qr_block(out, W - M - qs - 4 * module, qy, qs)
        tx = M
        tw = W - M - qs - 2 * pad - 8 - M
    else:
        pad = qr_block(out, M + 4 * module, qy, qs)
        tx = M + qs + 2 * pad + 8
        tw = W - M - tx
    if isinstance(line1, list):     # feste Zeilen nach Sinn statt automatischem Umbruch
        y = qy + 1 + cap(w1, s1)
        for i, l in enumerate(line1):
            assert druck.text_width(l, w1, s1) <= tw, l
            out.append(text(tx, y + i * s1 * 1.15, l, s1, w1, fg))
        y += (len(line1) - 1) * s1 * 1.15
    else:
        y = paragraph(out, tx, qy + 1, line1, s1, tw, w1, fg, 1.15)
    y = paragraph(out, tx, y + 3.5, line2, s2, tw, 500, sub, 1.3)
    rule = "Einzige Regel: Nur eintragen, was es wirklich gibt."
    if rule_in_text:        # Regel direkt unter den Text statt klein in die Fußzeile
        y = paragraph(out, tx, y + 3, rule, s2, tw, 600, fg, 1.3)   # dunkel, damit es sich von der grünen Adresse abhebt
    out.append(text(tx, qy + qs, url_label or druck.SHOW_STREETCOMPLETE, 5.2, 700, accent))
    out.append(text(M, foot, "OpenStreetMap-Community Fulda · osm.wiki/Fulda", 3.6, 500, sub))
    if not rule_in_text:
        out.append(text(W - M, foot, rule, 3.6, 500, sub, "end"))
    assert y < qy + qs - 6, ("Text am QR-Code zu lang", round(y, 1), round(qy + qs - 6, 1))
    return qy - pad     # Oberkante des weißen QR-Felds


def page(bg, body):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{bg}"/>',
        f'<g font-family="{druck.FONT}">', *body, "</g></svg>",
    ])


def build(name, svg_text):
    """SVG schreiben, Vorschau-PNG und komprimiertes PDF daraus erzeugen."""
    os.chdir(HERE)
    with open(f"{name}.svg", "w") as f:
        f.write(svg_text)
    druck.png(f"{name}.svg", f"{name}.png", dpi=110)
    druck.pdf([f"{name}.svg"], f"{name}-roh.pdf")
    make_a4.compress(f"{name}-roh.pdf", f"{name}.pdf")
    os.remove(f"{name}-roh.pdf")
    print(name, "ok")
