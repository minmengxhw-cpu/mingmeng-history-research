#!/usr/bin/env python3
"""Reconcile the public-web manifest with the current domestic index."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_MANIFEST = ROOT / "work" / "domestic" / "PUBLIC_WEB_EXTRACT_MANIFEST_20260728.jsonl"
DEFAULT_JSON = ROOT / "work" / "domestic" / "PUBLIC_WEB_IMPORT_RECONCILIATION_20260728.json"
DEFAULT_MD = ROOT / "work" / "domestic" / "PUBLIC_WEB_IMPORT_RECONCILIATION_20260728.md"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    manifest = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = []
    for item in manifest:
        download_id = item["download_id"]
        doc = conn.execute("SELECT id, doc_key, title FROM documents WHERE doc_key=?", (f"domestic-web/{download_id}",)).fetchone()
        page_count = fts_count = 0
        if doc:
            page_ids = [r[0] for r in conn.execute("SELECT id FROM pages WHERE document_id=?", (doc["id"],))]
            page_count = len(page_ids)
            fts_count = sum(conn.execute("SELECT 1 FROM page_fts WHERE rowid=?", (page_id,)).fetchone() is not None for page_id in page_ids)
        extracted = ROOT / item["extracted_text_path"]
        extracted_sha = digest(extracted) if extracted.is_file() else None
        rows.append(
            {
                "download_id": download_id,
                "title": item["title"],
                "formal_import": bool(item.get("formal_import")),
                "document_present": doc is not None,
                "page_count": page_count,
                "fts_count": fts_count,
                "extracted_text_present": extracted.is_file(),
                "extracted_text_sha256_matches": extracted_sha == item.get("extracted_text_sha256"),
                "db_doc_key": doc["doc_key"] if doc else None,
            }
        )
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    conn.close()
    gate = all(
        row["extracted_text_present"]
        and row["extracted_text_sha256_matches"]
        and ((row["formal_import"] and row["document_present"] and row["page_count"] > 0 and row["page_count"] == row["fts_count"]) or (not row["formal_import"] and not row["document_present"]))
        for row in rows
    ) and integrity == "ok"
    result = {"gate": "PASS" if gate else "HOLD", "read_only": True, "db_integrity": integrity, "manifest_rows": len(rows), "rows": rows}
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    imported = [r for r in rows if r["formal_import"]]
    held = [r for r in rows if not r["formal_import"]]
    lines = [
        "# 公开网页资料入库对账（2026-07-28）",
        "",
        f"- 门控：**{result['gate']}**",
        "- 本次为只读对账，不修改 SQLite。",
        f"- 清单：{len(rows)} 条；正式入库：{len(imported)} 条；保留线索未入库：{len(held)} 条。",
        f"- 数据库完整性：`{integrity}`。",
        "",
        "## 处置",
        "",
        "- 正式入库的网页文本均有本地抽取文件、文档、页面和 FTS 对应关系。",
        "- 未正式入库的维基百科导航/原始 wikitext 保留为线索，避免把导航性二次来源混入主库。",
        "- 所有条目仍标记为需要人工复核；公开网页和官方回顾不能替代同期一手原件。",
        "",
        "| ID | 正式入库 | 文档 | 页面/FTS | 文本 SHA256 | 标题 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(f"| {row['download_id']} | {row['formal_import']} | {row['document_present']} | {row['page_count']}/{row['fts_count']} | {row['extracted_text_sha256_matches']} | {row['title']} |")
    args.md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
