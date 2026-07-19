#!/usr/bin/env python3
"""Correct the Observer page boundary and add the independently identified page-5 article."""

import json
from pathlib import Path


CANDIDATES = Path("data/domestic/candidates.jsonl")
EVENTS = Path("data/domestic/event_coverage.json")
NEW_ID = "domestic:NLC:observer-1947-v3n11-han-depei"

NEW_RECORD = {
    "candidate_id": NEW_ID,
    "title": "人身自由的问题",
    "creator": "韩德培",
    "document_date": "1947-11-08",
    "document_date_precision": "day",
    "document_type": "同期政论周刊文章／公开原刊影像",
    "repository_code": "NLC",
    "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
    "collection_name": "民国期刊／观察",
    "archive_fonds": None,
    "archive_series": None,
    "archive_file": None,
    "archive_item": "NLC404-01J000332-6817",
    "catalog_reference": "NLC404-01J000332-6817；1947年《观察》第3卷第11期 PDF第5页",
    "catalog_reference_status": "verified",
    "source_url": "https://commons.wikimedia.org/wiki/File%3ANLC404-01J000332-6817_%E8%A7%82%E5%AF%9F_1947%E5%B9%B43%E5%8D%B711%E6%9C%9F.pdf",
    "source_url_role": "item_digital",
    "access_mode": "open",
    "access_note": "具体文件页可公开取得20页PDF；项目本地副本：data/domestic/press_scans/NLC404-01J000332-6817_观察_1947年3卷11期.pdf",
    "medium": "hybrid",
    "online_availability": "full_item_online",
    "rights_status": "unknown",
    "reuse_rights": "citation_only",
    "rights_basis": "Wikimedia页面及国家图书馆数字副本具体再利用规则待核",
    "copy_allowed": "unknown",
    "authenticity_level_proposed": "L1",
    "relevance_grade_proposed": "related",
    "event_tags": ["1947民盟被宣布非法"],
    "person_tags": ["韩德培"],
    "place_tags": ["上海", "北平"],
    "evidence_note": "逐页核读公开原刊扫描：PDF第5页转入《人身自由的问题》，页内署名为韩德培；该页与第4页董时进《我对于政府取缔民盟的感想》为不同文章，不能混作同文续页。",
    "evidence_type": "digital_image",
    "evidence_locator": "NLC404-01J000332-6817；本地PDF第5页；data/domestic/press_scans/NLC404-01J000332-6817_观察_1947年3卷11期.pdf",
    "uncertainty_note": "当前完成题名、署名和页码人工可视核验，全文逐字转录、文章主题与1947年民盟事件的具体关联仍待核读；原刊复制权利待核。",
    "checked_at": "2026-07-18",
    "checked_by": "codex",
    "review_status": "needs_human_review",
    "review_note": "新增同期原刊文章候选；已确认第5页为独立文章，待逐字转录与主题归类。",
}


def main() -> None:
    rows = [json.loads(line) for line in CANDIDATES.read_text(encoding="utf-8").splitlines() if line.strip()]
    changed = False
    for row in rows:
        if row.get("candidate_id") == "domestic:NLC:observer-1947-v3n11-dong-shijin":
            row["evidence_note"] = "逐页核读公开原刊扫描：PDF第4页刊载董时进署名的《我对于政府取缔民盟的感想》，该文在第4页结束；PDF第5页已转入韩德培《人身自由的问题》，不是董文续页。"
            row["evidence_locator"] = "NLC404-01J000332-6817；本地PDF第4页；data/domestic/press_scans/NLC404-01J000332-6817_观察_1947年3卷11期.pdf"
            row["review_note"] = "Codex于2026-07-18完成PDF第4页题名、署名和文章边界核读；已纠正此前将第5页误列为续页的问题。全文逐字转录仍待完成，L1不变。"
            changed = True
    if not any(row.get("candidate_id") == NEW_ID for row in rows):
        rows.append(NEW_RECORD)
        changed = True
        print("candidate=added")
    if not changed:
        print("candidate=already-correct")
    CANDIDATES.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )

    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    for event in events:
        if event.get("event_id") == "domestic-1947-illegal-dissolution":
            ids = event.setdefault("domestic_candidate_ids", [])
            if NEW_ID not in ids:
                ids.append(NEW_ID)
                print("event=linked")
            break
    EVENTS.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
