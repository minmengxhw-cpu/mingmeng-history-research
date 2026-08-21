#!/usr/bin/env python3
"""Audit the domestic academic-material layer without reading source bodies.

Only bibliographic metadata is selected from the staging database.  The report
is intentionally an acceptance aid: it measures tiering, completeness,
duplicates and citation gates, but never upgrades a record or copies a body.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
DEFAULT_POLICY = ROOT / "data/domestic/academic_source_policy.json"
DEFAULT_SNAPSHOT = ROOT / "data/domestic/academic_layer_snapshot.json"

INSTITUTION_SIGNALS = {
    "中国社会科学院": "cassi_or_research_institute_signal",
    "北京大学": "985_or_c9_signal",
    "清华大学": "985_or_c9_signal",
    "复旦大学": "985_or_c9_signal",
    "上海交通大学": "985_or_c9_signal",
    "浙江大学": "985_or_c9_signal",
    "南京大学": "985_or_c9_signal",
    "武汉大学": "985_or_c9_signal",
    "中山大学": "985_or_c9_signal",
    "南开大学": "985_or_c9_signal",
    "四川大学": "985_or_c9_signal",
    "中国人民大学": "985_or_c9_signal",
    "华东师范大学": "985_or_c9_signal",
    "首都师范大学": "recognized_university_signal",
    "香港中文大学": "recognized_university_signal",
    "中国民主同盟中央": "central_league_signal",
    "民盟中央": "central_league_signal",
    "中央文献研究室": "central_document_signal",
}


def normalize_title(value: str) -> str:
    return re.sub(r"[\s\W_]+", "", value or "", flags=re.UNICODE).lower()


def open_readonly(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def audit_snapshot(snapshot_path: Path, db_path: Path, policy_path: Path) -> dict:
    """Replay the tracked metadata snapshot when staging SQLite is absent.

    A clean checkout intentionally does not carry the private staging database.
    The snapshot is sufficient for aggregate acceptance metrics, but it cannot
    support per-record duplicate or institution checks, so that limitation is
    made explicit in the report.
    """
    base = {
        "db_path": str(db_path),
        "policy_path": str(policy_path),
        "snapshot_path": str(snapshot_path),
        "body_read": False,
        "formal_db_written": False,
        "snapshot_only": True,
        "source": "tracked_metadata_snapshot",
        "audit_mode": "metadata_snapshot_replay",
        "integrity_check": "not_run_snapshot_only",
        "status": "BLOCKED",
        "warnings": [],
    }
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        base["reason"] = f"tracked academic snapshot unreadable: {exc}"
        return base
    if not isinstance(snapshot, dict):
        base["reason"] = "tracked academic snapshot is not an object"
        return base
    if snapshot.get("status") != "PASS" or snapshot.get("body_read") is not False:
        base["reason"] = "tracked academic snapshot is not a PASS/body_read=false snapshot"
        return base

    duplicate_audit = snapshot.get("duplicate_audit")
    if not isinstance(duplicate_audit, dict):
        duplicate_audit = {}
    warnings = list(snapshot.get("warnings") or [])
    warnings.extend(
        [
            "staging SQLite is absent; only tracked aggregate metadata was replayed",
            "per-record duplicate, institution and integrity checks require the private staging database",
            "citation_ready and human_verified remain zero in the snapshot and do not upgrade formal evidence",
        ]
    )
    base.update(
        {
            "status": "PASS",
            "records": int(snapshot.get("records") or 0),
            "academic_records": int(snapshot.get("academic_records") or 0),
            "high_priority_academic_records_S_or_A": int(snapshot.get("high_priority") or 0),
            "scholarly_articles": int(snapshot.get("articles") or 0),
            "citation_ready": int(snapshot.get("citation_ready") or 0),
            "human_verified": int(snapshot.get("human_verified") or 0),
            "quality_tiers": snapshot.get("quality_tiers") or {},
            "fulltext_statuses": snapshot.get("fulltext_statuses") or {},
            "fulltext_readiness": snapshot.get("fulltext_readiness") or {},
            "metadata_missing_counts": snapshot.get("metadata_missing") or {},
            "duplicate_audit": duplicate_audit,
            "warnings": warnings,
        }
    )
    return base


def audit(db_path: Path, policy_path: Path, snapshot_path: Path = DEFAULT_SNAPSHOT) -> dict:
    report: dict = {
        "db_path": str(db_path),
        "policy_path": str(policy_path),
        "body_read": False,
        "status": "PASS",
        "warnings": [],
    }
    if not db_path.is_file():
        return audit_snapshot(snapshot_path, db_path, policy_path)
    if not policy_path.is_file():
        report["warnings"].append("academic source policy file missing")
    try:
        c = open_readonly(db_path)
        c.row_factory = sqlite3.Row
        exists = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='domestic_research_materials'"
        ).fetchone()
        if not exists:
            report.update({"status": "BLOCKED", "reason": "domestic_research_materials table missing"})
            c.close()
            return report
        rows = c.execute(
            """SELECT external_id, layer, title, author, institution,
                      publication_date, research_type, quality_tier,
                      source_url, local_path, sha256, fulltext_status,
                      review_status, citation_ready, human_verified
               FROM domestic_research_materials
               ORDER BY quality_tier, publication_date, external_id"""
        ).fetchall()
        integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
        c.close()
    except sqlite3.Error as exc:
        report.update({"status": "BLOCKED", "reason": f"sqlite read failed: {exc}"})
        return report

    tiers = collections.Counter(str(row["quality_tier"] or "UNSET") for row in rows)
    types = collections.Counter(str(row["research_type"] or "UNSET") for row in rows)
    fulltext = collections.Counter(str(row["fulltext_status"] or "UNSET") for row in rows)
    review = collections.Counter(str(row["review_status"] or "UNSET") for row in rows)
    layers = collections.Counter(str(row["layer"] or "UNSET") for row in rows)
    institutions = collections.Counter(str(row["institution"] or "未标注").strip() for row in rows)
    title_groups: dict[str, list[str]] = collections.defaultdict(list)
    signal_counts = collections.Counter()
    signal_examples: dict[str, list[str]] = collections.defaultdict(list)
    missing = collections.Counter()
    for row in rows:
        title = str(row["title"] or "").strip()
        key = normalize_title(title)
        if key:
            title_groups[key].append(str(row["external_id"]))
        institution = str(row["institution"] or "")
        for needle, signal in INSTITUTION_SIGNALS.items():
            if needle in institution:
                signal_counts[signal] += 1
                if len(signal_examples[signal]) < 5:
                    signal_examples[signal].append(str(row["external_id"]))
        for field in ("title", "author", "institution", "publication_date", "source_url"):
            if not str(row[field] or "").strip():
                missing[field] += 1

    duplicate_groups = [ids for ids in title_groups.values() if len(ids) > 1]
    academic_rows = [row for row in rows if row["layer"] == "SCHOLARLY_RESEARCH"]
    high_priority = [row for row in academic_rows if row["quality_tier"] in {"S", "A"}]
    report.update(
        {
            "integrity_check": integrity,
            "records": len(rows),
            "academic_records": len(academic_rows),
            "high_priority_academic_records_S_or_A": len(high_priority),
            "scholarly_articles": sum(1 for row in academic_rows if row["research_type"] == "SCHOLARLY_ARTICLE"),
            "citation_ready": sum(int(row["citation_ready"] or 0) for row in rows),
            "human_verified": sum(int(row["human_verified"] or 0) for row in rows),
            "quality_tiers": dict(sorted(tiers.items())),
            "research_types": dict(types.most_common()),
            "fulltext_statuses": dict(fulltext.most_common()),
            "review_statuses": dict(review.most_common()),
            "layers": dict(layers.most_common()),
            "top_institutions": [
                {"institution": name, "records": count}
                for name, count in institutions.most_common(20)
            ],
            "institution_signals": dict(signal_counts),
            "institution_signal_examples": dict(signal_examples),
            "metadata_missing_counts": dict(missing),
            "exact_normalized_title_duplicate_groups": len(duplicate_groups),
            "exact_normalized_title_duplicate_records": sum(len(ids) for ids in duplicate_groups),
            "source": "staging_sqlite",
            "audit_mode": "per_record_metadata",
            "snapshot_only": False,
            "formal_db_written": False,
            "warnings": [
                "institution signals are metadata matches, not an independent 985 or author-appointment verification",
                "citation_ready and human_verified are staging fields; they do not upgrade the formal research_index.sqlite gate",
            ],
        }
    )
    if integrity != "ok":
        report["status"] = "FAIL"
        report["warnings"].append("staging PRAGMA integrity_check is not ok")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.db, args.policy, args.snapshot)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"PASS", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
