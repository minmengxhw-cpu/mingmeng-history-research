#!/usr/bin/env python3
"""Normalize the selected local OCR metadata into conservative document objects.

Only the prior metadata manifest is read. The OCR bodies are not opened. The
result is a review/scope layer, not a staging or formal database import.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "work/domestic/local_private_ocr_metadata_20260730/LOCAL_PRIVATE_OCR_METADATA.jsonl"
OUT = ROOT / "work/domestic/local_private_ocr_metadata_20260730"


def title_from_filename(filename: str) -> str:
    stem = filename.removesuffix(".ocr.md")
    parts = stem.split("_", 2)
    return parts[2] if len(parts) == 3 else stem


def period_signals(title: str) -> list[str]:
    ranges = re.findall(r"((?:19|20)\d{2})\s*[-—]\s*((?:19|20)\d{2})", title)
    if ranges:
        return [f"{start}-{end}" for start, end in ranges]
    return sorted(set(re.findall(r"(?:19|20)\d{2}(?:[.]\d{1,2})?", title)))


def scope_and_class(title: str) -> tuple[str, str]:
    if "美国对外关系文件集" in title or "frus" in title.lower():
        return "overseas_out_of_domestic_scope", "overseas_primary_or_secondary"
    if any(term in title for term in ("民盟史", "组织简史", "编年史", "70年")):
        return "domestic_retrospective", "retrospective_local_history"
    if "沪盟通讯" in title:
        return "domestic_organizational_periodical", "organizational_periodical"
    if "三中全会" in title or "紧急声明" in title or "宣言" in title:
        return "domestic_historical_primary_candidate", "historical_primary_candidate"
    if any(term in title for term in ("简史", "60年", "70年", "解放前后", "史料")):
        return "domestic_retrospective", "retrospective_local_history"
    if any(term in title for term in ("报告", "记录", "大会文件", "通知", "决定", "政治报告")):
        return "domestic_official_or_internal", "official_or_internal_document"
    if any(term in title for term in ("附件", "函", "批复", "请示", "意见", "材料", "汇编", "传达", "工作要点", "述职", "提案")):
        return "domestic_official_or_internal", "official_or_internal_document"
    if "封面" in title:
        return "domestic_catalog_or_cover", "catalog_or_cover"
    if "参考资料" in title:
        return "domestic_reference_material", "reference_material"
    return "domestic_review_needed", "local_ocr_candidate"


def main() -> None:
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_sha = {}
    for row in rows:
        by_sha.setdefault(row["sha256"], row)

    objects = []
    for row in sorted(by_sha.values(), key=lambda item: item["filename"]):
        title = title_from_filename(row["filename"])
        scope, document_class = scope_and_class(title)
        objects.append(
            {
                "document_object_id": "LOCAL-DOC-" + row["sha256"][:16],
                "title": title,
                "local_path": row["local_path"],
                "bytes": row["bytes"],
                "sha256": row["sha256"],
                "scope": scope,
                "document_class": document_class,
                "period_signals": period_signals(title),
                "source_layer": row["source_layer"],
                "evidence_status": "machine_text_ready",
                "body_read_by_normalizer": False,
                "citation_ready": False,
                "human_verified": False,
                "next_gate": "review title/source/period and verify original or source record",
            }
        )

    manifest = OUT / "LOCAL_DOCUMENT_OBJECTS.jsonl"
    manifest.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in objects) + ("\n" if objects else ""), encoding="utf-8")
    scope_counts = Counter(row["scope"] for row in objects)
    class_counts = Counter(row["document_class"] for row in objects)
    report = {
        "report": "LOCAL_OCR_DOCUMENT_NORMALIZATION_20260730",
        "input_rows": len(rows),
        "unique_sha256_objects": len(objects),
        "scope_counts": dict(sorted(scope_counts.items())),
        "class_counts": dict(sorted(class_counts.items())),
        "domestic_scope_objects": sum(row["scope"] != "overseas_out_of_domestic_scope" for row in objects),
        "overseas_excluded_objects": scope_counts.get("overseas_out_of_domestic_scope", 0),
        "body_read_by_normalizer": False,
        "staging_db_written": False,
        "formal_db_written": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "manifest": str(manifest),
        "rule": "filename/metadata scope classification only; no semantic claim inferred",
    }
    (OUT / "NORMALIZATION_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review = [row for row in objects if row["scope"] == "domestic_review_needed"]
    (OUT / "DOMESTIC_REVIEW_QUEUE.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in review) + ("\n" if review else ""), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
