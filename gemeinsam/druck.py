"""Gemeinsame Bausteine für die OSM-Fulda-Drucksachen.

Schrift Barlow Condensed (OFL, ./fonts), Community-Angaben (community.toml), QR-Codes als Vektor,
Text-Messung für Zeilenumbruch und Ausrichtung. Alle Maße in mm.
"""
import base64
import os
import subprocess
import sys
import tomllib

import qrcode
from fontTools.ttLib import TTFont
from qrcode.constants import ERROR_CORRECT_M

DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DIR)
FONT_DIR = os.path.join(DIR, "fonts")

FONT = "Barlow Condensed"
INK = "#2d3335"        # Textfarbe wie im Titelbild (QR-Codes bleiben reinschwarz)
GREY = "#666"
ACCENT = "#3f7d32"     # Grün passend zur Karte im Titelbild

W, H = 85, 55          # Kartenformat
BLEED = 3              # Beschnitt rundum

# --- Community ---------------------------------------------------------------
# Alles, was auf eine Community gemünzt ist (Ort, Absender, Logo, Titelbild, QR-Ziele), steht in einer
# TOML-Datei: Standard ist community.toml (Fulda), eine andere wählt bauen.py über OSM_COMMUNITY.
# Fulda baut wie bisher in die Ordner der Drucksachen, jede andere Community nach ausgabe/<name>/.

DEFAULT_CONFIG = os.path.join(DIR, "community.toml")
CONFIG = os.path.abspath(os.environ.get("OSM_COMMUNITY") or DEFAULT_CONFIG)
with open(CONFIG, "rb") as _f:
    COMMUNITY = tomllib.load(_f)
EIGENE = CONFIG != DEFAULT_CONFIG
SLUG = os.path.splitext(os.path.basename(CONFIG))[0]


def _bild(key):
    p = COMMUNITY.get("bilder", {}).get(key)
    if not p:
        return None
    p = os.path.join(os.path.dirname(CONFIG), p)
    if not os.path.isfile(p):
        sys.exit(f"{CONFIG}: [bilder] {key} = {p} gibt es nicht")
    return p


ZWECKE = ["loslegen", "finden", "bearbeiten", "fotos", "chat", "wiki", "drucken"]   # shop ist freiwillig


def _pruefen(c):
    """Fehlende Einträge auf einmal melden – sonst bricht ein Skript irgendwo mit KeyError ab."""
    fehlt = [k for k in ("ort", "schriftzug") if not isinstance(c.get(k), str)]
    a = c.get("absender", {})
    fehlt += [f"absender.{k}" for k in ("name", "kontakt") if not a.get(k)]
    links = c.get("links", {})
    for z in ZWECKE + (["shop"] if "shop" in links else []):
        fehlt += [f"links.{z}.{k}" for k in ("url", "zeigen") if not links.get(z, {}).get(k)]
    if fehlt:
        sys.exit(f"{CONFIG}: es fehlt " + ", ".join(fehlt) + " (Vorlage: community-vorlage.toml)")


_pruefen(COMMUNITY)
ORT = COMMUNITY["ort"]
SCHRIFTZUG = COMMUNITY["schriftzug"]
ABSENDER = COMMUNITY["absender"]["name"]
_kontakt = COMMUNITY["absender"]["kontakt"]
KONTAKT = _kontakt if isinstance(_kontakt, str) else " · ".join(_kontakt)    # Liste oder ein String
LOGO = _bild("logo") or os.path.join(DIR, "assets", "osm-logo.svg")
BANNER = _bild("titelbild")          # None: der klassische Aushang zeigt Logo und Schriftzug
LINKS = COMMUNITY["links"]


def go(zweck):
    """Ziel des QR-Codes für einen Zweck (loslegen, finden, bearbeiten, fotos, chat, wiki, drucken, shop)."""
    return LINKS[zweck]["url"]


def show(zweck):
    """Adresse zum Abtippen unter dem QR-Code (manche scannen fremde QR-Codes lieber nicht)."""
    return LINKS[zweck]["zeigen"]


def ausgabe(teil):
    """Ordner für die Dateien einer Drucksache (aushang, motivkarten, …): Fulda im Repo, sonst ausgabe/<name>/."""
    d = os.path.join(ROOT, "ausgabe", SLUG, teil) if EIGENE else os.path.join(ROOT, teil)
    os.makedirs(d, exist_ok=True)
    return d


_gemeldet = set()


def shrink(s, weight, size, width, what="Text"):
    """Schriftgröße, bei der s in width passt – höchstens size. Meldet (einmal), wenn verkleinert wird;
    unter 2/3 der vorgesehenen Größe mit dem Rat, den Text in community.toml zu kürzen."""
    w = text_width(s, weight, size)
    if w <= width:
        return size
    new = size * width / w
    if (what, s, size) not in _gemeldet:
        _gemeldet.add((what, s, size))
        rat = " – schwer lesbar, lieber kürzen" if new < size * 2 / 3 else ""
        print(f"  Hinweis: {what} zu lang, auf {new / size:.0%} verkleinert{rat}: {s}", file=sys.stderr)
    return new


# --- Schrift -----------------------------------------------------------------

WEIGHT_FILES = {700: "Bold", 600: "SemiBold", 500: "Medium", 400: "Regular"}
_fonts = {}


def font(weight):
    if weight not in _fonts:
        _fonts[weight] = TTFont(os.path.join(FONT_DIR, f"BarlowCondensed-{WEIGHT_FILES[weight]}.ttf"))
    return _fonts[weight]


def text_width(text, weight, size, spacing=0.0):
    """Breite in mm (ohne Kerning), Laufweite nur zwischen den Zeichen."""
    f = font(weight)
    cmap, hmtx, upem = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    adv = sum(hmtx[cmap[ord(ch)]][0] for ch in text)
    return adv / upem * size + spacing * (len(text) - 1)


def cap_height(weight, size):
    f = font(weight)
    return f["OS/2"].sCapHeight / f["head"].unitsPerEm * size


def wrap(text, weight, size, width):
    lines, cur = [], ""
    for word in text.split(" "):   # nur normale Leerzeichen – \u00a0 hält zusammen
        if not word:
            continue
        trial = f"{cur} {word}".strip()
        if cur and text_width(trial, weight, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur] if cur else lines


def use_project_fonts():
    """Schriften aus ./fonts für rsvg-convert verfügbar machen, ohne sie zu installieren."""
    conf = os.path.join(FONT_DIR, "fonts.conf")
    with open(conf, "w") as f:
        f.write(f'<?xml version="1.0"?>\n<fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
                f'<dir>{FONT_DIR}</dir></fontconfig>\n')
    os.environ["FONTCONFIG_FILE"] = conf


# --- Grafik ------------------------------------------------------------------

def qr_path(data, x0, y0, size):
    """QR-Code als SVG-Pfad (Fehlerkorrektur M, ohne Ruhezone). -> (d, version, module, mm/modul)"""
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=0)
    qr.add_data(data)
    qr.make(fit=True)
    m = qr.get_matrix()
    n = len(m)
    s = size / n
    parts = []
    for r, row in enumerate(m):
        c = 0
        while c < n:
            if row[c]:
                start = c
                while c < n and row[c]:
                    c += 1
                parts.append(f"M{x0 + start * s:.4f},{y0 + r * s:.4f}h{(c - start) * s:.4f}v{s:.4f}h{-(c - start) * s:.4f}z")
            else:
                c += 1
    return "".join(parts), qr.version, n, s


def logo_svg(x, y, size, dpi=1200):
    """Logo als opakes PNG auf Weiß einbetten.

    Das Logo hat weichgezeichnete Schatten und halbtransparente Verläufe. Als Vektor landen die
    im PDF als Soft-Masks, die viele Druckertreiber als grauen Kasten ums Logo drucken.
    Vorab gerendert ohne Transparenz gibt es das Problem nicht (Karten sind weiß hinterlegt).
    """
    px = round(size / 25.4 * dpi)
    if LOGO.lower().endswith(".svg"):
        data = subprocess.run(["rsvg-convert", "-b", "white", "-w", str(px), "-h", str(px), LOGO],
                              check=True, capture_output=True).stdout
    else:                                        # Pixelbild: auf Weiß, quadratisch eingepasst
        from io import BytesIO
        from PIL import Image, ImageOps
        im = ImageOps.contain(Image.open(LOGO).convert("RGBA"), (px, px), Image.LANCZOS)   # auch vergrößern
        flat = Image.new("RGB", (px, px), "#fff")
        flat.paste(im, ((px - im.width) // 2, (px - im.height) // 2), im)
        buf = BytesIO()
        flat.save(buf, "PNG")
        data = buf.getvalue()
    href = "data:image/png;base64," + base64.b64encode(data).decode()
    return f'<image x="{x:.2f}" y="{y:.2f}" width="{size}" height="{size}" href="{href}"/>'


def card_page_upright(bg, body):
    """Karte hochkant 55x85 mm + Beschnitt; body in Kartenkoordinaten (0,0 = Endformat-Ecke). Vorschau/PDF."""
    w, h = H, W
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2 * BLEED}mm" height="{h + 2 * BLEED}mm" '
        f'viewBox="{-BLEED} {-BLEED} {w + 2 * BLEED} {h + 2 * BLEED}">',
        f'<rect x="{-BLEED}" y="{-BLEED}" width="{w + 2 * BLEED}" height="{h + 2 * BLEED}" fill="{bg}"/>',
        f'<g font-family="{FONT}">', *body, "</g></svg>",
    ])


def card_page_rotated(bg, body, side):
    """Dieselbe Hochkant-Karte quer gelegt (85x55 + Beschnitt) für den Bogen aus make_a4.py.

    side="vorne": gegen den Uhrzeigersinn (Oberkante links), "hinten": im Uhrzeigersinn (Oberkante rechts).
    Nach Duplex „an langer Kante spiegeln“ stehen dann beide Seiten aufrecht, wenn man die Karte
    seitlich umdreht.
    """
    m = f"matrix(0 -1 1 0 0 {H})" if side == "vorne" else f"matrix(0 1 -1 0 {W} 0)"
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W + 2 * BLEED}mm" height="{H + 2 * BLEED}mm" '
        f'viewBox="{-BLEED} {-BLEED} {W + 2 * BLEED} {H + 2 * BLEED}">',
        f'<rect x="{-BLEED}" y="{-BLEED}" width="{W + 2 * BLEED}" height="{H + 2 * BLEED}" fill="{bg}"/>',
        f'<g transform="{m}" font-family="{FONT}">', *body, "</g></svg>",
    ])


def png(svg, out, dpi=600):
    subprocess.run(["rsvg-convert", "-d", str(dpi), "-p", str(dpi), "-o", out, svg], check=True)


def pdf(svgs, out):
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", out, *svgs], check=True)
