#!/usr/bin/env python3
"""Review the 29 pending domestic candidates using conservative source rules."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


METADATA_ACCEPT_REPOSITORIES = {"HKU", "MM1941", "MX", "RCL", "SHDPZ"}


def decide(row: sqlite3.Row) -> tuple[str, str]:
    if (
        row["repository_code"] in METADATA_ACCEPT_REPOSITORIES
        and row["evidence_type"] in {"digital_image", "printed_finding_aid"}
        and row["catalog_reference_status"] in {"verified", "unpublished"}
    ):
        return (
            "ACCEPT_METADATA",
            "目录或本地内部汇编记录可核验；只接受元数据线索，不代表已取得原件，不提升citation_ready。",
        )
    return (
        "NEED_ORIGINAL",
        "目前只有二次线索或替代页面；在取得原刊影像、档案复制件或可核验全文前维持人工复核。",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    connection = sqlite3.connect(args.db)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """
        SELECT candidate_id,title,repository_code,repository_name,
               catalog_reference_status,access_mode,online_availability,
               evidence_type,authenticity_level_proposed,
               relevance_grade_proposed,review_status
        FROM domestic_candidates
        WHERE review_status='needs_human_review'
        ORDER BY candidate_id
        """
    ).fetchall()
    decisions = []
    for row in rows:
        outcome, reason = decide(row)
        decisions.append(
            {
                **dict(row),
                "decision": outcome,
                "decision_reason": reason,
                "citation_ready": False,
            }
        )

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(decisions[0]))
        writer.writeheader()
        writer.writerows(decisions)
    args.json.write_text(
        json.dumps(decisions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    backup = None
    applied = 0
    if args.apply:
        backup = args.db.with_name(
            f"{args.db.name}.candidate_review_20260728."
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pre.bak"
        )
        shutil.copy2(args.db, backup)
        for decision in decisions:
            if decision["decision"] != "ACCEPT_METADATA":
                continue
            note = (
                "2026-07-28 Codex复核：ACCEPT_METADATA。"
                + decision["decision_reason"]
            )
            cursor = connection.execute(
                """
                UPDATE domestic_candidates
                SET review_status='accepted',
                    review_note=?,
                    reviewed_at=?,
                    reviewed_by='codex',
                    check_outcome='pass',
                    authenticity_level_accepted=?,
                    relevance_grade_accepted=?
                WHERE candidate_id=? AND review_status='needs_human_review'
                """,
                (
                    note,
                    datetime.now().isoformat(timespec="seconds"),
                    decision["authenticity_level_proposed"],
                    decision["relevance_grade_proposed"],
                    decision["candidate_id"],
                ),
            )
            applied += max(cursor.rowcount, 0)
        connection.commit()

    counts = {
        row[0]: row[1]
        for row in connection.execute(
            """
            SELECT review_status,COUNT(*)
            FROM domestic_candidates
            GROUP BY review_status
            """
        )
    }
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    connection.close()
    print(
        json.dumps(
            {
                "reviewed": len(decisions),
                "accept_metadata": sum(
                    d["decision"] == "ACCEPT_METADATA" for d in decisions
                ),
                "need_original": sum(
                    d["decision"] == "NEED_ORIGINAL" for d in decisions
                ),
                "applied": applied if args.apply else 0,
                "backup": str(backup) if backup else None,
                "review_status_counts": counts,
                "integrity_check": integrity,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
