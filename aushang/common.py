#!/usr/bin/env python3
"""Gemeinsame Bausteine der Aushänge: Text, QR-Feld unten, Seite, Bauen.

Gezeichnet wird auf A4 hoch (210 x 297, alle Maße in mm); gedruckt werden zwei pro A4-Bogen im
Endformat 137 x 194 mm (A5-Verhältnis), mit Schnittmarken – build() verkleinert. Die Zeichnungen nutzen auch ../motivkarten; der klassische Aushang hat sein eigenes Skript
(make_klassisch.py).
Schrift, Farben und QR-Codes kommen aus ../gemeinsam (druck.py).
"""
import re
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
# Absender unten: Kontakt zur Community, nur Text (kein zweiter QR-Code). Der Name dunkel, die Adressen
# in der Akzentfarbe des Blatts – so fallen sie auf wie die Adresse am QR-Code.
FOOTER_NAME = "OpenStreetMap-Community Fulda"
FOOTER_LINKS = f"{druck.SHOW_WIKI} · {druck.SHOW_MATRIX}"
FOOTER = f"{FOOTER_NAME} · {FOOTER_LINKS}"
FOOTER_SIZE = 5.4            # gedruckt (Maßstab 137/210) gut 3,5 mm


def footer(out, x, y, ink, accent, size=FOOTER_SIZE, two_lines=False):
    """Absenderzeile; y = Grundlinie (bei zwei Zeilen die der unteren). Gibt die Breite zurück."""
    if two_lines:
        out.append(text(x, y - size * 1.25, FOOTER_NAME, size, 700, ink))
        out.append(text(x, y, FOOTER_LINKS, size, 700, accent))
        return max(druck.text_width(FOOTER_NAME, 700, size), druck.text_width(FOOTER_LINKS, 700, size))
    out.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-weight="700" fill="{ink}">'
               f'{escape(FOOTER_NAME)} · <tspan fill="{accent}">{escape(FOOTER_LINKS)}</tspan></text>')
    return druck.text_width(FOOTER, 700, size)


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


def qr_block(out, x, y, size, url, bg="#fff"):
    """QR-Code mit weißer Ruhezone von 4 Modulen (ISO/IEC 18004). Gibt die Ruhezone in mm zurück."""
    d, _, _, module = druck.qr_path(url, x, y, size)
    pad = 4 * module
    out.append(f'<rect x="{x - pad:.2f}" y="{y - pad:.2f}" width="{size + 2 * pad:.2f}" '
               f'height="{size + 2 * pad:.2f}" rx="2" fill="{bg}"/>')
    out.append(f'<path d="{d}" fill="#000"/>')
    return pad


def bottom(out, fg, sub, accent, line1, line2, *, url, qs=36, s1=6.2, s2=4.8, w1=600, qr_right=False, url_label=None):
    """QR-Code unten mit Text daneben, darunter die Absenderzeile über die ganze Breite. Ruhezone bündig am Rand.

    Die „Einzige Regel“ steht im Text am QR-Code, damit die Absenderzeile Platz für sich hat.
    qr_right=True: Text links an der Satzkante wie der Rest des Blatts, QR-Code rechts unten –
    dort endet die Leserichtung (Z-Muster), also genau da, wo man handeln soll.
    """
    foot = H - M + 3
    qy = foot - 14 - qs
    module = druck.qr_path(url, 0, 0, qs)[3]
    if qr_right:
        pad = qr_block(out, W - M - qs - 4 * module, qy, qs, url)
        tx = M
        tw = W - M - qs - 2 * pad - 8 - M
    else:
        pad = qr_block(out, M + 4 * module, qy, qs, url)
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
    y = paragraph(out, tx, y + 3, rule, s2, tw, 600, fg, 1.3)   # dunkel, damit es sich von der Adresse abhebt
    out.append(text(tx, qy + qs, url_label or druck.SHOW_STREETCOMPLETE, 5.2, 700, accent))
    assert footer(out, M, foot, fg, accent) <= TW, "Fußzeile zu lang"
    assert y < qy + qs - 6, ("Text am QR-Code zu lang", round(y, 1), round(qy + qs - 6, 1))
    return qy - pad     # Oberkante des weißen QR-Felds


def page(bg, body):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{bg}"/>',
        f'<g font-family="{druck.FONT}">', *body, "</g></svg>",
    ])


def _prefix_ids(svg, prefix):
    """IDs eindeutig machen – der Bogen enthält das Blatt zweimal."""
    ids = set(re.findall(r'\sid="([^"]+)"', svg))
    for i in ids:
        svg = svg.replace(f'id="{i}"', f'id="{prefix}{i}"').replace(f"url(#{i})", f"url(#{prefix}{i})")
    return svg


def a5(svg_text, uid):
    """Das Blatt als verschachteltes SVG in Blattkoordinaten (0..W x 0..H) für make_a4.a5_two_up."""
    inner = re.sub(r"^<svg [^>]*>", f'<svg x="0" y="0" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                   svg_text, count=1)
    return [_prefix_ids(inner, f"{uid}-")]


def build(name, svg_text):
    """SVG (A4-Koordinaten) und Vorschau-PNG schreiben, dazu den Druckbogen <name>-a4.pdf:
    zwei Blätter im Endformat 137 x 194 mm auf A4 quer, mit Schnittmarken (make_a4.a5_two_up)."""
    os.chdir(HERE)
    with open(f"{name}.svg", "w") as f:
        f.write(svg_text)
    druck.png(f"{name}.svg", f"{name}.png", dpi=110)
    with open(f"bogen-{name}.svg", "w") as f:
        f.write(make_a4.a5_two_up(lambda uid: a5(svg_text, uid), guides=True, view=(W, H)))
    druck.pdf([f"bogen-{name}.svg"], f"{name}-roh.pdf")
    make_a4.compress(f"{name}-roh.pdf", f"{name}-a4.pdf")
    os.remove(f"{name}-roh.pdf")
    print(name, "ok")
