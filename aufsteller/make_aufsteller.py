#!/usr/bin/env python3
"""Tischaufsteller für den Infostand – einer pro Druck, sagt, wofür er da ist.

Je ein A4-Blatt hoch, zweimal quer gefaltet, steht als Dreieck vor dem Stapel, von beiden Seiten lesbar:

    +-------------------+  0
    | Rückseite         |  (Kopf unten, steht nach dem Falten richtig)
    +- - - - - - - - - -+  FACE       <- Falz (Spitze)
    | Vorderseite       |
    +- - - - - - - - - -+  2 * FACE   <- Falz
    | Standfläche       |  nach innen umschlagen, unter die Rückseite schieben
    +-------------------+  297

Schauseite: links Vorschau des Drucks, rechts direkte Aufforderung ("Steck mich ein!") + Text,
unten QR-Code zum Repo ("Vergriffen?").
Vorschaubilder kommen aus den fertigen PNGs der anderen Drucke – die zuerst bauen.

Erzeugt aufsteller-<name>.svg / .png und aufsteller-a4.pdf (eine Seite pro Aufsteller).
"""
import base64
import os
import sys
import tempfile
from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "gemeinsam"))
import druck  # noqa: E402
import make_a4  # noqa: E402
from druck import ACCENT, GREY, INK, cap_height, qr_path, text_width, wrap  # noqa: E402

AW, AH = 210, 297     # A4 hoch
FACE = 125            # Höhe einer Schauseite, Rest (47 mm) ist Standfläche
M = 12                # Rand links/rechts
PAD = 8               # Abstand zum Falz
FOLD_COLOR = "#bbb"

CARD = ((85, 55), druck.BLEED)   # Endformat, Beschnitt im PNG
A5 = ((148, 210), 0)
# Vorschaubilder: (PNG, Format, Bildunterschrift oder None) – Hochformate nebeneinander, sonst untereinander.
# Text: Absätze als (Zwischenzeile halbfett oder None, Fließtext).
STANDS = [  # (Name, Vorschaubilder, Aufforderung, Absätze)
    ("mitmachkarte",
     [("mitmachkarte/mitmachkarte-vorne.png", CARD, None),
      ("mitmachkarte/mitmachkarte-hinten.png", CARD, None)],
     "Steck mich ein!",
     [(None, "Für alle, die mitmachen wollen: Ich zeige dir, wie du die Karte besser machst – "
             "per App, im Browser, mit Fotos – und wo du uns findest.")]),
    ("aushang",
     [("aushang/aushang-vorne.png", A5, None)],
     "Häng mich auf!",
     [(None, "Ins Schaufenster, an die Pinnwand, ans Schwarze Brett. Ich komme in zwei Fassungen:"),
      ("Für Glasscheiben: beidseitig bedruckt", "Von innen und außen lesbar."),
      ("Für Pinnwand und Brett: einseitig", "Die Rückseite sieht ja keiner.")]),
    ("infokarte",
     [("infokarte/infokarte.png", CARD, None)],
     "Leg mich aus!",
     [(None, "Ins Wartezimmer, ins Café, in den Waschsalon – überall, wo Leute warten. "
             "Nimm gleich ein paar mit.")]),
]

KICKER = "OPENSTREETMAP FULDA · KOSTENLOS"
KICKER_SIZE = 3.6
PREVIEW_MAX_W = 78
PREVIEW_GAP = 4
HEAD_MAX = 15.0
BODY = 5.2
BODY_LEAD = 1.32
PARA_GAP = 3.0
CAPTION = 3.2
FOOTER = ["Vergriffen? Alle Druckvorlagen zum Selbstdrucken:", "github.com/osm-fulda/osm-fulda-prints"]
FOOTER_URL = "https://github.com/osm-fulda/osm-fulda-prints"
FOOTER_SIZE = 3.4
FOOTER_QR = 14.0


def text(x, y, s, size, weight, fill=INK, anchor="start", spacing=None):
    sp = f' letter-spacing="{spacing:.3f}"' if spacing else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size:.3f}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{sp}>{escape(s)}</text>')


def preview(path, size, bleed, x, y, w):
    """Vorschau ohne Beschnitt als JPEG einbetten, mit Haarlinie als Papierkante."""
    im = Image.open(os.path.join(ROOT, path)).convert("RGB")
    if bleed:
        b = round(bleed * im.width / (size[0] + 2 * bleed))
        im = im.crop((b, b, im.width - b, im.height - b))
    h = w * size[1] / size[0]
    target = round(w / 25.4 * 300)
    im = im.resize((target, round(target * size[1] / size[0])), Image.LANCZOS)
    buf = BytesIO()
    im.save(buf, "JPEG", quality=90)
    href = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return [f'<image x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" href="{href}"/>',
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="none" '
            f'stroke="#bbb" stroke-width="0.2"/>']


def footer():
    """QR-Code + zwei Zeilen zum Repo, als Gruppe mittig knapp über dem unteren Falz."""
    tw = max(text_width(l, w, FOOTER_SIZE) for l, w in zip(FOOTER, (400, 600)))
    gap = 3
    x = (AW - FOOTER_QR - gap - tw) / 2
    qy = FACE - PAD + 2 - FOOTER_QR
    d, ver, n, s = qr_path(FOOTER_URL, x, qy, FOOTER_QR)
    tx = x + FOOTER_QR + gap
    lead = FOOTER_SIZE * 1.35
    y1 = qy + FOOTER_QR / 2 - lead / 2 + cap_height(400, FOOTER_SIZE) / 2
    return qy, s, [f'<path d="{d}" fill="#000"/>',
                   text(tx, y1, FOOTER[0], FOOTER_SIZE, 400, GREY),
                   text(tx, y1 + lead, FOOTER[1], FOOTER_SIZE, 600, INK)]


def face(images, head, body):
    """Eine Schauseite, Koordinaten 0..AW x 0..FACE, Oberkante = Falz an der Spitze."""
    out = []
    ky = PAD + cap_height(500, KICKER_SIZE)
    out.append(text(AW / 2, ky, KICKER, KICKER_SIZE, 500, GREY, anchor="middle", spacing=0.5))
    fy, module, foot = footer()
    out.extend(foot)
    top, bottom = ky + 6, fy - 6                    # Inhaltsbereich

    # Vorschau links, so groß wie Breite/Höhe erlauben
    (w0, h0), _ = images[0][1]
    n = len(images)
    cap_h = 2 + cap_height(500, CAPTION) if any(c for *_, c in images) else 0
    avail_h = bottom - top - cap_h
    if h0 > w0:   # Hochformat: nebeneinander
        iw = min((PREVIEW_MAX_W - PREVIEW_GAP * (n - 1)) / n, avail_h * w0 / h0)
        ih = iw * h0 / w0
        pw = n * iw + PREVIEW_GAP * (n - 1)
        boxes = [(M + i * (iw + PREVIEW_GAP), top + (avail_h - ih) / 2) for i in range(n)]
    else:         # Querformat: untereinander
        iw = min(PREVIEW_MAX_W, (avail_h - PREVIEW_GAP * (n - 1)) / n * w0 / h0)
        ih = iw * h0 / w0
        pw = iw
        y0 = top + (avail_h - n * ih - PREVIEW_GAP * (n - 1)) / 2
        boxes = [(M, y0 + i * (ih + PREVIEW_GAP)) for i in range(n)]
    for (path, (size, bleed), caption), (x, y) in zip(images, boxes):
        out.extend(preview(path, size, bleed, x, y, iw))
        if caption:
            out.append(text(x + iw / 2, y + ih + cap_h, caption, CAPTION, 500, GREY, anchor="middle"))

    # Text rechts, vertikal mittig
    tx = M + pw + 10
    tw = AW - M - tx
    hs = min(HEAD_MAX, HEAD_MAX * tw / text_width(head, 700, HEAD_MAX))
    lines = []    # (Text, Gewicht, Abstand zur vorigen Grundlinie)
    for i, (sub, para) in enumerate(body):
        first = 6 + cap_height(400, BODY) if i == 0 else BODY * BODY_LEAD + PARA_GAP
        if sub:
            lines.append((sub, 600, first))
            first = BODY * BODY_LEAD
        for j, line in enumerate(wrap(para, 400, BODY, tw)):
            lines.append((line, 400, first if j == 0 else BODY * BODY_LEAD))
    block = cap_height(700, hs) + sum(d for *_, d in lines)
    y = top + (bottom - top - block) / 2 + cap_height(700, hs)
    out.append(text(tx, y, head, hs, 700, ACCENT))
    for line, weight, d in lines:
        y += d
        out.append(text(tx, y, line, BODY, weight))
    assert block <= bottom - top, f"{head}: Text zu lang"
    return out, module


def sheet(images, head, body):
    f, module = face(images, head, body)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{AW}mm" height="{AH}mm" viewBox="0 0 {AW} {AH}">',
           f'<rect width="{AW}" height="{AH}" fill="#fff"/>',
           f'<g font-family="{druck.FONT}">',
           f'<g transform="rotate(180 {AW / 2} {FACE / 2})">', *f, "</g>",
           f'<g transform="translate(0,{FACE})">', *f, "</g>"]
    for y in (FACE, 2 * FACE):
        out.append(f'<line x1="0" y1="{y}" x2="{AW}" y2="{y}" stroke="{FOLD_COLOR}" '
                   f'stroke-width="0.2" stroke-dasharray="2 2"/>')
    base = (2 * FACE + AH) / 2
    out.append(text(AW / 2, base - 2, "Standfläche", 3.4, 600, GREY, anchor="middle"))
    out.append(text(AW / 2, base + 3, "An den gestrichelten Linien falten, diesen Streifen nach innen "
                    "unter die Rückseite schieben.", 3.0, 400, GREY, anchor="middle"))
    out.append("</g></svg>")
    return "\n".join(out), module


def main():
    os.chdir(HERE)
    druck.use_project_fonts()
    svgs = []
    for name, images, head, body in STANDS:
        svg, module = sheet(images, head, body)
        fn = f"aufsteller-{name}.svg"
        with open(fn, "w") as f:
            f.write(svg)
        druck.png(fn, f"aufsteller-{name}.png", dpi=100)
        svgs.append(fn)
        print(f"  {name:13} {head:16} Repo-QR {module:.2f} mm/Modul")
    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, "roh.pdf")
        druck.pdf(svgs, raw)
        make_a4.compress(raw, "aufsteller-a4.pdf")
    print("aufsteller-a4.pdf geschrieben (3 Seiten)")


if __name__ == "__main__":
    main()
