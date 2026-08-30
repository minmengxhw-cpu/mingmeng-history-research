#!/usr/bin/env python3
"""
T43 — Register 1947 光明报 OCR provenance from existing 20260723 batches.

Each 1947 GB batch has 16 pages with OCR markdown. Register provenance with stable unique keys.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(".")
OCR_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

BATCHES = [
    {
        "batch": "GB1947_13",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1947_13_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1947_13_20260723",
        "image_pattern": "work/domestic/continue_pages/1947_13_rendered/page-{:02d}.png OR 1947_13/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10453_光明報_1947年13期.pdf",
        "source_id": "NLC404-01J000514-10453_光明報_1947年13期",
        "year": 1947,
        "period": "1947 民盟一届二中全会",
        "title": "《光明報》1947年新十三號",
        "issue_date": "1947-01-18",
    },
    {
        "batch": "GB1947_14",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1947_14_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1947_14_20260723",
        "image_pattern": "work/domestic/continue_pages/1947_14/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10454_光明報_1947年14期.pdf",
        "source_id": "NLC404-01J000514-10454_光明報_1947年14期",
        "year": 1947,
        "period": "1947 民盟活动",
        "title": "《光明報》1947年14期",
        "issue_date": "1947",
    },
    {
        "batch": "GB1947_15",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1947_15_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1947_15_20260723",
        "image_pattern": "work/domestic/continue_pages/1947_15/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10455_光明報_1947年15期.pdf",
        "source_id": "NLC404-01J000514-10455_光明報_1947年15期",
        "year": 1947,
        "period": "1947 民盟活动",
        "title": "《光明報》1947年15期",
        "issue_date": "1947",
    },
    {
        "batch": "GB1947_18",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1947_18_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1947_18_20260723",
        "image_pattern": "work/domestic/continue_pages/1947_18/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10457_光明報_1947年18期.pdf",
        "source_id": "NLC404-01J000514-10457_光明報_1947年18期",
        "year": 1947,
        "period": "1947 民盟活动",
        "title": "《光明報》1947年18期",
        "issue_date": "1947",
    },
    {
        "batch": "GB1947_19",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1947_19_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1947_19_20260723",
        "image_pattern": "work/domestic/guangmingbao_1947_19_pages/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10458_光明報_1947年19期.pdf",
        "source_id": "NLC404-01J000514-10458_光明報_1947年19期",
        "year": 1947,
        "period": "1947 民盟活动",
        "title": "《光明報》1947年19期",
        "issue_date": "1947",
    },
    {
        "batch": "GB1947_12",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1947_12_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1947_12_20260723",
        "image_pattern": "work/domestic/continue_pages/1947_12/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-72818_光明報_1947年12期.pdf",
        "source_id": "NLC404-01J000514-72818_光明報_1947年12期",
        "year": 1947,
        "period": "1947 早期民盟",
        "title": "《光明報》1947年12期",
        "issue_date": "1947",
    },
    {
        "batch": "GB1947_16_17",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1947_16-17_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1947_16-17_20260723",
        "image_pattern": "work/domestic/continue_pages/1947_16-17/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10456_光明報_1947年16–17期.pdf",
        "source_id": "NLC404-01J000514-10456_光明報_1947年16–17期",
        "year": 1947,
        "period": "1947 早期民盟",
        "title": "《光明報》1947年16–17期",
        "issue_date": "1947",
    },
    {
        "batch": "GB1947_20",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1947_issue20_front_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1947_issue20_front_20260723",
        "image_pattern": "work/domestic/continue_pages/1947_20/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10459_光明報_1947年20期.pdf",
        "source_id": "NLC404-01J000514-10459_光明報_1947年20期",
        "year": 1947,
        "period": "1947 民盟活动",
        "title": "《光明報》1947年20期",
        "issue_date": "1947",
    },
    {
        "batch": "GB1947_21",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1947_issue21_front_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1947_issue21_front_20260723",
        "image_pattern": "work/domestic/continue_pages/1947_21/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10460_光明報_1947年21期.pdf",
        "source_id": "NLC404-01J000514-10460_光明報_1947年21期",
        "year": 1947,
        "period": "1947 民盟活动",
        "title": "《光明報》1947年21期",
        "issue_date": "1947",
    },
    {
        "batch": "GB1947_22",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1947_issue22_front_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1947_issue22_front_20260723",
        "image_pattern": "work/domestic/continue_pages/1947_22/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10483_光明報_1947年22期.pdf",
        "source_id": "NLC404-01J000514-10483_光明報_1947年22期",
        "year": 1947,
        "period": "1947 民盟活动",
        "title": "《光明報》1947年22期",
        "issue_date": "1947",
    },
    {
        "batch": "GB1948_v1n1",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1948_v1n1_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/guangmingbao_1948_1949/v1n1_ocr",
        "image_pattern": "work/domestic/guangmingbao_1948_1949/v1n1_pages/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10484_光明報_1948年1卷1期.pdf",
        "source_id": "NLC404-01J000514-10484_光明報_1948年1卷1期",
        "year": 1948,
        "period": "1948 民盟三中全会",
        "title": "《光明報》1948年第一卷第一期",
        "issue_date": "1948-03-01",
    },
    {
        "batch": "GB1948_v1n12",
        "manifest": "work/domestic/paddle_ocr_guangmingbao_1948_v1n12_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_guangmingbao_1948_v1n12_20260723",
        "image_pattern": "work/domestic/continue_pages/1948_v1n12/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10514_光明報_1948年1卷12期.pdf",
        "source_id": "NLC404-01J000514-10514_光明報_1948年1卷12期",
        "year": 1948,
        "period": "1948 民盟史料",
        "title": "《光明報》1948年第一卷第十二期",
        "issue_date": "1948-08-16",
    },
    {
        "batch": "DAGANGBAO_1947_1106",
        "manifest": "work/domestic/paddle_ocr_dagangbao_vol114_1947_1106_manifest_20260723.jsonl",
        "ocr_dir": "work/domestic/paddle_ocr_observer_dagangbao_20260723",
        "image_pattern": "work/domestic/continue_pages/dagangbao_1947_1106/page-{:02d}.png",
        "source_file": "data/domestic/press_scans/NLC511-012031312030001-21906_大公報_第114卷.pdf",
        "source_id": "NLC511-012031312030001-21906_大公報_第114卷",
        "year": 1947,
        "period": "1947 民盟被宣布为非法",
        "title": "《大公報》第114卷1947年11月6日第2版关键页",
        "issue_date": "1947-11-06",
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
    task = f"T43_{batch['batch']}"
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
                # Find page image
                page_label = p.get("page_label", "")
                ocr_dir = ROOT / batch["ocr_dir"]
                page_image = None
                # Try patterns in image_pattern
                pattern = batch.get("image_pattern", "")
                # parse patterns like "rendered/page-{:02d}.png OR 1947_13/page-{:02d}.png"
                patterns = pattern.split(" OR ")
                for sub_pattern in patterns:
                    try:
                        formatted = sub_pattern.format(int(page_label))
                    except Exception:
                        formatted = sub_pattern
                    cand = ROOT / formatted
                    if cand.exists():
                        page_image = cand
                        break
                # Fallback: same dir as OCR
                if page_image is None:
                    for name in [f"page-{page_label}.png", f"page-{int(page_label):02d}.png", f"page-{int(page_label)}.png"]:
                        cand = ocr_dir / name
                        if cand.exists():
                            page_image = cand
                            break
                if page_image is None:
                    for f in ocr_dir.glob(f"page-{page_label}*"):
                        if f.suffix.lower() == ".png":
                            page_image = f
                            break
                page_image_sha = sha256_file(page_image) if page_image else None
                # line count
                with open(ocr_md_path) as f:
                    text = f.read()
                ocr_lines = sum(1 for l in text.splitlines() if l.strip())
                # Determine confidence
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
        "out_idx": str(out_idx),
        "out_prov": str(out_prov),
    }


def main():
    results = []
    for b in BATCHES:
        results.append(register(b))
    summary = {
        "task_id": "T43",
        "batches": results,
        "total_rows": sum(r.get("rows", 0) for r in results if not r.get("skipped")),
        "total_valid": sum(r.get("valid_rows", 0) for r in results if not r.get("skipped")),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out = RESEARCH_DIR / "T43_1947_GB_OCR_REGISTRATION.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
