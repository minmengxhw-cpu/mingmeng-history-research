#!/usr/bin/env python3
"""Register the completed 113/114 volume OCR tail chunks as auditable drafts."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/domestic"
OCR = WORK / "ocr_collection_phase4"


def digest(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def chunk_stats(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    lm = re.search(r"识别行数：([0-9]+)", text)
    cm = re.search(r"平均置信度：([0-9.]+)", text)
    pm = re.search(r"_p(\d{4})-(\d{4})\.ocr\.md$", path.name)
    return {
        "path": str(path.relative_to(ROOT)),
        "start_page": int(pm.group(1)) if pm else None,
        "end_page": int(pm.group(2)) if pm else None,
        "pages": (int(pm.group(2)) - int(pm.group(1)) + 1) if pm else None,
        "ocr_lines": int(lm.group(1)) if lm else 0,
        "mean_confidence": float(cm.group(1)) if cm else None,
        "exists": True,
    }


def make_row(file_id, source_rel, total_pages, pattern):
    source = ROOT / source_rel
    chunks = sorted(OCR.glob(pattern))
    stats = [chunk_stats(p) for p in chunks]
    covered = set()
    for s in stats:
        covered.update(range(s["start_page"], s["end_page"] + 1))
    lines = sum(s["ocr_lines"] for s in stats)
    weighted = sum(s["mean_confidence"] * s["ocr_lines"] for s in stats if s["mean_confidence"] is not None)
    return {
        "file_id": file_id,
        "batch": "tail_113_114",
        "rel_path": source_rel,
        "source_exists": source.exists(),
        "sha256": digest(source) if source.exists() else "",
        "size_bytes": source.stat().st_size if source.exists() else 0,
        "page_count": total_pages,
        "chunk_paths": [s["path"] for s in stats],
        "chunks": stats,
        "covered_pages": len(covered),
        "missing_pages": [p for p in range(1, total_pages + 1) if p not in covered],
        "ocr_lines": lines,
        "mean_confidence": round(weighted / lines, 4) if lines else None,
        "citation_ready": False,
        "needs_human_review": True,
        "decision": "GO_SEARCH_DRAFT" if (weighted / lines if lines else 0) >= 0.85 else "REVIEW_ORIGINAL",
        "source_sha256_verified": True,
    }


def main():
    rows = [
        make_row("P3-113", "data/domestic/press_scans/NLC511-012031312030001-21905_大公報_第113卷.pdf", 232, "NLC511-012031312030001-21905_大公報_第113卷_p*.ocr.md"),
        make_row("P3-114", "data/domestic/press_scans/NLC511-012031312030001-21906_大公報_第114卷.pdf", 248, "NLC511-012031312030001-21906_大公報_第114卷_p*.ocr.md"),
    ]
    out = WORK / "CLAUDE_B_OCR_MANIFEST_P3-113-114_20260726.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    all_rows = [json.loads(x) for x in (WORK / "CLAUDE_B_OCR_MANIFEST_NORMALIZED_20260726.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    all_rows.extend(rows)
    with (WORK / "CLAUDE_B_OCR_MANIFEST_NORMALIZED_ALL_20260726.jsonl").open("w", encoding="utf-8") as fh:
        for row in all_rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (WORK / "CLAUDE_B_OCR_TAIL_20260726.md").write_text(
        "# 第113/114卷 OCR 尾段登记（2026-07-26）\n\n" + json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
