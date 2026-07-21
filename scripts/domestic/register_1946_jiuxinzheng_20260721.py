#!/usr/bin/env python3
"""Register 批次 K-3: 1946 旧政协 / 新政协史料。

WebSearch 2026-07-21 核读：

1. 人民政协网 黄炎培的旧政协会议之路（2024-12-10）
2. 中共与民盟的一次君子协定——1946"旧政协"（搜狐网）
3. 风雨同舟共议国是（中国共产党新闻网 2024-09-30）
4. 1946年1月10日"政协会议"否定国民党独裁统治（搜狐网）

等级：L2 accepted（人民政协网 + 中国共产党新闻网 + 主流官方/学术）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:RMZXB:2024-12-10-huangyanpei-jiuxinzheng",
        "title": "《黄炎培的旧政协会议之路》（人民政协网 2024-12-10）",
        "creator": "人民政协网",
        "document_date": "2024-12-10",
        "document_date_precision": "day",
        "document_type": "人民政协网官方历史专题",
        "repository_code": "RMZXB",
        "repository_name": "人民政协网（rmzxb.com.cn）",
        "collection_name": "民盟 / 民主党派 + 1946 旧政协",
        "archive_item": "http://www.rmzxb.com.cn/c/2024-12-10/3645690.shtml",
        "catalog_reference": "人民政协网 2024-12-10 发布",
        "catalog_reference_status": "verified",
        "source_url": "http://www.rmzxb.com.cn/c/2024-12-10/3645690.shtml",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "人民政协网公开访问；含黄炎培 1946 旧政协参与史料",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "人民政协网 = 全国政协主管",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946政治协商会议"],
        "person_tags": ["黄炎培", "中国民主建国会", "中国民主同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《黄炎培的旧政协会议之路》（人民政协网 2024-12-10）；"
            "黄炎培 1946-01 出席政治协商会议（重庆）；"
            "民建创始人黄炎培 + 民盟前身；"
            "L2 等级：人民政协网官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.rmzxb.com.cn/c/2024-12-10/3645690.shtml",
        "uncertainty_note": "L1 升级需原件。",
    },
    {
        "candidate_id": "domestic:CPC:2024-09-30-fengyutongzhou-gongyi-guoshi",
        "title": "《风雨同舟 共议国是》（中国共产党新闻网 cpc.people.com.cn 2024-09-30）",
        "creator": "中国共产党新闻网",
        "document_date": "2024-09-30",
        "document_date_precision": "day",
        "document_type": "中共党史官方新闻报道（1946 旧政协）",
        "repository_code": "CPC",
        "repository_name": "中国共产党新闻网（cpc.people.com.cn）",
        "collection_name": "中共党史",
        "archive_item": "http://cpc.people.com.cn/n1/2024/0930/c443712-40331438.html",
        "catalog_reference": "中国共产党新闻网 2024-09-30 发布",
        "catalog_reference_status": "verified",
        "source_url": "http://cpc.people.com.cn/n1/2024/0930/c443712-40331438.html",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "中共党史网公开访问；含 1946 旧政协与中共合作史料",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "中国共产党新闻网 = 中共中央组织部主管",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946政治协商会议"],
        "person_tags": ["中国共产党", "中国民主同盟", "黄炎培", "张澜", "沈钧儒"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《风雨同舟 共议国是》（中共党史网 2024-09-30）；"
            "1946 旧政协与中共合作；"
            "民盟积极响应；"
            "L2 等级：中国共产党新闻网 = 中共中央组织部主管。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://cpc.people.com.cn/n1/2024/0930/c443712-40331438.html",
        "uncertainty_note": "L1 升级需原件。",
    },
    {
        "candidate_id": "domestic:SH:1946-junzi-xieding-jiuxinzheng",
        "title": "《中共与民盟的一次君子协定——1946\"旧政协\"》（搜狐网 2024）",
        "creator": "搜狐网（转学术文章）",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "搜狐网学术历史专题（转 1946 旧政协史料）",
        "repository_code": "SH",
        "repository_name": "搜狐网（sohu.com）",
        "collection_name": "民盟 + 旧政协",
        "archive_item": "https://www.sohu.com/a/800286372_122010799",
        "catalog_reference": "搜狐网 2024 转载",
        "catalog_reference_status": "verified",
        "source_url": "https://www.sohu.com/a/800286372_122010799",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "搜狐网公开访问",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "搜狐网",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946政治协商会议"],
        "person_tags": ["中国共产党", "中国民主同盟", "张澜", "黄炎培", "沈钧儒", "罗隆基", "梁漱溟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《中共与民盟的一次君子协定——1946 旧政协》（搜狐网 2024）；"
            "1946-01 旧政协期间中共与民盟合作；"
            "L2 等级：搜狐网转学术。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.sohu.com/a/800286372_122010799",
        "uncertainty_note": "L1 升级需原件。",
    },
    {
        "candidate_id": "domestic:SH:2010-01-10-zhenxie-huifu",
        "title": "《1946 年 1 月 10 日 \"政协会议\" 否定国民党独裁统治》（搜狐新闻 2010）",
        "creator": "搜狐新闻",
        "document_date": "2010-01-10",
        "document_date_precision": "day",
        "document_type": "搜狐新闻历史专题",
        "repository_code": "SH",
        "repository_name": "搜狐新闻（news.sohu.com）",
        "collection_name": "民盟 + 1946 旧政协",
        "archive_item": "https://news.sohu.com/20100110/n269474189.shtml",
        "catalog_reference": "搜狐新闻 2010-01-10 旧政协周年纪念",
        "catalog_reference_status": "verified",
        "source_url": "https://news.sohu.com/20100110/n269474189.shtml",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "搜狐新闻公开访问",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "搜狐新闻",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946政治协商会议"],
        "person_tags": ["中国民主同盟", "黄炎培", "张澜"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《1946-01-10 政协会议否定国民党独裁统治》（搜狐 2010）；"
            "L2 等级：搜狐新闻专题。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://news.sohu.com/20100110/n269474189.shtml",
        "uncertainty_note": "L1 升级需原件。",
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
                    f"L2 needs_human_review 1946 旧政协史料（批次 K-3）；"
                    f"WebSearch 2026-07-21 核读。"
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