#!/usr/bin/env python3
"""Record page-level evidence for Guangming Bao 1946 issue 11."""

import json
from pathlib import Path


PATH = Path("data/domestic/candidates.jsonl")
EVENTS = Path("data/domestic/event_coverage.json")
NEW_ID = "domestic:NLC:guangmingbao-1946-issue11-anti-one-party-constitution"

NEW_RECORD = {
    "candidate_id": NEW_ID,
    "title": "反对一党独裁的宪法！",
    "creator": "《光明報》社论",
    "document_date": "1946-09-13",
    "document_date_precision": "day",
    "document_type": "同期报刊社论／公开原刊影像",
    "repository_code": "NLC",
    "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
    "collection_name": "民国期刊／光明報",
    "archive_item": "NLC404-01J000514-23806",
    "catalog_reference": "NLC404-01J000514-23806；1946年《光明報》新十一號 PDF第1、3页",
    "catalog_reference_status": "verified",
    "source_url": "https://commons.wikimedia.org/wiki/File%3ANLC404-01J000514-23806_%E5%85%89%E6%98%8E%E5%A0%B1_1946%E5%B9%B411%E6%9C%9F.pdf",
    "source_url_role": "item_digital",
    "access_mode": "open",
    "access_note": "公开20页PDF；本地副本：data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf",
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
    "place_tags": ["上海"],
    "evidence_note": "逐页核读公开原刊：PDF第1页目录列出‘反对一党独裁宪法（社论）’，PDF第3页正文首页大标题为《反对一党独裁的宪法！》。该社论是1946年国民大会与宪法争议的同期民盟机关报证据。",
    "evidence_type": "digital_image",
    "evidence_locator": "NLC404-01J000514-23806；本地PDF第1、3页；data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf",
    "uncertainty_note": "已核对题名、期号、日期、目录和正文首页；全文逐字转录、社论署名和与民盟正式声明的文本关系仍待核读，原刊复制权利待核。",
    "checked_at": "2026-07-18",
    "checked_by": "codex",
    "review_status": "needs_human_review",
    "review_note": "新增同期社论候选；已确认PDF第3页正文首页，待逐字转录并与政协决议、正式汇编和民盟发言互校。",
}

ARTICLE_RECORDS = [
    {
        "candidate_id": "domestic:NLC:guangmingbao-1946-issue11-zhang-lan-shanghai-welcome-speech",
        "title": "张澜在上海各人民团体欢迎茶会演讲词",
        "creator": "张澜",
        "document_date": "1946-09-13",
        "document_date_precision": "day",
        "document_type": "同期报刊演讲词／公开原刊影像",
        "repository_code": "NLC",
        "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
        "collection_name": "民国期刊／光明報",
        "archive_item": "NLC404-01J000514-23806",
        "catalog_reference": "NLC404-01J000514-23806；PDF第1页目录、第5页正文",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File%3ANLC404-01J000514-23806_%E5%85%89%E6%98%8E%E5%A0%B1_1946%E5%B9%B411%E6%9C%9F.pdf",
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "公开20页PDF；本地副本：data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf",
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
        "place_tags": ["上海"],
        "evidence_note": "公开原刊逐页核读：PDF第1页目录列出该演讲词，PDF第5页为对应正文页；刊物为《光明報》新十一號，版面日期为1946-09-13。",
        "evidence_type": "digital_image",
        "evidence_locator": "NLC404-01J000514-23806；本地PDF第1、5页；data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf",
        "uncertainty_note": "已确认目录题名、作者、期号、日期和正文页；全文逐字转录及与同期正式会议记录的异文关系仍待核读，原刊复制权利待核。",
        "checked_at": "2026-07-19",
        "checked_by": "codex",
        "review_status": "needs_human_review",
        "review_note": "新增同期演讲词候选；已完成目录页与正文起始页核验，待全文转录及文献互校。",
    },
    {
        "candidate_id": "domestic:NLC:guangmingbao-1946-issue11-china-at-1947-threshold",
        "title": "中国，在一九四七年的门槛上",
        "creator": "黄药眠",
        "document_date": "1946-09-13",
        "document_date_precision": "day",
        "document_type": "同期报刊文章／公开原刊影像",
        "repository_code": "NLC",
        "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
        "collection_name": "民国期刊／光明報",
        "archive_item": "NLC404-01J000514-23806",
        "catalog_reference": "NLC404-01J000514-23806；PDF第1页目录、第6—8页正文",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File%3ANLC404-01J000514-23806_%E5%85%89%E6%98%8E%E5%A0%B1_1946%E5%B9%B411%E6%9C%9F.pdf",
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "公开20页PDF；本地副本：data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf",
        "medium": "hybrid",
        "online_availability": "full_item_online",
        "rights_status": "unknown",
        "reuse_rights": "citation_only",
        "rights_basis": "Wikimedia页面及国家图书馆数字副本具体再利用规则待核",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L1",
        "relevance_grade_proposed": "related",
        "event_tags": ["1946拒绝国民大会"],
        "person_tags": ["黄药眠", "中国民主同盟"],
        "place_tags": ["中国"],
        "evidence_note": "公开原刊逐页核读：PDF第1页目录列出题名并署黄药眠，PDF第6页正文以同名大标题开始，PDF第7—8页为连续正文；刊物版面日期为1946-09-13。",
        "evidence_type": "digital_image",
        "evidence_locator": "NLC404-01J000514-23806；本地PDF第1、6—8页；data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf",
        "uncertainty_note": "已确认目录、作者、题名、期号、日期和正文连续页范围；全文逐字转录与作者文集、同期政治文件的互校仍待完成，原刊复制权利待核。",
        "checked_at": "2026-07-19",
        "checked_by": "codex",
        "review_status": "needs_human_review",
        "review_note": "新增同期政治评论候选；已完成目录和正文首篇页级核验，待全文转录及史料关系标注。",
    },
    {
        "candidate_id": "domestic:NLC:guangmingbao-1946-issue11-truman-december-18-statement",
        "title": "评杜鲁门总统十二月十八日的声明",
        "creator": "《光明報》社论",
        "document_date": "1946-09-13",
        "document_date_precision": "day",
        "document_type": "同期报刊社论／公开原刊影像",
        "repository_code": "NLC",
        "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
        "collection_name": "民国期刊／光明報",
        "archive_item": "NLC404-01J000514-23806",
        "catalog_reference": "NLC404-01J000514-23806；PDF第1页目录、第2页正文",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File%3ANLC404-01J000514-23806_%E5%85%89%E6%98%8E%E5%A0%B1_1946%E5%B9%B411%E6%9C%9F.pdf",
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "公开20页PDF；本地副本：data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf",
        "medium": "hybrid",
        "online_availability": "full_item_online",
        "rights_status": "unknown",
        "reuse_rights": "citation_only",
        "rights_basis": "Wikimedia页面及国家图书馆数字副本具体再利用规则待核",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L1",
        "relevance_grade_proposed": "related",
        "event_tags": ["1946拒绝国民大会"],
        "person_tags": ["杜鲁门", "中国民主同盟"],
        "place_tags": ["中国"],
        "evidence_note": "公开原刊逐页核读：PDF第1页目录列出该社论，PDF第2页正文页顶可核到完整题名；正文讨论政协会决议、民盟人士受压和美国对华政策。",
        "evidence_type": "digital_image",
        "evidence_locator": "NLC404-01J000514-23806；本地PDF第1—2页；data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf",
        "uncertainty_note": "已确认题名、期号、日期、目录和正文起始页；全文逐字转录、社论署名规则及与杜鲁门原声明的文本比对仍待完成，原刊复制权利待核。",
        "checked_at": "2026-07-19",
        "checked_by": "codex",
        "review_status": "needs_human_review",
        "review_note": "新增同期社论候选；已完成目录与正文首页核验，待全文转录及外部文件互校。",
    },
]


def main() -> None:
    rows = [json.loads(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    seen = False
    for row in rows:
        if row.get("candidate_id") == "domestic:NLC:guangmingbao-1946-issue11":
            row["evidence_note"] = "逐页核读公开原刊扫描：PDF第1页目录明确列出‘反对一党独裁宪法（社论）’，PDF第3页正文首页可视核到《反对一党独裁的宪法！》大标题；该期仍是1946年国大争议的同期原刊，不替代民盟正式声明。"
            row["evidence_type"] = "digital_image"
            row["evidence_locator"] = "NLC404-01J000514-23806；本地PDF第1、3页；data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf"
            row["review_note"] = "Codex于2026-07-18完成PDF第1页目录和第3页正文首页页级核读；全文逐字转录和张澜演讲页码仍待完成，L1不变。"
            seen = True
    if not any(row.get("candidate_id") == NEW_ID for row in rows):
        rows.append(NEW_RECORD)
        print("candidate=added")
    elif not seen:
        raise SystemExit("issue-level candidate missing")
    for record in ARTICLE_RECORDS:
        if not any(row.get("candidate_id") == record["candidate_id"] for row in rows):
            rows.append(record)
            print(f"article=added:{record['candidate_id']}")
    PATH.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n", encoding="utf-8")

    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    for event in events:
        if event.get("event_id") == "domestic-1946-refuse-national-assembly":
            ids = event.setdefault("domestic_candidate_ids", [])
            if NEW_ID not in ids:
                ids.append(NEW_ID)
                print("event=linked")
            for record in ARTICLE_RECORDS:
                article_id = record["candidate_id"]
                if article_id not in ids:
                    ids.append(article_id)
                    print(f"event=linked:{article_id}")
            break
    else:
        raise SystemExit("event not found")
    EVENTS.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
