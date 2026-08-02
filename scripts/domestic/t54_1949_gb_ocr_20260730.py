#!/usr/bin/env python3
"""
T54 — Register 1949 GB OCR provenance.

1949 GB v2n1 and v2n12 have OCR batches.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from datetime import datetime

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
OCR_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

BATCHES = [
    {
        "batch": "GB1949_v2n1",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1949_v2n1_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1949_v2n1_20260723",
        "image_pattern": "work/domestic/guangmingbao_1948_1949/v2n1_pages/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-_光明報_1949年2卷1期.pdf",
        "source_id": "NLC404-01J000514_光明報_1949年2卷1期",
        "year": 1949,
        "period": "1949 民盟新政协",
        "title": "《光明報》1949年第二卷第一期",
        "issue_date": "1949",
    },
    {
        "batch": "GB1949_v2n12",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1949_v2n12_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1949_v2n12_20260723",
        "image_pattern": "work/domestic/guangmingbao_1948_1949/v2n12_pages/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-_光明報_1949年2卷12期.pdf",
        "source_id": "NLC404-01J000514_光明報_1949年2卷12期",
        "year": 1949,
        "period": "1949 民盟新政协",
        "title": "《光明報》1949年第二卷第十二期",
        "issue_date": "1949",
    },
]


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_provenance_id(task, image_sha, ocr_sha):
    raw = f"{task}|{image_sha}|{ocr_sha}"
    return f"PROV-{task}-{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


def register(batch):
    rows = []
    manifest_path = ROOT / batch["manifest"]
    if not manifest_path.exists():
        return {"batch": batch["batch"], "skipped": True, "reason": "no manifest"}
    task = f"T54_{batch['batch']}"
    source_path = ROOT / batch["source_file"]
    source_sha = sha256_file(source_path)
    source_size = source_path.stat().st_size if source_path.exists() else 0
    with open(manifest_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            pages = rec.get("pages", [])
            for p in pages:
                ocr_md_rel = p.get("ocr_markdown")
                if not ocr_md_rel:
                    continue
                ocr_md_path = ROOT / ocr_md_rel
                if not ocr_md_path.exists():
                    continue
                ocr_sha = sha256_file(ocr_md_path)
                page_label = p.get("page_label", "")
                page_image = None
                pattern = batch.get("image_pattern", "")
                try:
                    formatted = pattern.format(int(page_label))
                except Exception:
                    formatted = pattern
                cand = ROOT / formatted
                if cand.exists():
                    page_image = cand
                if page_image is None:
                    ocr_dir = ROOT / batch["ocr_dir"]
                    for name in [f"page-{page_label}.png", f"page-{int(page_label):02d}.png"]:
                        c = ocr_dir / name
                        if c.exists():
                            page_image = c
                            break
                page_image_sha = sha256_file(page_image) if page_image else None
                with open(ocr_md_path) as f:
                    text = f.read()
                ocr_lines = sum(1 for l in text.splitlines() if l.strip())
                conf = float(p.get("mean_confidence", 0.0))
                image_sha256 = page_image_sha or f"NO_IMAGE_{task}_{page_label}"
                row = {
                    "mapping_id": f"MAPV-{task}-p{page_label}",
                    "mapping_kind": "OCR_REUSE_20260723",
                    "source_id": batch["source_id"],
                    "source_file": batch["source_file"],
                    "source_sha256": source_sha,
                    "source_file_size": source_size,
                    "source_title": batch["title"],
                    "period": batch["period"],
                    "year": batch["year"],
                    "pdf_page_no": int(page_label) if page_label.isdigit() else None,
                    "physical_page_no": int(page_label) if page_label.isdigit() else None,
                    "printed_page": None,
                    "issue_date": batch["issue_date"],
                    "issue_no": None,
                    "edition": "public_scan_20260723",
                    "page_image_path": str(page_image.relative_to(ROOT)) if page_image else None,
                    "page_image_sha256": page_image_sha,
                    "mapping_basis": ["source_title", "physical_page_no", "edition"],
                    "rights_status": "PUBLIC_LOCAL_SOURCE; rights_scope_not_human_verified",
                    "citation_ready": False,
                    "human_verified": False,
                    "relation_required": None,
                    "validated_at": datetime.utcnow().isoformat() + "Z",
                    "ocr_md_path": str(ocr_md_path.relative_to(ROOT)),
                    "ocr_engine": "PaddleOCR",
                    "ocr_model": "PP-OCRv6_medium_det + PP-OCRv6_medium_rec",
                    "provenance_id": stable_provenance_id(task, image_sha256, ocr_sha or ""),
                    "ocr_md_sha256": ocr_sha,
                    "ocr_lines": ocr_lines,
                    "ocr_mean_confidence": conf,
                    "ocr_mode": "REAL_PAGE_BY_PAGE",
                    "machine_visual_status": "NOT_REVIEWED",
                    "text_structure_status": "MACHINE_OCR_COMPLETE",
                    "valid": page_image_sha is not None and ocr_sha is not None,
                }
                rows.append(row)
    out_idx = OCR_DIR / f"{task}_PAGE_INDEX.jsonl"
    out_prov = OCR_DIR / f"{task}_PAGE_PROVENANCE.jsonl"
    out_prov_v2 = OCR_DIR / f"{task}_PAGE_PROVENANCE.v2.jsonl"
    with open(out_idx, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out_prov, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out_prov_v2, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {
        "task": task,
        "batch": batch["batch"],
        "rows": len(rows),
        "valid_rows": sum(1 for r in rows if r["valid"]),
    }


def main():
    results = []
    for b in BATCHES:
        results.append(register(b))
    summary = {
        "task_id": "T54",
        "batches": results,
        "total_rows": sum(r.get("rows", 0) for r in results),
        "total_valid": sum(r.get("valid_rows", 0) for r in results),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out = RESEARCH_DIR / "T54_1949_GB_OCR_REGISTRATION.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
