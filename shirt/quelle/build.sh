#!/usr/bin/env bash
# Build all shirt uploads and the preview.
# Usage: ./build.sh [FONT_DIR]
# FONT_DIR: BarlowCondensed-Bold.ttf, BarlowCondensed-SemiBold.ttf, IBMPlexMono-Bold.ttf
#           (all OFL). Default: ../../gemeinsam/fonts
set -euo pipefail
cd "$(dirname "$0")"
fonts=${1:-../../gemeinsam/fonts}
python3 logo.py "$fonts"
python3 tags.py "$fonts"
python3 vorschau.py "$fonts"
