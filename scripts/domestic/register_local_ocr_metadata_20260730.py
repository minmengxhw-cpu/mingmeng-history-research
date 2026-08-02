#!/usr/bin/env python3
"""Register metadata for selected local OCR files without reading their bodies.

The source files remain in their existing local knowledge-base location. This
creates only a metadata manifest in the research project; it does not copy,
move, delete, or import the files into either SQLite database.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = Path("/Users/cheer/Documents/民盟/knowledge_base/data/processed/ocr_markdown_overnight_2026-07-10")
OUT = ROOT / "work/domestic/local_private_ocr_metadata_20260730"
KEYWORDS = ("陕西民盟史", "沪盟通讯", "民主同盟", "陕西", "民盟")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify(name: str) -> str:
    if "陕西民盟史" in name:
        return "retrospective_local_history"
    if "沪盟通讯" in name:
        return "organizational_periodical"
    if any(term in name for term in ("报告", "记录", "大会文件", "通知", "决定")):
        return "official_or_internal_document"
    return "local_ocr_candidate"


def main() -> None:
    files = [
        path for path in sorted(SOURCE_DIR.glob("*.ocr.md"))
        if any(keyword in path.name for keyword in KEYWORDS)
    ] if SOURCE_DIR.exists() else []
    rows = []
    for path in files:
        name = path.name
        dates = sorted(set(re.findall(r"(?:19|20)\d{2}(?:[.-]\d{1,2})?", name)))
        rows.append(
            {
                "metadata_id": "LOCAL-OCR-" + sha256_file(path)[:16],
                "filename": name,
                "local_path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "file_kind": "ocr_markdown",
                "source_layer": "local_private_knowledge_base",
                "document_class": classify(name),
                "filename_date_signals": dates,
                "evidence_status": "machine_text_ready",
                "citation_ready": False,
                "human_verified": False,
                "body_read_by_registration": False,
                "formal_db_written": False,
                "staging_db_written": False,
                "classification_rule": "filename and file metadata only; semantic meaning not inferred",
            }
        )
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = OUT / "LOCAL_PRIVATE_OCR_METADATA.jsonl"
    manifest.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + ("\n" if rows else ""), encoding="utf-8")
    report = {
        "report": "LOCAL_PRIVATE_OCR_METADATA_20260730",
        "source_directory": str(SOURCE_DIR),
        "rows": len(rows),
        "classes": {name: sum(row["document_class"] == name for row in rows) for name in sorted({row["document_class"] for row in rows})},
        "body_read_by_registration": False,
        "staging_db_written": False,
        "formal_db_written": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "manifest": str(manifest),
    }
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(
        "# 本地私有 OCR 元数据登记\n\n"
        "本登记只记录文件名、路径、大小和 SHA256，不读取正文，不复制或移动原文件。\n\n"
        f"- 文件数：{len(rows)}\n"
        "- 当前全部保持 machine_text_ready；不得直接当作 citation_ready。\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
