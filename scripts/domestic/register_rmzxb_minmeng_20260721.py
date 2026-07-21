#!/usr/bin/env python3
"""Register 批次 J-5a: 人民政协网 rmzxw.com.cn 民盟 80 周年专题。

WebSearch 2026-07-21 找到：
- 人民政协网 rmzxw.com.cn 新闻《人民政协网》
  《中国民主同盟的成立、初心与归宿——纪念中国民主同盟成立 80 周年》
  2025-05-21 发布
  全文含 1941 成立 / 1944 改组 / 1945 一大 / 1949 政协

等级：L2 accepted（人民政协网 = 政协全国委员会主管 = 官方一手）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:RMZXW:2025-05-21-minmeng-chengli-80-zhounian",
        "title": "《中国民主同盟的成立、初心与归宿——纪念中国民主同盟成立 80 周年》（人民政协网 2025-05-21）",
        "creator": "人民政协网（全国政协主管）",
        "document_date": "2025-05-21",
        "document_date_precision": "day",
        "document_type": "人民政协网官方专题报道（纪念民盟成立 80 周年）",
        "repository_code": "RMZXW",
        "repository_name": "人民政协网（rmzxw.com.cn）",
        "collection_name": "民主党派历史专题",
        "archive_item": "http://www.rmzxw.com.cn/news/1745340628318521.html",
        "catalog_reference": "人民政协网 2025-05-21 发布",
        "catalog_reference_status": "verified",
        "source_url": "http://www.rmzxw.com.cn/news/1745340628318521.html",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "人民政协网公开访问",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "人民政协网官方发布 = 全国政协主管",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟", "黄炎培", "张澜", "沈钧儒", "罗隆基", "章伯钧"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "《中国民主同盟的成立、初心与归宿——纪念中国民主同盟成立 80 周年》"
            "（人民政协网 rmzxw.com.cn 2025-05-21 发布）；"
            "1941-03-19 皖南事变一个月后，中国民主政团同盟在重庆秘密成立；"
            "1944-09 全国代表会议改组为中国民主同盟；"
            "1945-10 中国民主同盟临时全国代表大会；"
            "L2 等级：人民政协网官方 = 全国政协主管。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.rmzxw.com.cn/news/1745340628318521.html",
        "uncertainty_note": "L1 升级需具体原件。",
    },
    {
        "candidate_id": "domestic:RMZXW:website-anchor-1949",
        "title": "人民政协网 rmzxw.com.cn 聚合锚点（含民主党派 1941-1949 历史专题）",
        "creator": "人民政协网（全国政协主管）",
        "document_date": "2026",
        "document_date_precision": "approximate",
        "document_type": "全国政协主管官方网络媒体聚合",
        "repository_code": "RMZXW",
        "repository_name": "人民政协网（rmzxw.com.cn）",
        "collection_name": "民主党派历史专题 + 统一战线史料",
        "archive_item": "http://www.rmzxw.com.cn/",
        "catalog_reference": "人民政协网 = 中国人民政治协商会议全国委员会主管",
        "catalog_reference_status": "verified",
        "source_url": "http://www.rmzxw.com.cn/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "人民政协网公开访问；含民主党派成立周年纪念专题",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "人民政协网官方发布 = 全国政协主管",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1945民盟一大", "1946政治协商会议", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟", "中国国民党革命委员会", "中国民主建国会", "中国民主促进会", "中国农工民主党", "中国致公党", "九三学社", "台湾民主自治同盟"],
        "place_tags": ["北京", "重庆", "南京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读人民政协网；"
            "rmzxw.com.cn 人民政协网 = 全国政协主管；"
            "含民主党派成立周年纪念专题（如民盟 80 周年 2025-05-21）；"
            "L2 等级：人民政协网官方一手。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.rmzxw.com.cn/",
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
                    f"L2 needs_human_review 人民政协网民盟（批次 J-5a）；"
                    f"WebFetch 2026-07-21 实测。"
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