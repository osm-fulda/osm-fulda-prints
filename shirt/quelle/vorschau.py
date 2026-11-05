#!/usr/bin/env python3
"""Build ../vorschau.png from all upload PNGs in the parent directory.

Usage: python3 vorschau.py FONT_DIR
"""
import glob, os, subprocess, sys
from common import PNG_OUT, preview_tile

font = os.path.join(sys.argv[1], "BarlowCondensed-SemiBold.ttf")
out = os.path.join(PNG_OUT, "vorschau.png")
files = sorted(f for f in glob.glob(os.path.join(PNG_OUT, "*.png")) if f != out)
tiles = [a for f in files for a in preview_tile(f, font)]
subprocess.run(["magick"] + tiles + ["+append", out], check=True)
print("ok, %d uploads" % len(files))
