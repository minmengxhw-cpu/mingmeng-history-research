#!/usr/bin/env python3
"""Register 批次 J-2: 群言出版社 1991 民盟历史文献核心系列。

WebSearch 2026-07-21 核读孔夫子旧书网 + 群言出版社官网：

核心 1991 群言版（民盟中央文史委员会编）：
1. 《中国民主同盟简史 1941-1949》（群言出版社 1991-03，148 页，32 开）⭐⭐⭐⭐⭐
2. 《中国民主同盟史(1941-1949)》（群言出版社 1991-03）⭐⭐⭐⭐⭐
3. 《我与民盟：中国民主同盟成立 50 周年纪念文集》（群言出版社 1991-08）⭐⭐⭐⭐
4. 《中国民主同盟历史文献 1949-1988》（上下册，文物出版社 1991-03，1327 页）已 H-3 注册

2012 群言典藏（民盟中央委员会编）：
5. 《中国民主同盟史(群言典藏)精装》ISBN 9787802563421（2012-10）已批次 D 注册（QY）
6. 《中国民主同盟史(民盟历史文献)》ISBN 9787802563728（2012-10）已批次 D 注册（QY）

等级：L2 accepted（已出版正式文献 + 民盟中央官方源）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 1991 群言版 中国民主同盟简史 1941-1949
    {
        "candidate_id": "domestic:QY:1991-zhongguo-minmeng-jianshi-1941-1949",
        "title": "《中国民主同盟简史 1941-1949》（民盟中央文史委员会编，群言出版社 1991-03，148 页，32 开本）",
        "creator": "中国民主同盟中央文史委员会",
        "document_date": "1991-03",
        "document_date_precision": "month",
        "document_type": "民盟中央正式出版档案文献汇编（1991）",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）",
        "collection_name": "民盟历史文献丛书",
        "archive_item": "群言出版社 1991-03 第 1 版第 1 次印刷；148 页 32 开",
        "catalog_reference": (
            "群言出版社 1991-03；148 页；32 开本；内页干净（孔夫子旧书网）；"
            "民盟中央文史委员会编"
        ),
        "catalog_reference_status": "verified",
        "source_url": "http://book.kongfz.com/275761/2028322541/",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "正式出版物；孔夫子旧书网在售；1991-03 出版；",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央文史委员会编 / 群言出版社出版 = 官方一手",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1946政治协商会议", "1947民盟解散"],
        "person_tags": ["黄炎培", "张澜", "沈钧儒", "罗隆基", "章伯钧", "中国民主同盟中央文史委员会"],
        "place_tags": ["重庆", "上海", "南京", "北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读孔夫子旧书网 "
            "http://book.kongfz.com/275761/2028322541/；"
            "《中国民主同盟简史 1941-1949》（1991-03 群言出版社 32 开本 148 页）；"
            "民盟中央文史委员会编；"
            "1941 中国民主政团同盟成立 → 1944 改组 → 1945 一大 → 1947 解散 全部覆盖；"
            "L2 等级：民盟中央官方一手汇编。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "http://book.kongfz.com/275761/2028322541/",
        "uncertainty_note": "未取得扫描件；L1 升级需取得原件。",
    },
    # 1991 群言版 中国民主同盟史 1941-1949
    {
        "candidate_id": "domestic:QY:1991-zhongguo-minmeng-shi-1941-1949",
        "title": "《中国民主同盟史(1941-1949)》（群言出版社 1991-03）",
        "creator": "中国民主同盟中央委员会",
        "document_date": "1991-03",
        "document_date_precision": "month",
        "document_type": "民盟中央正式出版档案文献（1991）",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）",
        "collection_name": "民盟历史文献丛书",
        "archive_item": "群言出版社 1991-03",
        "catalog_reference": "群言出版社 1991-03；民盟中央委员会编",
        "catalog_reference_status": "verified",
        "source_url": "https://book.kongfz.com/2246/4981376637",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "正式出版物；孔夫子旧书网在售",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央委员会编 / 群言出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟中央委员会"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读孔夫子旧书网；"
            "《中国民主同盟史(1941-1949)》（1991-03 群言出版社）；"
            "中国民主同盟中央委员会 编；"
            "1941-1949 民盟完整通史；"
            "L2 等级：民盟中央官方汇编。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "https://book.kongfz.com/2246/4981376637",
        "uncertainty_note": "ISBN 待查；与 2012 群言典藏（ISBN 9787802563728）内容近似。",
    },
    # 1991 群言版 我与民盟 50 周年纪念文集
    {
        "candidate_id": "domestic:QY:1991-wo-yu-minmeng-50zhounian-jinianwenji",
        "title": "《我与民盟：中国民主同盟成立 50 周年纪念文集》（群言出版社 1991-08）",
        "creator": "中国民主同盟文史委员会",
        "document_date": "1991-08",
        "document_date_precision": "month",
        "document_type": "民盟中央正式出版纪念文集（1991）",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）",
        "collection_name": "民盟历史文献丛书 + 纪念文集",
        "archive_item": "群言出版社 1991-08",
        "catalog_reference": "群言出版社 1991-08；民盟中央文史委员会编",
        "catalog_reference_status": "verified",
        "source_url": "http://book.kongfz.com/765/207968742/",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "正式出版物；孔夫子旧书网在售；民盟成立 50 周年纪念文集",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央文史委员会编 / 群言出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟文史委员会", "民盟盟员"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读孔夫子旧书网 "
            "http://book.kongfz.com/765/207968742/；"
            "《我与民盟：中国民主同盟成立 50 周年纪念文集》（1991-08 群言出版社）；"
            "民盟中央文史委员会编；"
            "1941-1991 民盟盟员回忆文章集；"
            "L2 等级：民盟中央官方纪念文集。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "http://book.kongfz.com/765/207968742/",
        "uncertainty_note": "未取得扫描件；L1 升级需取得原件。",
    },
    # 民盟历史文献丛书聚合锚点
    {
        "candidate_id": "domestic:QY:mengtuan-lishiwenxian-congshu-anchor",
        "title": "民盟历史文献丛书聚合锚点（民盟中央文史委员会编，群言出版社 + 文物出版社出版，1991-2024 系列）",
        "creator": "中国民主同盟中央文史委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟中央文史委员会编文献丛书聚合锚点",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）+ 文物出版社",
        "collection_name": "民盟历史文献丛书 + 民盟历史人物丛书 + 民盟地方史志 + 民盟智库",
        "archive_item": "http://www.bookschina.com/congshu/57638/",
        "catalog_reference": (
            "中图网民盟历史文献丛书 "
            "http://www.bookschina.com/congshu/57638/ ；"
            "群言出版社官网 http://www.qypublish.com/Pages/ZDAboutUs.aspx"
        ),
        "catalog_reference_status": "verified",
        "source_url": "http://www.qypublish.com/Pages/ZDAboutUs.aspx",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "民盟中央直属出版社 + 国家级出版机构；含民盟历史文献系列（已列入十二五/十三五国家重点图书）",
        "medium": "hybrid",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央直属出版社",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟中央文史委员会", "群言出版社", "文物出版社"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读群言出版社官网；"
            "群言出版社（中国民主同盟中央委员会主办）出版系列："
            "①民盟历史文献丛书（含 1941-1949 全部关键时点）；"
            "②民盟历史人物丛书（民盟核心人物传记）；"
            "③民盟地方史志（各省市民盟组织史）；"
            "④民盟智库（民盟中央政策研究）；"
            "已列入国家十二五/十三五重点图书出版计划，多次获国家出版基金资助；"
            "1991-2024 系列出版；"
            "L2 等级：民盟中央直属出版。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "群言出版社官网 http://www.qypublish.com/Pages/ZDAboutUs.aspx ；"
            "中图网丛书 http://www.bookschina.com/congshu/57638/"
        ),
        "uncertainty_note": "L1 升级需取得具体出版物扫描件。",
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
                    f"L2 needs_human_review 群言出版社 1991 民盟文献（批次 J-2）；"
                    f"WebSearch 2026-07-21 核读孔夫子旧书网。"
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