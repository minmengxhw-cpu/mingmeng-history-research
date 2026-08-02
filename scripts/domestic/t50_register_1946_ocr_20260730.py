#!/usr/bin/env python3
"""
T50 — Register pre-existing 1946 OCR pages with stable unique keys.

For 1946 docs in `work/domestic/minmeng_wenxian_1946/`:
- early_probe_ocr (page-021..025)
- late_probe_ocr (page-074..078)
- boundary_31_39_ocr
- around_39_42_ocr
- formation_9_13_ocr (page-009..013)
- contents_005_008_ocr
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from datetime import datetime

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
OCR_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"
SRC_DIR = ROOT / "work/domestic/minmeng_wenxian_1946"
SOURCE_FILE = "data/domestic/sourcebooks/NLC416-01jh004281-12557_民主同盟文獻_1946.pdf"
SOURCE_ID = "NLC416-01jh004281-12557_民主同盟文獻_1946"


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


OCR_FOLDERS = [
    "early_probe_ocr",
    "late_probe_ocr",
    "boundary_31_39_ocr",
    "around_39_42_ocr",
    "formation_9_13_ocr",
    "contents_005_008_ocr",
]
IMG_FOLDERS = {
    "early_probe_ocr": "early_probe_images",
    "late_probe_ocr": "late_probe_images",
    "boundary_31_39_ocr": "boundary_31_39_images",
    "around_39_42_ocr": "around_39_42_images",
    "formation_9_13_ocr": "formation_9_13_images",
    "contents_005_008_ocr": None,
}


def main():
    source_path = ROOT / SOURCE_FILE
    source_sha = sha256_file(source_path)
    source_size = source_path.stat().st_size if source_path.exists() else 0
    rows = []
    for ocr_folder in OCR_FOLDERS:
        ocr_dir = SRC_DIR / ocr_folder
        if not ocr_dir.exists():
            continue
        img_folder = IMG_FOLDERS.get(ocr_folder)
        img_dir = SRC_DIR / img_folder if img_folder else None
        for ocr_md in sorted(ocr_dir.glob("*.ocr.md")):
            page_label = ocr_md.stem.replace(".ocr", "").replace("page-", "")
            # Find page image
            page_image = None
            if img_dir:
                for ext in [".png", ".jpg"]:
                    cand = img_dir / f"page-{page_label}{ext}"
                    if cand.exists():
                        page_image = cand
                        break
            # Try variants
            if page_image is None:
                for variant in [f"page-{int(page_label):03d}" if page_label.isdigit() else page_label, page_label]:
                    for ext in [".png", ".jpg"]:
                        cand = SRC_DIR / f"{variant}{ext}"
                        if cand.exists():
                            page_image = cand
                            break
                    if page_image:
                        break
            page_image_sha = sha256_file(page_image) if page_image else None
            ocr_sha = sha256_file(ocr_md)
            with open(ocr_md) as f:
                text = f.read()
            ocr_lines = sum(1 for l in text.splitlines() if l.strip())
            image_sha256 = page_image_sha or f"NO_IMAGE_{page_label}"
            phys = int(page_label) if page_label.isdigit() else None
            row = {
                "mapping_id": f"MAPV-T50_{ocr_folder}-p{page_label}",
                "mapping_kind": "OCR_REUSE_20260719",
                "source_id": SOURCE_ID,
                "source_file": SOURCE_FILE,
                "source_sha256": source_sha,
                "source_file_size": source_size,
                "source_title": "《民主同盟文獻》1946",
                "period": "1946 政治协商与民主政治",
                "year": 1946,
                "pdf_page_no": phys,
                "physical_page_no": phys,
                "printed_page": None,
                "issue_date": "《民主同盟文獻》1946",
                "issue_no": None,
                "edition": "minmeng_wenxian_1946",
                "page_image_path": str(page_image.relative_to(ROOT)) if page_image else None,
                "page_image_sha256": page_image_sha,
                "mapping_basis": ["source_title", "physical_page_no", "edition"],
                "rights_status": "PUBLIC_LOCAL_SOURCE; rights_scope_not_human_verified",
                "citation_ready": False,
                "human_verified": False,
                "relation_required": None,
                "validated_at": datetime.utcnow().isoformat() + "Z",
                "ocr_md_path": str(ocr_md.relative_to(ROOT)),
                "ocr_engine": "PaddleOCR",
                "ocr_model": "PP-OCRv6_medium_det + PP-OCRv6_medium_rec",
                "provenance_id": stable_provenance_id(f"T50_{ocr_folder}", image_sha256, ocr_sha or ""),
                "ocr_md_sha256": ocr_sha,
                "ocr_lines": ocr_lines,
                "ocr_mode": "REAL_PAGE_BY_PAGE",
                "machine_visual_status": "NOT_REVIEWED",
                "text_structure_status": "MACHINE_OCR_COMPLETE",
                "valid": page_image_sha is not None and ocr_sha is not None,
            }
            rows.append(row)
    out_idx = OCR_DIR / "T50_PAGE_INDEX.jsonl"
    out_prov = OCR_DIR / "T50_PAGE_PROVENANCE.jsonl"
    out_prov_v2 = OCR_DIR / "T50_PAGE_PROVENANCE.v2.jsonl"
    with open(out_idx, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out_prov, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out_prov_v2, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "task_id": "T50",
        "rows": len(rows),
        "valid_rows": sum(1 for r in rows if r["valid"]),
        "ocr_folders": OCR_FOLDERS,
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out = RESEARCH_DIR / "T50_OCR_REGISTRATION.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
