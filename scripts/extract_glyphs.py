#!/usr/bin/env python3
"""One-off: export Lilex glyph outlines to assets/fonts/lilex-glyphs.json.

render.py draws text from these outlines instead of embedding the font, so
the graphics look identical in every browser at every scale. Needs fontTools
and brotli, but only when re-running this script.

Usage: python3 scripts/extract_glyphs.py path/to/Lilex/ttf
"""
import json
import os
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

CHARS = [chr(c) for c in range(0x21, 0x7F)] + ["·", "–", "—"]
WEIGHTS = {"400": "Regular", "500": "Medium", "700": "Bold"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts", "lilex-glyphs.json")


def main(src):
    data = {"unitsPerEm": None, "advance": None, "glyphs": {}}
    for weight, name in WEIGHTS.items():
        font = TTFont(os.path.join(src, f"Lilex-{name}.ttf"))
        gs, cmap = font.getGlyphSet(), font.getBestCmap()
        data["unitsPerEm"] = font["head"].unitsPerEm
        data["advance"] = font["hmtx"][cmap[ord("M")]][0]
        glyphs = {}
        for ch in CHARS:
            pen = SVGPathPen(gs)
            gs[cmap[ord(ch)]].draw(pen)
            path = pen.getCommands()
            if path:
                glyphs[ch] = path
        data["glyphs"][weight] = glyphs
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    print(f"wrote {OUT} ({os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1])
