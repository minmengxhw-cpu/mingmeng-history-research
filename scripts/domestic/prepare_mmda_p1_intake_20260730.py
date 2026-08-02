#!/usr/bin/env python3
"""Prepare a conservative local intake manifest for the three MMDA P1 leads.

The script scans the existing incoming directory only. It never downloads,
renames, deletes, OCRs, or imports files. It is safe to rerun after the user
places an authorized original PDF/image in the incoming directory.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "work/domestic/MMDA_1942_1943_PRIORITY_QUEUE_20260728.jsonl"
INCOMING = ROOT / "data/domestic/raw/mmda/incoming"
OUT = ROOT / "work/domestic/mmda_p1_intake_20260730"
P1_COUNT = 3
ALLOWED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".wav", ".mp3", ".mp4"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    queue = [json.loads(line) for line in QUEUE.read_text(encoding="utf-8").splitlines() if line.strip()]
    p1 = [row for row in queue if row.get("queue_rank") == 1][:P1_COUNT]
    incoming_files = [
        path for path in sorted(INCOMING.rglob("*"))
        if path.is_file() and path.name != "README.md" and path.suffix.lower() in ALLOWED_SUFFIXES
    ] if INCOMING.exists() else []

    file_records = []
    for path in incoming_files:
        file_records.append(
            {
                "path": str(path),
                "filename": path.name,
                "suffix": path.suffix.lower(),
                "mime_guess": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "status": "LOCAL_FILE_NEEDS_EXPLICIT_P1_MAPPING",
            }
        )

    records = []
    for row in p1:
        records.append(
            {
                "candidate_id": row.get("candidate_id"),
                "title": row.get("title"),
                "document_date": row.get("document_date"),
                "catalog_reference": row.get("catalog_reference"),
                "source_url": row.get("source_url"),
                "queue_rank": row.get("queue_rank"),
                "current_access": row.get("online_availability"),
                "ingest_gate": "original_file_sha_and_explicit_mapping_required",
                "local_intake_status": "WAITING_FOR_LOCAL_ORIGINAL" if not file_records else "NEEDS_EXPLICIT_FILE_MAPPING",
                "candidate_local_files": [item["path"] for item in file_records],
                "citation_ready": False,
                "human_verified": False,
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "P1_INTAKE_MANIFEST.jsonl").open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    (OUT / "LOCAL_FILES.json").write_text(json.dumps(file_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "report": "MMDA_P1_INTAKE_PREP_20260730",
        "p1_queue_rows": len(p1),
        "incoming_original_files": len(file_records),
        "records_waiting": sum(item["local_intake_status"] == "WAITING_FOR_LOCAL_ORIGINAL" for item in records),
        "explicit_mapping_required": sum(item["local_intake_status"] == "NEEDS_EXPLICIT_FILE_MAPPING" for item in records),
        "ocr_started": False,
        "staging_written": False,
        "formal_db_written": False,
        "rule": "hash and explicit source mapping precede OCR; no inferred mapping",
        "outputs": [str(OUT / "P1_INTAKE_MANIFEST.jsonl"), str(OUT / "LOCAL_FILES.json")],
    }
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# MMDA P1 本地接收准备",
        "",
        "本次只扫描本地 incoming，不下载、不重命名、不删除、不 OCR、不写数据库。",
        "",
        f"- P1 目录记录：{len(p1)} 条",
        f"- 已发现本地原件：{len(file_records)} 个",
        f"- 等待原件：{report['records_waiting']} 条",
        "",
        "## P1 队列",
        "",
        "| 日期 | 标题 | 本地状态 |",
        "|---|---|---|",
    ]
    for item in records:
        md.append(f"| {item['document_date']} | {item['title']} | {item['local_intake_status']} |")
    md.extend(
        [
            "",
            "## 文件入场后的固定顺序",
            "",
            "1. 按目录 ID 显式映射到一条 P1 记录。",
            "2. 登记原文件名、字节数、文件类型、SHA256、来源 URL 和下载时间。",
            "3. 通过文件完整性后再拆页、绑定物理页号和运行 PaddleOCR。",
            "4. 结果先进入 staging；`citation_ready` 和 `human_verified` 默认保持 false。",
            "",
        ]
    )
    (OUT / "README.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
