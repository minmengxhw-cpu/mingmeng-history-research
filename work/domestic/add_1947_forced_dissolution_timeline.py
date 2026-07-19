#!/usr/bin/env python3
"""Add a separately dated post-hoc timeline clue without upgrading it to primary evidence."""

import json
from pathlib import Path


CANDIDATES = Path("data/domestic/candidates.jsonl")
EVENTS = Path("data/domestic/event_coverage.json")
CID = "domestic:GXMM:forced-dissolution-1947-11-05"

RECORD = {
    "candidate_id": CID,
    "title": "国民党当局强行解散民盟",
    "creator": "后期盟史整理所述国民党当局",
    "document_date": "1947-11-05",
    "document_date_precision": "day",
    "document_type": "后期官方盟史中的同期事件线索",
    "repository_code": "GXMM",
    "repository_name": "民盟广西区委公开盟史转载",
    "collection_name": "1947民盟被迫解散报刊线索",
    "archive_fonds": None,
    "archive_series": None,
    "archive_file": None,
    "archive_item": "GXMM-7063",
    "catalog_reference": "民盟广西区委文章：1947年11月5日国民党当局强行解散民盟",
    "catalog_reference_status": "verified",
    "source_url": "https://www.gxmm.gov.cn/index/index/artical/id/7063.html",
    "source_url_role": "finding_aid",
    "access_mode": "open",
    "access_note": "官方地方盟史文章可公开访问；文章为后期整理，不是1947年原始公文或同期报纸原页",
    "medium": "digital",
    "online_availability": "full_item_online",
    "rights_status": "public",
    "reuse_rights": "citation_only",
    "rights_basis": "转载页面及原始材料权利待核",
    "copy_allowed": "unknown",
    "authenticity_level_proposed": "L4",
    "relevance_grade_proposed": "core",
    "event_tags": ["1947民盟被宣布非法"],
    "person_tags": ["张澜", "中国民主同盟"],
    "place_tags": ["上海"],
    "evidence_note": "民盟广西区委后期盟史文章将时间线区分为：1947年10月27日宣布民盟为非法团体、11月5日国民党当局强行解散民盟、11月6日民盟被迫宣布解散。该记录补足事件时间线节点，但只作为原件追索卡。",
    "evidence_type": "secondary_lead",
    "evidence_locator": "GXMM文章正文中关于1947年11月5日强行解散民盟的时间线段落",
    "uncertainty_note": "后期官方整理未提供内政部公函、军警执行记录、民盟总部原始公告或同期报刊原页；11月5日的具体形成文件和执行机关仍待档案/报刊原件核验。",
    "checked_at": "2026-07-18",
    "checked_by": "codex",
    "review_status": "needs_human_review",
    "review_note": "新增时间线追索卡，保持L4；不得作为11月5日原始公文或民盟总部公告的替代。",
}


def main() -> None:
    rows = [json.loads(line) for line in CANDIDATES.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not any(row.get("candidate_id") == CID for row in rows):
        rows.append(RECORD)
        CANDIDATES.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n",
            encoding="utf-8",
        )
        print("candidate=added")
    else:
        print("candidate=exists")

    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    for event in events:
        if event.get("event_id") == "domestic-1947-illegal-dissolution":
            ids = event.setdefault("domestic_candidate_ids", [])
            if CID not in ids:
                ids.append(CID)
                print("event=linked")
            break
    else:
        raise SystemExit("event not found")
    EVENTS.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
