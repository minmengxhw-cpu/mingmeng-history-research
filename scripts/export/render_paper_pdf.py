#!/usr/bin/env python3
"""Render one markdown paper under docs/ to output/pdf.

Usage:
  python3 scripts/export/render_paper_pdf.py newspapersg docs/_newspapersg-paper.md
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from weasyprint import HTML


ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "output" / "pdf"

CSS = """
@page {
  size: A4;
  margin: 24mm 22mm 22mm;
  @bottom-center { content: counter(page); color: #7b725f; font-size: 9pt; }
}
body {
  font-family: "Noto Serif CJK SC", "Songti SC", serif;
  color: #211f18;
  font-size: 11pt;
  line-height: 1.85;
}
h1 {
  font-size: 23pt;
  color: #5a3a26;
  line-height: 1.35;
  text-align: center;
  margin: 8mm 0 10mm;
  padding-bottom: 5mm;
  border-bottom: 1pt solid #b9a98c;
}
h2 {
  font-size: 15pt;
  color: #0f6b5b;
  margin: 9mm 0 3mm;
  border-left: 4pt solid #0f6b5b;
  padding-left: 3mm;
}
p { margin: 0 0 3mm; text-align: justify; text-indent: 2em; }
blockquote {
  margin: 4mm 0;
  padding: 3mm 5mm;
  background: #f7f1e5;
  border-left: 3pt solid #b9a98c;
  color: #4b4438;
}
blockquote p { text-indent: 0; }
"""


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def inline_md(text: str) -> str:
    text = esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def markdown_to_html(md: str) -> str:
    parts: list[str] = []
    para: list[str] = []
    quote: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            parts.append(f"<p>{inline_md(' '.join(para).strip())}</p>")
            para = []

    def flush_quote() -> None:
        nonlocal quote
        if quote:
            parts.append("<blockquote>" + "".join(f"<p>{inline_md(q)}</p>" for q in quote) + "</blockquote>")
            quote = []

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            flush_quote()
            continue
        if line.startswith(">"):
            flush_para()
            quote.append(line.lstrip("> ").strip())
            continue
        flush_quote()
        m = re.match(r"^(#{1,2})\s+(.+)$", line)
        if m:
            flush_para()
            level = len(m.group(1))
            parts.append(f"<h{level}>{inline_md(m.group(2).strip())}</h{level}>")
            continue
        para.append(line.strip())
    flush_para()
    flush_quote()
    return "\n".join(parts)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: render_paper_pdf.py <platform> <markdown-path>")
    platform = sys.argv[1]
    md_path = Path(sys.argv[2])
    if not md_path.is_absolute():
        md_path = ROOT / md_path
    OUT.mkdir(parents=True, exist_ok=True)
    html_body = markdown_to_html(md_path.read_text(encoding="utf-8"))
    out = OUT / f"mingmeng-{platform}-paper.pdf"
    HTML(string=f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>{html_body}").write_pdf(str(out))
    print(out)


if __name__ == "__main__":
    main()
