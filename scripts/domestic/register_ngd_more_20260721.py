#!/usr/bin/env python3
"""Register 批次 J-3b: 农工党中央 ngd.org.cn + 澎湃政务 + 各党派 sub-pages。

WebFetch + WebSearch 2026-07-21 实测：

A. 农工党中央 ngd.org.cn：
1. 简介 - http://www.ngd.org.cn/gs/jj/index.htm
2. 解放前的农工党专题 - http://www.ngd.org.cn/jczt/jwklngdlsmjz/mjzjchj/32591.htm
3. 一干会议专题 - https://baike.baidu.com/item/中国农工民主党第一次全国干部会议/7553310

B. 澎湃政务号【94 年前的今天】：
- 中国农工民主党在上海成立 2024-08-09

C. 民进 / 致公 / 九三 / 台盟 各党派省委官网扫荡

等级：L2 accepted（各党派中央官方 + 澎湃政务号）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 农工党中央简介
    {
        "candidate_id": "domestic:NGD:website-jianjie-anchor",
        "title": "中国农工党中央简介（ngd.org.cn，1930-08-09 邓演达上海一干会议成立）",
        "creator": "中国农工民主党中央委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "农工党中央官方网站一手",
        "repository_code": "NGD",
        "repository_name": "中国农工民主党（ngd.org.cn）",
        "collection_name": "农工党中央简介",
        "archive_item": "http://www.ngd.org.cn/gs/jj/index.htm",
        "catalog_reference": "WebFetch 2026-07-21 实测 ngd.org.cn/gs/jj/index.htm",
        "catalog_reference_status": "verified",
        "source_url": "http://www.ngd.org.cn/gs/jj/index.htm",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "农工党中央官方公开发布；含 1930-08-09 一干会议 + 1947-02-03 农工党定名",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "农工党中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1930农工党前身成立", "1947农工党定名", "1949民盟参与政协"],
        "person_tags": ["邓演达", "黄琪翔", "章伯钧", "季方", "彭泽民", "中国农工民主党"],
        "place_tags": ["上海", "南京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测农工党中央 ngd.org.cn；"
            "中国农工民主党中央委员会官方简介；"
            "1930-08-09 上海法租界萨坡赛路 290 号（今淡水路 332 弄 1 号）一干会议成立；"
            "邓演达为主持人；章伯钧 / 黄琪翔 / 季方 / 丘哲 等 30 余人出席；"
            "通过《中国国民党临时行动委员会政治主张》；"
            "邓演达被推举为总干事；"
            "1947-02-03 改名中国农工民主党；"
            "L2 等级：农工党中央官方一手。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.ngd.org.cn/gs/jj/index.htm",
        "uncertainty_note": "L1 升级需原件。",
    },
    # 农工党解放前专题
    {
        "candidate_id": "domestic:NGD:jie-fang-qian-jiao-tuan-ji-fengyun",
        "title": "《解放前的农工党》（农工党中央 ngd.org.cn 党史专题 + 精彩画卷）",
        "creator": "中国农工民主党中央委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "农工党中央党史专题",
        "repository_code": "NGD",
        "repository_name": "中国农工民主党（ngd.org.cn）",
        "collection_name": "农工党中央党史专题 / 精彩画卷",
        "archive_item": "http://www.ngd.org.cn/jczt/jwklngdlsmjz/mjzjchj/32591.htm",
        "catalog_reference": "ngd.org.cn/jczt/jwklngdlsmjz/mjzjchj/32591.htm 解放前的农工党",
        "catalog_reference_status": "verified",
        "source_url": "http://www.ngd.org.cn/jczt/jwklngdlsmjz/mjzjchj/32591.htm",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "农工党中央官方党史专题；含 1927-1949 农工党历史",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "农工党中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1930农工党前身", "1935中华民族解放行动委员会", "1947农工党定名", "1949民盟参与政协"],
        "person_tags": ["邓演达", "黄琪翔", "章伯钧", "季方", "彭泽民", "中国农工民主党"],
        "place_tags": ["上海", "南京", "香港", "延安"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读农工党中央 ngd.org.cn 党史专题；"
            "《解放前的农工党》+《精彩画卷》系列；"
            "覆盖 1930 一干会议 + 1935 中华民族解放行动委员会 + 1947 农工党定名 + "
            "1949 参与政协；"
            "L2 等级：农工党中央官方党史。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.ngd.org.cn/jczt/jwklngdlsmjz/mjzjchj/32591.htm",
        "uncertainty_note": "L1 升级需原件。",
    },
    # 澎湃政务【94 年前的今天】农工党
    {
        "candidate_id": "domestic:PP:2024-08-09-nonggong-dang-chengli",
        "title": "澎湃【94 年前的今天】中国农工民主党在上海成立（澎湃政务号 2024-08-09）",
        "creator": "澎湃新闻政务号 + 农工党中央",
        "document_date": "2024-08-09",
        "document_date_precision": "day",
        "document_type": "澎湃政务号转载 + 农工党中央官方公众号",
        "repository_code": "PP",
        "repository_name": "澎湃新闻（thepaper.cn）",
        "collection_name": "94 年前的今天系列 + 民主党派周年纪念",
        "archive_item": "https://www.thepaper.cn/newsDetail_forward_28368220",
        "catalog_reference": "澎湃政务号 2024-08-09 发布",
        "catalog_reference_status": "verified",
        "source_url": "https://www.thepaper.cn/newsDetail_forward_28368220",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "澎湃政务号公开访问",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "澎湃政务号 + 农工党中央官方公众号",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1930农工党前身"],
        "person_tags": ["邓演达", "章伯钧", "黄琪翔", "季方", "彭泽民", "中国农工民主党"],
        "place_tags": ["上海"],
        "evidence_note": (
            "WebSearch + WebFetch 2026-07-21 核读澎湃；"
            "【94 年前的今天】中国农工民主党在上海成立；"
            "1930-08-09 邓演达等上海一干会议成立；"
            "L2 等级：澎湃政务号转载 + 农工党中央官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.thepaper.cn/newsDetail_forward_28368220",
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
                    f"L2 needs_human_review 农工党中央 + 澎湃（批次 J-3b）；"
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