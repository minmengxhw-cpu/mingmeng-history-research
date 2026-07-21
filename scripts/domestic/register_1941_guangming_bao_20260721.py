#!/usr/bin/env python3
"""Register 批次 K-1: 1941 香港光明报（民盟机关报）3 篇史料。

WebSearch 2026-07-21 核读：

1. 人民政协网 "吃'百家饭'的《光明报》" 2015-04-09
   - http://www.rmzxb.com.cn/c/2015-04-09/479732.shtml

2. 财新网 "梁漱溟与俞颂华共办《光明报》纪念" 2023-10-18
   - https://mini.caixin.com/m/2023-10-18/102117719.html

3. 人民网党史频道 "梁漱溟在香港出版民盟机关刊物《光明报》" 2013-01-24
   - http://dangshi.people.com.cn/n/2013/0124/c85037-20316609.html

核心信息：
- 1941-09-18 香港《光明报》创刊
- 社长：梁漱溟；总编辑：俞颂华
- 1941-10-10 刊登《中国民主政团同盟成立宣言》+ 十大纲领
- 1941-12 太平洋战争爆发后停刊
- 1946-08 + 1948-03 两度复刊
- 中共（周恩来 / 八路军驻港办事处 / 范长江 4000 港币）支持

等级：L2 accepted（人民政协网 + 财新 + 人民网党史）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:RMZXB:2015-04-09-guangming-bao-chibaijiafan",
        "title": "《吃\"百家饭\"的《光明报》》（人民政协网 rmzxb.com.cn 2015-04-09）",
        "creator": "人民政协网",
        "document_date": "2015-04-09",
        "document_date_precision": "day",
        "document_type": "人民政协网官方历史专题报道",
        "repository_code": "RMZXB",
        "repository_name": "人民政协网（rmzxb.com.cn）",
        "collection_name": "民盟 1941 历史专题",
        "archive_item": "http://www.rmzxb.com.cn/c/2015-04-09/479732.shtml",
        "catalog_reference": "人民政协网 2015-04-09 发布",
        "catalog_reference_status": "verified",
        "source_url": "http://www.rmzxb.com.cn/c/2015-04-09/479732.shtml",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "人民政协网公开访问；含 1941 香港光明报创刊史料",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "人民政协网 = 全国政协主管",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["梁漱溟", "俞颂华", "萨空了", "周恩来", "范长江", "李济深", "中国民主政团同盟"],
        "place_tags": ["香港"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《吃\"百家饭\"的《光明报》》（人民政协网 2015-04-09）；"
            "1941-09-18 香港《光明报》创刊；"
            "1941-10-10 刊登中国民主政团同盟成立宣言 + 十大纲领；"
            "L2 等级：人民政协网官方 = 全国政协主管。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.rmzxb.com.cn/c/2015-04-09/479732.shtml",
        "uncertainty_note": "L1 升级需原件报纸影像。",
    },
    {
        "candidate_id": "domestic:CAIXIN:2023-10-18-liangshuming-yushenghua-guangmingbao",
        "title": "《梁漱溟与俞颂华共办《光明报》纪念》（财新网 2023-10-18）",
        "creator": "财新网",
        "document_date": "2023-10-18",
        "document_date_precision": "day",
        "document_type": "财新网学术历史专题报道",
        "repository_code": "CAIXIN",
        "repository_name": "财新网（caixin.com）",
        "collection_name": "民盟 1941 历史专题",
        "archive_item": "https://mini.caixin.com/m/2023-10-18/102117719.html",
        "catalog_reference": "财新网 2023-10-18 mini 移动版",
        "catalog_reference_status": "verified",
        "source_url": "https://mini.caixin.com/m/2023-10-18/102117719.html",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "财新网公开访问",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "财新网",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["梁漱溟", "俞颂华", "中国民主政团同盟"],
        "place_tags": ["香港"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《梁漱溟与俞颂华共办《光明报》纪念》（财新网 2023-10-18）；"
            "梁漱溟 1941-03-29 离渝赴香港筹办民盟机关报《光明报》；"
            "1941-09-18 创刊；"
            "L2 等级：财新网学术专题。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://mini.caixin.com/m/2023-10-18/102117719.html",
        "uncertainty_note": "L1 升级需原件。",
    },
    {
        "candidate_id": "domestic:RMTZ:2013-01-24-liangshuming-xianggang-guangmingbao",
        "title": "《梁漱溟在香港出版民盟机关刊物《光明报》》（人民网党史频道 2013-01-24）",
        "creator": "人民网党史频道",
        "document_date": "2013-01-24",
        "document_date_precision": "day",
        "document_type": "人民网党史频道官方历史专题报道",
        "repository_code": "RMTZ",
        "repository_name": "人民网党史频道（dangshi.people.com.cn）",
        "collection_name": "民盟 1941 历史专题",
        "archive_item": "http://dangshi.people.com.cn/n/2013/0124/c85037-20316609.html",
        "catalog_reference": "人民网党史频道 2013-01-24 发布",
        "catalog_reference_status": "verified",
        "source_url": "http://dangshi.people.com.cn/n/2013/0124/c85037-20316609.html",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "人民网党史频道公开访问",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "人民网党史频道官方",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["梁漱溟", "中国民主政团同盟"],
        "place_tags": ["香港"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《梁漱溟在香港出版民盟机关刊物《光明报》》（人民网党史频道 2013-01-24）；"
            "L2 等级：人民网党史频道官方 = 中共党媒党史。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://dangshi.people.com.cn/n/2013/0124/c85037-20316609.html",
        "uncertainty_note": "L1 升级需原件报纸影像。",
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
                    f"L2 needs_human_review 1941 光明报（批次 K-1）；"
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