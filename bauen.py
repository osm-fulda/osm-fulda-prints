#!/usr/bin/env python3
"""Alle Drucksachen bauen – für Fulda oder für eure Community.

    python3 bauen.py                    # Fulda (gemeinsam/community.toml), schreibt ins Repo
    python3 bauen.py musterstadt.toml   # eure Angaben, schreibt nach ausgabe/musterstadt/

Vorlage für eigene Angaben: community-vorlage.toml. Die Shirts (shirt/) baut shirt/quelle/build.sh.
"""
import importlib.util
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FULDA = os.path.join(ROOT, "gemeinsam", "community.toml")   # wie druck.DEFAULT_CONFIG
SKRIPTE = [   # Reihenfolge: Motivkarten nutzen die Aushang-Zeichnungen, Aufsteller die Vorschaubilder aller
    "aushang/make_klassisch.py",
    "aushang/make_gelb.py",
    "aushang/make_pixel.py",
    "aushang/make_pappe.py",
    "aushang/make_sozial.py",
    "motivkarten/make_motivkarten.py",
    "mitmachkarte/make_mitmachkarte.py",
    "aufsteller/make_aufsteller.py",
]


def pruefen():
    """Fehlende Programme und Python-Pakete auf einmal melden, statt mitten im Bauen abzubrechen."""
    fehlt = []
    if sys.version_info < (3, 11):
        fehlt.append("Python 3.11 oder neuer")
    for modul, paket in [("qrcode", "qrcode"), ("fontTools", "fonttools"), ("PIL", "pillow")]:
        if importlib.util.find_spec(modul) is None:
            fehlt.append(f"Python-Paket {paket}  (pip install {paket})")
    if not shutil.which("rsvg-convert"):
        fehlt.append("rsvg-convert  (Fedora: librsvg2-tools, Debian/Ubuntu: librsvg2-bin, macOS: brew install librsvg)")
    if fehlt:
        sys.exit("Es fehlt:\n  " + "\n  ".join(fehlt))
    if not shutil.which("gs"):
        print("Hinweis: ohne Ghostscript (gs) werden die PDFs deutlich größer.\n")


def main():
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help")):
        sys.exit(__doc__)
    pruefen()
    env = dict(os.environ)
    env.pop("OSM_COMMUNITY", None)          # nur das Argument zählt, nicht eine alte Shell-Variable
    ziel = ROOT
    if len(sys.argv) == 2:
        config = os.path.abspath(sys.argv[1])
        if not os.path.isfile(config):
            sys.exit(f"{sys.argv[1]} gibt es nicht. Vorlage: community-vorlage.toml")
        if config != FULDA:                 # dieselbe Regel wie druck.ausgabe
            env["OSM_COMMUNITY"] = config
            ziel = os.path.join(ROOT, "ausgabe", os.path.splitext(os.path.basename(config))[0])
    for skript in SKRIPTE:
        print(f"== {skript}", flush=True)
        r = subprocess.run([sys.executable, os.path.join(ROOT, skript)], env=env)
        if r.returncode:
            sys.exit(f"\n{skript} ist fehlgeschlagen (siehe oben).")
    print(f"\nFertig. Druckbögen (*-a4.pdf) in {os.path.relpath(ziel)}/")


if __name__ == "__main__":
    main()
