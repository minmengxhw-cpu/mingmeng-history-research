#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit the distinct full-text objects in the crosswalk material queue."""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "work/domestic/staging_20260730/crosswalk_material_review_queue/FULLTEXT_FIRST.jsonl"
OUT = ROOT / "work/domestic/staging_20260730/crosswalk_fulltext_audit"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def visible_html(raw: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    status_counts = Counter()
    for row in rows:
        path = Path(row["local_path"]) if row.get("local_path") else None
        if path and not path.is_absolute():
            path = ROOT / path
        checks = {
            "path_exists": bool(path and path.is_file()),
            "sha_present": bool(row.get("sha256")),
            "sha_matches": False,
            "format_matches_status": False,
            "nonempty": False,
            "title_signal_visible": False,
            "title_signal_applicable": False,
        }
        actual_sha = None
        byte_count = 0
        visible_chars = 0
        if checks["path_exists"]:
            actual_sha = sha(path)
            byte_count = path.stat().st_size
            checks["sha_matches"] = actual_sha == row.get("sha256")
            checks["nonempty"] = byte_count > 0
            if path.suffix.lower() == ".pdf":
                checks["format_matches_status"] = row.get("fulltext_status") == "FULLTEXT_PDF" and path.read_bytes()[:4] == b"%PDF"
                visible_chars = 0
                checks["title_signal_applicable"] = False
                checks["title_signal_visible"] = None
            elif path.suffix.lower() in (".html", ".htm"):
                text = visible_html(path.read_text(encoding="utf-8", errors="replace"))
                visible_chars = len(text)
                checks["format_matches_status"] = row.get("fulltext_status") == "FULLTEXT_HTML_CANDIDATE"
                checks["title_signal_applicable"] = True
                title = re.sub(r"[^\u3400-\u9fffA-Za-z0-9]", "", row.get("material_title") or "")
                title_token = title[:8]
                checks["title_signal_visible"] = bool(title_token and title_token in re.sub(r"[^\u3400-\u9fffA-Za-z0-9]", "", text))
            else:
                checks["format_matches_status"] = False
        failed = [key for key, value in checks.items() if key != "title_signal_applicable" and value is False]
        status = "FULLTEXT_FILE_PASS" if not failed else "HOLD_FULLTEXT_FILE"
        status_counts[status] += 1
        results.append({
            "material_external_id": row["material_external_id"],
            "material_title": row["material_title"],
            "fulltext_status": row["fulltext_status"],
            "local_path": row.get("local_path"),
            "expected_sha256": row.get("sha256"),
            "actual_sha256": actual_sha,
            "byte_count": byte_count,
            "visible_char_count_for_html": visible_chars,
            "checks": checks,
            "failed_checks": failed,
            "audit_status": status,
            "citation_ready": 0,
            "human_verified": 0,
        })
    report = {
        "run_id": "crosswalk_fulltext_audit_20260730",
        "input_distinct_fulltext_objects": len(rows),
        "status_counts": dict(status_counts),
        "citation_ready": 0,
        "human_verified": 0,
        "body_excerpts_persisted": False,
        "formal_db_written": False,
    }
    (OUT / "AUDIT.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
