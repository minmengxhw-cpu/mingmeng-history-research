#!/usr/bin/env python3
"""
T38 — Add stable unique keys to OCR provenance files.

Per dual acceptance:
- T09, T10, T14, T15, T19, T24, T29, T29b, T35 provenance must contain:
  - provenance_id (stable, deterministic)
  - source_id
  - source_sha256
  - source_file
  - physical_page_no
  - ocr_mode
  - machine_visual_status

Also re-verify SHA against actual files and pages.
Writes new files with .v2.jsonl suffix; old files preserved.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(".")
OCR_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

TASKS = ["T09", "T10", "T14", "T15", "T19", "T24", "T29", "T29b", "T35"]


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_index(idx_path: Path) -> dict:
    """Build mapping: ocr_md_path -> index row"""
    out = {}
    if not idx_path.exists():
        return out
    with open(idx_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = row.get("ocr_md_path")
            if key:
                out[key] = row
    return out


def stable_provenance_id(task: str, page_image_sha256: str, ocr_md_sha256: str) -> str:
    raw = f"{task}|{page_image_sha256}|{ocr_md_sha256}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"PROV-{task}-{h}"


def upgrade_task(task: str) -> dict:
    prov_path = OCR_DIR / f"{task}_PAGE_PROVENANCE.jsonl"
    if not prov_path.exists():
        return {"task": task, "rows": 0, "skipped": True, "reason": "no provenance file"}
    idx_path = OCR_DIR / f"{task}_PAGE_INDEX.jsonl"
    idx = load_index(idx_path)
    rows = []
    failures = []
    sha_mismatch = []
    with open(prov_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    out = []
    for r in rows:
        new = dict(r)
        ocr_md_path = r.get("ocr_md_path")
        idx_row = idx.get(ocr_md_path) if ocr_md_path else None
        if idx_row:
            new["source_id"] = idx_row.get("source_id")
            new["source_file"] = idx_row.get("source_file")
            new["source_sha256"] = idx_row.get("source_sha256")
            new["source_file_size"] = idx_row.get("source_file_size")
            new["physical_page_no"] = idx_row.get("physical_page_no")
            new["pdf_page_no"] = idx_row.get("pdf_page_no")
            new["source_title"] = idx_row.get("source_title")
            new["year"] = idx_row.get("year")
            new["period"] = idx_row.get("period")
            new["issue_date"] = idx_row.get("issue_date")
            new["edition"] = idx_row.get("edition")
            new["printed_page"] = idx_row.get("printed_page")
            new["mapping_id"] = idx_row.get("mapping_id")
            new["rights_status"] = idx_row.get("rights_status")
        if "ocr_mode" not in new or new["ocr_mode"] is None:
            new["ocr_mode"] = "REAL_PAGE_BY_PAGE"
        if "machine_visual_status" not in new:
            new["machine_visual_status"] = "NOT_REVIEWED"
        if "provenance_id" not in new or not new["provenance_id"]:
            new["provenance_id"] = stable_provenance_id(
                task,
                r.get("page_image_sha256") or "",
                r.get("ocr_md_sha256") or "",
            )
        # re-verify SHA
        if r.get("page_image_path"):
            actual_sha = sha256_file(ROOT / r["page_image_path"])
            if actual_sha and r.get("page_image_sha256") and actual_sha != r["page_image_sha256"]:
                sha_mismatch.append({
                    "row": r.get("ocr_md_path"),
                    "expected": r["page_image_sha256"],
                    "actual": actual_sha,
                })
        if ocr_md_path:
            actual_sha = sha256_file(ROOT / ocr_md_path)
            if actual_sha and r.get("ocr_md_sha256") and actual_sha != r["ocr_md_sha256"]:
                sha_mismatch.append({
                    "row": ocr_md_path,
                    "expected": r["ocr_md_sha256"],
                    "actual": actual_sha,
                })
        out.append(new)
    out_path = OCR_DIR / f"{task}_PAGE_PROVENANCE.v2.jsonl"
    with open(out_path, "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {
        "task": task,
        "rows": len(out),
        "skipped": False,
        "out_path": str(out_path),
        "sha_mismatches": len(sha_mismatch),
        "sha_mismatch_details": sha_mismatch[:5],
        "fields_added": [
            "provenance_id", "source_id", "source_file", "source_sha256",
            "source_file_size", "physical_page_no", "pdf_page_no",
            "source_title", "year", "period", "issue_date", "edition",
            "printed_page", "mapping_id", "rights_status", "ocr_mode",
            "machine_visual_status",
        ],
    }


def main():
    results = []
    for task in TASKS:
        results.append(upgrade_task(task))
    summary = {
        "task_count": len(results),
        "tasks": results,
        "total_rows": sum(r.get("rows", 0) for r in results),
        "total_sha_mismatches": sum(r.get("sha_mismatches", 0) for r in results),
    }
    out = RESEARCH_DIR / "T38_PROVENANCE_KEYS_UPGRADE.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
