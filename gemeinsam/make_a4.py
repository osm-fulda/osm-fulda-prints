#!/usr/bin/env python3
"""A4-Druckbogen (2x5 Visitenkarten, Schnittmarken) aus zwei Karten-SVGs.

Aufruf (normalerweise über die make_*.py der einzelnen Karten):
    python3 gemeinsam/make_a4.py VORNE.svg HINTEN.svg -o bogen.pdf
    python3 gemeinsam/make_a4.py KARTE.svg -o bogen.pdf   # einseitig

Die SVGs dürfen in Inkscape o.ä. bearbeitet werden. Erwartet wird eine Karte
85x55 mm, optional mit Beschnitt rundum (z.B. 91x61 mm = 3 mm Beschnitt).
Der Beschnitt wird abgeschnitten, nur das Endformat landet auf dem Bogen.
Das Raster ist zentriert -> Vorder- und Rückseite liegen beim Duplexdruck
deckungsgleich ("an langer Kante spiegeln").

Schnittlinien: Die Vorderseite bekommt durchgehende, hellgraue Haarlinien über den ganzen
Bogen – sie bleiben auf jedem Teilstück sichtbar, egal in welcher Reihenfolge geschnitten wird.
Die Rückseite bekommt sie nicht (Duplex-Versatz würde sie sonst auf die Karte schieben).
Mit der Vorderseite nach oben schneiden.
"""
import argparse
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import druck

W, H = druck.W, druck.H     # Endformat Karte in mm
A4_W, A4_H = 210, 297
COLS, ROWS = 2, 5
MARK_LEN = 6.0             # Länge Schnittmarken in mm
MARK_GAP = 2.0             # Abstand Schnittmarke -> Kartenraster
MARK_WIDTH = 0.15          # Strichstärke Schnittmarken in mm
GUIDE_WIDTH = 0.1          # durchgehende Schnittlinien (nur Vorderseite)
GUIDE_COLOR = "#aaa"

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
UNIT_MM = {"mm": 1, "cm": 10, "in": 25.4, "pt": 25.4 / 72, "pc": 25.4 / 6, "px": 25.4 / 96, "": 25.4 / 96}


def to_mm(value):
    m = re.fullmatch(r"\s*([\d.]+)\s*([a-z]*)\s*", value or "")
    if not m or m.group(2) not in UNIT_MM:
        raise ValueError(f"Unbekannte Größenangabe: {value!r}")
    return float(m.group(1)) * UNIT_MM[m.group(2)]


def card_symbol(path, ident):
    """Karteninhalt als <g id=...> plus viewBox des Endformats (Beschnitt fällt beim Clippen weg)."""
    root = ET.parse(path).getroot()
    w_mm, h_mm = to_mm(root.get("width")), to_mm(root.get("height"))
    bleed_x, bleed_y = (w_mm - W) / 2, (h_mm - H) / 2
    if bleed_x < -0.01 or bleed_y < -0.01 or abs(bleed_x - bleed_y) > 0.01:
        raise SystemExit(f"{path}: {w_mm:.1f}x{h_mm:.1f} mm passt nicht zu {W}x{H} mm (+ gleichmäßiger Beschnitt)")
    vb = [float(v) for v in re.split(r"[\s,]+", (root.get("viewBox") or f"0 0 {w_mm} {h_mm}").strip())]
    sx, sy = vb[2] / w_mm, vb[3] / h_mm
    trim = (vb[0] + bleed_x * sx, vb[1] + bleed_y * sy, W * sx, H * sy)
    # IDs eindeutig machen, falls Vorder- und Rückseite gleiche IDs nutzen (z.B. Inkscape "rect1")
    _prefix_ids(root, ident + "-")
    group = ET.Element(f"{{{SVG_NS}}}g", id=ident)
    skip = {"width", "height", "x", "y", "viewBox", "id", "version", "preserveAspectRatio"}
    for k, v in root.attrib.items():   # Präsentationsattribute (style, fill, font-family ...) übernehmen
        if k not in skip and not k.startswith("{"):
            group.set(k, v)
    group.extend(list(root))
    return group, " ".join(f"{v:.4f}" for v in trim)


def _prefix_ids(root, prefix):
    ids = {el.get("id") for el in root.iter() if el.get("id") and el is not root}
    if not ids:
        return
    href = f"{{{XLINK_NS}}}href"
    pat = re.compile(r"url\(\s*#([^)\s]+)\s*\)")
    for el in root.iter():
        if el is not root and el.get("id") in ids:
            el.set("id", prefix + el.get("id"))
        for attr in (href, "href"):
            v = el.get(attr)
            if v and v.startswith("#") and v[1:] in ids:
                el.set(attr, "#" + prefix + v[1:])
        for attr, v in list(el.attrib.items()):
            if "url(" in v:
                el.set(attr, pat.sub(lambda m: f"url(#{prefix}{m.group(1)})" if m.group(1) in ids else m.group(0), v))
        if el.tag == f"{{{SVG_NS}}}style" and el.text:
            el.text = pat.sub(lambda m: f"url(#{prefix}{m.group(1)})" if m.group(1) in ids else m.group(0), el.text)


def sheet(card_path, ident, guides=False):
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)
    gw, gh = COLS * W, ROWS * H
    x0, y0 = (A4_W - gw) / 2, (A4_H - gh) / 2
    assert x0 >= MARK_GAP + MARK_LEN and y0 >= MARK_GAP + MARK_LEN, "zu wenig Rand für Schnittmarken"

    svg = ET.Element(f"{{{SVG_NS}}}svg", width=f"{A4_W}mm", height=f"{A4_H}mm", viewBox=f"0 0 {A4_W} {A4_H}")
    ET.SubElement(svg, f"{{{SVG_NS}}}rect", width=str(A4_W), height=str(A4_H), fill="#fff")
    group, viewbox = card_symbol(card_path, ident)
    ET.SubElement(svg, f"{{{SVG_NS}}}defs").append(group)
    for r in range(ROWS):
        for c in range(COLS):
            cell = ET.SubElement(svg, f"{{{SVG_NS}}}svg", x=f"{x0 + c * W:.3f}", y=f"{y0 + r * H:.3f}",
                                 width=str(W), height=str(H), viewBox=viewbox, overflow="hidden")
            ET.SubElement(cell, f"{{{SVG_NS}}}use", {f"{{{XLINK_NS}}}href": f"#{ident}"})

    def line(x1, y1, x2, y2):
        ET.SubElement(svg, f"{{{SVG_NS}}}line", x1=f"{x1:.3f}", y1=f"{y1:.3f}", x2=f"{x2:.3f}", y2=f"{y2:.3f}",
                      stroke="#000", **{"stroke-width": str(MARK_WIDTH)})

    for c in range(COLS + 1):
        x = x0 + c * W
        line(x, y0 - MARK_GAP - MARK_LEN, x, y0 - MARK_GAP)
        line(x, y0 + gh + MARK_GAP, x, y0 + gh + MARK_GAP + MARK_LEN)
    for r in range(ROWS + 1):
        y = y0 + r * H
        line(x0 - MARK_GAP - MARK_LEN, y, x0 - MARK_GAP, y)
        line(x0 + gw + MARK_GAP, y, x0 + gw + MARK_GAP + MARK_LEN, y)
    if guides:
        g = {"stroke": GUIDE_COLOR, "stroke-width": str(GUIDE_WIDTH)}
        for c in range(COLS + 1):
            x = f"{x0 + c * W:.3f}"
            ET.SubElement(svg, f"{{{SVG_NS}}}line", x1=x, y1="0", x2=x, y2=str(A4_H), **g)
        for r in range(ROWS + 1):
            y = f"{y0 + r * H:.3f}"
            ET.SubElement(svg, f"{{{SVG_NS}}}line", x1="0", y1=y, x2=str(A4_W), y2=y, **g)
    return ET.tostring(svg, encoding="unicode")


use_project_fonts = druck.use_project_fonts


def compress(src, dst):
    """Ghostscript: doppelte Bilder zusammenfassen, Fotos auf 300 dpi JPEG (cairo bettet
    jedes <use>-Bild einzeln und verlustfrei ein -> sonst schnell 15+ MB). Vektoren/Schriften bleiben."""
    if not shutil.which("gs"):
        shutil.copy(src, dst)
        return
    subprocess.run(["gs", "-q", "-o", dst, "-sDEVICE=pdfwrite", "-dPDFSETTINGS=/prepress",
                    "-dDetectDuplicateImages=true", "-dCompatibilityLevel=1.6", src], check=True)


def build(front, back, out):
    use_project_fonts()
    with tempfile.TemporaryDirectory() as tmp:
        pages = []
        sides = [(front, "vorne")] + ([(back, "hinten")] if back else [])
        for i, (path, ident) in enumerate(sides):
            p = os.path.join(tmp, f"{i}-{ident}.svg")
            with open(p, "w") as f:
                f.write(sheet(path, ident, guides=(i == 0)))
            pages.append(p)
        raw = os.path.join(tmp, "roh.pdf")
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", raw, *pages], check=True)
        compress(raw, out)
    print(f"{out}: Seite 1 = {front}, Seite 2 = {back or '– (einseitig)'}, {COLS}x{ROWS} Karten")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("vorne")
    ap.add_argument("hinten", nargs="?", help="weglassen = einseitig")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    build(a.vorne, a.hinten, a.out)


if __name__ == "__main__":
    main()
