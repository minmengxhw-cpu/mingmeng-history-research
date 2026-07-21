#!/usr/bin/env python3
"""Register 批次 J-3c: 致公党/九三学社/台盟 官方权威一手。

urllib 2026-07-21 实测：

1. 中国致公党 zg.org.cn（146806 字节，党部官网主页）
2. 九三学社 93.gov.cn 简介 / 章程 / 历届中央委员会
   - 1945-09-03 民主科学座谈会改为九三座谈会
   - 1946-05-04 九三座谈会改称九三学社
   - 响应"五一口号" + 接受中国共产党领导
   - 参加中国人民政治协商会议第一届全体会议
3. 台盟 taimeng.org.cn 简介/章程
   - 1947-11-12 在香港成立
   - 接受中国共产党领导
   - 响应"五一口号" + 参加政协一届全体会议
   - 参与创建中华人民共和国

等级：L2 accepted（各党派中央官方一手）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 致公党 zg.org.cn 官方主页
    {
        "candidate_id": "domestic:ZG:website-anchor",
        "title": "中国致公党中央委员会官网（zg.org.cn，含 1925 美洲旧金山成立 + 1947-05 上海改组）",
        "creator": "中国致公党中央委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "致公党中央官方网站一手",
        "repository_code": "ZG",
        "repository_name": "中国致公党（zg.org.cn）",
        "collection_name": "致公党中央官网",
        "archive_item": "http://www.zg.org.cn/",
        "catalog_reference": "WebFetch/urllib 2026-07-21 实测 zg.org.cn 146806 字节",
        "catalog_reference_status": "verified",
        "source_url": "http://www.zg.org.cn/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "致公党中央官方公开发布；含 1925-10 美洲旧金山成立 + 1947-05 上海改组三次代表大会",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "致公党中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1925致公党前身", "1947致公党改组", "1949民盟参与政协"],
        "person_tags": ["司徒美堂", "陈其尤", "黄鼎臣", "中国致公党"],
        "place_tags": ["北京", "上海", "旧金山"],
        "evidence_note": (
            "urllib 2026-07-21 实测 zg.org.cn；"
            "致公党中央委员会官方主页（146806 字节，GBK）；"
            "1925-10 美洲旧金山洪门致公堂改组成立；"
            "1947-05 上海第三次代表大会改组为现代政党；"
            "司徒美堂 / 陈其尤 / 黄鼎臣 等历任主席；"
            "L2 等级：致公党中央官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.zg.org.cn/",
        "uncertainty_note": "L1 升级需具体原件。",
    },
    # 九三学社 简介
    {
        "candidate_id": "domestic:93:bsjs-jsjj-jianyao-1945-1949",
        "title": "九三学社中央委员会简介（93.gov.cn/bsjs-jsjj/，1945-09-03 民主科学座谈会 + 1946-05-04 改称九三学社）",
        "creator": "九三学社中央委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "九三学社中央官方网站一手",
        "repository_code": "93",
        "repository_name": "九三学社（93.gov.cn）",
        "collection_name": "九三学社中央简介",
        "archive_item": "http://www.93.gov.cn:80/bsjs-jsjj/",
        "catalog_reference": "urllib 2026-07-21 实测 93.gov.cn/bsjs-jsjj/",
        "catalog_reference_status": "verified",
        "source_url": "http://www.93.gov.cn:80/bsjs-jsjj/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "九三学社中央官方公开发布；含 1945-1949 历史时点",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "九三学社中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945九三学社前身", "1946九三学社定名", "1949民盟参与政协"],
        "person_tags": ["许德珩", "潘菽", "张西曼", "涂长望", "梁希", "九三学社"],
        "place_tags": ["重庆", "北京"],
        "evidence_note": (
            "urllib 2026-07-21 实测 93.gov.cn/bsjs-jsjj/；"
            "九三学社中央简介 71050 字节；"
            "1944 民主科学座谈会在重庆成立（继承五四反帝爱国民主科学精神）；"
            "1945-09-03 改名为九三座谈会（纪念抗战胜利）；"
            "1946-05-04 改称九三学社；"
            "响应中共五一口号；接受中国共产党领导；"
            "参加中国人民政治协商会议第一届全体会议；"
            "为建立中华人民共和国作出积极贡献；"
            "L2 等级：九三学社中央官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.93.gov.cn:80/bsjs-jsjj/",
        "uncertainty_note": "L1 升级需具体原件。",
    },
    # 九三学社 历届中央委员会
    {
        "candidate_id": "domestic:93:bsjs-ljzywyh-anchor",
        "title": "九三学社中央历届中央委员会索引页（93.gov.cn/bsjs-ljzywyh/，含 1945-09 成立后历届）",
        "creator": "九三学社中央委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "九三学社中央官方历届中央委员会索引",
        "repository_code": "93",
        "repository_name": "九三学社（93.gov.cn）",
        "collection_name": "历届中央委员会",
        "archive_item": "http://www.93.gov.cn:80/bsjs-ljzywyh/",
        "catalog_reference": "urllib 2026-07-21 实测 93.gov.cn/bsjs-ljzywyh/ 71057 字节",
        "catalog_reference_status": "verified",
        "source_url": "http://www.93.gov.cn:80/bsjs-ljzywyh/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "九三学社中央官方历届中央委员会索引页",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "九三学社中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945九三学社前身", "1946九三学社定名"],
        "person_tags": ["许德珩", "潘菽", "九三学社中央委员会"],
        "place_tags": ["北京"],
        "evidence_note": (
            "urllib 2026-07-21 实测 93.gov.cn/bsjs-ljzywyh/；"
            "九三学社中央历届中央委员会索引页（71057 字节）；"
            "含 1945-09 成立后历届（许德珩主席等）；"
            "L2 等级：九三学社中央官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.93.gov.cn:80/bsjs-ljzywyh/",
        "uncertainty_note": "L1 升级需具体届次详情。",
    },
    # 台盟 简介
    {
        "candidate_id": "domestic:TM:tmly-tmjj-jianyao-1947",
        "title": "台盟中央简介（taimeng.org.cn/tmly/tmjj/，1947-11-12 香港成立，响应二二八事件）",
        "creator": "台湾民主自治同盟中央委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "台盟中央官方网站一手",
        "repository_code": "TM",
        "repository_name": "台湾民主自治同盟（taimeng.org.cn）",
        "collection_name": "台盟简介 / 台盟章程",
        "archive_item": "http://www.taimeng.org.cn/tmly/tmjj/",
        "catalog_reference": "urllib 2026-07-21 实测 taimeng.org.cn/tmly/tmjj/ 20298 字节",
        "catalog_reference_status": "verified",
        "source_url": "http://www.taimeng.org.cn/tmly/tmjj/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "台盟中央官方公开发布；含 1947-11-12 香港成立 + 二二八事件背景",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "台盟中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1947二二八事件", "1947台盟成立", "1949民盟参与政协"],
        "person_tags": ["谢雪红", "杨克煌", "苏新", "台湾民主自治同盟"],
        "place_tags": ["香港", "台湾"],
        "evidence_note": (
            "urllib 2026-07-21 实测 taimeng.org.cn/tmly/tmjj/；"
            "台盟中央简介 20298 字节；"
            "台盟于 1947-11-12 在香港成立；"
            "接受中国共产党的领导；参加新民主主义革命；"
            "支持台湾人民的反帝爱国民主斗争；"
            "响应中共五一口号；"
            "参加中国人民政治协商会议第一届全体会议；"
            "参与创建中华人民共和国；"
            "L2 等级：台盟中央官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.taimeng.org.cn/tmly/tmjj/",
        "uncertainty_note": "L1 升级需具体原件。",
    },
    # 台盟 章程
    {
        "candidate_id": "domestic:TM:tmly-tmzc-zhangcheng",
        "title": "台盟中央章程（taimeng.org.cn/tmly/tmzc/，最新版本）",
        "creator": "台湾民主自治同盟中央委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "台盟中央官方最新章程",
        "repository_code": "TM",
        "repository_name": "台湾民主自治同盟（taimeng.org.cn）",
        "collection_name": "台盟章程",
        "archive_item": "http://www.taimeng.org.cn/tmly/tmzc/",
        "catalog_reference": "urllib 2026-07-21 实测 taimeng.org.cn/tmly/tmzc/ 19093 字节",
        "catalog_reference_status": "verified",
        "source_url": "http://www.taimeng.org.cn/tmly/tmzc/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "台盟中央官方最新章程",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "台盟中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1947台盟成立", "1949民盟参与政协"],
        "person_tags": ["台湾民主自治同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "urllib 2026-07-21 实测；"
            "台盟中央最新章程 19093 字节；"
            "L2 等级：台盟中央官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.taimeng.org.cn/tmly/tmzc/",
        "uncertainty_note": "L1 升级需具体届次章程原件。",
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
                    f"L2 needs_human_review 致公/九三/台盟中央官方一手（批次 J-3c）；"
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