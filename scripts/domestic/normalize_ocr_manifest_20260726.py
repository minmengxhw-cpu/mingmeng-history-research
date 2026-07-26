#!/usr/bin/env python3
"""Normalize OCR manifests and derive missing page ranges without touching SQLite."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/domestic"


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def pdf_pages(path: Path):
    try:
        out = subprocess.check_output(["pdfinfo", str(path)], text=True, stderr=subprocess.STDOUT)
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def main():
    names = [
        ("accepted21", "CLAUDE_OCR_MANIFEST_ACCEPTED21_20260726.jsonl"),
        ("pending37", "CLAUDE_OCR_MANIFEST_PENDING37_20260726.jsonl"),
        ("accepted_orphan", "CLAUDE_OCR_MANIFEST_P3-023_20260726.jsonl"),
    ]
    rows = []
    seen = set()
    for batch, name in names:
        for raw in read_jsonl(WORK / name):
            fid = raw["file_id"]
            if fid in seen:
                continue
            seen.add(fid)
            source = ROOT / raw["rel_path"]
            exists = source.exists()
            actual_sha = sha256(source) if exists else ""
            actual_size = source.stat().st_size if exists else 0
            actual_pages = pdf_pages(source) if exists and source.suffix.lower() == ".pdf" else raw.get("pdf_pages_actual")
            chunks = raw.get("chunk_paths") or []
            chunk_exists = all((ROOT / c).exists() for c in chunks) if chunks else bool(raw.get("all_chunks_exist"))
            repaired = raw.get("sha256_manifest") != actual_sha or str(raw.get("size_bytes_manifest")) != str(actual_size)
            out = dict(raw)
            out.update({
                "batch": batch,
                "sha256": actual_sha,
                "size_bytes": actual_size,
                "page_count": actual_pages,
                "source_exists": exists,
                "all_chunks_exist": chunk_exists,
                "ocr_output_paths": chunks,
                "manifest_repaired": repaired,
                "repair_reason": "standardized_from_actual_disk_file" if repaired else "already_matches_disk",
                "citation_ready": False,
                "needs_human_review": True,
            })
            rows.append(out)

    out_jsonl = WORK / "CLAUDE_B_OCR_MANIFEST_NORMALIZED_20260726.jsonl"
    with out_jsonl.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    fields = ["file_id", "batch", "rel_path", "source_exists", "sha256", "size_bytes", "page_count", "all_chunks_exist", "manifest_repaired", "repair_reason"]
    with (WORK / "CLAUDE_B_MANIFEST_NORMALIZATION_20260726.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})

    missing = []
    targets = [
        ("P3-113", "data/domestic/press_scans/NLC511-012031312030001-21905_大公報_第113卷.pdf", 232),
        ("P3-114", "data/domestic/press_scans/NLC511-012031312030001-21906_大公報_第114卷.pdf", 248),
    ]
    for fid, rel, total in targets:
        prefix = Path(rel).stem
        covered = set()
        pattern = re.compile(re.escape(prefix) + r"_p(\d{4})-(\d{4})\.ocr\.md$")
        for path in (WORK / "ocr_collection_phase4").glob(prefix + "_p*.ocr.md"):
            m = pattern.search(path.name)
            if m:
                covered.update(range(int(m.group(1)), int(m.group(2)) + 1))
        missing_pages = [p for p in range(1, total + 1) if p not in covered]
        if missing_pages:
            start = prev = missing_pages[0]
            for page in missing_pages[1:] + [None]:
                if page is not None and page == prev + 1:
                    prev = page
                    continue
                missing.append({"file_id": fid, "source_path": rel, "total_pages": total, "start_page": start, "end_page": prev, "page_count": prev - start + 1})
                if page is not None:
                    start = prev = page

    qfields = ["file_id", "source_path", "total_pages", "start_page", "end_page", "page_count"]
    with (WORK / "CLAUDE_B_MISSING_PAGE_QUEUE_20260726.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=qfields)
        writer.writeheader()
        writer.writerows(missing)
    md = ["# Claude B 缺页队列（2026-07-26）", "", f"发现 {len(missing)} 个连续缺页区间。", ""]
    for row in missing:
        md.append(f"- `{row['file_id']}`：p{row['start_page']:04d}–p{row['end_page']:04d}（{row['page_count']} 页）")
    (WORK / "CLAUDE_B_MISSING_PAGE_QUEUE_20260726.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    summary = {
        "normalized_records": len(rows),
        "batches": {b: sum(r["batch"] == b for r in rows) for b, _ in names},
        "source_missing": sum(not r["source_exists"] for r in rows),
        "sha_mismatch_repaired": sum(r["manifest_repaired"] for r in rows),
        "chunks_missing": sum(not r["all_chunks_exist"] for r in rows),
        "missing_page_ranges": missing,
        "sqlite_touched": False,
    }
    (WORK / "CLAUDE_B_MANIFEST_NORMALIZATION_20260726.md").write_text(
        "# Claude B Manifest 规范化报告（2026-07-26）\n\n" + json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
