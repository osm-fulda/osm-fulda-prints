#!/usr/bin/env python3
"""Aushang für sozial Engagierte: „Für dich ein Bordstein. Für andere ein Berg.“ (A5, gezeichnet auf A4).

  aushang-sozial.png, aushang-sozial-a4.pdf (Bogen, 2x A5)

Idee: Perspektivwechsel durch Größe. Ein Bordstein als Felswand mit Gipfelfahne, mit Maßpfeil „12 cm“;
davor vier Menschen (Rollator, Kinderwagen, Langstock, Rollstuhl). Motiv der Zielgruppe: anderen helfen, Barrieren sichtbar machen.
StreetComplete fragt genau das ab (Bordsteinhöhe, Rampen, Rollstuhl-Zugang, Blindenleitlinien).
"""
import os

import common as c
from common import druck, text

W, H, M = 210, 297, 16
TW = W - 2 * M
BG = "#efe7ff"
ACCENT = "#5f3dc4"
SUB = "#4a4458"
STONE_FRONT, STONE_TOP, STONE_LINE = "#a3a9b0", "#c9ced3", "#8a9097"
GROUND = "#d9cff5"


def lines_block(out, y, lines, size, weight, col, lead=1.28):
    """Feste Zeilen (Umbruch nach Sinn). y = Oberkante. Gibt letzte Grundlinie zurück."""
    y += druck.cap_height(weight, size)
    for i, line in enumerate(lines):
        assert druck.text_width(line, weight, size) <= TW, line
        out.append(text(M, y + i * size * lead, line, size, weight, col))
    return y + (len(lines) - 1) * size * lead


# --- Figuren (Seitenansicht, nach rechts zur Mauer gewandt) -----------------------------------
# Flache Piktogramme, jede Figur in einer eigenen Farbe statt Hautfarbe.
# x = linke Kante, g = Boden, h = Körpergröße stehend.

def _st(col, w):
    return f'stroke="{col}" stroke-width="{w:.2f}" stroke-linecap="round" stroke-linejoin="round" fill="none"'


def _line(out, pts, col, w):
    out.append('<path d="M' + " L".join(f"{px:.2f},{py:.2f}" for px, py in pts) + f'" {_st(col, w)}/>')


def wheelchair(out, x, g, h, col):
    s = h * 0.62                                      # Raddurchmesser
    r = s / 2
    cx, cy = x + r, g - r
    w = h * 0.055
    out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r - w / 2:.2f}" {_st(col, w)}/>')
    fx, fr = cx + s * 0.8, s * 0.1
    out.append(f'<circle cx="{fx:.2f}" cy="{g - fr:.2f}" r="{fr - w / 3:.2f}" {_st(col, w * 0.8)}/>')
    seat = cy - s * 0.1
    _line(out, [(cx - s * 0.15, cy - s * 0.7), (cx - s * 0.05, seat), (cx + s * 0.55, seat), (fx, g - 2 * fr)], col, w)
    out.append(f'<circle cx="{cx + s * 0.1:.2f}" cy="{cy - s * 1.12:.2f}" r="{h * 0.085:.2f}" fill="{col}"/>')   # Kopf
    _line(out, [(cx + s * 0.08, cy - s * 0.88), (cx + s * 0.08, seat - h * 0.05)], col, h * 0.13)            # Rumpf
    _line(out, [(cx + s * 0.1, cy - s * 0.8), (cx + s * 0.34, cy - s * 0.5), (cx + s * 0.32, cy - s * 0.25)], col, w)
    _line(out, [(cx + s * 0.12, seat - h * 0.05), (cx + s * 0.55, seat - h * 0.05), (cx + s * 0.62, g - s * 0.28)],
          col, h * 0.09)
    return s * 1.0


def cane_walker(out, x, g, h, col):
    """Person mit weißem Langstock (rote Spitze)."""
    px = x + h * 0.12
    out.append(f'<circle cx="{px + h * 0.02:.2f}" cy="{g - h * 0.91:.2f}" r="{h * 0.085:.2f}" fill="{col}"/>')
    _line(out, [(px, g - h * 0.78), (px, g - h * 0.46)], col, h * 0.13)
    _line(out, [(px, g - h * 0.46), (px - h * 0.09, g - h * 0.02)], col, h * 0.09)
    _line(out, [(px, g - h * 0.46), (px + h * 0.12, g - h * 0.02)], col, h * 0.09)
    hand = (px + h * 0.17, g - h * 0.5)
    _line(out, [(px + h * 0.01, g - h * 0.72), hand], col, h * 0.055)
    tip = (px + h * 0.48, g)
    _line(out, [hand, tip], c.INK, h * 0.035)                     # Umriss, damit Weiß sichtbar ist
    _line(out, [hand, tip], "#ffffff", h * 0.02)
    _line(out, [(tip[0] - h * 0.06, tip[1] - h * 0.07), tip], "#e03131", h * 0.03)
    return h * 0.62


def rollator_user(out, x, g, h, col):
    """Ältere Person, leicht gebeugt, mit Rollator."""
    px = x + h * 0.1
    out.append(f'<circle cx="{px + h * 0.12:.2f}" cy="{g - h * 0.84:.2f}" r="{h * 0.085:.2f}" fill="{col}"/>')
    _line(out, [(px + h * 0.08, g - h * 0.72), (px, g - h * 0.44)], col, h * 0.13)
    _line(out, [(px, g - h * 0.44), (px - h * 0.04, g - h * 0.02)], col, h * 0.09)
    _line(out, [(px, g - h * 0.44), (px + h * 0.1, g - h * 0.02)], col, h * 0.09)
    grip = (px + h * 0.3, g - h * 0.5)
    _line(out, [(px + h * 0.08, g - h * 0.66), grip], col, h * 0.055)
    frame = "#495057"
    rw = h * 0.05
    rear, front = (px + h * 0.3, g - rw), (px + h * 0.55, g - rw)
    _line(out, [grip, rear], frame, h * 0.03)
    _line(out, [(grip[0] + h * 0.04, grip[1]), front], frame, h * 0.03)
    _line(out, [(px + h * 0.31, g - h * 0.28), (px + h * 0.5, g - h * 0.28)], frame, h * 0.03)    # Sitzbügel
    for wx, wy in (rear, front):
        out.append(f'<circle cx="{wx:.2f}" cy="{wy:.2f}" r="{rw:.2f}" fill="{frame}"/>')
    return h * 0.7


def stroller_parent(out, x, g, h, col):
    """Elternteil mit Kinderwagen."""
    px = x + h * 0.1
    out.append(f'<circle cx="{px + h * 0.02:.2f}" cy="{g - h * 0.91:.2f}" r="{h * 0.085:.2f}" fill="{col}"/>')
    _line(out, [(px, g - h * 0.78), (px, g - h * 0.46)], col, h * 0.13)
    _line(out, [(px, g - h * 0.46), (px - h * 0.08, g - h * 0.02)], col, h * 0.09)
    _line(out, [(px, g - h * 0.46), (px + h * 0.1, g - h * 0.02)], col, h * 0.09)
    handle = (px + h * 0.26, g - h * 0.58)
    _line(out, [(px + h * 0.01, g - h * 0.72), handle], col, h * 0.055)
    frame = "#495057"
    _line(out, [handle, (px + h * 0.36, g - h * 0.36)], frame, h * 0.03)
    bx, by, bw, bh = px + h * 0.34, g - h * 0.44, h * 0.38, h * 0.2
    out.append(f'<path d="M{bx:.2f},{by:.2f} H{bx + bw:.2f} Q{bx + bw:.2f},{by + bh:.2f} {bx + bw / 2:.2f},{by + bh:.2f} '
               f'Q{bx:.2f},{by + bh:.2f} {bx:.2f},{by:.2f} Z" fill="#74c0fc"/>')                      # Wanne
    out.append(f'<path d="M{bx + bw * 0.55:.2f},{by:.2f} A{bw * 0.45:.2f},{bw * 0.45:.2f} 0 0 0 {bx + bw:.2f},{by:.2f} Z" '
               f'fill="#4dabf7"/>')                                                                   # Verdeck
    for wx in (bx + bw * 0.2, bx + bw * 0.85):
        _line(out, [(bx + bw / 2, by + bh), (wx, g - h * 0.06)], frame, h * 0.025)
        out.append(f'<circle cx="{wx:.2f}" cy="{g - h * 0.06:.2f}" r="{h * 0.06:.2f}" fill="{frame}"/>')
    return h * 0.85


def cliff(out, x0, top, ground):
    """Ein Bordstein, gezeichnet wie eine Felswand: oben Gehweg und Gipfelfahne, vorne zerklüftet."""
    import random
    rnd = random.Random(12)
    pts = [(x0 + 4, top)]
    yy = top
    while yy < ground - 6:                       # zerklüftete Vorderkante
        yy += rnd.uniform(7, 13)
        pts.append((x0 + rnd.uniform(-5, 6), min(yy, ground)))
    pts.append((x0 - 3, ground))
    d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + f" L{W + 2},{ground} L{W + 2},{top} Z"
    out.append(f'<path d="{d}" fill="{STONE_FRONT}"/>')
    for _ in range(9):                           # Risse und Kanten im Fels
        cx, cy = x0 + rnd.uniform(8, W - x0 - 4), rnd.uniform(top + 10, ground - 8)
        out.append(f'<path d="M{cx:.1f},{cy:.1f} l{rnd.uniform(-6, 6):.1f},{rnd.uniform(5, 12):.1f} '
                   f'l{rnd.uniform(-4, 4):.1f},{rnd.uniform(4, 9):.1f}" stroke="{STONE_LINE}" stroke-width="0.9" '
                   f'fill="none" stroke-linecap="round"/>')
    for _ in range(5):                           # helle Flächen
        cx, cy = x0 + rnd.uniform(6, W - x0 - 10), rnd.uniform(top + 8, ground - 14)
        out.append(f'<path d="M{cx:.1f},{cy:.1f} l7,-3 l3,7 l-8,2 Z" fill="#b8bdc3"/>')
    out.append(f'<rect x="{x0 + 2:.1f}" y="{top - 4:.1f}" width="{W - x0:.1f}" height="5" fill="{STONE_TOP}"/>')   # Gehweg oben
    fx = x0 + 10                                 # Gipfelfahne
    out.append(f'<line x1="{fx:.1f}" y1="{top - 4:.1f}" x2="{fx:.1f}" y2="{top - 20:.1f}" stroke="{c.INK}" stroke-width="0.9"/>')
    out.append(f'<path d="M{fx:.1f},{top - 20:.1f} L{fx + 9:.1f},{top - 17:.1f} L{fx:.1f},{top - 14:.1f} Z" fill="#e03131"/>')
    # Maßpfeil „12 cm“ auf dem Fels
    ax = x0 + 22
    st = 'stroke="#ffffff" stroke-width="1" stroke-linecap="round" fill="none"'
    out.append(f'<line x1="{ax:.2f}" y1="{top + 2:.2f}" x2="{ax:.2f}" y2="{ground - 1:.2f}" {st}/>')
    for yy, dd in [(top + 2, 1), (ground - 1, -1)]:
        out.append(f'<path d="M{ax - 2.6:.2f},{yy + 3.8 * dd:.2f} L{ax:.2f},{yy:.2f} L{ax + 2.6:.2f},{yy + 3.8 * dd:.2f}" {st}/>')
    ls = 10
    ly = (top + ground) / 2
    lw = druck.text_width("12 cm", 700, ls)
    out.append(f'<rect x="{ax - lw / 2 - 2:.2f}" y="{ly - ls * 0.55:.2f}" width="{lw + 4:.2f}" height="{ls * 1.1:.2f}" '
               f'fill="{STONE_FRONT}"/>')
    out.append(text(ax, ly + druck.cap_height(700, ls) / 2, "12 cm", ls, 700, "#ffffff", "middle"))


def scene(out, top, ground, x_cliff, fh):
    out.append(f'<rect x="0" y="{ground:.2f}" width="{W}" height="6" fill="{GROUND}"/>')
    cliff(out, x_cliff, top, ground)
    # Jede Figur stellt die Frage, die StreetComplete wirklich stellt (Sprechblase über dem Kopf).
    # Kopfposition relativ zur linken Kante x: (dx, dy) in Körpergrößen.
    figs = [(rollator_user, "#e8590c", (0.22, 0.84), ["Gibt es hier", "eine Bank?"]),
            (stroller_parent, "#0c8599", (0.12, 0.91), ["Gibt es eine", "Rampe?"]),
            (cane_walker, ACCENT, (0.14, 0.91), ["Gibt es", "Leitlinien?"]),
            (wheelchair, "#c2255c", (0.372, 1.0), ["Wie hoch ist", "der Bordstein?"])]
    x = M - 2
    prev_right = 0
    for fig, col, (dx, dy), q in figs:
        hx, hy = x + dx * fh, ground - dy * fh
        prev_right = bubble(out, hx, hy - fh * 0.12 - 3, q, col, prev_right)
        x += fig(out, x, ground, fh, col) + 0.5
    assert x < x_cliff - 4, ("Figuren stoßen an den Fels", x, x_cliff)


def bubble(out, hx, tip_y, lines, col, min_x, size=4.4):
    """Sprechblase, Spitze bei (hx, tip_y). Rückt nach rechts, falls sie die vorige berühren würde."""
    w = max(druck.text_width(l, 600, size) for l in lines) + 5
    h = len(lines) * size * 1.2 + 3
    bx = max(hx - w * 0.35, min_x + 2)
    by = tip_y - 3 - h
    out.append(f'<path d="M{hx - 1.8:.2f},{by + h - 0.5:.2f} L{hx:.2f},{tip_y:.2f} L{hx + 1.8:.2f},{by + h - 0.5:.2f} Z" fill="#fff"/>')
    out.append(f'<rect x="{bx:.2f}" y="{by:.2f}" width="{w:.2f}" height="{h:.2f}" rx="2.5" fill="#fff" '
               f'stroke="{col}" stroke-width="0.6"/>')
    out.append(f'<path d="M{hx - 1.8:.2f},{by + h - 0.3:.2f} L{hx:.2f},{tip_y:.2f} L{hx + 1.8:.2f},{by + h - 0.3:.2f}" '
               f'fill="none" stroke="{col}" stroke-width="0.6"/>')
    for i, line in enumerate(lines):
        out.append(text(bx + 2.5, by + 1.6 + druck.cap_height(600, size) + i * size * 1.2, line, size, 600, c.INK))
    return bx + w


def poster():
    out = []
    # Der Fels steht rechts und reicht fast bis oben. Der Titel nutzt den Himmel links darüber,
    # die Menschen stehen unten links am Fuß. Alliteration Bordstein – Berg.
    x_cliff = 134
    top, ground = M + 24, M + 176
    y = lines_block(out, M + 6, ["Für dich", "ein Bordstein."], 19, 700, c.INK, lead=1.02)
    y = lines_block(out, y + 9, ["Für andere", "ein Berg."], 27, 700, ACCENT, lead=0.98)
    assert M + druck.text_width("ein Bordstein.", 700, 19) < x_cliff - 6
    scene(out, top, ground, x_cliff, 39)
    y = ground + 6 + 7

    # Die Fragen stehen in den Sprechblasen; alles Weitere steht in einem Block neben dem QR-Code.
    qtop = c.bottom(out, c.INK, SUB, ACCENT,
                      ["Ein Fingertipp von dir macht", "den Weg für andere planbar."],   # zwei gleich lange Zeilen
                      # beide früheren Textblöcke in einem: was die App tut und was die Antworten bewirken
                      "Die App StreetComplete fragt dich unterwegs nach Stufen, Rampen und Bordsteinen. "
                      "Mit deinen Antworten planen andere ihren Weg – zum Beispiel mit Wheelmap.",
                      url=druck.go("a/sozial"), qs=51, s1=9.0, s2=5.0, w1=700, qr_right=True,
                      url_label="Scan und hilf mit → streetcomplete.app")   # Pfeil zeigt zum QR-Code
    assert y < qtop - 6, (y, qtop)
    return c.page(BG, out)


def main():
    druck.use_project_fonts()
    c.build("aushang-sozial", poster())


if __name__ == "__main__":
    main()
