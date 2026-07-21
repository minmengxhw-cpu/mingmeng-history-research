#!/usr/bin/env python3
"""Register 批次 K-2: 中央社会主义学院 zysy.org.cn 聚合锚点 + 中国社会科学院 cssn.cn 民主党派相关。

urllib 2026-07-21 实测 zysy.org.cn 主站（44779 字节）：
- 中央社会主义学院 = 1956 成立（院庆 70 周年）
- 含民主党派中常会 / 各民主党派中央相关活动
- 含统一战线学论坛

cssn.cn 中国史栏目：
- 民主党派相关文章
- 延安时期等历史研究

等级：L2 accepted（中央社会主义学院 = 中共中央直属事业单位；社科院 = 国家级学术机构）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:ZSY:website-anchor-1941-1949",
        "title": "中央社会主义学院 / 中华文化学院官网（zysy.org.cn，1956 成立，含民主党派研究）",
        "creator": "中央社会主义学院",
        "document_date": "2026",
        "document_date_precision": "approximate",
        "document_type": "中央社会主义学院（中共中央直属事业单位）官方",
        "repository_code": "ZSY",
        "repository_name": "中央社会主义学院 / 中华文化学院（zysy.org.cn）",
        "collection_name": "民主党派研究 + 统一战线研究",
        "archive_item": "https://www.zysy.org.cn/",
        "catalog_reference": "中央社会主义学院 = 1956-10 成立；中共中央直属事业单位",
        "catalog_reference_status": "verified",
        "source_url": "https://www.zysy.org.cn/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "中央社会主义学院官方公开发布；44779 字节主站；含民主党派研究专题",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "中央社会主义学院官方",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["中央社会主义学院", "民主党派", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "urllib 2026-07-21 实测 zysy.org.cn 44779 字节；"
            "中央社会主义学院主站含民主党派专区；"
            "院庆 70 周年（1956-2026）；"
            "民主党派中常会下半年工作部署；"
            "统一战线高端智库；"
            "L2 等级：中央社会主义学院 = 中共中央直属事业单位。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.zysy.org.cn/",
        "uncertainty_note": "L1 升级需具体民主党派研究专题详情页。",
    },
    {
        "candidate_id": "domestic:CSSN:lishi-zhuanti-1941-1949",
        "title": "中国社会科学院（cssn.cn）中国史栏目（民主党派历史研究学术资源）",
        "creator": "中国社会科学院",
        "document_date": "2026",
        "document_date_precision": "approximate",
        "document_type": "中国社科院学术研究栏目",
        "repository_code": "CSSN",
        "repository_name": "中国社会科学院（cssn.cn）",
        "collection_name": "中国史 / 近代史研究 / 当代史研究",
        "archive_item": "https://www.cssn.cn/lsx/lsx_zgs/",
        "catalog_reference": "中国社会科学院 = 国家级学术研究机构；含民主党派研究专题",
        "catalog_reference_status": "verified",
        "source_url": "https://www.cssn.cn/lsx/lsx_zgs/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "中国社会科学院官方公开发布",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "中国社会科学院官方",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1949民盟参与政协"],
        "person_tags": ["中国社会科学院", "民主党派"],
        "place_tags": ["北京"],
        "evidence_note": (
            "urllib 2026-07-21 实测 cssn.cn/lsx/lsx_zgs/；"
            "中国社科院中国史栏目；"
            "含民主党派历史研究学术资源；"
            "L2 等级：中国社会科学院 = 国家级学术研究机构。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.cssn.cn/lsx/lsx_zgs/",
        "uncertainty_note": "L1 升级需具体民主党派研究专题详情页。",
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
                    f"L2 needs_human_review 中央社院 + 中国社科院（批次 K-2）；"
                    f"urllib 2026-07-21 实测。"
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