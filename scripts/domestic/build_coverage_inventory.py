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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pdf_pages(path: Path) -> str:
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
    pdf_roots = [project / "data/domestic/press_scans", project / "data/domestic/sourcebooks"]
    pdfs = sorted({p for root in pdf_roots if root.exists() for p in root.rglob("*.pdf")})
    manifests = load_manifests(project / "work/domestic")
    conn = sqlite3.connect(db_path)
    rows: list[dict[str, str]] = []
    for path in pdfs:
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
        if indexed_pages:
            status = "indexed"
        elif source_manifests:
            status = "manifest_only"
        else:
            status = "source_only"
        rows.append(
            {
                "source_path": rel,
                "source_group": "sourcebooks" if "/sourcebooks/" in f"/{rel}" else "press_scans",
                "pdf_pages": pdf_pages(path),
                "sha256": sha256(path),
                "manifest_records": str(len(source_manifests)),
                "manifest_pages": str(manifest_pages),
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
    lines = [
        "# 国内来源全量覆盖清单",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        f"来源 PDF：{len(rows)}；已入库：{counts['indexed']}；仅有 manifest：{counts['manifest_only']}；仅有来源文件：{counts['source_only']}。",
        "",
        "详细字段见同名 CSV。状态定义：`indexed` 表示 manifest record 已在 SQLite 中找到对应 domestic-ocr 文档；`manifest_only` 表示有 OCR manifest 但尚未入库；`source_only` 表示当前尚未关联到 manifest。",
        "",
        "| 状态 | 数量 |",
        "| --- | ---: |",
        f"| indexed | {counts['indexed']} |",
        f"| manifest_only | {counts['manifest_only']} |",
        f"| source_only | {counts['source_only']} |",
        "",
        "## 待处理来源",
        "",
    ]
    for row in rows:
        if row["status"] != "indexed":
            lines.append(f"- `{row['status']}`：`{row['source_path']}`（{row['pdf_pages']} 页，SHA256 `{row['sha256']}`）")
    args.output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"pdfs": len(rows), "counts": dict(counts), "csv": str(args.output_csv), "md": str(args.output_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
