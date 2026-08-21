#!/usr/bin/env python3
"""Build a read-only content-layer and storage-disposition audit.

The audit deliberately reads metadata only.  It counts documents and pages
without selecting page bodies, reads candidate/editorial states, and inspects
the tracked academic metadata snapshot.  It does not write the formal SQLite
database, change citation states, copy source paths, or delete local files.

This is the Phase 0 companion to the domestic/foreign parity report: parity
answers whether a researcher can enter a usable path, while this report
answers what each local asset is allowed to do in that path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data/research_index.sqlite"
DEFAULT_ACADEMIC = ROOT / "data/domestic/academic_layer_metadata.json"


# These are storage/search roles, not historical evidence grades.  In
# particular, an OCR row is never promoted to a primary-source claim here.
LAYER_RULES: dict[str, dict[str, Any]] = {
    "DOMESTIC_SEARCH_LAYER": {
        "label": "国内正式检索层",
        "source_types": [
            "domestic_page_ocr",
            "domestic_sourcebook_ocr",
            "domestic_public_scan",
            "domestic_conference_journal",
            "domestic_official_media",
            "domestic_ocr_review",
        ],
        "use": "可进入国内检索和研究包；证据等级仍由页级门禁决定。",
    },
    "DOMESTIC_OCR_STAGING": {
        "label": "国内 OCR/试验派生层",
        "source_types": ["domestic_ocr_pilot"],
        "use": "只作定位和质量复核，不单独关闭一手证据缺口。",
    },
    "DOMESTIC_NAVIGATION_LAYER": {
        "label": "国内网页与转录导航层",
        "source_types": ["domestic_public_web", "domestic_public_transcription"],
        "use": "用于发现、背景和版本对读；不因可访问而变成原件。",
    },
    "DOMESTIC_ACADEMIC_LAYER": {
        "label": "国内学术解释层",
        "source_types": ["domestic_academic_fulltext"],
        "use": "用于解释、争议和原件线索；不替代同期一手材料。",
    },
    "FOREIGN_RESEARCH_LAYER": {
        "label": "海外研究层",
        "source_types": [
            "frus_epub",
            "drnh",
            "wilson",
            "cia",
            "newspapersg",
            "hathi_ia",
            "hoover",
        ],
        "use": "按海外平台既有研究路径提供对读和引用入口。",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
    )


def _counter_rows(rows: list[tuple[Any, Any]]) -> dict[str, int]:
    return {
        str(key or "unknown"): int(value or 0)
        for key, value in sorted(rows, key=lambda item: str(item[0] or "unknown"))
    }


def _formal_snapshot(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        return {"exists": False, "errors": [f"missing database: {db_path}"]}

    with sqlite3.connect(db_path) as conn:
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        foreign_keys = int(
            conn.execute("PRAGMA foreign_key_check").fetchall().__len__()
        )
        source_type_rows = conn.execute(
            """
            SELECT s.source_type, COUNT(DISTINCT d.id), COUNT(p.id)
            FROM sources AS s
            LEFT JOIN documents AS d ON d.source_id = s.id
            LEFT JOIN pages AS p ON p.document_id = d.id
            GROUP BY s.source_type
            ORDER BY s.source_type
            """
        ).fetchall()
        source_type_counts = {
            str(source_type or "unknown"): {
                "documents": int(documents or 0),
                "pages": int(pages or 0),
            }
            for source_type, documents, pages in source_type_rows
        }
        domestic_source_type_rows = conn.execute(
            """
            SELECT s.source_type, COUNT(DISTINCT d.id), COUNT(p.id)
            FROM sources AS s
            LEFT JOIN documents AS d ON d.source_id = s.id
            LEFT JOIN pages AS p ON p.document_id = d.id
            WHERE COALESCE(d.source_platform, '') = 'domestic'
            GROUP BY s.source_type
            ORDER BY s.source_type
            """
        ).fetchall()
        domestic_totals = conn.execute(
            """
            SELECT COUNT(DISTINCT d.id), COUNT(p.id)
            FROM documents AS d
            LEFT JOIN pages AS p ON p.document_id = d.id
            WHERE COALESCE(d.source_platform, '') = 'domestic'
            """
        ).fetchone()
        all_totals = conn.execute(
            """
            SELECT COUNT(DISTINCT d.id), COUNT(p.id)
            FROM documents AS d
            LEFT JOIN pages AS p ON p.document_id = d.id
            """
        ).fetchone()
        candidate_status = {}
        candidate_total = 0
        candidate_ingested = 0
        if _table_exists(conn, "domestic_candidates"):
            candidate_status = _counter_rows(
                conn.execute(
                    "SELECT review_status, COUNT(*) FROM domestic_candidates GROUP BY review_status"
                ).fetchall()
            )
            candidate_total = int(
                conn.execute("SELECT COUNT(*) FROM domestic_candidates").fetchone()[0]
            )
            candidate_ingested = int(
                conn.execute(
                    "SELECT COUNT(*) FROM domestic_candidates WHERE ingested_document_id IS NOT NULL"
                ).fetchone()[0]
            )
        editorial_decisions = {}
        if _table_exists(conn, "domestic_editorial_decisions"):
            editorial_decisions = _counter_rows(
                conn.execute(
                    "SELECT decision, COUNT(*) FROM domestic_editorial_decisions GROUP BY decision"
                ).fetchall()
            )
        registry_count = 0
        registry_status = {}
        if _table_exists(conn, "domestic_sources"):
            registry_count = int(
                conn.execute("SELECT COUNT(*) FROM domestic_sources").fetchone()[0]
            )
            registry_status = _counter_rows(
                conn.execute(
                    "SELECT status, COUNT(*) FROM domestic_sources GROUP BY status"
                ).fetchall()
            )

    return {
        "exists": True,
        "path": str(db_path),
        "sha256": _sha256(db_path),
        "integrity_check": integrity,
        "foreign_key_violation_count": foreign_keys,
        "all_documents": int(all_totals[0] or 0),
        "all_pages": int(all_totals[1] or 0),
        "domestic_documents": int(domestic_totals[0] or 0),
        "domestic_pages": int(domestic_totals[1] or 0),
        "source_type_counts": source_type_counts,
        "domestic_source_type_counts": {
            str(source_type or "unknown"): {
                "documents": int(documents or 0),
                "pages": int(pages or 0),
            }
            for source_type, documents, pages in domestic_source_type_rows
        },
        "candidate_total": candidate_total,
        "candidate_ingested_document_count": candidate_ingested,
        "candidate_review_status_counts": candidate_status,
        "editorial_decision_counts": editorial_decisions,
        "source_registry_count": registry_count,
        "source_registry_status_counts": registry_status,
    }


def _academic_snapshot(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "errors": [f"missing academic snapshot: {path}"]}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"exists": False, "errors": [f"invalid academic snapshot: {exc}"]}
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        return {"exists": False, "errors": ["academic snapshot records is not a list"]}
    tiers = Counter()
    fulltext = Counter()
    roles = Counter()
    citation_ready = 0
    body_read = bool(payload.get("body_read"))
    for record in records:
        if not isinstance(record, dict):
            continue
        tiers[str(record.get("quality_tier") or "UNCLASSIFIED")] += 1
        fulltext[str(record.get("fulltext_status") or "UNCLASSIFIED")] += 1
        roles[str(record.get("record_role") or "UNCLASSIFIED")] += 1
        citation_ready += int(bool(record.get("citation_ready")))
    return {
        "exists": True,
        "path": str(path),
        "sha256": _sha256(path),
        "records": len(records),
        "quality_tier_counts": dict(sorted(tiers.items())),
        "fulltext_status_counts": dict(sorted(fulltext.items())),
        "record_role_counts": dict(sorted(roles.items())),
        "citation_ready_count": citation_ready,
        "body_read": body_read,
        "formal_db_written": bool(payload.get("formal_db_written")),
        "local_paths_included": bool(payload.get("local_paths_included")),
    }


def _layer_rows(source_type_counts: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    assigned: set[str] = set()
    rows: list[dict[str, Any]] = []
    for code, rule in LAYER_RULES.items():
        source_types = list(rule["source_types"])
        documents = sum(source_type_counts.get(item, {}).get("documents", 0) for item in source_types)
        pages = sum(source_type_counts.get(item, {}).get("pages", 0) for item in source_types)
        assigned.update(source_types)
        rows.append(
            {
                "code": code,
                "label": rule["label"],
                "source_types": source_types,
                "documents": documents,
                "pages": pages,
                "use": rule["use"],
            }
        )
    unknown = sorted(set(source_type_counts) - assigned)
    if unknown:
        rows.append(
            {
                "code": "UNMAPPED_SOURCE_TYPES",
                "label": "未映射来源类型",
                "source_types": unknown,
                "documents": sum(source_type_counts[item]["documents"] for item in unknown),
                "pages": sum(source_type_counts[item]["pages"] for item in unknown),
                "use": "必须先补来源角色，不进入自动证据升级。",
            }
        )
    return rows


def build_report(
    db_path: Path = DEFAULT_DB,
    academic_path: Path = DEFAULT_ACADEMIC,
) -> dict[str, Any]:
    formal = _formal_snapshot(db_path)
    academic = _academic_snapshot(academic_path)
    errors = [*formal.get("errors", []), *academic.get("errors", [])]
    layers = _layer_rows(formal.get("source_type_counts", {}))
    formal_ok = formal.get("integrity_check") == "ok" and formal.get("foreign_key_violation_count") == 0
    status = "PASS" if formal_ok and not errors else "FAIL"
    return {
        "schema_version": "domestic_content_tier_audit.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "metadata_only_formal_db_candidates_academic_snapshot",
        "status": status,
        "body_read": False,
        "page_bodies_read": False,
        "formal_db_written": False,
        "auto_delete": False,
        "auto_promote_citation_ready": False,
        "errors": errors,
        "formal_db": formal,
        "layers": layers,
        "academic_snapshot": academic,
        "next_actions": [
            "优先处理 UNMAPPED_SOURCE_TYPES；未补来源角色前不自动升级证据状态。",
            "对 DOMESTIC_OCR_STAGING 做定向视觉复核，不整本重复 OCR。",
            "对 DOMESTIC_NAVIGATION_LAYER 只保留导航和版本对读作用。",
            "同 SHA 或同文版本只建立关系，不自动删除本地副本。",
        ],
        "interpretation": {
            "layers": "层级是资料在平台中的工作角色，不等同于历史证据等级。",
            "domestic_search": "进入正式检索层不代表已关闭对应事件的一手原件缺口。",
            "academic": "学术层是解释和线索层；citation_ready=0 或 body_read=false 时不能生成正式引文。",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--academic", type=Path, default=DEFAULT_ACADEMIC)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.db, args.academic)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "layers": len(report["layers"]),
                "unmapped_source_types": next(
                    (len(row["source_types"]) for row in report["layers"] if row["code"] == "UNMAPPED_SOURCE_TYPES"),
                    0,
                ),
                "domestic_documents": report["formal_db"].get("domestic_documents", 0),
                "academic_records": report["academic_snapshot"].get("records", 0),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
