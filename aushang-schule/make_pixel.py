#!/usr/bin/env python3
"""Schul-Aushang „Level 1: Schulweg“ in Pixel-Optik (A4 hoch), helle und dunkle Fassung.

  aushang-schule-pixel.png/pdf          – helle Fassung, wird gedruckt
  aushang-schule-pixel-dunkel.png/pdf   – optional (python3 make_pixel.py dunkel), viel Toner

Regeln, nach denen das Blatt gebaut ist:
- Eine Geschichte: Titel, Bild, Spruch und QR-Text reden alle vom Schulweg.
- Lesereihenfolge 1-2-3-4: Titel → Spielbild → Spruch → QR. Nichts sonst konkurriert.
- Alles, was zum Spiel gehört (Erfolg, Anzeige, Lücken), liegt IM Bild, wie auf einem Bildschirm.
- Pixel-Grafik: ein Grundpixel U. Jedes Pixel ist ein ganzes Vielfaches davon (keine „Mixels“),
  keine weichen Kanten, eine kleine Farbpalette. Silkscreen hat ein Pixel = 1/8 Geviert,
  darum ist die Schriftgröße immer 8 × (Vielfaches von U).
- QR-Code mit Ruhezone von 4 Modulen (ISO/IEC 18004), Handlungsaufforderung direkt daneben.
- Kontrast nach WCAG: Fließtext mindestens 4,5:1, große Schrift und Grafik mindestens 3:1.
"""
import os
import random

from fontTools.ttLib import TTFont

import common as c
from common import druck

W, H, M = 210, 297, 16
TW = W - 2 * M
PIX = "Silkscreen"
U = 0.75                 # Grundpixel in mm
T = 4 * U                # Kachel der Karte = 4 U = 3 mm

# Spielfarben (gleich in beiden Fassungen, denn sie gehören zum „Bildschirm“)
UI_BG, UI_LINE, UI_TEXT = "#1d2140", "#3dff8f", "#ffffff"
GOLD = "#ffd43b"
GAP = "#e4572e"          # Lücken-Marker
GAP_TEXT = "#ff7a59"     # Rot für Text auf dunklem Grund
GRASS, GRASS2 = "#4fa83d", "#3f9131"
ROAD, LINE, WALK = "#5d616d", "#f2f2f2", "#b9bcc4"
WALL, WINDOW, DOOR = "#ead9a8", "#2b3a67", "#6d4c2f"
ROOFS = ["#c8553d", "#a0522d", "#d9822b"]
SCHOOL_ROOF = "#3f6fb5"
TREE, TREE2 = "#2e7d32", "#256628"
WATER = "#4aa3df"
POLE, LAMP = "#3a3d46", "#ffe066"
PATH = GOLD

THEMES = {
    "dunkel": dict(bg=UI_BG, fg="#ffffff", sub="#aab0d6", level=UI_LINE, accent=UI_LINE, frame="#ffffff"),
    "hell": dict(bg="#f6f3ea", fg=c.INK, sub="#5a6080", level="#17924a", accent="#17924a", frame=c.INK),
}

_pf = {}


def pfont():
    if not _pf:
        _pf["b"] = TTFont(os.path.join(druck.FONT_DIR, "Silkscreen-Bold.ttf"))
    return _pf["b"]


def psize(k):
    """Schriftgröße, bei der ein Schriftpixel k × U groß ist."""
    return 8 * k * U


def pwidth(s, k):
    f = pfont()
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    # der letzte Pixel Abstand gehört nicht zur sichtbaren Breite
    return (sum(hmtx[cmap[ord(c)]][0] for c in s) / 125 - 1) * k * U


def ptext(x, top, s, k, fill, anchor="start"):
    """Pixeltext; top = Oberkante der Großbuchstaben (5 Schriftpixel hoch)."""
    return (f'<text x="{x:.2f}" y="{top + 5 * k * U:.2f}" font-family="{PIX}" font-size="{psize(k):.2f}" '
            f'font-weight="700" fill="{fill}" text-anchor="{anchor}">{c.escape(s)}</text>')


def sprite(out, x, y, k, rows, colors):
    """Pixelbild aus Zeichen-Zeilen; ein Zeichen = k × U."""
    p = k * U
    for r, line in enumerate(rows):
        c = 0
        while c < len(line):
            ch = line[c]
            if ch not in colors:
                c += 1
                continue
            start = c
            while c < len(line) and line[c] == ch:
                c += 1
            out.append(f'<rect x="{x + start * p:.2f}" y="{y + r * p:.2f}" width="{(c - start) * p + 0.02:.2f}" '
                       f'height="{p + 0.02:.2f}" fill="{colors[ch]}"/>')


def panel(out, x, y, w, h, fill, line, k=1, b=1):
    """Fenster mit Pixel-Ecken (Stufe k × U) und 1-U-Rahmen."""
    def notched(x, y, w, h, n):
        return (f"M{x + n},{y} H{x + w - n} V{y + n} H{x + w} V{y + h - n} H{x + w - n} V{y + h} "
                f"H{x + n} V{y + h - n} H{x} V{y + n} H{x + n} Z")
    n = k * U
    out.append(f'<path d="{notched(x, y, w, h, n)}" fill="{line}"/>')
    out.append(f'<path d="{notched(x + b * U, y + b * U, w - 2 * b * U, h - 2 * b * U, n)}" fill="{fill}"/>')


# --- Sprites -----------------------------------------------------------------

HERO = ["..HHHH..", ".HHHHHH.", ".SSSSSS.", ".SESSES.", ".SSSSSS.", "..SSSS..",
        ".GGGGGG.", "SGGGGGGS", ".BB..BB.", ".BB..BB."]
HERO_C = {"H": "#4a2f1d", "S": "#f1c08b", "E": UI_BG, "G": UI_LINE, "B": "#3b4a8a"}
QMARK = [".XXX.", "X...X", "....X", "...X.", "..X..", ".....", "..X.."]
FOOT_L = ["X.X.XX", "......", "XXXXX.", "XXXXXX", ".XXXXX", ".XXXX.",
          ".XXX..", ".XXX..", ".XXXX.", ".XXXX.", "..XX.."]   # großer Zeh innen (rechts)
FOOT_R = [line[::-1] for line in FOOT_L]


def feet(out, x, y, k, col):
    sprite(out, x, y + 2 * k * U, k, FOOT_L, {"X": col})
    sprite(out, x + 7 * k * U, y, k, FOOT_R, {"X": col})


# --- Karte -------------------------------------------------------------------

class Grid:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.c = [[GRASS] * cols for _ in range(rows)]

    def fill(self, x, y, w, h, col):
        for r in range(max(0, y), min(self.rows, y + h)):
            for c in range(max(0, x), min(self.cols, x + w)):
                self.c[r][c] = col

    def set(self, x, y, col):
        self.fill(x, y, 1, 1, col)

    def svg(self, out, x0, y0):
        for r, row in enumerate(self.c):
            c = 0
            while c < self.cols:
                start, col = c, row[c]
                while c < self.cols and row[c] == col:
                    c += 1
                out.append(f'<rect x="{x0 + start * T:.2f}" y="{y0 + r * T:.2f}" '
                           f'width="{(c - start) * T + 0.02:.2f}" height="{T + 0.02:.2f}" fill="{col}"/>')


def house(g, x, y, w, h, roof):
    g.fill(x, y, w, 2, roof)
    g.fill(x, y + 2, w, h - 2, WALL)
    for wx in range(x + 1, x + w - 1, 2):
        g.set(wx, y + 3, WINDOW)
    g.set(x + w // 2, y + h - 1, DOOR)


def tree(g, x, y):
    g.fill(x, y, 3, 2, TREE)
    g.set(x + 1, y, TREE2)
    g.set(x + 1, y + 2, DOOR)


def lamp(g, x, y):
    g.fill(x, y, 2, 1, POLE)
    g.fill(x, y + 1, 1, 3, POLE)
    g.set(x + 1, y + 1, LAMP)


def game_screen(out, x0, y0, cols, rows):
    """Spielbild: Karte, Weg, Figur, Lücken, Erfolg oben, Lücken-Zähler unten rechts."""
    rnd = random.Random(36037)
    g = Grid(cols, rows)
    for _ in range(cols * rows // 9):
        g.set(rnd.randrange(cols), rnd.randrange(rows), GRASS2)

    top = 11                     # oben Platz für die Erfolgs-Meldung
    ry, rx = top + 15, 34        # Hauptstraße (Zeile), Querstraße (Spalte)
    for c in range(cols):        # Bach ganz oben
        g.fill(c, 0, 1, 2 + (c % 7 < 3), WATER)
    g.fill(0, ry - 1, cols, 1, WALK)
    g.fill(0, ry, cols, 3, ROAD)
    g.fill(0, ry + 3, cols, 1, WALK)
    g.fill(rx - 1, top - 2, 1, rows, WALK)
    g.fill(rx, top - 2, 3, rows, ROAD)
    g.fill(rx + 3, top - 2, 1, rows, WALK)
    for c in range(1, cols, 4):
        if not rx - 1 <= c <= rx + 3:
            g.fill(c, ry + 1, 2, 1, LINE)
    for i in range(3):                               # 1 Zebrastreifen
        g.fill(rx - 6 + i * 2, ry, 1, 3, LINE)
    g.fill(rx + 4, ry - 1, 6, 1, GRASS)              # Lücke: Gehweg fehlt

    for x, yy, w, h, roof in [(3, ry + 6, 7, 6, 0), (13, ry + 7, 6, 5, 1), (22, ry + 6, 7, 6, 2),
                              (8, ry + 14, 8, 6, 2), (20, ry + 15, 6, 5, 0),
                              (3, top + 4, 6, 5, 1), (18, top + 5, 7, 6, 0)]:
        house(g, x, yy, w, h, ROOFS[roof])
    sx, sy = rx + 9, top + 3                         # Schule
    g.fill(sx, sy, 18, 3, SCHOOL_ROOF)
    g.fill(sx, sy + 3, 18, 6, WALL)
    for wx in range(sx + 1, sx + 17, 2):
        g.set(wx, sy + 4, WINDOW)
        g.set(wx, sy + 6, WINDOW)
    g.fill(sx + 8, sy + 7, 2, 2, DOOR)
    g.fill(sx + 17, sy - 3, 1, 3, "#dddddd")
    g.fill(sx + 18, sy - 3, 3, 2, GAP)
    for tx, ty in [(10, top + 10), (27, top + 1), (rx + 6, ry + 7), (rx + 16, ry + 8), (cols - 5, ry + 6),
                   (cols - 4, top + 11), (2, ry + 19), (28, ry + 18), (rx + 6, ry + 14)]:
        tree(g, tx, ty)
    lamp(g, 12, ry - 4)                              # 2 Lampen
    lamp(g, rx + 22, ry + 4)
    g.svg(out, x0, y0)

    # Weg vom Haus zur Schule: Punkte 2 U groß, mittig in der Kachel
    path = [(6, ry + 5), (6, ry + 4)] + [(c, ry + 4) for c in range(6, rx - 1)] + \
           [(rx - 2, r) for r in range(ry + 4, sy + 10, -1)] + [(c, sy + 10) for c in range(rx - 2, sx + 9)]
    for i, (c, r) in enumerate(path):
        if i % 2 == 0:
            out.append(f'<rect x="{x0 + c * T + U:.2f}" y="{y0 + r * T + U:.2f}" width="{2 * U:.2f}" '
                       f'height="{2 * U:.2f}" fill="{PATH}"/>')

    sprite(out, x0 + 29 * T, y0 + (top + 8) * T, 2, HERO, HERO_C)   # Figur neben dem Weg

    # 3 Lücken: rotes Feld (14 × 18 U) mit Fragezeichen aus 2-U-Pixeln
    for c, r in [(rx + 5, ry - 6), (rx - 11, ry - 6), (24, top + 1)]:
        mx, my = x0 + c * T, y0 + r * T
        panel(out, mx, my, 18 * U, 22 * U, GAP, "#ffffff", 2, b=2)   # Rahmen 2 U wie die Figur
        sprite(out, mx + 4 * U, my + 4 * U, 2, QMARK, {"X": "#ffffff"})

    # Erfolg oben, wie eine Meldung im Spiel
    l1, l2 = "ERFOLG FREIGESCHALTET", "FUSSGÄNGER"
    tw = 4 * U + 26 * U + 4 * U + max(pwidth(l1, 1), pwidth(l2, 2)) + 5 * U
    th = 34 * U
    tx, ty = x0 + round((cols * T - tw) / 2 / U) * U, y0 + T
    panel(out, tx, ty, tw, th, UI_BG, GOLD, 2)
    feet(out, tx + 4 * U, ty + 4 * U, 2, GOLD)
    out.append(ptext(tx + 34 * U, ty + 8 * U, l1, 1, GOLD))
    out.append(ptext(tx + 34 * U, ty + 19 * U, l2, 2, UI_TEXT))

    # Anzeige unten rechts: nur die Zahl, nach der der QR-Text fragt („Wie viele Lücken …?“).
    # Sie passt zum Bild: drei rote Fragezeichen.
    lab, val = "LÜCKEN", "3"
    lw, vw = pwidth(lab, 2), pwidth(val, 2)
    hw, hh = 5 * U + lw + 8 * U + vw + 5 * U, 22 * U
    hx, hy = x0 + cols * T - hw - 4 * U, y0 + rows * T - hh - 4 * U
    panel(out, hx, hy, hw, hh, UI_BG, UI_LINE, 2)
    out.append(ptext(hx + 5 * U, hy + 7 * U, lab, 2, UI_TEXT))
    out.append(ptext(hx + hw - 5 * U, hy + 7 * U, val, 2, GAP_TEXT, "end"))


# Eigene Pixel-Schrift für den Titel (5 × 7): exakt im Raster, ohne Seitenabstand links,
# und ein W, das wie ein W aussieht.
TITLE_FONT = {
    "S": [".XXXX", "X....", "X....", ".XXX.", "....X", "....X", "XXXX."],
    "C": [".XXXX", "X....", "X....", "X....", "X....", "X....", ".XXXX"],
    "H": ["X...X", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"],
    "U": ["X...X", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    "L": ["X....", "X....", "X....", "X....", "X....", "X....", "XXXXX"],
    "W": ["X...X", "X...X", "X...X", "X.X.X", "X.X.X", "XX.XX", "X...X"],
    "E": ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "XXXXX"],
    "G": [".XXXX", "X....", "X....", "X..XX", "X...X", "X...X", ".XXXX"],
    "V": ["X...X", "X...X", "X...X", "X...X", ".X.X.", ".X.X.", "..X.."],
    "1": ["..X..", ".XX..", "..X..", "..X..", "..X..", "..X..", ".XXX."],
    " ": ["....."] * 7,
}


def title(out, x, y, s, k, col):
    """Titel aus TITLE_FONT; Zeichen 5 + 1 Pixel breit, 7 hoch, ein Pixel = k × U. Gibt die Höhe zurück."""
    for i, ch in enumerate(s):
        sprite(out, x + i * 6 * k * U, y, k, TITLE_FONT[ch], {"X": col})
    return 7 * k * U


def title_width(s, k):
    return (len(s) * 6 - 1) * k * U


# --- Seite -------------------------------------------------------------------

def poster(t):
    out = ['<g shape-rendering="crispEdges">']
    y = M
    y += title(out, M, y, "LEVEL 1", 2, t["level"]) + 5
    y += title(out, M, y, "SCHULWEG", 5, t["fg"]) + 7

    cols, rows = int(TW // T), 45
    mw, mh = cols * T, rows * T
    mx = M + (TW - mw) / 2
    out.append(f'<rect x="{mx - 2 * U:.2f}" y="{y - 2 * U:.2f}" width="{mw + 4 * U:.2f}" height="{mh + 4 * U:.2f}" '
               f'fill="{t["frame"]}"/>')
    out.append(f'<clipPath id="screen"><rect x="{mx:.2f}" y="{y:.2f}" width="{mw:.2f}" height="{mh:.2f}"/></clipPath>')
    out.append('<g clip-path="url(#screen)">')
    game_screen(out, mx, y, cols, rows)
    out.append("</g>")
    y += mh + 2 * U + 9

    ss = 13
    base_y = y + druck.cap_height(700, ss)
    out.append(f'<text x="{M}" y="{base_y:.2f}" font-size="{ss}" font-weight="700" fill="{t["fg"]}">'
               f'<tspan fill="{t["accent"]}">(K)</tspan>ein Spiel. Dein echter Schulweg.</text>')
    out.append("</g>")
    top_qr = c.bottom(out, t["fg"], t["sub"], t["accent"],
                        "Wie viele Lücken hat dein Schulweg? Scan und sieh nach.",
                        # Motiv der Zielgruppe: Quests, Erfolge, Rang – und dass es wirklich etwas bringt
                        "StreetComplete ist wie eine Quest-Karte: Aufgaben lösen, Erfolge holen, aufsteigen. "
                        "Nur dass jede Antwort echten Menschen hilft.",
                        qs=40, s1=7.0, s2=4.7, w1=700, rule_in_text=True)
    assert base_y < top_qr - 6, (base_y, top_qr)
    assert title_width("SCHULWEG", 5) <= TW
    return c.page(t["bg"], out)


def main():
    druck.use_project_fonts()
    # Gedruckt wird die helle Fassung (weniger Toner, sauber aus dem Schulkopierer);
    # die dunkle bleibt als Option: python3 make_pixel.py dunkel
    import sys
    theme = sys.argv[1] if len(sys.argv) > 1 else "hell"
    c.build("aushang-schule-pixel" + ("" if theme == "hell" else f"-{theme}"), poster(THEMES[theme]))


if __name__ == "__main__":
    main()
