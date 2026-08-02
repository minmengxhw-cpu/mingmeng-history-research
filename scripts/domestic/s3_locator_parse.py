#!/usr/bin/env python3
"""从 evidence_locator 鲁棒提取 OCR md 文件（支持 png/及/至/子目录推导）。"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def extract_ocr_candidates(locator: str) -> list[Path]:
    """从 locator 提取可能存在的 .ocr.md 路径。

    策略：
    1) 直接匹配 .ocr.md 完整路径
    2) 匹配 .png 引用，推导同目录/子目录 ocr 的 .ocr.md
    3) 匹配含 NLC 的「ocr_xxx」目录
    """
    found: dict[str, Path] = {}

    def add(p: Path):
        key = str(p)
        if p.exists():
            found[key] = p

    # 1) .ocr.md 完整路径
    for m in re.finditer(r"([^\s;，,、及至]+\.ocr\.md)", locator or ""):
        raw = m.group(1).strip("；;，,、及 ")
        p = Path(raw)
        if not p.is_absolute():
            p = ROOT / p
        add(p)

    # 2) .png 引用推导
    for m in re.finditer(r"(work/domestic/[^\s;，,、及至]+\.png)", locator or ""):
        png = m.group(1).strip()
        png_p = ROOT / png
        # 同目录同 basename
        add(png_p.with_suffix(".ocr.md"))
        # 子目录 ocr/ 同 basename
        add(png_p.parent / "ocr" / (png_p.stem + ".ocr.md"))
        # 子目录 ocrXXX/
        for sub in png_p.parent.iterdir():
            if sub.is_dir() and "ocr" in sub.name:
                add(sub / (png_p.stem + ".ocr.md"))
        # 同级 *_ocr 目录
        for sibling in png_p.parent.parent.iterdir():
            if sibling.is_dir() and (sibling.name.startswith(png_p.parent.name) or png_p.parent.name.startswith(sibling.name)):
                if "ocr" in sibling.name:
                    add(sibling / (png_p.stem + ".ocr.md"))

    # 3) 整页范围 "page-16.png至page-20.png" → 尝试该目录下全部 ocr
    for m in re.finditer(r"([^\s;，、]+)\.png(?:[至到]([^\s;，、]+)\.png)?", locator or ""):
        p0 = m.group(1)
        p1 = m.group(2)
        base_dir = ROOT / p0[: p0.rfind("/")] if "/" in p0 else None
        if base_dir and base_dir.exists():
            for f in sorted(base_dir.glob("*.ocr.md")):
                add(f)

    return list(found.values())


def main():
    import sqlite3
    db = sqlite3.connect(ROOT / "data/research_index.sqlite")
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT candidate_id, evidence_locator FROM domestic_candidates "
        "WHERE candidate_id IN "
        "('domestic:NLC:guangmingbao-1946-issue03','domestic:NLC:guangmingbao-1946-issue07',"
        "'domestic:NLC:minxian-v1n9-democracy-vs-nondemocracy-1944-11-20',"
        "'domestic:NLC:guangmingbao-1948-1949-v2n12-article',"
        "'domestic:NLC:guangmingbao-1946-issue01-refounding-editorial')"
    ).fetchall()
    for r in rows:
        hits = extract_ocr_candidates(r["evidence_locator"])
        print(f"{r['candidate_id']}:")
        for h in hits:
            print(f"  → {h.relative_to(ROOT)}")
        if not hits:
            print("  (无命中)")
        print()


if __name__ == "__main__":
    sys.exit(main())
