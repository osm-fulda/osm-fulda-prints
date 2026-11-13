#!/usr/bin/env python3
"""Aushang für Umweltbewusste: Demo-Pappschild „Mapping for Future“ (A5, gezeichnet auf A4).

  aushang-pappe.png, aushang-pappe-a4.pdf (Bogen, 2x A5)

Idee: Ästhetik der Klima-Demos (Pappe, Filzstift, Klebeband) und ein Wortspiel auf „Fridays for Future“,
gewendet auf OpenStreetMap. Ein Bild, eine Botschaft, ein QR-Code zu StreetComplete.
Schrift auf dem Schild: Permanent Marker (Apache 2.0, ../gemeinsam/fonts), sonst Barlow Condensed.
"""
import math
import os
import random

from fontTools.ttLib import TTFont

import common as c
from common import druck, text, paragraph

W, H, M = 210, 297, 16
TW = W - 2 * M
MARKER = "Permanent Marker"
BG = "#a9d8f2"          # Himmel
KRAFT, KRAFT_DARK, KRAFT_LIGHT = "#c9a06a", "#a97f4a", "#d8b380"
TAPE = "#f3ead2"
PEN = "#1f2224"
PEN_GREEN = "#1f7a3a"

_mf = {}


def mwidth(s, size):
    if not _mf:
        _mf["f"] = TTFont(os.path.join(druck.FONT_DIR, "PermanentMarker-Regular.ttf"))
    f = _mf["f"]
    cmap, hmtx, upem = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] for c in s) / upem * size


def mcap(size):
    return 758 / 1024 * size


def mtext(x, y, s, size, fill, rot=0.0, bold=0.0, anchor="start"):
    stroke = (f' stroke="{fill}" stroke-width="{bold:.2f}" stroke-linejoin="round"' if bold else "")
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{MARKER}" font-size="{size:.2f}" fill="{fill}"{stroke} '
            f'text-anchor="{anchor}" transform="rotate({rot:.2f} {x:.2f} {y:.2f})">{c.escape(s)}</text>')


def squiggle(out, x1, x2, y, col, sw, seed=1):
    pts = [(x1 + (x2 - x1) * j / 14, y + math.sin(j * 1.3 + seed) * 0.9) for j in range(15)]
    out.append('<path d="M' + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) +
               f'" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" fill="none"/>')


def doodle(out, kind, x, y, s, pen=PEN):
    """Kleine Filzstift-Kritzelei, linke obere Ecke (x, y), Größe s."""
    st = f'stroke="{pen}" stroke-width="{s * 0.08:.2f}" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "baum":
        out.append(f'<line x1="{x + s * 0.5:.1f}" y1="{y + s * 0.55:.1f}" x2="{x + s * 0.5:.1f}" y2="{y + s:.1f}" {st}/>')
        for cx, cy, r in [(0.5, 0.32, 0.3), (0.28, 0.48, 0.22), (0.72, 0.48, 0.22)]:
            out.append(f'<circle cx="{x + s * cx:.1f}" cy="{y + s * cy:.1f}" r="{s * r:.1f}" fill="#7bd17b" {st}/>')
    elif kind == "rad":
        for wx in (0.2, 0.8):
            out.append(f'<circle cx="{x + s * wx:.1f}" cy="{y + s * 0.7:.1f}" r="{s * 0.2:.1f}" fill="none" {st}/>')
        pts = [(0.2, 0.7), (0.42, 0.35), (0.5, 0.7), (0.2, 0.7)]
        out.append('<path d="M' + " L".join(f"{x + s * a:.1f},{y + s * b:.1f}" for a, b in pts) + f'" fill="none" {st}/>')
        out.append(f'<path d="M{x + s * 0.42:.1f},{y + s * 0.35:.1f} L{x + s * 0.72:.1f},{y + s * 0.35:.1f} '
                   f'L{x + s * 0.8:.1f},{y + s * 0.7:.1f} M{x + s * 0.5:.1f},{y + s * 0.7:.1f} L{x + s * 0.72:.1f},{y + s * 0.35:.1f} '
                   # Vorbau vom Steuerrohr nach oben, Lenker daran; Sattelstütze mit Sattel
                   f'M{x + s * 0.72:.1f},{y + s * 0.35:.1f} L{x + s * 0.7:.1f},{y + s * 0.2:.1f} '
                   f'M{x + s * 0.64:.1f},{y + s * 0.2:.1f} L{x + s * 0.8:.1f},{y + s * 0.18:.1f} '
                   f'M{x + s * 0.42:.1f},{y + s * 0.35:.1f} L{x + s * 0.4:.1f},{y + s * 0.26:.1f} '
                   f'M{x + s * 0.33:.1f},{y + s * 0.25:.1f} L{x + s * 0.47:.1f},{y + s * 0.25:.1f}" fill="none" {st}/>')
    elif kind == "bus":
        out.append(f'<rect x="{x:.1f}" y="{y + s * 0.2:.1f}" width="{s:.1f}" height="{s * 0.55:.1f}" rx="{s * 0.08:.1f}" fill="#ffd43b" {st}/>')
        for wx in (0.1, 0.38, 0.66):
            out.append(f'<rect x="{x + s * wx:.1f}" y="{y + s * 0.3:.1f}" width="{s * 0.22:.1f}" height="{s * 0.17:.1f}" fill="#bfe6ff" {st}/>')
        for wx in (0.22, 0.78):
            out.append(f'<circle cx="{x + s * wx:.1f}" cy="{y + s * 0.78:.1f}" r="{s * 0.1:.1f}" fill="{PEN}"/>')


def jagged_rect(rnd, x, y, w, h, j):
    """Rechteck mit leicht unruhigen Kanten wie bei geschnittener Pappe."""
    pts = []
    for (x1, y1), (x2, y2) in [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                               ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]:
        n = 14
        for i in range(n):
            t = i / n
            pts.append((x1 + (x2 - x1) * t + rnd.uniform(-j, j), y1 + (y2 - y1) * t + rnd.uniform(-j, j)))
    return "M" + " L".join(f"{px:.2f},{py:.2f}" for px, py in pts) + " Z"


def board(out, rnd, cx, cy, w, h, rot, fill, texture, stick=0.0, uid="b", tex_light=KRAFT_LIGHT, tex_dark=KRAFT_DARK,
          stick_w=10.0, stick_op=1.0):
    """Schild (Pappe oder Plakatkarton) mit Schatten, optional an einer Holzlatte. Gibt (x, y, Ende) zurück."""
    x, y = cx - w / 2, cy - h / 2
    out.append(f'<g transform="rotate({rot} {cx:.1f} {cy:.1f})">')
    if stick:
        sx = cx - stick_w / 2
        out.append(f'<g opacity="{stick_op}"><rect x="{sx:.1f}" y="{cy:.1f}" width="{stick_w}" height="{h / 2 + stick:.1f}" fill="#b07a45"/>')
        out.append(f'<rect x="{sx:.1f}" y="{cy:.1f}" width="{stick_w / 4:.2f}" height="{h / 2 + stick:.1f}" fill="#c99560"/></g>')
    d = jagged_rect(rnd, x, y, w, h, 0.9)
    out.append(f'<path d="{d}" fill="#000" opacity="0.2" transform="translate(2.2 3)"/>')
    out.append(f'<path d="{d}" fill="{fill}"/>')
    if texture:
        out.append(f'<clipPath id="{uid}"><path d="{d}"/></clipPath><g clip-path="url(#{uid})">')
        for i in range(0, int(h), 3):
            out.append(f'<rect x="{x}" y="{y + i:.1f}" width="{w}" height="1.1" fill="{tex_light}" opacity="0.35"/>')
        for _ in range(int(w * h / 90)):
            out.append(f'<circle cx="{x + rnd.uniform(0, w):.1f}" cy="{y + rnd.uniform(0, h):.1f}" '
                       f'r="{rnd.uniform(0.15, 0.6):.2f}" fill="{tex_dark}" opacity="{rnd.uniform(0.25, 0.6):.2f}"/>')
        out.append("</g>")
    return x, y


def earth(out, cx, cy, r):
    """Gekritzelte Erde mit Kartennadel, im Filzstift-Stil."""
    out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#7cc4ef" stroke="{PEN}" stroke-width="1.6"/>')
    blobs = ["M{a},{b} q3,-4 7,-2 q2,3 -1,6 q-4,2 -6,-1 z", "M{c},{d} q4,-1 6,3 q-1,4 -5,4 q-3,-3 -1,-7 z"]
    out.append(f'<path d="' + blobs[0].format(a=f"{cx - r * 0.6:.1f}", b=f"{cy - r * 0.2:.1f}") + " " +
               blobs[1].format(c=f"{cx + r * 0.1:.1f}", d=f"{cy + r * 0.05:.1f}") +
               f'" fill="#5fb85f" stroke="{PEN}" stroke-width="1.1"/>')
    px, py = cx + r * 0.15, cy - r * 0.55          # Nadel steckt in der Erde (70 % Größe)
    out.append(f'<g transform="translate({px:.2f} {py:.2f}) scale(0.7) translate({-px:.2f} {-py:.2f})">')
    out.append(f'<path d="M{px:.1f},{py:.1f} C{px - 2.5:.1f},{py - 4:.1f} {px - 4.5:.1f},{py - 6:.1f} {px - 4.5:.1f},{py - 9:.1f} '
               f'A4.5,4.5 0 1 1 {px + 4.5:.1f},{py - 9:.1f} C{px + 4.5:.1f},{py - 6:.1f} {px + 2.5:.1f},{py - 4:.1f} {px:.1f},{py:.1f} Z" '
               f'fill="#e4572e" stroke="{PEN}" stroke-width="1.3"/>')
    out.append(f'<circle cx="{px:.1f}" cy="{py - 9:.1f}" r="1.7" fill="#fff"/>')
    out.append("</g>")


def main_sign(out, cx, cy, w, h, rot, stick=16):
    rnd = random.Random(2026)
    x, y = board(out, rnd, cx, cy, w, h, rot, KRAFT, True, stick=stick, uid="pappe")
    # Anspielung auf „Fridays for Future“, ohne den Namen der Bewegung zu übernehmen.
    # Zwei große Wörter mit Abstand; dazwischen links „for“, rechts die Erde mit Kartennadel.
    mid = x + w / 2
    gap_k = 1.45                                   # Abstand zwischen den Wörtern, in Versalhöhen
    size = min((w - 40) / mwidth("MAPPING", 1), (w - 40) / mwidth("FUTURE", 1),
               (h - 30) / ((2 + gap_k) * mcap(1)))
    cap_ = mcap(size)
    gap = cap_ * gap_k
    top = y + (h - (2 * cap_ + gap)) / 2 + 1
    y1, y2 = top + cap_, top + 2 * cap_ + gap
    out.append(mtext(mid - 2, y1, "MAPPING", size, PEN, -3.5, bold=0.7, anchor="middle"))
    out.append(mtext(mid + 2, y2, "FUTURE", size, PEN, 1.5, bold=0.7, anchor="middle"))
    fx = mid - mwidth("FUTURE", size) / 2
    fs = size * 0.75
    ym = y1 + gap / 2 + mcap(fs) / 2 + 1            # Mitte zwischen den Zeilen
    out.append(mtext(fx + 2, ym, "for", fs, PEN_GREEN, -7, bold=0.5))
    earth(out, mid + mwidth("FUTURE", size) / 2 - 14, y1 + gap / 2 + 1, 15)
    squiggle(out, fx + 2, fx + mwidth("FUTURE", size) + 2, y2 + 5.5, PEN_GREEN, 2.4, 0.3)
    squiggle(out, fx + 12, fx + mwidth("FUTURE", size) - 6, y2 + 9.5, PEN_GREEN, 1.8, 1.7)
    out.append("</g>")
    return cy + h / 2


def crowd(out):
    """Drei Schilder im Hintergrund, in verschiedenen Höhen, Materialien und Brauntönen, je mit Kritzelei.

    Die Schrift sitzt im oberen Teil, der über dem großen Schild sichtbar bleibt, und füllt ihn aus.
    """
    rnd = random.Random(7)
    for cx, cy, w, h, rot, fill, tex, txt, size, col, kind in [
            (100, 25, 66, 34, 3, "#d3f0d0", None, ["BUS &", "BAHN!"], 8.5, PEN, "bus"),          # weit hinten
            (40, 42, 76, 46, 6, "#fbfaf6", None, ["MEHR", "GRÜN!"], 11.5, PEN_GREEN, "baum"),
            (172, 38, 80, 48, -5, "#9c7449", ("#b08658", "#6f4f2c"), ["RAD-", "WEGE!"], 11, "#fbfaf6", "rad")]:
        # Latten enden hinter dem großen Schild, damit sie nicht wie Beine darunter herausragen
        kw = dict(tex_light=tex[0], tex_dark=tex[1]) if tex else {}
        x, y = board(out, rnd, cx, cy, w, h, rot, fill, bool(tex), stick=62, uid=f"c{cx}", **kw)
        ty = y + 5 + mcap(size)
        tw = max(mwidth(t, size) for t in txt) + 3
        ds = min(18, mcap(size) * 2.2)
        left = kind == "bus"                      # beim Bus steht die Kritzelei links, die Schrift rechts
        tx = x + 8 + (ds + 5 if left else 0)
        for i, t in enumerate(txt):
            out.append(mtext(tx + i * 3, ty + i * mcap(size) * 1.35, t, size, col, rnd.uniform(-3, 2), bold=0.4))
        last = ty + mcap(size) * 1.35
        squiggle(out, tx + 2, tx + 2 + tw * 0.9, last + 3, col, 1.1, cx)
        doodle(out, kind, x + 6 if left else x + 14 + tw, y + 5, ds, pen=col if kind == "rad" else PEN)
        out.append("</g>")


def qr_note(out, x, y, size, rot, url):
    """QR-Code auf einem weißen Zettel, mit Klebeband an die Latte geklebt."""
    rnd = random.Random(11)
    d_qr, _, _, module = druck.qr_path(url, 0, 0, size)
    pad = max(8, 4 * module + 2)            # Ruhezone ≥ 4 Module
    w, h = size + 2 * pad, size + 2 * pad + 8
    cx, cy = x + w / 2, y + h / 2
    out.append(f'<g transform="rotate({rot} {cx:.1f} {cy:.1f})">')
    d = jagged_rect(rnd, x, y, w, h, 0.4)
    out.append(f'<path d="{d}" fill="#000" opacity="0.2" transform="translate(1.6 2.2)"/>')
    out.append(f'<path d="{d}" fill="#fff"/>')
    out.append(f'<g transform="translate({x + pad:.2f} {y + pad:.2f})"><path d="{d_qr}" fill="#000"/></g>')
    out.append(text(cx, y + pad + size + 7.5, druck.SHOW_STREETCOMPLETE, 5.2, 700, c.INK, "middle"))
    out.append(f'<rect x="{cx - 14:.1f}" y="{y - 4:.1f}" width="28" height="9" fill="{TAPE}" opacity="0.9" '
               f'transform="rotate(-6 {cx:.1f} {y:.1f})"/>')
    out.append("</g>")
    return w, h


def poster():
    out = []
    crowd(out)
    sw, sh = TW - 4, 128
    stick_x = W / 2
    end = main_sign(out, stick_x, M + 27 + sh / 2, sw, sh, -4, stick=H)   # oben Platz für Himmel
    y0 = end + 7

    # rechts: QR-Zettel unten ans Schild geklebt; darunter ein Streifen Klebeband mit „Scan mich!“ quer über den Pfosten
    qs = 40
    nx = stick_x + 14
    ny = end - 12                                  # oben auf das Schild geklebt, hängt nach unten
    nw, nh = qr_note(out, nx, ny, qs, 3, druck.go("a/pappe"))
    lx, ly, lw_, lh = stick_x + 6, ny + nh + 16, 52, 13     # weiter rechts unten, linkes Ende auf dem Pfosten
    out.append(f'<g transform="rotate(-4 {lx + lw_ / 2:.1f} {ly + lh / 2:.1f})">')
    out.append(f'<path d="{jagged_rect(random.Random(5), lx, ly, lw_, lh, 0.5)}" fill="#000" opacity="0.15" transform="translate(1 1.5)"/>')
    out.append(f'<path d="{jagged_rect(random.Random(5), lx, ly, lw_, lh, 0.5)}" fill="{TAPE}"/>')
    out.append(mtext(lx + 5, ly + lh / 2 + mcap(7.5) / 2, "SCAN MICH!", 7.5, PEN, 0, bold=0.3))
    out.append("</g>")

    # links: ein großer Satz, ein kleiner, ohne Kasten direkt auf dem Himmel
    lw = stick_x - 10 - M
    y = paragraph(out, M, y0 + 4, "Die Zukunft beginnt vor deiner Tür.", 11, lw, 700, c.INK, 1.08)

    # Feste Zeilenumbrüche nach Sinn statt automatischem Umbruch: jede Frage eine Zeile,
    # Sätze brechen an Komma und Doppelpunkt. Motiv der Zielgruppe: etwas bewirken, kein Profit.
    def block(y, lines, weight, col, gap):
        y += gap + druck.cap_height(weight, 5.6)
        for i, line in enumerate(lines):
            out.append(text(M, y + i * 5.6 * 1.28, line, 5.6, weight, col))
        return y + (len(lines) - 1) * 5.6 * 1.28
    y = block(y, ["Wo endet der Radweg?", "Wo fehlt Schatten?", "Wo ist die nächste Ladesäule?"], 600, c.INK, 5)
    y = block(y, ["Was du in OpenStreetMap einträgst,", "nutzen Rad-Apps, Forschung", "und Stadtplanung."],
              500, c.INK, 4)
    y = block(y, ["Keine Firma, kein Profit –", "über zwei Millionen Freiwillige weltweit."], 500, "#2b4a5e", 4)
    assert all(druck.text_width(l, 600, 5.6) <= lw for l in ["Was du in OpenStreetMap einträgst,",
                                                              "über zwei Millionen Freiwillige weltweit."])
    foot = H - M + 3
    # Absender zweizeilig links vom Pfosten (Name dunkel, Adressen grün), darunter klein die Regel
    fy = foot - 6.5
    fw = c.footer(out, M, fy, c.INK, PEN_GREEN, two_lines=True)
    # Linke Kante des Pfostens auf Höhe der Zeile (Schild samt Pfosten um -4° gedreht, Latte 10 mm breit)
    a = math.radians(4)
    top_line = fy - c.FOOTER_SIZE * 1.25 - druck.cap_height(700, c.FOOTER_SIZE)
    pole = stick_x - 5 * math.cos(a) + (top_line - (M + 27 + sh / 2)) * math.sin(a)
    assert M + fw < pole - 3, "Fußzeile läuft in den Pfosten"
    out.append(text(M, foot, "Einzige Regel: Nur eintragen, was es wirklich gibt.", 3.6, 500, "#2b4a5e"))
    assert y < top_line - 4, (round(y, 1), round(top_line - 4, 1))
    assert ly + lh < H - 4, "Klebeband ragt aus dem Blatt"
    return c.page(BG, out)


def main():
    druck.use_project_fonts()
    c.build("aushang-pappe", poster())


if __name__ == "__main__":
    main()
