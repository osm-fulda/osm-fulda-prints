#!/usr/bin/env bash
# Check a shirt logo for DTF print limits at its real print size.
# Usage: ./check.sh FILE.svg WIDTH_MM OUT.png
# Red in OUT.png: ink thinner than 1 mm (film can lift in the wash).
# Blue in OUT.png: gaps narrower than 0.5 mm (can fill up in print).
# Needs rsvg-convert and ImageMagick (magick).
set -euo pipefail
svg=$1; width_mm=$2; out=$3
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT

dpi=300
px=$(( width_mm * dpi * 10 / 254 ))
r_ink=$(awk "BEGIN{print 0.5 * $dpi / 25.4}")   # radius of a 1 mm disk
r_gap=$(awk "BEGIN{print 0.25 * $dpi / 25.4}")  # radius of a 0.5 mm disk

rsvg-convert -w "$px" "$svg" -o "$tmp/c.png"
magick "$tmp/c.png" -alpha extract -threshold 50% "$tmp/a.png"
# opening removes ink thinner than the disk, closing fills gaps narrower than the disk
magick "$tmp/a.png" -morphology Open "Disk:$r_ink" "$tmp/o.png"
magick "$tmp/a.png" -morphology Close "Disk:$r_gap" "$tmp/cl.png"
magick "$tmp/a.png" "$tmp/o.png" -compose minus_src -composite "$tmp/thin.png"
magick "$tmp/cl.png" "$tmp/a.png" -compose minus_src -composite "$tmp/gap.png"

ink=$(magick "$tmp/a.png" -format '%[fx:mean]' info:)
thin=$(magick "$tmp/thin.png" -format '%[fx:mean]' info:)
gap=$(magick "$tmp/gap.png" -format '%[fx:mean]' info:)
awk -v f="$svg" -v w="$width_mm" -v i="$ink" -v t="$thin" -v g="$gap" 'BEGIN{
  printf "%s @ %s mm: %.1f%% of ink thinner than 1 mm, gaps < 0.5 mm: %.2f%% of area\n",
         f, w, t / i * 100, g * 100 }'

size=$(magick identify -format '%wx%h' "$tmp/c.png")
magick "$tmp/c.png" -background "#3d4045" -flatten \
  \( -size "$size" xc:"#ff2020" "$tmp/thin.png" -alpha off -compose copy_opacity -composite \) \
  -compose over -composite \
  \( -size "$size" xc:"#20a0ff" "$tmp/gap.png" -alpha off -compose copy_opacity -composite \) \
  -compose over -composite "$out"
