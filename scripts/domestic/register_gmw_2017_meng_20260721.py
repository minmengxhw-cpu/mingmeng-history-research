#!/usr/bin/env python3
"""Register 批次 J-5b: 光明日报 2017-12-07 民盟新闻背景。

urllib 2026-07-21 实测 epaper.gmw.cn：
- 2017-12-07 光明日报第 08 版《新闻背景：中国民主同盟》
- 新华社北京 12 月 6 日电
- 民盟 1941-03-19 重庆秘密成立
- 1941-11-16 张澜公开宣布成立
- 1944-09 全国代表会议改名为中国民主同盟

等级：L2 accepted（光明日报官方 = 党报 = 官方一手）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:GMD:2017-12-07-xinwen-beijing-zhongguo-minmeng",
        "title": "《新闻背景：中国民主同盟》（光明日报 2017-12-07 第 08 版，新华社北京 12 月 6 日电）",
        "creator": "新华社 / 光明日报",
        "document_date": "2017-12-07",
        "document_date_precision": "day",
        "document_type": "光明日报官方历史报道",
        "repository_code": "GMD",
        "repository_name": "光明日报（gmw.cn）",
        "collection_name": "民主党派专题报道",
        "archive_item": "http://epaper.gmw.cn/gmrb/html/2017-12/07/nw.D110000gmrb_20171207_8-03.htm",
        "catalog_reference": (
            "光明日报 2017-12-07 第 08 版；"
            "新华社北京 12 月 6 日电；42010 字节全文"
        ),
        "catalog_reference_status": "verified",
        "source_url": "http://epaper.gmw.cn/gmrb/html/2017-12/07/nw.D110000gmrb_20171207_8-03.htm",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "光明日报 epaper 公开访问；42010 字节全文",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "光明日报 = 中共党报 = 官方一手",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大"],
        "person_tags": ["张澜", "沈钧儒", "黄炎培", "中国民主同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "urllib 2026-07-21 实测光明日报 epaper；"
            "《新闻背景：中国民主同盟》（2017-12-07 第 08 版 42010 字节）；"
            "1941-03-19 重庆秘密成立中国民主政团同盟；"
            "1941-11-16 张澜公开宣布成立；"
            "1944-09 全国代表会议改名为中国民主同盟；"
            "抗日战争和解放战争时期民盟与中共合作反帝反封建反官僚资本；"
            "L2 等级：光明日报官方 = 中共党报 = 官方一手。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://epaper.gmw.cn/gmrb/html/2017-12/07/nw.D110000gmrb_20171207_8-03.htm",
        "uncertainty_note": "L1 升级需光明日报原件。",
    },
    {
        "candidate_id": "domestic:GMD:2022-12-22-zhongguo-minmeng-baojing",
        "title": "《中国民主同盟》新闻背景报道（光明日报 2022-12-22 第 02 版，新华社 12-21 电）",
        "creator": "新华社 / 光明日报",
        "document_date": "2022-12-22",
        "document_date_precision": "day",
        "document_type": "光明日报官方历史报道",
        "repository_code": "GMD",
        "repository_name": "光明日报（gmw.cn）",
        "collection_name": "民主党派专题报道",
        "archive_item": "https://news.gmw.cn/2022-12/22/content_36249069.htm",
        "catalog_reference": (
            "光明日报 2022-12-22 第 02 版；孙宗鹤 编辑；9471 字节"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://news.gmw.cn/2022-12/22/content_36249069.htm",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "光明日报官方公开发布；已批次 H-2 注册（已有候选）",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "光明日报 = 中共党报",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟", "黄炎培", "张澜"],
        "place_tags": ["北京"],
        "evidence_note": (
            "urllib 2026-07-21 实测 9471 字节；"
            "中国民主同盟第十三届中央委员会相关报道；"
            "L2 等级：光明日报官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://news.gmw.cn/2022-12/22/content_36249069.htm",
        "uncertainty_note": "已批次 H-2 注册。",
    },
    {
        "candidate_id": "domestic:GMD:epaper-meng-1941-1949-aggregate",
        "title": "光明日报 epaper.gmw.cn 民盟 1941-1949 报道聚合（已发现 2 篇）",
        "creator": "光明日报",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "光明日报 epaper 聚合",
        "repository_code": "GMD",
        "repository_name": "光明日报 epaper（epaper.gmw.cn）",
        "collection_name": "民主党派专题报道 epaper",
        "archive_item": "http://epaper.gmw.cn/",
        "catalog_reference": "光明日报 epaper 公开访问",
        "catalog_reference_status": "verified",
        "source_url": "http://epaper.gmw.cn/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "光明日报 epaper 公开访问；含民盟历史专题报道",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "光明日报 epaper = 中共党报 = 官方一手",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "urllib 2026-07-21 实测 epaper.gmw.cn；"
            "光明日报 epaper = 中共中央宣传部直属党报；"
            "已发现 2 篇民盟专题：2017-12-07 新闻背景 + 2022-12-22 中国民主同盟；"
            "L2 等级：光明日报党报官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://epaper.gmw.cn/",
        "uncertainty_note": "L1 升级需具体原件。",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default=TODAY)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing = {r["candidate_id"] for r in rows}

    added, skipped = [], []
    for record in NEW_RECORDS:
        cid = record["candidate_id"]
        if cid in existing:
            skipped.append(cid)
            continue
        record.update(
            {
                "checked_at": args.checked_at,
                "checked_by": "claude-code",
                "review_status": "needs_human_review",
                "review_note": (
                    f"L2 needs_human_review 光明日报民盟（批次 J-5b）；"
                    f"urllib 2026-07-21 实测 epaper.gmw.cn。"
                ),
            }
        )
        rows.append(record)
        added.append(cid)

    if args.apply:
        args.jsonl.write_text(
            "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows),
            encoding="utf-8",
        )
    print(json.dumps(
        {"added": added, "skipped": skipped, "applied": args.apply,
         "total_records": len(rows), "added_count": len(added)},
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())