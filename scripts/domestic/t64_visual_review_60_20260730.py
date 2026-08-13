#!/usr/bin/env python3
"""
T64 — Visual review expansion: 60 pages from T09/T10/T14/T15/T50.
"""
from __future__ import annotations
import hashlib
import json
import random
from pathlib import Path
from PIL import Image
from datetime import datetime

ROOT = Path(".")
OCR_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr/visual_review"
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

random.seed(999)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(img_path, ocr_md_path):
    try:
        img = Image.open(img_path)
        gray = img.convert("L").resize((64, 64))
        pixels = list(gray.getdata())
        non_blank = sum(1 for p in pixels if p < 240)
        ratio = non_blank / len(pixels)
    except Exception:
        return {"classification": "HOLD"}
    text = ""
    if ocr_md_path.exists():
        with open(ocr_md_path) as f:
            text = f.read()
    text_len = len(text)
    if ratio < 0.005:
        return {"classification": "BLANK", "non_blank_ratio": ratio, "text_len": text_len}
    if any(m in text for m in ["民主同盟", "民盟", "光明報", "光明报", "Vol.", "Vol"]) and text_len < 200:
        return {"classification": "TITLE_PAGE", "non_blank_ratio": ratio, "text_len": text_len}
    if "目录" in text or "目次" in text:
        return {"classification": "TOC", "non_blank_ratio": ratio, "text_len": text_len}
    if text_len < 100:
        return {"classification": "SHORT_PRIMARY_TEXT", "non_blank_ratio": ratio, "text_len": text_len}
    return {"classification": "OTHER", "non_blank_ratio": ratio, "text_len": text_len}


def main():
    sources = []
    target_tasks = ["T09", "T10", "T14", "T15", "T50"]
    for task in target_tasks:
        # Match exact file name or with suffix
        for p in sorted(OCR_DIR.glob(f"{task}_PAGE_PROVENANCE.v2.jsonl")):
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
                        sources.append((p.stem, r))
    sample = random.sample(sources, min(60, len(sources)))
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
    out_path = RESEARCH_DIR / "T64_VISUAL_REVIEW_60PAGES.jsonl"
    with open(out_path, "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "task_id": "T64",
        "sampled": len(out),
        "classifications": classifications,
        "out_path": str(out_path),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = ROOT / "work/domestic/minimax_autonomous_research_20260730/research/T64_VISUAL_REVIEW_ACCEPTANCE.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
