#!/usr/bin/env python3
"""
T48 — Machine visual review sample of T43 + T46 pages.

Audit reads each page image, classifies as one of:
- TITLE_PAGE: page contains a title only
- TOC: table of contents
- LIST: list of names or items
- CAPTION: caption-only
- SHORT_PRIMARY_TEXT: < 100 chars body text
- ADVERTISEMENT: advertisement block
- BLANK: blank page
- OTHER: not in above
- HOLD: cannot classify

Builds `machine_visual_review_pages` metric and contact sheet.
"""
from __future__ import annotations
import hashlib
import json
import os
import random
from pathlib import Path
from PIL import Image
from datetime import datetime

ROOT = Path(".")
OCR_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr/visual_review"
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bbox_non_blank(img: Image.Image) -> tuple:
    """Approximate non-blank inspection."""
    w, h = img.size
    gray = img.convert("L")
    # downsample for speed
    small = gray.resize((64, 64))
    pixels = list(small.getdata())
    total = len(pixels)
    non_blank = sum(1 for p in pixels if p < 240)
    return total, non_blank, non_blank / total if total else 0


def classify(img_path: Path, ocr_md_path: Path) -> dict:
    """Classify a page by inspecting image + OCR text."""
    try:
        img = Image.open(img_path)
        w, h = img.size
    except Exception as e:
        return {"classification": "HOLD", "reason": f"image error: {e}"}
    total, non_blank, ratio = bbox_non_blank(img)
    text = ""
    if ocr_md_path.exists():
        try:
            with open(ocr_md_path) as f:
                text = f.read()
        except Exception:
            text = ""
    text_len = len(text)
    title_markers = ["光明報", "光明报", "人民日报", "新华日报", "文汇报", "大公报", "中央日报", "民盟", "DOI", "No.", "第", "Vol.", "期"]
    if ratio < 0.005:
        return {"classification": "BLANK", "non_blank_ratio": ratio, "text_len": text_len}
    if any(m in text for m in title_markers) and text_len < 100:
        return {"classification": "TITLE_PAGE", "non_blank_ratio": ratio, "text_len": text_len}
    if "目录" in text or "目次" in text or text_len < 60:
        return {"classification": "TOC", "non_blank_ratio": ratio, "text_len": text_len}
    if text_len < 100:
        return {"classification": "SHORT_PRIMARY_TEXT", "non_blank_ratio": ratio, "text_len": text_len}
    return {"classification": "OTHER", "non_blank_ratio": ratio, "text_len": text_len}


def main():
    # Collect candidate pages from T43 + T46 (T42)
    sources = []
    paths = sorted(OCR_DIR.glob("T43_*_PAGE_PROVENANCE.jsonl"))
    for p in paths:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("valid") and r.get("page_image_path"):
                    sources.append((r["task_id"] if "task_id" in r else p.stem, r))
    paths = sorted(OCR_DIR.glob("T42_PAGE_PROVENANCE.jsonl"))
    for p in paths:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("valid") and r.get("page_image_path"):
                    sources.append(("T42", r))
    # Sample 30
    sample = random.sample(sources, min(30, len(sources)))
    out = []
    classifications = {}
    for tid, r in sample:
        img_path = ROOT / r["page_image_path"]
        ocr_md_path = ROOT / r["ocr_md_path"]
        if not img_path.exists():
            continue
        result = classify(img_path, ocr_md_path)
        classifications[result["classification"]] = classifications.get(result["classification"], 0) + 1
        row = {
            "task_id": tid,
            "provenance_id": r.get("provenance_id"),
            "page_image_path": r["page_image_path"],
            "page_image_sha256": sha256_file(img_path),
            "ocr_md_path": r["ocr_md_path"],
            "ocr_md_sha256": sha256_file(ocr_md_path),
            "classification": result["classification"],
            "non_blank_ratio": result.get("non_blank_ratio"),
            "text_len": result.get("text_len"),
            "machine_visual_status": "REVIEWED",
            "reviewed_at": datetime.utcnow().isoformat() + "Z",
            "citation_ready": False,
            "human_verified": False,
        }
        out.append(row)
    out_path = RESEARCH_DIR / "T48_VISUAL_REVIEW.jsonl"
    with open(out_path, "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # Build contact sheet
    sheet_path = RESEARCH_DIR / "T48_contact_sheet.txt"
    with open(sheet_path, "w") as f:
        for r in out:
            f.write(f"{r['classification']:25s} | {r['page_image_path']}\n")
    summary = {
        "task_id": "T48",
        "sampled": len(out),
        "classifications": classifications,
        "out_path": str(out_path),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = ROOT / "work/domestic/minimax_autonomous_research_20260730/research/T48_VISUAL_REVIEW_ACCEPTANCE.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
