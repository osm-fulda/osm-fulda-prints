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

Schauseite: links Vorschau des Drucks, rechts Spruch ("Wir haben dich angefixt? …") + wofür die Karte da ist,
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

CARD_UPRIGHT = ((55, 85), druck.BLEED)   # Karten hochkant, Beschnitt im PNG
A5 = ((148, 210), 0)
A4 = ((210, 297), 0)                     # Aushänge, die auf A4 gezeichnet und als A5 gedruckt werden

# Ein Aufsteller pro Oberkategorie, je vor seinen Stapel am Stand.
# "single": Vorschaubilder (PNG, Format, Bildunterschrift oder None) links, Text rechts;
#           Titel als Text oder Liste fester Zeilen; Text als Absätze (Zwischenzeile halbfett
#           oder None, Fließtext oder Liste fester Zeilen).
# "series": Aufforderung und Satz oben, darunter alle Motive der Reihe nebeneinander,
#           je mit Namen und Zielgruppe – so sucht sich jeder das Motiv aus, das zu seinem Ort passt.
STANDS = [
    ("mitmachkarte", "single", ["Wir haben dich angefixt?", "", "Jetzt kommst du da", "nicht wieder raus."],
     [("mitmachkarte/mitmachkarte-vorne.png", CARD_UPRIGHT, None),
      ("mitmachkarte/mitmachkarte-hinten.png", CARD_UPRIGHT, None)],
     [(None, ["Auf dieser Karte steht alles, was du brauchst:", "Apps, Fotos, am PC bearbeiten –",
              "und wo du uns findest."])]),
    ("aushang", "series", "Häng mich auf!",
     [("aushang/aushang-klassisch.png", A5, ("Klassisch", "für alle")),
      ("aushang/aushang-gelb.png", A4, ("Gelb", "Politik, Daten")),
      ("aushang/aushang-pixel.png", A4, ("Pixel", "Gamer")),
      ("aushang/aushang-pappe.png", A4, ("Pappe", "Umwelt, Klima")),
      ("aushang/aushang-sozial.png", A4, ("Sozial", "Barrierefreiheit"))],
     "Ans Schwarze Brett, an die Pinnwand, ins Schaufenster. Such dir das Motiv aus, "
     "das zu den Leuten dort passt."),
    ("motivkarten", "series", "Leg mich aus!",
     [("motivkarten/motivkarte-klassisch.png", CARD_UPRIGHT, ("Klassisch", "für alle")),
      ("motivkarten/motivkarte-gelb.png", CARD_UPRIGHT, ("Gelb", "Politik, Daten")),
      ("motivkarten/motivkarte-pixel.png", CARD_UPRIGHT, ("Pixel", "Gamer")),
      ("motivkarten/motivkarte-pappe.png", CARD_UPRIGHT, ("Pappe", "Umwelt, Klima")),
      ("motivkarten/motivkarte-sozial.png", CARD_UPRIGHT, ("Sozial", "Barrierefreiheit"))],
     "Ins Wartezimmer, ins Café, in den Jugendtreff – überall, wo Leute warten. "
     "Such dir ein Motiv aus und nimm gleich ein paar mit."),
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
    heads = head if isinstance(head, list) else [head]     # feste Zeilen nach Sinn; "" = kleiner Abstand
    hs = min(HEAD_MAX, *(HEAD_MAX * tw / text_width(h, 700, HEAD_MAX) for h in heads if h))
    hlead = hs * 1.05
    hsteps = [hlead * (0.35 if h == "" else 1) for h in heads[1:]]   # Abstand zur vorigen Zeile
    lines = []    # (Text, Gewicht, Abstand zur vorigen Grundlinie)
    for i, (sub, para) in enumerate(body):
        first = 6 + cap_height(400, BODY) if i == 0 else BODY * BODY_LEAD + PARA_GAP
        if sub:
            lines.append((sub, 600, first))
            first = BODY * BODY_LEAD
        if isinstance(para, list):                  # feste Zeilen nach Sinn
            assert all(text_width(l, 400, BODY) <= tw for l in para), f"{head}: Zeile zu breit"
        for j, line in enumerate(para if isinstance(para, list) else wrap(para, 400, BODY, tw)):
            lines.append((line, 400, first if j == 0 else BODY * BODY_LEAD))
    block = cap_height(700, hs) + sum(hsteps) + sum(d for *_, d in lines)
    y = top + (bottom - top - block) / 2 + cap_height(700, hs)
    for i, h in enumerate(heads):
        if i:
            y += hsteps[i - 1]
        if h:
            out.append(text(tx, y, h, hs, 700, ACCENT))
    for line, weight, d in lines:
        y += d
        out.append(text(tx, y, line, BODY, weight))
    assert block <= bottom - top, f"{head}: Text zu lang"
    return out, module


SERIES_HEAD = 13.0
SERIES_BODY = 4.8
SERIES_GAP = 4.5                 # zwischen den Vorschaubildern
NAME_SIZE, ROLE_SIZE = 3.8, 3.2  # Bildunterschrift: Motiv und Zielgruppe


def face_series(items, head, intro):
    """Schauseite für eine Reihe: Aufforderung links, Satz rechts daneben, darunter alle Motive."""
    out = []
    ky = PAD + cap_height(500, KICKER_SIZE)
    out.append(text(AW / 2, ky, KICKER, KICKER_SIZE, 500, GREY, anchor="middle", spacing=0.5))
    fy, module, foot = footer()
    out.extend(foot)
    top, bottom = ky + 6, fy - 5

    # Kopfzeile: Aufforderung + Satz, gemeinsam vertikal mittig
    hw = text_width(head, 700, SERIES_HEAD)
    tx = M + hw + 8
    lines = wrap(intro, 400, SERIES_BODY, AW - M - tx)
    lead = SERIES_BODY * BODY_LEAD
    body_h = cap_height(400, SERIES_BODY) + (len(lines) - 1) * lead
    row_h = max(cap_height(700, SERIES_HEAD), body_h)
    out.append(text(M, top + (row_h + cap_height(700, SERIES_HEAD)) / 2, head, SERIES_HEAD, 700, ACCENT))
    y = top + (row_h - body_h) / 2 + cap_height(400, SERIES_BODY)
    for i, line in enumerate(lines):
        out.append(text(tx, y + i * lead, line, SERIES_BODY, 400))

    # Motive nebeneinander, so groß wie Breite und Höhe erlauben, mittig
    n = len(items)
    cap_h = 2.2 + cap_height(600, NAME_SIZE) + 1.6 + cap_height(500, ROLE_SIZE)
    y0 = top + row_h + 6
    avail_h = bottom - y0 - cap_h
    ratios = [size[1] / size[0] for _, (size, _), _ in items]
    iw = min((AW - 2 * M - SERIES_GAP * (n - 1)) / n, avail_h / max(ratios))
    assert iw > 25, f"{head}: Vorschaubilder zu klein ({iw:.1f} mm)"
    x0 = (AW - n * iw - SERIES_GAP * (n - 1)) / 2
    ih_max = iw * max(ratios)
    base = y0 + (avail_h - ih_max) / 2 + ih_max      # Reihe mittig im freien Raum; Bilder unten bündig
    for i, (path, (size, bleed), (name, role)) in enumerate(items):
        x = x0 + i * (iw + SERIES_GAP)
        ih = iw * size[1] / size[0]
        out.extend(preview(path, size, bleed, x, base - ih, iw))
        ny = base + 2.2 + cap_height(600, NAME_SIZE)
        out.append(text(x + iw / 2, ny, name, NAME_SIZE, 600, INK, anchor="middle"))
        out.append(text(x + iw / 2, ny + 1.6 + cap_height(500, ROLE_SIZE), role, ROLE_SIZE, 500, GREY,
                        anchor="middle"))
    return out, module


def sheet(kind, head, images, body):
    f, module = (face if kind == "single" else face_series)(images, head, body)
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
    for name, kind, head, images, body in STANDS:
        svg, module = sheet(kind, head, images, body)
        fn = f"aufsteller-{name}.svg"
        with open(fn, "w") as f:
            f.write(svg)
        druck.png(fn, f"aufsteller-{name}.png", dpi=100)
        svgs.append(fn)
        print(f"  {name:13} {' '.join(head) if isinstance(head, list) else head:28} Repo-QR {module:.2f} mm/Modul")
    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, "roh.pdf")
        druck.pdf(svgs, raw)
        make_a4.compress(raw, "aufsteller-a4.pdf")
    print(f"aufsteller-a4.pdf geschrieben ({len(STANDS)} Seiten)")


if __name__ == "__main__":
    main()
