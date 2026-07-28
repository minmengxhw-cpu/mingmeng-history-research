#!/usr/bin/env python3
"""Build a provenance-aware inventory of local domestic PDF sources.

The report intentionally separates source files, OCR manifests, and indexed
documents. A PDF with OCR drafts is not treated as indexed unless the manifest
record can be found in research_index.sqlite.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def integer(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def pdf_pages(path: Path) -> str:
    if path.suffix.lower() in IMAGE_SUFFIXES:
        return "1"
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    match = re.search(r"^Pages:\s+(\d+)$", result.stdout, re.MULTILINE)
    return match.group(1) if match else ""


def load_manifests(root: Path) -> dict[str, list[dict]]:
    by_source: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(root.rglob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line in lines:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            source = record.get("source_path")
            record_id = record.get("record_id")
            if source and record_id:
                record = dict(record)
                record["manifest_path"] = str(path)
                by_source[source].append(record)
    return by_source


def load_local_draft_coverage(project: Path) -> dict[str, dict[str, object]]:
    """Load locally retained full-OCR draft manifests without importing text.

    The accepted21 handoff uses ``rel_path`` and ``chunk_paths`` rather than
    the formal ``record_id/pages`` shape. A draft is counted only when its
    declared physical page count is known and every referenced OCR chunk is
    present locally. These drafts remain local-only and are not citation-ready.
    """

    by_source: dict[str, dict[str, object]] = {}
    root = project / "work/domestic"
    for manifest_path in sorted(root.glob("CLAUDE_OCR_MANIFEST_ACCEPTED21_*.jsonl")):
        try:
            lines = manifest_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line in lines:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            source = record.get("source_path") or record.get("rel_path")
            pages = record.get("pdf_pages_actual") or record.get("pdf_pages_manifest")
            chunks = record.get("chunk_paths") or []
            if not source or integer(str(pages)) is None or not chunks:
                continue
            page_count = integer(str(pages)) or 0
            existing_chunks = []
            for chunk in chunks:
                chunk_path = Path(str(chunk))
                if not chunk_path.is_absolute():
                    chunk_path = project / chunk_path
                if not chunk_path.exists():
                    break
                existing_chunks.append(str(chunk))
            else:
                current = by_source.setdefault(
                    str(source), {"pages": 0, "records": 0, "paths": []}
                )
                current["pages"] = max(int(current["pages"]), page_count)
                current["records"] = int(current["records"]) + 1
                current["paths"] = sorted(set(current["paths"]) | set(existing_chunks))
    return by_source


def indexed_stats(conn: sqlite3.Connection, record_id: str) -> tuple[int, int, str]:
    key = f"domestic-ocr/{record_id}"
    row = conn.execute(
        """
        SELECT COUNT(DISTINCT d.id), COUNT(p.id), COALESCE(GROUP_CONCAT(d.title, '；'), '')
        FROM documents d LEFT JOIN pages p ON p.document_id=d.id
        WHERE d.doc_key=?
        """,
        (key,),
    ).fetchone()
    return int(row[0]), int(row[1]), row[2] or ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--db", type=Path, default=Path("data/research_index.sqlite"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    project = args.project.resolve()
    db_path = (project / args.db).resolve() if not args.db.is_absolute() else args.db
    source_roots = [
        project / "data/domestic/press_scans",
        project / "data/domestic/sourcebooks",
        project / "data/domestic/gazette_scans",
    ]
    source_files = sorted(
        {
            p
            for root in source_roots
            if root.exists()
            for p in root.rglob("*")
            if p.is_file() and (p.suffix.lower() == ".pdf" or p.suffix.lower() in IMAGE_SUFFIXES)
        }
    )
    manifests = load_manifests(project / "work/domestic")
    local_drafts = load_local_draft_coverage(project)
    conn = sqlite3.connect(db_path)
    rows: list[dict[str, str]] = []
    for path in source_files:
        rel = path.relative_to(project).as_posix()
        source_manifests = manifests.get(rel, [])
        # Some older manifests carry an absolute source path.
        if not source_manifests:
            source_manifests = manifests.get(str(path), [])
        indexed_docs = 0
        indexed_pages = 0
        titles: list[str] = []
        record_ids: list[str] = []
        manifest_pages = 0
        for record in source_manifests:
            record_ids.append(record["record_id"])
            manifest_pages += len(record.get("pages", []))
            docs, pages, record_titles = indexed_stats(conn, record["record_id"])
            indexed_docs += docs
            indexed_pages += pages
            if record_titles:
                titles.append(record_titles)
        draft = local_drafts.get(rel, {})
        draft_pages = int(draft.get("pages", 0))
        draft_records = int(draft.get("records", 0))
        draft_paths = "；".join(str(path) for path in draft.get("paths", []))
        physical_pages = integer(pdf_pages(path))
        if physical_pages is not None and indexed_pages > physical_pages:
            status = "formal_page_count_anomaly"
        elif physical_pages is not None and indexed_pages == physical_pages:
            status = "formal_page_complete"
        elif physical_pages is not None and draft_pages >= physical_pages:
            status = "draft_ready_formal_gap"
        elif draft_pages:
            status = "draft_partial_formal_gap"
        elif indexed_pages:
            status = "indexed_partial_no_draft"
        elif source_manifests:
            status = "manifest_only"
        else:
            status = "source_only"
        rows.append(
            {
                "source_path": rel,
                "source_group": (
                    "sourcebooks"
                    if "/sourcebooks/" in f"/{rel}"
                    else "gazette_scans"
                    if "/gazette_scans/" in f"/{rel}"
                    else "press_scans"
                ),
                "pdf_pages": str(physical_pages or ""),
                "sha256": sha256(path),
                "manifest_records": str(len(source_manifests)),
                "manifest_pages": str(manifest_pages),
                "ocr_draft_records": str(draft_records),
                "ocr_draft_pages": str(draft_pages),
                "ocr_draft_paths": draft_paths,
                "indexed_documents": str(indexed_docs),
                "indexed_pages": str(indexed_pages),
                "status": status,
                "record_ids": "；".join(record_ids),
                "indexed_titles": "；".join(titles),
            }
        )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["source_path"]
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    counts = defaultdict(int)
    for row in rows:
        counts[row["status"]] += 1
    physical_total = sum(integer(row["pdf_pages"]) or 0 for row in rows)
    draft_total = sum(integer(row["ocr_draft_pages"]) or 0 for row in rows)
    indexed_total = sum(integer(row["indexed_pages"]) or 0 for row in rows)
    lines = [
        "# 国内来源全量覆盖清单",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        f"来源文件：{len(rows)}；物理页：{physical_total}；本地 OCR 草稿页：{draft_total}；SQLite 正式入库页：{indexed_total}。",
        "",
        "详细字段见同名 CSV。`formal_page_complete` 才表示物理页与 SQLite 页级入库相等；`draft_ready_formal_gap` 表示本地已有完整 OCR 草稿但尚未进入正式页层；`draft_partial_formal_gap` 表示只有部分 OCR 草稿。OCR 草稿和其 manifest 仍保留在本机，未随本次元数据提交上传。",
        "",
        "| 状态 | 数量 |",
        "| --- | ---: |",
        f"| formal_page_complete | {counts['formal_page_complete']} |",
        f"| formal_page_count_anomaly | {counts['formal_page_count_anomaly']} |",
        f"| draft_ready_formal_gap | {counts['draft_ready_formal_gap']} |",
        f"| draft_partial_formal_gap | {counts['draft_partial_formal_gap']} |",
        f"| indexed_partial_no_draft | {counts['indexed_partial_no_draft']} |",
        f"| manifest_only | {counts['manifest_only']} |",
        f"| source_only | {counts['source_only']} |",
        "",
        "## 待处理来源",
        "",
    ]
    for row in rows:
        if row["status"] != "formal_page_complete":
            lines.append(f"- `{row['status']}`：`{row['source_path']}`（{row['pdf_pages']} 页，SHA256 `{row['sha256']}`）")
    args.output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"pdfs": len(rows), "counts": dict(counts), "csv": str(args.output_csv), "md": str(args.output_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
