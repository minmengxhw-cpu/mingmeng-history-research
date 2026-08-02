#!/usr/bin/env python3
"""Extract only the OCR text section from an auditable PaddleOCR Markdown draft."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    text = args.input.read_text(encoding="utf-8", errors="replace")
    if "## 识别文本" in text:
        text = text.split("## 识别文本", 1)[1]
    if "## 明细" in text:
        text = text.split("## 明细", 1)[0]
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text.strip() + "\n", encoding="utf-8")
    print(f"extracted {args.input} -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
