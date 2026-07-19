#!/usr/bin/env python3
"""Record page-level evidence for Guangming Bao 1946 issue 8."""

import json
from pathlib import Path


PATH = Path("data/domestic/candidates.jsonl")
EVENTS = Path("data/domestic/event_coverage.json")
NEW_ID = "domestic:NLC:guangmingbao-1946-issue8-conditional-national-assembly"

NEW_RECORD = {
    "candidate_id": NEW_ID,
    "title": "论有条件参加国大",
    "creator": "《光明報》社论",
    "document_date": "1946-08",
    "document_date_precision": "month",
    "document_type": "同期报刊社论／公开原刊影像",
    "repository_code": "NLC",
    "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
    "collection_name": "民国期刊／光明報",
    "archive_item": "NLC404-01J000514-10429",
    "catalog_reference": "NLC404-01J000514-10429；1946年《光明報》新八號 PDF第1页",
    "catalog_reference_status": "verified",
    "source_url": "https://commons.wikimedia.org/wiki/File%3ANLC404-01J000514-10429_%E5%85%89%E6%98%8E%E5%A0%B1_1946%E5%B9%B48%E6%9C%9F.pdf",
    "source_url_role": "item_digital",
    "access_mode": "open",
    "access_note": "公开16页PDF；本地副本：data/domestic/press_scans/NLC404-01J000514-10429_光明報_1946年8期.pdf",
    "medium": "hybrid",
    "online_availability": "full_item_online",
    "rights_status": "unknown",
    "reuse_rights": "citation_only",
    "rights_basis": "Wikimedia页面及国家图书馆数字副本具体再利用规则待核",
    "copy_allowed": "unknown",
    "authenticity_level_proposed": "L1",
    "relevance_grade_proposed": "core",
    "event_tags": ["1946拒绝国民大会"],
    "person_tags": ["张澜", "中国民主同盟"],
    "place_tags": [],
    "evidence_note": "逐页核读公开原刊：PDF第1页为《光明報》新八號封面/首版，中央大标题为《论有条件参加国大》，同页可见民盟机关报报头和1946年8期标识；这是拒绝参加国大争议的同期原刊社论证据。",
    "evidence_type": "digital_image",
    "evidence_locator": "NLC404-01J000514-10429；本地PDF第1页；data/domestic/press_scans/NLC404-01J000514-10429_光明報_1946年8期.pdf",
    "uncertainty_note": "公开元数据只给出1946年8期，未给出公历日；已核对题名和首版版面，全文逐字转录、具体出版日和社论署名仍待核读，原刊复制权利待核。",
    "checked_at": "2026-07-18",
    "checked_by": "codex",
    "review_status": "needs_human_review",
    "review_note": "新增同期社论候选；已确认PDF第1页大标题，待逐字转录并与正式汇编、政协决议和民盟立场文件互校。",
}


def main() -> None:
    rows = [json.loads(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    for row in rows:
        if row.get("candidate_id") == "domestic:NLC:guangmingbao-1946-issue8":
            row["evidence_note"] = "逐页核读公开原刊扫描：PDF第1页为《光明報》新八號首版，中央大标题可视核到《论有条件参加国大》；同页可辨识民盟机关报报头和1946年8期标识。"
            row["evidence_type"] = "digital_image"
            row["evidence_locator"] = "NLC404-01J000514-10429；本地PDF第1页；data/domestic/press_scans/NLC404-01J000514-10429_光明報_1946年8期.pdf"
            row["review_note"] = "Codex于2026-07-18完成PDF第1页期号、报头和社论标题页级核读；全文逐字转录和公历出版日仍待完成，L1不变。"
            break
    else:
        raise SystemExit("issue-level candidate missing")
    if not any(row.get("candidate_id") == NEW_ID for row in rows):
        rows.append(NEW_RECORD)
        print("candidate=added")
    PATH.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n", encoding="utf-8")
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    for event in events:
        if event.get("event_id") == "domestic-1946-refuse-national-assembly":
            ids = event.setdefault("domestic_candidate_ids", [])
            if NEW_ID not in ids:
                ids.append(NEW_ID)
                print("event=linked")
            break
    else:
        raise SystemExit("event not found")
    EVENTS.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
