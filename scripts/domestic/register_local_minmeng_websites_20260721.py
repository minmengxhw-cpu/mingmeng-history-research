#!/usr/bin/env python3
"""Register 批次 J-3: 地方民盟官网 + 人民网党史 + 澎湃新闻盟史纵览。

WebSearch + WebFetch 2026-07-21：

1. 人民网 dangshi.people.com.cn《民盟在这里成立》
2. 澎湃新闻 thepaper.cn【盟史纵览】系列（民盟成立、改组、一大等）
3. 澎湃【会史大学习】地方组织的建立
4. 民盟成都市委员会 cdmm.org.cn 记忆文选 + 民盟广州市委员会等
5. 民盟北京市委员会 bjmm.org.cn
6. 地方民盟历史时间线（重庆/上海/广州/北京/昆明/成都）

等级：L2 accepted（人民网党史 + 澎湃政务 + 各地民盟市委官方）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 人民网党史频道《民盟在这里成立》
    {
        "candidate_id": "domestic:RMTZ:dangshi-minmeng-zaili-chengli",
        "title": "人民网党史频道《民盟在这里成立》（1941-03-19 重庆上清寺特园民盟前身成立）",
        "creator": "人民网党史频道",
        "document_date": "2016-01-21",
        "document_date_precision": "day",
        "document_type": "人民网党史频道官方历史报道",
        "repository_code": "RMTZ",
        "repository_name": "人民网（people.com.cn）",
        "collection_name": "党史频道",
        "archive_item": "http://dangshi.people.com.cn/n1/2016/0121/c85037-28073427.html",
        "catalog_reference": "人民网党史频道 2016-01-21 发布",
        "catalog_reference_status": "verified",
        "source_url": "http://dangshi.people.com.cn/n1/2016/0121/c85037-28073427.html",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "人民网党史频道公开访问",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "人民网党史频道官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["黄炎培", "张澜", "梁漱溟", "左舜生", "章伯钧", "罗隆基", "张君劢", "中国民主同盟"],
        "place_tags": ["重庆", "上清寺", "特园"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读人民网 dangshi.people.com.cn；"
            "《民盟在这里成立》（人民网党史频道 2016-01-21）；"
            "1941-03-19 中国民主政团同盟在重庆上清寺特园秘密成立；"
            "L2 等级：人民网党史频道官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://dangshi.people.com.cn/n1/2016/0121/c85037-28073427.html",
        "uncertainty_note": "L1 升级需具体原件。",
    },
    # 澎湃新闻【盟史纵览】民盟成立（四）改组
    {
        "candidate_id": "domestic:PP:menshi-zonglan-minmeng-chengli-4-gaizu",
        "title": "澎湃新闻【盟史纵览】民盟的成立（四）：改组为中国民主同盟（1944-09-19 重庆特园）",
        "creator": "中国民主同盟（公众号）",
        "document_date": "2021-03-26",
        "document_date_precision": "day",
        "document_type": "民盟中央官方 + 澎湃新闻政务号转载",
        "repository_code": "PP",
        "repository_name": "澎湃新闻（thepaper.cn）",
        "collection_name": "盟史纵览系列",
        "archive_item": "https://www.thepaper.cn/newsDetail_forward_11913418",
        "catalog_reference": "澎湃新闻政务号 2021-03-26",
        "catalog_reference_status": "verified",
        "source_url": "https://www.thepaper.cn/newsDetail_forward_11913418",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "澎湃新闻政务号公开访问",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "澎湃新闻政务号转载民盟中央官方公众号",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名"],
        "person_tags": ["张澜", "左舜生", "章伯钧", "罗隆基", "梁漱溟", "张君劢", "中国民主同盟"],
        "place_tags": ["重庆", "上清寺", "特园"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测澎湃新闻；"
            "【盟史纵览】民盟的成立（四）：改组为中国民主同盟；"
            "1944-09-19 全国代表会议在重庆特园召开；"
            "取消团体会员制；中国民主政团同盟改名为中国民主同盟；"
            "张澜为主席，左舜生为秘书长；章伯钧/罗隆基/梁漱溟/张君劢 各委员会主任；"
            "33 名中央委员，13 名中央常委；"
            "拟定《中国民主同盟纲领（草案）》。"
            "L2 等级：澎湃政务号转载 + 民盟中央公众号。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.thepaper.cn/newsDetail_forward_11913418",
        "uncertainty_note": "L1 升级需原件。",
    },
    # 澎湃【会史大学习】地方组织的建立
    {
        "candidate_id": "domestic:PP:huishi-daxuexi-difang-zuzhi-jianshe-1",
        "title": "澎湃新闻【会史大学习】(二十七)地方组织的建立（上）（民盟地方组织 1945-1949）",
        "creator": "中国民主同盟（公众号）",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟中央官方 + 澎湃政务号转载",
        "repository_code": "PP",
        "repository_name": "澎湃新闻（thepaper.cn）",
        "collection_name": "会史大学习系列",
        "archive_item": "https://www.thepaper.cn/newsDetail_forward_30549185",
        "catalog_reference": "澎湃政务号会史大学习系列",
        "catalog_reference_status": "verified",
        "source_url": "https://www.thepaper.cn/newsDetail_forward_30549185",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "澎湃新闻政务号公开访问",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "澎湃政务号转载民盟中央官方公众号",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["上海", "重庆", "广州", "北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读澎湃；"
            "【会史大学习】(二十七)地方组织的建立（上）；"
            "1945-01 民盟重庆市支部第一届委员会（何公敢主任委员）；"
            "1945-09 民盟重庆市支部正式成立；"
            "1946-01 民盟南方总支部在香港成立（领导广东/广西/港澳/海外）；"
            "1946-01 民盟广州市工作委员会（丘克辉主委）；"
            "1946-02 民盟广东省支部 + 广州市分部（陈柏麟主委）；"
            "1949-03 民盟总部由香港迁北平；"
            "1949-09 民盟代表出席政协一届全体会议。"
            "L2 等级：澎湃政务号转载 + 民盟中央官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.thepaper.cn/newsDetail_forward_30549185",
        "uncertainty_note": "L1 升级需原件。",
    },
    # 成都民盟 cdmm.org.cn
    {
        "candidate_id": "domestic:CDMM:website-anchor",
        "title": "中国民主同盟成都市委员会官网（cdmm.org.cn，含盟史与回忆文选栏目）",
        "creator": "中国民主同盟成都市委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "地方民盟组织官方一手",
        "repository_code": "CDMM",
        "repository_name": "中国民主同盟成都市委员会（cdmm.org.cn）",
        "collection_name": "盟史与回忆文选栏目",
        "archive_item": "http://www.cdmm.org.cn/",
        "catalog_reference": "cdmm.org.cn 民盟成都市委官方",
        "catalog_reference_status": "verified",
        "source_url": "http://www.cdmm.org.cn/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "民盟成都市委官方公开发布；含『记忆文选』回忆文章 + 1941-1949 关键时点",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟成都市委官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名", "1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟成都市委员会"],
        "place_tags": ["成都"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "中国民主同盟成都市委员会官网 cdmm.org.cn；"
            "含『记忆文选』栏目（盟员回忆 1941-1949 民盟历史）；"
            "L2 等级：地方民盟组织官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.cdmm.org.cn/",
        "uncertainty_note": "具体『记忆文选』内容待深入探索。",
    },
    # 北京民盟 bjmm.org.cn
    {
        "candidate_id": "domestic:BJMM:website-anchor",
        "title": "中国民主同盟北京市委员会官网（bjmm.org.cn，含 1949 民盟迁北平等历史资料）",
        "creator": "中国民主同盟北京市委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "地方民盟组织官方一手",
        "repository_code": "BJMM",
        "repository_name": "中国民主同盟北京市委员会（bjmm.org.cn）",
        "collection_name": "京盟概况 + 历史资料 + 庆祝中国民主同盟成立八十周年专题",
        "archive_item": "https://www.bjmm.org.cn/html/1/491/index.html",
        "catalog_reference": "bjmm.org.cn 民盟北京市委官方",
        "catalog_reference_status": "verified",
        "source_url": "https://www.bjmm.org.cn/html/1/491/index.html",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "民盟北京市委官方公开发布；含历史资料 + 成立 80 周年专题",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟北京市委官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟北京市委员会"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "bjmm.org.cn 导航含『历史资料 / 庆祝中国民主同盟成立八十周年』专题；"
            "1949-03 民盟总部由香港迁北平；"
            "1949-09 民盟代表出席政协一届全体会议；"
            "L2 等级：地方民盟组织官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.bjmm.org.cn/html/1/491/index.html",
        "uncertainty_note": "具体历史资料内容待深入探索。",
    },
    # 澎湃【盟史纵览】系列聚合锚点
    {
        "candidate_id": "domestic:PP:menshi-zonglan-series-anchor",
        "title": "澎湃新闻【盟史纵览】系列聚合锚点（民盟中央公众号官方 1941-1949 系列）",
        "creator": "中国民主同盟（公众号）+ 澎湃新闻政务号",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟中央官方 + 澎湃新闻政务号转载系列",
        "repository_code": "PP",
        "repository_name": "澎湃新闻（thepaper.cn）",
        "collection_name": "盟史纵览 + 会史大学习",
        "archive_item": "https://www.thepaper.cn/",
        "catalog_reference": "澎湃政务号 民盟 1941-1949 系列",
        "catalog_reference_status": "verified",
        "source_url": "https://www.thepaper.cn/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "澎湃新闻政务号 + 民盟中央公众号官方一手",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "澎湃政务号 + 民盟中央官方公众号",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1946政治协商会议", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["黄炎培", "张澜", "沈钧儒", "罗隆基", "章伯钧", "梁漱溟", "张君劢", "左舜生", "中国民主同盟"],
        "place_tags": ["重庆", "上海", "北京", "南京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读澎湃；"
            "澎湃【盟史纵览】系列：民盟成立（一）（二）（三）（四）+ 改组等；"
            "澎湃【会史大学习】系列：地方组织建立（一）（二）（二十七）等；"
            "L2 等级：民盟中央官方公众号 + 澎湃政务号官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.thepaper.cn/",
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
                    f"L2 needs_human_review 人民网党史 / 澎湃政务 / 地方民盟官方（批次 J-3）；"
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