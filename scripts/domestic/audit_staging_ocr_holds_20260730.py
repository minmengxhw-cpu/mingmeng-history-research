#!/usr/bin/env python3
"""Audit, but do not auto-resolve, OCR binding holds and invalid rows."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/ocr_hold_audit_20260730"


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def candidate_paths(source_file: str) -> list[Path]:
    path = Path(source_file)
    if not path.name:
        return []
    directory = ROOT / path.parent
    if not directory.is_dir():
        return []
    # T54 omitted the NLC resource number between the final hyphen and title.
    # This creates a review candidate only; it never changes the binding.
    pattern_name = re.sub(r"(NLC[^-_]+(?:-[^-_]+)*)-_", r"\1-*", path.name)
    candidates = sorted(directory.glob(pattern_name))
    return [x for x in candidates if x.is_file()]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    docs_by_path = {
        r["local_path"]: r["canonical_document_key"]
        for r in c.execute(
            """SELECT p.local_path, d.canonical_document_key
               FROM page_assets p JOIN documents d ON d.id=p.document_id
               WHERE p.local_path IS NOT NULL"""
        )
    }
    rows = c.execute(
        """SELECT * FROM ocr_versions
           WHERE binding_status='HOLD_UNBOUND_SOURCE_FILE' OR valid=0
           ORDER BY provenance_id"""
    ).fetchall()
    results = []
    reason_counts = Counter()
    for row in rows:
        reasons: list[str] = []
        if row["binding_status"] == "HOLD_UNBOUND_SOURCE_FILE":
            reasons.append("UNBOUND_SOURCE_FILE")
        if not row["valid"]:
            reasons.append("PROVENANCE_VALID_FALSE")
        source_file = str(row["source_file"] or "")
        source_path = ROOT / source_file
        if not source_path.is_file():
            reasons.append("SOURCE_FILE_NOT_FOUND")
        if not row["source_sha256"]:
            reasons.append("SOURCE_SHA_MISSING")
        ocr_path = ROOT / str(row["ocr_md_path"] or "")
        if not row["ocr_md_path"] or not ocr_path.is_file():
            reasons.append("OCR_MARKDOWN_NOT_FOUND")
        image_path = ROOT / str(row["page_image_path"] or "")
        if not row["page_image_path"] or not image_path.is_file():
            reasons.append("PAGE_IMAGE_NOT_FOUND")
        if row["ocr_confidence"] is not None and float(row["ocr_confidence"]) < 0.60:
            reasons.append("LOW_OCR_CONFIDENCE")
        candidates = []
        if row["binding_status"] == "HOLD_UNBOUND_SOURCE_FILE":
            for candidate in candidate_paths(source_file):
                candidate_sha = file_sha(candidate)
                candidates.append(
                    {
                        "path": str(candidate.relative_to(ROOT)),
                        "sha256": candidate_sha,
                        "sha_matches_record": bool(row["source_sha256"] and candidate_sha == row["source_sha256"]),
                        "canonical_document_key": docs_by_path.get(str(candidate.relative_to(ROOT))),
                    }
                )
        for reason in reasons:
            reason_counts[reason] += 1
        results.append(
            {
                "provenance_id": row["provenance_id"],
                "source_id": row["source_id"],
                "source_file": source_file,
                "canonical_document_key": row["canonical_document_key"],
                "binding_status": row["binding_status"],
                "valid": bool(row["valid"]),
                "ocr_confidence": row["ocr_confidence"],
                "reasons": reasons,
                "candidate_paths": candidates,
                "action": "HOLD_REQUIRES_SOURCE_SHA_OR_EXPLICIT_MAPPING",
            }
        )
    c.close()
    (OUT / "OCR_HOLD_AUDIT.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in results)
    )
    report = {
        "report": "DOMESTIC_OCR_HOLD_AUDIT_20260730",
        "rows_audited": len(results),
        "unbound_rows": sum(x["binding_status"] == "HOLD_UNBOUND_SOURCE_FILE" for x in results),
        "invalid_rows": sum(not x["valid"] for x in results),
        "reason_counts": dict(reason_counts),
        "auto_resolved": 0,
        "formal_db_written": False,
        "rule": "candidate paths are evidence for review only; no OCR binding is inferred",
    }
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    md = [
        "# OCR provenance HOLD 审计",
        "",
        "本报告只审计不自动修复。候选路径不会改变 canonical 绑定，除非后续取得 source SHA 或明确的人工映射证据。",
        "",
        f"- 审计行数：{len(results)}",
        f"- 未绑定：{report['unbound_rows']}",
        f"- invalid：{report['invalid_rows']}",
        f"- 自动修复：{report['auto_resolved']}",
        "",
        "## 原因统计",
        "",
    ]
    md.extend(f"- {k}: {v}" for k, v in sorted(reason_counts.items()))
    md += ["", "所有记录继续保持 HOLD，不能直接成为 citation-ready。"]
    (OUT / "REPORT.md").write_text("\n".join(md) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
