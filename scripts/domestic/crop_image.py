#!/usr/bin/env python3
"""Crop a raster image by an explicit top-left box for OCR experiments."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--x", type=int, default=0)
    parser.add_argument("--y", type=int, default=0)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, required=True)
    args = parser.parse_args()

    with Image.open(args.input) as image:
        width, height = image.size
        x0 = max(0, args.x)
        y0 = max(0, args.y)
        x1 = min(width, x0 + (args.width or width))
        y1 = min(height, y0 + args.height)
        if x1 <= x0 or y1 <= y0:
            raise SystemExit("crop box is empty")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.crop((x0, y0, x1, y1)).save(args.output)
        print(f"saved {args.output} size={x1-x0}x{y1-y0} box=({x0},{y0},{x1},{y1})")


if __name__ == "__main__":
    main()
