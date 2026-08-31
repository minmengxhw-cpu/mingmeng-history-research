#!/usr/bin/env python3
"""Audit local source availability for two historical primary candidates.

Only filenames, sizes and SHA256 values are inspected. The two OCR Markdown
files are not opened and no related file is auto-bound to a candidate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OBJECTS = ROOT / "work/domestic/local_private_ocr_metadata_20260730/LOCAL_DOCUMENT_OBJECTS.jsonl"
KNOWLEDGE_BASE = Path("<local-user>/Documents/民盟/knowledge_base")
OUT = ROOT / "work/domestic/local_private_ocr_metadata_20260730/historical_primary_audit"
TARGET_IDS = ("J067-001-001-105", "J067-001-001-108")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metadata(path: Path) -> dict:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path), "suffix": path.suffix.lower()}


def main() -> None:
    objects = [json.loads(line) for line in OBJECTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    targets = [row for row in objects if row["document_class"] == "historical_primary_candidate"]
    related = []
    if KNOWLEDGE_BASE.exists():
        for path in KNOWLEDGE_BASE.rglob("*"):
            if not path.is_file():
                continue
            name = path.name
            if any(target in name for target in TARGET_IDS) or "三中全会" in name:
                related.append(metadata(path))

    rows = []
    for row in targets:
        exact_originals = [
            item for item in related
            if row["title"].split("民盟", 1)[-1].strip("_ ") in Path(item["path"]).name
            and not Path(item["path"]).name.endswith(".ocr.md")
        ]
        rows.append(
            {
                "document_object_id": row["document_object_id"],
                "candidate_title": row["title"],
                "candidate_sha256": row["sha256"],
                "ocr_path": row["local_path"],
                "ocr_status": "OCR_ONLY_NO_ORIGINAL" if not exact_originals else "ORIGINAL_CANDIDATE_REQUIRES_EXPLICIT_MAPPING",
                "exact_original_candidates": exact_originals,
                "related_three_plenary_files": related,
                "auto_bound": False,
                "citation_ready": False,
                "human_verified": False,
                "next_action": "locate source record or original scan; verify J067 ID and page chain before OCR/staging",
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "PRIMARY_CANDIDATE_SOURCE_AUDIT.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )
    report = {
        "report": "LOCAL_HISTORICAL_PRIMARY_SOURCE_AUDIT_20260730",
        "target_candidates": len(rows),
        "ocr_only_candidates": sum(row["ocr_status"] == "OCR_ONLY_NO_ORIGINAL" for row in rows),
        "exact_original_candidates": sum(bool(row["exact_original_candidates"]) for row in rows),
        "related_three_plenary_files_found": len(related),
        "auto_bound": 0,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "body_read": False,
        "staging_db_written": False,
        "formal_db_written": False,
        "rule": "related filenames are evidence for review only; no automatic binding",
        "output": str(OUT / "PRIMARY_CANDIDATE_SOURCE_AUDIT.jsonl"),
    }
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(
        "# J067 三中全会历史一手候选来源审计\n\n"
        "当前只确认本地 OCR Markdown；相关文件名不自动等同于候选原件。\n\n"
        f"- 候选数：{len(rows)}\n"
        f"- 只有 OCR、未找到同 ID 原件：{report['ocr_only_candidates']}\n"
        f"- 发现相关三中全会文件名：{report['related_three_plenary_files_found']}\n"
        "- 下一步：核对 J067 目录/原件关系，建立来源记录和页链。\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
