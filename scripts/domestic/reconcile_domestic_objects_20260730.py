#!/usr/bin/env python3
"""Reconcile domestic handoff rows into document/page/object-level metrics.

Read-only with respect to source data and the formal SQLite.  Outputs a new
phase-0 report under work/domestic/phase0_reconciliation_20260730/.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work/domestic/phase0_reconciliation_20260730"
QUEUE = ROOT / "work/domestic/grok_next_stage_20260730/05_handoff/DOMESTIC_PRIMARY_OCR_QUEUE.jsonl"
MACHINE_QUEUE = ROOT / "work/domestic/grok_next_stage_20260730/05_handoff/DOMESTIC_MACHINE_TEXT_QUEUE.jsonl"
SCHOLARLY_QUEUE = ROOT / "work/domestic/grok_next_stage_20260730/05_handoff/SCHOLARLY_FULLTEXT_QUEUE.jsonl"
FORMAL_DB = ROOT / "data/research_index.sqlite"
EXPECTED_FORMAL_SHA = "738d81525c09bbff09266db00e54916bf1ec220ee169751bf1b64f3fb0626944"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path) -> tuple[list[dict], int]:
    rows: list[dict] = []
    errors = 0
    if not path.exists():
        return rows, 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
            else:
                errors += 1
        except json.JSONDecodeError:
            errors += 1
    return rows, errors


def source_document_key(local_path: str | None, object_id: str | None) -> str:
    if not local_path:
        return f"object:{object_id or 'unknown'}"
    path = Path(local_path)
    if path.parent.name == "images":
        return f"asset-parent:{path.parent.parent.name}"
    stem = path.stem
    stem = re.sub(r"_page[_-]?\d+$", "", stem, flags=re.I)
    stem = re.sub(r"[_-](?:alternate_scan|scan|ocr)$", "", stem, flags=re.I)
    return f"file:{stem}"


def page_number(local_path: str | None) -> int | None:
    if not local_path:
        return None
    match = re.search(r"(?:page|p)[_-]?(\d+)", Path(local_path).name, flags=re.I)
    return int(match.group(1)) if match else None


def file_kind(row: dict) -> str:
    path = str(row.get("local_path") or "").lower()
    magic = str(row.get("magic") or "").lower()
    if path.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")) or magic in {"png", "jpeg", "jpg", "tiff"}:
        return "page_image"
    if path.endswith(".pdf") or magic == "pdf":
        return "pdf_original_or_scan"
    if path.endswith((".html", ".htm", ".txt")) or magic in {"html", "text"}:
        return "machine_text"
    return "other"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, queue_errors = load_jsonl(QUEUE)
    machine_rows, machine_errors = load_jsonl(MACHINE_QUEUE)
    scholarly_rows, scholarly_errors = load_jsonl(SCHOLARLY_QUEUE)

    documents: dict[str, dict] = {}
    pages: list[dict] = []
    sha_to_paths: defaultdict[str, set[str]] = defaultdict(set)
    path_to_rows: defaultdict[str, list[str]] = defaultdict(list)
    for row in rows:
        path = row.get("local_path")
        doc_key = source_document_key(path, row.get("object_id"))
        entry = documents.setdefault(
            doc_key,
            {
                "canonical_document_key": doc_key,
                "titles": set(),
                "phases": Counter(),
                "buckets": Counter(),
                "row_count": 0,
                "page_row_count": 0,
                "file_row_count": 0,
                "unique_sha256": set(),
                "unique_paths": set(),
            },
        )
        entry["titles"].add(str(row.get("title") or ""))
        entry["phases"][str(row.get("historical_phase") or "unknown")] += 1
        entry["buckets"][str(row.get("reclass_bucket") or "unknown")] += 1
        entry["row_count"] += 1
        kind = file_kind(row)
        if kind == "page_image":
            entry["page_row_count"] += 1
        else:
            entry["file_row_count"] += 1
        if row.get("sha256"):
            entry["unique_sha256"].add(row["sha256"])
            sha_to_paths[row["sha256"]].add(str(path or ""))
        if path:
            entry["unique_paths"].add(str(path))
            path_to_rows[str(path)].append(str(row.get("object_id") or ""))
        pages.append(
            {
                "object_id": row.get("object_id"),
                "canonical_document_key": doc_key,
                "local_path": path,
                "page_no": page_number(path),
                "sha256": row.get("sha256"),
                "file_kind": kind,
                "historical_phase": row.get("historical_phase"),
                "reclass_bucket": row.get("reclass_bucket"),
                "title": row.get("title"),
            }
        )

    document_rows = []
    for key, value in sorted(documents.items()):
        document_rows.append(
            {
                "canonical_document_key": key,
                "title": sorted(x for x in value["titles"] if x)[:5],
                "dominant_phase": value["phases"].most_common(1)[0][0] if value["phases"] else "unknown",
                "phase_counts": dict(value["phases"]),
                "bucket_counts": dict(value["buckets"]),
                "row_count": value["row_count"],
                "page_row_count": value["page_row_count"],
                "file_row_count": value["file_row_count"],
                "unique_sha256_count": len(value["unique_sha256"]),
                "unique_path_count": len(value["unique_paths"]),
            }
        )

    duplicate_sha = {
        sha: sorted(paths)
        for sha, paths in sha_to_paths.items()
        if sha and len(paths) > 1
    }
    duplicate_paths = {path: ids for path, ids in path_to_rows.items() if len(set(ids)) > 1}

    report = {
        "report": "DOMESTIC_CANONICAL_RECONCILIATION_20260730",
        "formal_db_sha256": sha256(FORMAL_DB),
        "formal_db_unchanged": sha256(FORMAL_DB) == EXPECTED_FORMAL_SHA,
        "inputs": {
            "primary_ocr_queue": {"path": str(QUEUE), "rows": len(rows), "json_errors": queue_errors},
            "machine_text_queue": {"path": str(MACHINE_QUEUE), "rows": len(machine_rows), "json_errors": machine_errors},
            "scholarly_fulltext_queue": {"path": str(SCHOLARLY_QUEUE), "rows": len(scholarly_rows), "json_errors": scholarly_errors},
        },
        "primary_ocr": {
            "queue_rows": len(rows),
            "canonical_document_objects": len(document_rows),
            "page_asset_rows": sum(1 for x in pages if x["file_kind"] == "page_image"),
            "pdf_or_scan_rows": sum(1 for x in pages if x["file_kind"] == "pdf_original_or_scan"),
            "unique_paths": len({x["local_path"] for x in pages if x["local_path"]}),
            "unique_sha256": len({x["sha256"] for x in pages if x["sha256"]}),
            "duplicate_sha_groups": len(duplicate_sha),
            "duplicate_path_groups": len(duplicate_paths),
            "phase_rows": dict(Counter(str(x.get("historical_phase") or "unknown") for x in rows)),
            "bucket_rows": dict(Counter(str(x.get("reclass_bucket") or "unknown") for x in rows)),
        },
        "warnings": [
            "page-level rows are not document counts",
            "PDF and derived page images must be collapsed by canonical_document_key",
            "1978-present rows require source-level historical-date verification",
            "formal database was not modified",
        ],
    }
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (OUT / "DOCUMENTS.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in document_rows)
    )
    (OUT / "PAGE_ASSETS.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in pages)
    )
    (OUT / "DUPLICATE_SHA.json").write_text(json.dumps(duplicate_sha, ensure_ascii=False, indent=2) + "\n")
    (OUT / "DUPLICATE_PATHS.json").write_text(json.dumps(duplicate_paths, ensure_ascii=False, indent=2) + "\n")

    with (OUT / "DOCUMENTS.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["canonical_document_key", "dominant_phase", "row_count", "page_row_count", "file_row_count", "unique_sha256_count", "unique_path_count"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: row[k] for k in fields} for row in document_rows)

    md = [
        "# 国内 canonical 文献/物理页重算",
        "",
        f"- OCR 队列行数：{len(rows)}",
        f"- canonical 文献对象：{len(document_rows)}",
        f"- 页图资产行：{report['primary_ocr']['page_asset_rows']}",
        f"- PDF/扫描文件行：{report['primary_ocr']['pdf_or_scan_rows']}",
        f"- 唯一路径：{report['primary_ocr']['unique_paths']}",
        f"- 唯一 SHA：{report['primary_ocr']['unique_sha256']}",
        f"- SHA 重复组：{report['primary_ocr']['duplicate_sha_groups']}",
        f"- 路径重复组：{report['primary_ocr']['duplicate_path_groups']}",
        f"- 正式库未改变：{report['formal_db_unchanged']}",
        "",
        "## 时期分布（按队列行，尚非最终文献分布）",
        "",
    ]
    md.extend(f"- {key}: {value}" for key, value in sorted(report["primary_ocr"]["phase_rows"].items()))
    md += ["", "## 说明", "", "页图、PDF 和其派生 OCR 必须在 canonical 文献层合并；本报告不向正式 SQLite 写入任何记录。"]
    (OUT / "REPORT.md").write_text("\n".join(md) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
