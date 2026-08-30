#!/usr/bin/env python3
"""Register 批次 J-2b: 群言出版社民盟历史人物丛书 + 中国民主同盟七十年。

WebSearch 2026-07-21 核读孔夫子旧书网 + 中图网：

民盟历史人物丛书（群言出版社）：
1. 民盟历史文献:陶行知（夏德清 / 武素月，2013）
2. 民盟历史文献:楚图南（张维，2013）
3. 民盟历史文献:童第周（俞为洁，2014）
4. 民盟历史文献:杜斌丞（张国全，2014）

中国民主同盟七十年（群言出版社 2011-05，ISBN 9787802562325，348 页）

庆阳民盟史（中国文史出版社 2021）

等级：L2 accepted（已出版正式文献 + 民盟中央系列）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 中国民主同盟七十年
    {
        "candidate_id": "domestic:QY:2011-zhongguo-minmeng-qishinian",
        "title": "《中国民主同盟七十年》(中国民主同盟中央委员会编，群言出版社 2011-05，ISBN 9787802562325，348 页)",
        "creator": "中国民主同盟中央委员会",
        "document_date": "2011-05",
        "document_date_precision": "month",
        "document_type": "民盟中央正式出版纪念文献汇编",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）",
        "collection_name": "民盟历史文献丛书",
        "archive_item": "群言出版社 2011-05 第 1 版；348 页；定价 25.00 元",
        "catalog_reference": (
            "ISBN 9787802562325；群言出版社 2011-05；"
            "中国民主同盟中央委员会编"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://book.kongfz.com/245792/1048098624/",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "正式出版物；孔夫子旧书网在售",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央委员会编 / 群言出版社出版 = 官方一手",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟中央委员会"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读孔夫子旧书网 "
            "https://book.kongfz.com/245792/1048098624/；"
            "《中国民主同盟七十年》（2011-05 群言出版社 348 页）；"
            "中国民主同盟中央委员会 编；"
            "1941 成立到 2011 70 年民盟完整历史；"
            "L2 等级：民盟中央官方纪念汇编。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "https://book.kongfz.com/245792/1048098624/",
        "uncertainty_note": "L1 升级需取得扫描件。",
    },
    # 民盟历史文献:陶行知
    {
        "candidate_id": "domestic:QY:2013-minmeng-taoxingzhi",
        "title": "《民盟历史文献:陶行知》（夏德清、武素月，群言出版社 2013）",
        "creator": "夏德清、武素月",
        "document_date": "2013",
        "document_date_precision": "year",
        "document_type": "民盟中央系列出版（民盟历史人物丛书）",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）",
        "collection_name": "民盟历史人物丛书",
        "archive_item": "群言出版社 2013",
        "catalog_reference": "群言出版社 2013；夏德清 / 武素月 著；民盟历史文献系列",
        "catalog_reference_status": "verified",
        "source_url": "https://baike.baidu.com/item/民盟历史文献:陶行知/16295650",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "正式出版物；民盟历史人物系列",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "群言出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1945民盟一大"],
        "person_tags": ["陶行知", "中国民主同盟"],
        "place_tags": ["上海", "重庆"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《民盟历史文献:陶行知》（夏德清/武素月，群言出版社 2013）；"
            "陶行知 = 民盟中央常委（1945 一大）+ 1946-11 逝世；"
            "L2 等级：群言出版社民盟系列。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "https://baike.baidu.com/item/民盟历史文献:陶行知/16295650",
        "uncertainty_note": "ISBN 待查。",
    },
    # 民盟历史文献:楚图南
    {
        "candidate_id": "domestic:QY:2013-minmeng-chutunan",
        "title": "《民盟历史文献:楚图南》（张维，群言出版社 2013）",
        "creator": "张维",
        "document_date": "2013",
        "document_date_precision": "year",
        "document_type": "民盟中央系列出版",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）",
        "collection_name": "民盟历史人物丛书",
        "archive_item": "群言出版社 2013",
        "catalog_reference": "群言出版社 2013；张维 著",
        "catalog_reference_status": "verified",
        "source_url": "https://baike.baidu.com/item/民盟历史文献:楚图南/16254658",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "正式出版物；",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "群言出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["楚图南", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《民盟历史文献:楚图南》（张维，群言出版社 2013）；"
            "楚图南 = 民盟中央主席（1986-1987）+ 一届政协代表；"
            "L2 等级：群言出版社民盟系列。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "https://baike.baidu.com/item/民盟历史文献:楚图南/16254658",
        "uncertainty_note": "ISBN 待查。",
    },
    # 民盟历史文献:童第周
    {
        "candidate_id": "domestic:QY:2014-minmeng-tongdizhou",
        "title": "《民盟历史文献:童第周》（俞为洁，群言出版社 2014）",
        "creator": "俞为洁",
        "document_date": "2014",
        "document_date_precision": "year",
        "document_type": "民盟中央系列出版",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）",
        "collection_name": "民盟历史人物丛书",
        "archive_item": "群言出版社 2014",
        "catalog_reference": "群言出版社 2014；俞为洁 著",
        "catalog_reference_status": "verified",
        "source_url": "https://baike.baidu.com/item/民盟历史文献:童第周/16449893",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "正式出版物；",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "群言出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协"],
        "person_tags": ["童第周", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《民盟历史文献:童第周》（俞为洁，群言出版社 2014）；"
            "童第周 = 民盟中央副主席（1980-1988）+ 著名生物学家；"
            "L2 等级：群言出版社民盟系列。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "https://baike.baidu.com/item/民盟历史文献:童第周/16449893",
        "uncertainty_note": "ISBN 待查。",
    },
    # 民盟历史文献:杜斌丞
    {
        "candidate_id": "domestic:QY:2014-minmeng-dubincheng",
        "title": "《民盟历史文献:杜斌丞》（张国全，群言出版社 2014）",
        "creator": "张国全",
        "document_date": "2014",
        "document_date_precision": "year",
        "document_type": "民盟中央系列出版",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）",
        "collection_name": "民盟历史人物丛书",
        "archive_item": "群言出版社 2014",
        "catalog_reference": "群言出版社 2014；张国全 著",
        "catalog_reference_status": "verified",
        "source_url": "https://baike.baidu.com/item/民盟历史文献:杜斌丞/16384705",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "正式出版物；",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "群言出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1947民盟解散"],
        "person_tags": ["杜斌丞", "中国民主同盟西北总支部"],
        "place_tags": ["西安"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《民盟历史文献:杜斌丞》（张国全，群言出版社 2014）；"
            "杜斌丞 = 民盟西北总支部核心创始人（1942-） + 1947-10-07 西安玉祥门外就义；"
            "L2 等级：群言出版社民盟系列。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "https://baike.baidu.com/item/民盟历史文献:杜斌丞/16384705",
        "uncertainty_note": "ISBN 待查。",
    },
    # 庆阳民盟史
    {
        "candidate_id": "domestic:QY:2021-qingyang-minmeng-shi",
        "title": "《庆阳民盟史》（中国文史出版社 2021，记录庆阳民盟 1944-2019）",
        "creator": "民盟甘肃省庆阳市委员会",
        "document_date": "2021",
        "document_date_precision": "year",
        "document_type": "民盟地方组织史（甘肃庆阳）",
        "repository_code": "QY",
        "repository_name": "中国文史出版社",
        "collection_name": "民盟地方史志系列",
        "archive_item": "中国文史出版社 2021",
        "catalog_reference": "中国文史出版社 2021；民盟庆阳市委员会编",
        "catalog_reference_status": "verified",
        "source_url": "http://www.qingyangwang.com.cn/content/2021-11/11/content_536994.htm",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "正式出版物；2021-11-11 出版发行；",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟地方组织编 / 中国文史出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名", "1945民盟一大"],
        "person_tags": ["中国民主同盟", "民盟甘肃省庆阳市委员会"],
        "place_tags": ["庆阳", "甘肃"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "《庆阳民盟史》（中国文史出版社 2021）；"
            "记录庆阳民盟 1944-2019 发展历程；"
            "甘肃地方民盟史，覆盖 1944 改组后阶段；"
            "L2 等级：地方组织官方编 + 中国文史出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "http://www.qingyangwang.com.cn/content/2021-11/11/content_536994.htm",
        "uncertainty_note": "ISBN 待查。",
    },
    # 民盟历史人物丛书聚合锚点
    {
        "candidate_id": "domestic:QY:mengtuan-lishi-renwu-congshu-anchor",
        "title": "民盟历史人物丛书聚合锚点（群言出版社出版，陶行知/楚图南/童第周/杜斌丞/费孝通 等民盟核心人物传记系列）",
        "creator": "群言出版社 + 民盟中央",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟历史人物丛书聚合锚点",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）",
        "collection_name": "民盟历史人物丛书（民盟历史文献系列子系列）",
        "archive_item": "https://book.douban.com/series/40660",
        "catalog_reference": "豆瓣民盟历史人物历史文献丛书",
        "catalog_reference_status": "verified",
        "source_url": "https://book.douban.com/series/40660",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "豆瓣系列页公开；含多本民盟核心人物传记",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "群言出版社官方系列",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["陶行知", "楚图南", "童第周", "杜斌丞", "费孝通", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读豆瓣 "
            "https://book.douban.com/series/40660 ；"
            "民盟历史人物丛书 = 民盟中央直属群言出版社 2013-2014 系列；"
            "已注册：陶行知 / 楚图南 / 童第周 / 杜斌丞；"
            "待补：费孝通 / 吴晗 / 梁漱溟 / 胡愈之 / 邓初民 等更多民盟核心；"
            "L2 等级：群言出版社系列。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://book.douban.com/series/40660",
        "uncertainty_note": "L1 升级需取得具体人物传记原件。",
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
                    f"L2 needs_human_review 群言出版社民盟系列（批次 J-2b）；"
                    f"WebSearch 2026-07-21 核读孔夫子旧书网 + 豆瓣。"
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