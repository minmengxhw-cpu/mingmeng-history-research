#!/usr/bin/env python3
"""
T35 — Build provenance for the 30 T35 pages that already have OCR.
T35 had 30 PAGE_INDEX entries and 30 OCR batch files but no provenance yet.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
OCR_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_provenance_id(task: str, page_image_sha256: str, ocr_md_sha256: str) -> str:
    raw = f"{task}|{page_image_sha256}|{ocr_md_sha256}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"PROV-{task}-{h}"


def run():
    idx_path = OCR_DIR / "T35_PAGE_INDEX.jsonl"
    rows = []
    with open(idx_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    out_rows = []
    missing_image = 0
    missing_ocr = 0
    for r in rows:
        ocr_md_path = r.get("ocr_md_path")
        page_image_path = r.get("page_image_path")
        # SHA actual
        page_image_sha = sha256_file(ROOT / page_image_path) if page_image_path else None
        ocr_md_sha = sha256_file(ROOT / ocr_md_path) if ocr_md_path else None
        if page_image_sha is None:
            missing_image += 1
        if ocr_md_sha is None:
            missing_ocr += 1
        # OCR line count
        ocr_lines = 0
        if ocr_md_path and (ROOT / ocr_md_path).exists():
            with open(ROOT / ocr_md_path) as f:
                text = f.read()
            ocr_lines = sum(1 for line in text.splitlines() if line.strip())
        prov = {
            "provenance_id": stable_provenance_id("T35", r.get("page_image_sha256") or "", r.get("ocr_md_sha256") or ""),
            "source_id": r.get("source_id"),
            "source_file": r.get("source_file"),
            "source_sha256": r.get("source_sha256"),
            "source_file_size": r.get("source_file_size"),
            "physical_page_no": r.get("physical_page_no"),
            "pdf_page_no": r.get("pdf_page_no"),
            "source_title": r.get("source_title"),
            "year": r.get("year"),
            "period": r.get("period"),
            "issue_date": r.get("issue_date"),
            "issue_no": r.get("issue_no"),
            "edition": r.get("edition"),
            "printed_page": r.get("printed_page"),
            "page_image_path": page_image_path,
            "page_image_sha256": page_image_sha or r.get("page_image_sha256"),
            "ocr_md_path": ocr_md_path,
            "ocr_md_sha256": ocr_md_sha or r.get("ocr_md_sha256"),
            "ocr_engine": r.get("ocr_engine", "PaddleOCR"),
            "ocr_model": r.get("ocr_model", "PP-OCRv6_medium_det + PP-OCRv6_medium_rec"),
            "ocr_mode": "REAL_PAGE_BY_PAGE",
            "ocr_lines": ocr_lines,
            "text_structure_status": "MACHINE_OCR_COMPLETE",
            "machine_visual_status": "NOT_REVIEWED",
            "citation_ready": False,
            "human_verified": False,
            "valid": page_image_sha is not None and ocr_md_sha is not None,
            "mapping_id": r.get("mapping_id"),
            "rights_status": r.get("rights_status"),
        }
        out_rows.append(prov)
    out = OCR_DIR / "T35_PAGE_PROVENANCE.jsonl"
    with open(out, "w") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    v2 = OCR_DIR / "T35_PAGE_PROVENANCE.v2.jsonl"
    with open(v2, "w") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "task_id": "T35",
        "rows": len(out_rows),
        "missing_image": missing_image,
        "missing_ocr": missing_ocr,
        "out_path": str(out),
        "v2_path": str(v2),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = RESEARCH_DIR / "T35_OCR_ACCEPTANCE.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
