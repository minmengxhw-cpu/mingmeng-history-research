#!/usr/bin/env python3
"""Extend the 1949 source map with already-ingested official archive routes.

The formal SQLite pages selected here already have domestic provenance, but
most have not gone through the bounded visual-review batch used for strict
citation.  The generated map therefore records them as ``navigation_only``.
It never reads page text, changes SQLite, changes source images, or promotes a
page to the citation gate.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "research_index.sqlite"
MAP_PATH = ROOT / "data" / "domestic" / "1949_new_pcc_source_map.json"
SOURCE_URL = "https://www.saac.gov.cn/daj/gqzt/index.html"
PAGE_IDS = list(range(20691, 20726)) + [20772]
MAP_EVENT_ID = "domestic-1949-new-pcc"
REVIEW_SCOPE = "archival_scan_page_identity_pending_visual_review"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_root(db_path: Path) -> Path:
    return db_path.resolve().parent.parent


def resolve_source(root: Path, raw: str) -> Path:
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
    missing_ids = [page_id for page_id in PAGE_IDS if page_id not in existing_page_ids]
    if not missing_ids:
        print(json.dumps({"status": "NOOP", "added": 0}, ensure_ascii=False))
        return 0

    source_base = source_root(DB_PATH)
    sources: list[dict[str, object]] = []
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        for page_id in missing_ids:
            row = connection.execute(
                """
                SELECT p.id AS page_id, p.page_label,
                       d.doc_key, d.title, d.date_guess,
                       pp.source_file, pp.source_sha256, pp.source_file_size,
                       pp.physical_page_no, pp.pdf_page_no
                  FROM pages p
                  JOIN documents d ON d.id=p.document_id
                  JOIN page_provenance pp ON pp.page_id=p.id
                 WHERE p.id=? AND d.source_platform='domestic'
                """,
                (page_id,),
            ).fetchone()
            if row is None:
                raise SystemExit(f"missing domestic provenance page: {page_id}")
            source_file = str(row["source_file"] or "")
            source_sha = str(row["source_sha256"] or "").lower()
            source_path = resolve_source(source_base, source_file)
            if len(source_sha) != 64 or not source_path.is_file():
                raise SystemExit(f"source file/hash unavailable for page {page_id}")
            actual_sha = sha256(source_path)
            if actual_sha != source_sha:
                raise SystemExit(
                    f"source hash mismatch for page {page_id}: expected {source_sha}, got {actual_sha}"
                )
            title = str(row["title"] or f"SAAC page {page_id}")
            physical_page = int(row["physical_page_no"] or row["pdf_page_no"] or 0)
            sources.append(
                {
                    "source_id": f"saac-1949-pcc-navigation-page-{page_id}",
                    "title": title,
                    "source_role": "official_archive_digital_scan_navigation",
                    "evidence_level": "L1",
                    "source_file": source_file,
                    "source_sha256": source_sha,
                    "source_file_size": int(row["source_file_size"] or source_path.stat().st_size),
                    "page_count": 1,
                    "source_url": SOURCE_URL,
                    "access_note": "正式库已有页级 provenance；本轮仅补专题导航，未完成本批视觉复核。",
                    "page_records": [
                        {
                            "page_id": page_id,
                            "page_label": str(row["page_label"] or ""),
                            "physical_page_no": physical_page,
                            "target": "1949新政协筹备与一届全体会议的官方档案路径",
                            "role": title,
                            "status": "navigation_only",
                            "review_status": "review_only",
                            "citation_ready": False,
                            "needs_human_review": True,
                            "review_scope": REVIEW_SCOPE,
                            "page_image_sha256": source_sha,
                            "caveat": "页面可以作为原始档案导航入口；完成本地原图视觉复核、页级人工说明后，才可能进入严格引用层。",
                        }
                    ],
                }
            )

    payload["sources"].extend(sources)
    payload["evidence_scope"] = (
        "国家档案局／中央档案馆公开专题中的已核验档案影像页，及正式库已登记但待视觉复核的导航页；"
        "只登记页级来源、哈希和引用边界"
    )
    payload["primary_evidence_gap"] = (
        "已核验17个影像页并新增36个待视觉复核导航页；1949年筹备会完整记录、代表发言、完整代表名册连续件、"
        "第一届全体会议全套档案，以及民盟代表在会中发言和互动的完整页级对位仍待补齐。"
        "本地图不把单页影像宣称为完整档案卷宗或完整名单。"
    )
    MAP_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "added": len(sources), "page_ids": missing_ids}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
