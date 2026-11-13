#!/usr/bin/env python3
"""Motivkarten 55x85 mm hochkant, doppelseitig – zum Liegenlassen (Wartezimmer, Café, Infostand).

Vorderseite: nur der Hingucker, je ein Motiv (klein gefasste Aushänge).
Rückseite:   für alle Motive gleich – „Fehlt was? Trag es ein.“, ein QR-Code, Community-Kontakt.

Druckbogen: das gewohnte Raster 2x5 mit 85x55 (../gemeinsam/make_a4.py), die Karten liegen darin
gedreht. Vorderseite gegen den Uhrzeigersinn, Rückseite im Uhrzeigersinn: Nach „an langer Kante
spiegeln“ stehen beide Seiten aufrecht, wenn man die Karte seitlich umdreht.

  motivkarte-<motiv>.png, motivkarte-hinten.png   – Vorschau hochkant
  motivkarte-<motiv>-a4.pdf                       – Bogen, Seite 1 Motiv, Seite 2 Rückseite
  vorschau.png                                    – alle Vorderseiten und die Rückseite nebeneinander

Motive: klassisch, gelb, pixel, pappe, sozial – wie die Aushänge in ../aushang.
Pixel, Pappe und Sozial werden mit den Zeichenfunktionen aus ../aushang
auf eine „virtuelle“ Fläche gezeichnet, die so breit ist wie A4 (210, Rand 16), und dann verkleinert.
"""
import os
import sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gemeinsam"))
sys.path.insert(0, os.path.join(HERE, "..", "aushang"))
import druck  # noqa: E402
import make_a4  # noqa: E402
import make_pappe as pappe  # noqa: E402  Zeichnungen und Texte aus ../aushang
import make_pixel as px  # noqa: E402
import make_sozial as sozial  # noqa: E402

W, H = 55, 85            # Karte hochkant (Endformat)
B = druck.BLEED          # Beschnitt rundum
SAFE = 4                 # Sicherheitsabstand innen
HEAD_BACK = 9.5         # Titel der Rückseite (höchstens; passt sich an die Breite an)
TW = W - 2 * SAFE
INK, GREY, ACCENT = druck.INK, druck.GREY, druck.ACCENT

# Virtuelle Fläche für die Aushang-Motive: 210 breit wie A4, Rand 16 → auf der Karte Rand ≈ 4,2 mm
VS = W / 210                 # Maßstab virtuell → Karte
VW, VH, VM = 210, H / VS, 16

BACK = {
    "head": ["Fehlt was?", "Trag es ein."],
    # das Warum: wohin die Antwort geht (OSM ist keine Karte, sondern freie Daten)
    "body": ["Deine Antwort landet in OpenStreetMap –", "freie Daten, die Apps weltweit nutzen."],
    "rule": ["Einzige Regel: Nur eintragen,", "was es wirklich gibt."],     # feste Zeilen
    "community": ["OpenStreetMap-Community Fulda", f"{druck.SHOW_WIKI} · {druck.SHOW_MATRIX}"],
}


# --- Text --------------------------------------------------------------------

def text(x, y, s, size, weight=400, fill=INK, anchor="start", spacing=None):
    sp = f' letter-spacing="{spacing:.3f}"' if spacing else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size:.3f}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{sp}>{escape(s)}</text>')


def cap(weight, size):
    return druck.cap_height(weight, size)


def fit(lines, weight, max_size, width=TW):
    """Größte Schrift bis max_size, bei der jede Zeile in die Breite passt."""
    return min(max_size, *(max_size * width / druck.text_width(l, weight, max_size) for l in lines))


def lines_block(out, y, lines, size, weight, fill=INK, lead=1.12, x=SAFE, anchor="start"):
    """Feste Zeilen; y = Oberkante. Gibt die letzte Grundlinie zurück."""
    y += cap(weight, size)
    for i, l in enumerate(lines):
        assert druck.text_width(l, weight, size) <= TW + 0.01, ("zu breit", l)
        out.append(text(x, y + i * size * lead, l, size, weight, fill, anchor))
    return y + (len(lines) - 1) * size * lead


# --- Vorderseiten --------------------------------------------------------------

def front_klassisch():
    """Die ruhige Fassung, wie die frühere Infokarte: Logo, Schriftzug und der Aufhänger des Aushangs.

    Alles mittig. Das quadratische Logo statt des breiten Titelbilds, das hochkant wie ein Klotz wirkt.
    """
    out = []
    ls = 30
    y = 7
    out.append(druck.logo_svg((W - ls) / 2, y, ls))
    y += ls + 3
    kick, ks = "OPENSTREETMAP FULDA", 2.6
    sp = 0.55
    y += cap(500, ks)
    out.append(text(W / 2 + sp / 2, y, kick, ks, 500, GREY, "middle", spacing=sp))
    head = ["Du nutzt diese", "Karte jeden Tag.", "Ohne es zu wissen."]
    hs = fit(head, 700, 7.2)
    y = lines_block(out, y + 5, head, hs, 700, lead=1.12, x=W / 2, anchor="middle")
    sub = ["Gemacht von Menschen wie dir –", "auch in Fulda."]
    y = lines_block(out, y + 3.6, sub, 3.6, 500, ACCENT, lead=1.25, x=W / 2, anchor="middle")
    assert y < H - SAFE - 2, ("Vorderseite zu voll", round(y, 1))
    return "#fff", out


def front_gelb():
    """Politik: Wem gehört die Karte? Nur Typografie auf Gelb, wie der Aushang.

    Drei Absätze – Google, Apple, OpenStreetMap –, dazwischen feine Linien.
    """
    out = []
    dim = "#6b5a12"
    ss = fit(["gehört Google.", "OpenStreetMap"], 600, 6.0)
    gap = 2.6                                     # Abstand Text → Linie → Text

    def rule(y):
        if GELB_RULE == "kurz":
            out.append(f'<line x1="{SAFE}" y1="{y:.2f}" x2="{SAFE + 6}" y2="{y:.2f}" stroke="{dim}" stroke-width="0.5"/>')
        elif GELB_RULE == "ton":
            out.append(f'<line x1="{SAFE}" y1="{y:.2f}" x2="{W - SAFE}" y2="{y:.2f}" stroke="#e8b80f" stroke-width="0.35"/>')

    y = lines_block(out, SAFE + 1, ["Google Maps", "gehört Google."], ss, 500, dim, lead=1.1)
    rule(y + gap)
    y = lines_block(out, y + 2 * gap, ["Apple Maps", "gehört Apple."], ss, 500, dim, lead=1.1)
    rule(y + gap)
    y = lines_block(out, y + 2 * gap, ["OpenStreetMap", "gehört"], ss, 700, INK, lead=1.1)
    big = fit(["DIR."], 700, 34)
    y = lines_block(out, y + 3, ["DIR."], big, 700, INK, x=SAFE - 0.8)
    foot = "Gemeingut statt Geschäftsmodell."          # Daten unter offener Lizenz, gehören keinem
    assert y < H - SAFE - 6, ("Vorderseite zu voll", round(y, 1))
    out.append(text(SAFE, H - SAFE, foot, fit([foot], 600, 4.4), 600, INK))
    return "#ffd43b", out


# Trennung zwischen Google / Apple / OpenStreetMap: "abstand" (keine Linie), "kurz", "ton"
GELB_RULE = "ton"


def scaled(body):
    """Virtuelle Zeichnung (A4-Breite) auf Kartengröße verkleinern."""
    return [f'<g transform="scale({VS:.6f})">', *body, "</g>"]


def front_pixel():
    """Level 1: Dein Viertel – Titel, Spielbild mit Erfolg „Bürger“, Spruch."""
    t = px.THEMES["hell"]
    out = ['<g shape-rendering="crispEdges">']
    y = VM
    for i, (s, k, col) in enumerate(px.TITLE):
        y += px.title(out, VM, y, s, k, t[col]) + (7 if i == len(px.TITLE) - 1 else 5)
    ss = 21
    slogan_h = cap(700, ss) + ss * 1.12
    cols = int((VW - 2 * VM) // px.T)
    rows = min(50, int((VH - VM - slogan_h - 12 - y - 4 * px.U) // px.T))
    mw, mh = cols * px.T, rows * px.T
    mx = VM + (VW - 2 * VM - mw) / 2
    out.append(f'<rect x="{mx - 2 * px.U:.2f}" y="{y - 2 * px.U:.2f}" width="{mw + 4 * px.U:.2f}" '
               f'height="{mh + 4 * px.U:.2f}" fill="{t["frame"]}"/>')
    out.append(f'<clipPath id="screen"><rect x="{mx:.2f}" y="{y:.2f}" width="{mw:.2f}" height="{mh:.2f}"/></clipPath>')
    out.append('<g clip-path="url(#screen)">')
    px.game_screen(out, mx, y, cols, rows)
    out.append("</g></g>")
    # Spruch unten, zweizeilig; das grüne „(K)“ wie auf dem Aushang
    base = VH - VM - ss * 1.12
    out.append(f'<text x="{VM}" y="{base:.2f}" font-size="{ss}" font-weight="700" fill="{t["fg"]}">'
               f'<tspan fill="{t["accent"]}">(K)</tspan>ein Spiel.</text>')
    out.append(text(VM, base + ss * 1.12, "Dein echtes Viertel.", ss, 700, t["fg"]))
    assert druck.text_width("Dein echtes Viertel.", 700, ss) <= VW - 2 * VM
    assert y + mh + 2 * px.U + 8 < base - cap(700, ss), "Spielbild stößt an den Spruch"
    return t["bg"], scaled(out)


def front_pappe():
    """Mapping for Future: Schilder im Hintergrund, großes Pappschild, Spruch auf Klebeband am Pfosten."""
    import random
    out = []
    pappe.crowd(out)
    sh = 150
    end = pappe.main_sign(out, VW / 2, VM + 30 + sh / 2, VW - 2 * VM - 4, sh, -4, stick=VH)
    # Spruch auf zwei Streifen Klebeband quer über den Pfosten
    for i, (line, rot) in enumerate([("DIE ZUKUNFT BEGINNT", -3), ("VOR DEINER TÜR!", 2)]):
        size = 13
        lw = pappe.mwidth(line, size) + 14
        lh = pappe.mcap(size) + 10
        lx = (VW - lw) / 2 + (-6 if i == 0 else 10)
        ly = end + 34 + i * (lh + 6)
        rnd = random.Random(30 + i)
        d = pappe.jagged_rect(rnd, lx, ly, lw, lh, 0.5)
        out.append(f'<g transform="rotate({rot} {lx + lw / 2:.1f} {ly + lh / 2:.1f})">')
        out.append(f'<path d="{d}" fill="#000" opacity="0.15" transform="translate(1 1.5)"/>')
        out.append(f'<path d="{d}" fill="{pappe.TAPE}"/>')
        out.append(pappe.mtext(lx + 7, ly + lh / 2 + pappe.mcap(size) / 2, line, size, pappe.PEN, 0, bold=0.3))
        out.append("</g>")
        assert lx > 4 and lx + lw < VW - 4, ("Klebeband zu breit", line)
    assert ly + lh < VH - VM, "Klebeband ragt unten heraus"
    return pappe.BG, scaled(out)


FELS_X, FIG_H = 154, 46      # Sozial: linke Kante des Felses, Körpergröße der Figuren (virtuell)


def front_sozial():
    """Für dich ein Bordstein. Für andere ein Berg. – hoher Fels, vier Menschen davor, eine Frage.

    Der Fels ist schmaler als auf dem Aushang, damit alle vier Figuren groß genug Platz haben.
    """
    out = []
    x_cliff, fh = FELS_X, FIG_H
    top, ground = VM + 24, VH - VM - 2
    tw = x_cliff - 8 - VM                         # Titel links neben dem Fels
    s1 = min(fit(["Für dich", "ein Bordstein."], 700, 26, tw),
             fit(["Für andere", "ein Berg."], 700, 26 * 27 / 19, tw) * 19 / 27)
    s2 = s1 * 27 / 19
    y = sozial.lines_block(out, VM + 8, ["Für dich", "ein Bordstein."], s1, 700, INK, lead=1.02)
    sozial.lines_block(out, y + 10, ["Für andere", "ein Berg."], s2, 700, sozial.ACCENT, lead=0.98)
    out.append(f'<rect x="{-B / VS:.1f}" y="{ground:.2f}" width="{VW + 2 * B / VS:.1f}" '
               f'height="{VH - ground + B / VS:.2f}" fill="{sozial.GROUND}"/>')
    sozial.cliff(out, x_cliff, top, ground)
    # Fels und Gehweg rechts bis in den Beschnitt verlängern (der Aushang endet an der Blattkante)
    bx, bw = VW + 1, B / VS + 1
    out.append(f'<rect x="{bx}" y="{top:.2f}" width="{bw:.2f}" height="{ground - top:.2f}" fill="{sozial.STONE_FRONT}"/>')
    out.append(f'<rect x="{bx}" y="{top - 4:.2f}" width="{bw:.2f}" height="5" fill="{sozial.STONE_TOP}"/>')
    x = VM - 2
    chair = None
    for fig, col in [(sozial.rollator_user, "#e8590c"), (sozial.stroller_parent, "#0c8599"),
                     (sozial.cane_walker, sozial.ACCENT), (sozial.wheelchair, "#c2255c")]:
        if fig is sozial.wheelchair:
            chair = x
        x += fig(out, x, ground, fh, col) + 1.0
    assert x < x_cliff - 4, ("Figuren stoßen an den Fels", round(x, 1))
    # Eine Frage, groß genug für die Karte – die, die StreetComplete wirklich stellt
    hx, hy = chair + 0.372 * fh, ground - fh
    right = sozial.bubble(out, hx, hy - fh * 0.12 - 3, ["Wie hoch ist", "der Bordstein?"], "#c2255c", VM + 30,
                          size=10)
    assert right < VW - 4, "Sprechblase ragt aus der Karte"
    return sozial.BG, scaled(out)


FRONTS = {"klassisch": front_klassisch, "gelb": front_gelb, "pixel": front_pixel,
          "pappe": front_pappe, "sozial": front_sozial}


# --- Rückseite ----------------------------------------------------------------

def back(url):
    """Alles mittig: Frage, Code, Adresse, zwei kurze Absätze, Absender als Gruppe aus Logo und Text."""
    out = []
    mid = W / 2
    hs = fit(BACK["head"], 700, HEAD_BACK)
    y = lines_block(out, SAFE + 0.5, BACK["head"], hs, 700, lead=1.02, x=mid, anchor="middle")
    qs = 22
    _, ver, n, module = druck.qr_path(url, 0, 0, qs)
    pad = 4 * module                                    # Ruhezone: Grund ist weiß, nur frei halten
    qy = y + 1.2 + pad
    d = druck.qr_path(url, (W - qs) / 2, qy, qs)[0]
    print(f"  QR {url}: v{ver} {n}x{n} Module, {module:.2f} mm/Modul")
    out.append(f'<path d="{d}" fill="#000"/>')
    y = qy + qs + 1.4 + cap(700, 3.6)
    out.append(text(mid, y, druck.SHOW_STREETCOMPLETE, 3.6, 700, ACCENT, "middle"))
    y = lines_block(out, y + 3, BACK["body"], 2.8, 500, INK, lead=1.3, x=mid, anchor="middle")
    y = lines_block(out, y + 2, BACK["rule"], 2.8, 600, INK, lead=1.3, x=mid, anchor="middle")
    # Absender unten: Logo und zwei Zeilen als Gruppe, mittig
    ls, fs = 9, 2.6
    c1, c2 = BACK["community"]
    tw = max(druck.text_width(c1, 700, fs), druck.text_width(c2, 600, fs))
    gx = (W - (ls + 1.6 + tw)) / 2
    ly = H - SAFE - ls + 0.5
    out.append(f'<line x1="{SAFE + 4}" y1="{ly - 2.4:.2f}" x2="{W - SAFE - 4}" y2="{ly - 2.4:.2f}" '
               f'stroke="#ccc" stroke-width="0.2"/>')
    assert y < ly - 5, ("Rückseite zu voll", round(y, 1), round(ly - 5, 1))
    assert gx >= SAFE - 1, "Absender zu breit"
    out.append(druck.logo_svg(gx, ly, ls))
    tx = gx + ls + 1.6
    out.append(text(tx, ly + ls / 2 - 0.6, c1, fs, 700, INK))
    out.append(text(tx, ly + ls / 2 + cap(600, fs) + 0.9, c2, fs, 600, ACCENT))
    return "#fff", out


# --- Seiten -------------------------------------------------------------------

portrait = druck.card_page_upright


def landscape(bg, body, side):
    return druck.card_page_rotated(bg, body, side)


def write(name, svg):
    with open(name, "w") as f:
        f.write(svg)


LABELS = {"klassisch": "Klassisch", "gelb": "Gelb", "pixel": "Pixel", "pappe": "Pappe", "sozial": "Sozial",
          "hinten": "Rückseite (alle)"}


def overview(out="vorschau.png", h=700, gap=20, head=44):
    """Alle Vorderseiten nebeneinander, rechts mit Abstand die Rückseite, je mit Beschriftung."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(os.path.join(druck.FONT_DIR, "BarlowCondensed-SemiBold.ttf"), 30)
    keys = list(FRONTS) + ["hinten"]
    cards = []
    for k in keys:
        im = Image.open(f"motivkarte-{k}.png").convert("RGB")
        cards.append(im.resize((round(im.width * h / im.height), h), Image.LANCZOS))
    cw = cards[0].width
    width = gap + len(keys) * (cw + gap) + 2 * gap          # Extra-Abstand vor der Rückseite
    sheet = Image.new("RGB", (width, head + h + 2 * gap), "white")
    draw = ImageDraw.Draw(sheet)
    x = gap
    for k, im in zip(keys, cards):
        if k == "hinten":
            x += 2 * gap
        sheet.paste(im, (x, head + gap))
        draw.rectangle([x - 1, head + gap - 1, x + cw, head + gap + h], outline="#999")
        draw.text((x + cw / 2, gap + head / 2), LABELS[k], font=font, fill=INK, anchor="mm")
        x += cw + gap
    sheet.save(out)


def main():
    os.chdir(HERE)
    druck.use_project_fonts()
    for key, make in FRONTS.items():
        # Rückseite sieht überall gleich aus, nur der QR-Code ist je Motiv ein anderer Pfad
        bg, body = back(druck.go(f"k/{key}"))
        write(f"bogen-hinten-{key}.svg", landscape(bg, body, "hinten"))
        if key == "klassisch":      # Vorschau der Rückseite
            write("motivkarte-hinten.svg", portrait(bg, body))
            druck.png("motivkarte-hinten.svg", "motivkarte-hinten.png", dpi=400)
        bg, body = make()
        write(f"motivkarte-{key}.svg", portrait(bg, body))
        write(f"bogen-{key}.svg", landscape(bg, body, "vorne"))
        druck.png(f"motivkarte-{key}.svg", f"motivkarte-{key}.png", dpi=400)
        make_a4.build(f"bogen-{key}.svg", f"bogen-hinten-{key}.svg", f"motivkarte-{key}-a4.pdf")
    overview()


if __name__ == "__main__":
    main()
