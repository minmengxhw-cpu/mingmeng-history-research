#!/usr/bin/env python3
"""Extend the 1947 dissolution map with canonical gazette navigation pages.

The four gazette issues already have canonical domestic pages and provenance
in the formal SQLite index.  This script adds only metadata-only navigation
records to the topic map.  It does not read page text, write SQLite, copy raw
files, or promote a page to strict citation status.  The source artifacts are
local research material and remain outside the Git history.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "research_index.sqlite"
MAP_PATH = ROOT / "data" / "domestic" / "1947_dissolution_source_map.json"
MAP_EVENT_ID = "domestic-1947-illegal-dissolution"
REVIEW_SCOPE = "gazette_page_identity_navigation_pending_target_document_review"

ISSUES = (
    {
        "doc_id": "ROC1947-10-27",
        "source_id": "roc-gazette-2964-1947-10-27-navigation",
        "title": "《國民政府公報》第2964號（1947年10月27日）整册页级导航",
        "target": "1947-10-27官方公报整册：政府公函负向核查与原件路径",
    },
    {
        "doc_id": "ROC1947-10-30",
        "source_id": "roc-gazette-2967-1947-10-30-navigation",
        "title": "《國民政府公報》第2967號（1947年10月30日）整册页级导航",
        "target": "1947-10-30官方公报整册：事件前后行政材料检索路径",
    },
    {
        "doc_id": "ROC1947-11-06",
        "source_id": "roc-gazette-2973-1947-11-06-navigation",
        "title": "《國民政府公報》第2973號（1947年11月6日）整册页级导航",
        "target": "1947-11-06官方公报整册：解散日期负向核查路径",
    },
    {
        "doc_id": "ROC1947-11-07",
        "source_id": "roc-gazette-2974-1947-11-07-navigation",
        "title": "《國民政府公報》第2974號（1947年11月7日）整册页级导航",
        "target": "1947-11-07官方公报整册：解散次日行政材料检索路径",
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_root(db_path: Path) -> Path:
    # The formal DB is a symlink to the local research-data checkout.  Resolve
    # it so source_file paths are checked against the data-bearing root.
    return db_path.resolve().parent.parent


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else root / path


def main() -> int:
    payload = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    if payload.get("event_id") != MAP_EVENT_ID:
        raise SystemExit("unexpected source map event_id")

    existing_page_ids = {
        int(page["page_id"])
        for source in payload.get("sources", [])
        if isinstance(source, dict)
        for page in source.get("page_records", [])
        if isinstance(page, dict) and str(page.get("page_id") or "").isdigit()
    }
    existing_source_ids = {
        str(source.get("source_id"))
        for source in payload.get("sources", [])
        if isinstance(source, dict) and source.get("source_id")
    }

    source_base = source_root(DB_PATH)
    additions: list[dict[str, object]] = []
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        for issue in ISSUES:
            if issue["source_id"] in existing_source_ids:
                continue
            rows = connection.execute(
                """
                SELECT p.id AS page_id, p.page_label,
                       d.doc_id, d.title,
                       pp.source_file, pp.source_sha256, pp.source_file_size,
                       pp.physical_page_no, pp.pdf_page_no,
                       pp.page_image_sha256
                  FROM pages p
                  JOIN documents d ON d.id=p.document_id
                  JOIN page_provenance pp ON pp.page_id=p.id
                 WHERE d.doc_id=?
                   AND d.source_platform='domestic'
                 ORDER BY pp.physical_page_no, pp.pdf_page_no, p.id
                """,
                (issue["doc_id"],),
            ).fetchall()
            if not rows:
                raise SystemExit(f"missing canonical domestic pages: {issue['doc_id']}")

            source_files = {str(row["source_file"] or "") for row in rows}
            if len(source_files) != 1 or not next(iter(source_files)):
                raise SystemExit(f"canonical source file is not unique: {issue['doc_id']}")
            source_file = next(iter(source_files))
            source_path = resolve_path(source_base, source_file)
            if not source_path.is_file():
                raise SystemExit(f"source file unavailable: {source_file}")

            source_hashes = {str(row["source_sha256"] or "").lower() for row in rows}
            if len(source_hashes) != 1 or len(next(iter(source_hashes))) != 64:
                raise SystemExit(f"source hash is not unique/valid: {issue['doc_id']}")
            source_sha = next(iter(source_hashes))
            actual_sha = sha256(source_path)
            if actual_sha != source_sha:
                raise SystemExit(
                    f"source hash mismatch for {issue['doc_id']}: expected {source_sha}, got {actual_sha}"
                )

            page_records: list[dict[str, object]] = []
            for row in rows:
                page_id = int(row["page_id"])
                if page_id in existing_page_ids:
                    continue
                physical_page = int(row["physical_page_no"] or row["pdf_page_no"] or 0)
                page_records.append(
                    {
                        "page_id": page_id,
                        "page_label": str(row["page_label"] or ""),
                        "physical_page_no": physical_page,
                        "pdf_page_no": int(row["pdf_page_no"] or physical_page),
                        "target": issue["target"],
                        "role": f"官方公报整册第{physical_page}页的本地影像导航",
                        "status": "navigation_only",
                        "review_status": "review_only",
                        "citation_ready": False,
                        "needs_human_review": True,
                        "review_scope": REVIEW_SCOPE,
                        "page_image_sha256": str(row["page_image_sha256"] or ""),
                        "caveat": (
                            "本页用于定位官方公报整册及页级影像；不证明目标政府公函或民盟总部公告存在，"
                            "也不替代目标文件原件。完成目标文件级视觉复核和来源说明后，才可能进入严格引用层。"
                        ),
                    }
                )
            if not page_records:
                continue
            additions.append(
                {
                    "source_id": issue["source_id"],
                    "title": issue["title"],
                    "source_role": "official_gazette_issue_navigation",
                    "evidence_level": "L1",
                    "source_file": source_file,
                    "source_sha256": source_sha,
                    "source_file_size": int(source_path.stat().st_size),
                    "page_count": len(rows),
                    "access_note": (
                        "正式库已有 canonical 页级 provenance；影像与 PDF 位于本地资料根，"
                        "本轮只补专题导航，不把整册或其中任一页升级为严格引用。"
                    ),
                    "page_records": page_records,
                }
            )

    payload["sources"].extend(additions)
    payload["evidence_scope"] = (
        "同期报刊页级证据、官方公报负向核查，以及正式库已登记的四期官方公报整册导航；"
        "正文原件、OCR和严格引用状态分离登记"
    )
    payload["primary_evidence_gap"] = (
        "现有同期报刊严格页级证据保留不变；新增四期官方公报共56个导航页，"
        "其中1947-10-27政府公函、1947-11-06民盟总部解散公告及其完整底本仍未完成原件闭环。"
        "导航页只提供整册和页级定位，不把负向核查误报为目标文件不存在。"
    )
    MAP_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "added_sources": len(additions),
                "added_pages": sum(len(item["page_records"]) for item in additions),
                "source_ids": [item["source_id"] for item in additions],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
