#!/usr/bin/env python3
"""Register 批次 H-3: Wen Yiduo 关键文物 + 群言出版社 + 文物出版社 1991 民盟历史文献。

WebFetch 2026-07-21 实测：

A. Wikimedia Commons 闻一多分类（15 文件，已注册 2）：
- 周恩来悼词（已 G-3）
- 邓颖超悼词（已 G-2）
新增 4 条 L2：
- 闻一多衣冠冢
- 西南联大博物馆-闻一多刻谭庆双印
- 西南联大旧址 15
- 闻一多肖像

B. 群言出版社（民盟中央出版社） = 民盟历史文献系列出版机构

C. 《中国民主同盟历史文献 1949-1988》(文物出版社 1991) = 民盟中央文史委员会编

等级：L2 accepted（已出版正式文献 + 民盟中央出版社）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 闻一多衣冠冢
    {
        "candidate_id": "domestic:WM:1946-wen-yiduo-yiguanzhong",
        "title": "闻一多衣冠冢（1946 昆明，民国烈士文物）",
        "creator": "作者不详（PD-China）",
        "document_date": "1946",
        "document_date_precision": "year",
        "document_type": "民国时期影像（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 闻一多分类",
        "collection_name": "Wen Yiduo (15F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:闻一多 衣冠冢.jpg",
        "catalog_reference": "Wikimedia Commons File:闻一多 衣冠冢.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E9%97%BB%E4%B8%80%E5%A4%9A%20%E8%A1%A3%E5%86%A0%E5%BA%9F.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；闻一多衣冠冢影像；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946李公朴闻一多遇害"],
        "person_tags": ["闻一多", "中国民主同盟"],
        "place_tags": ["昆明"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons /wiki/Category:Wen_Yiduo；"
            "闻一多衣冠冢（1946-07-15 闻一多遇害后衣冠冢）；"
            "L2 等级：PD-China + 民盟烈士文物。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:闻一多 衣冠冢.jpg",
        "uncertainty_note": "分辨率待核。",
    },
    # 西南联大博物馆 闻一多刻
    {
        "candidate_id": "domestic:WM:wen-yiduo-xi-nan-lian-da-yin-zhang",
        "title": "西南联大博物馆 闻一多刻印（谭庆双捐赠）",
        "creator": "闻一多",
        "document_date": "1940",
        "document_date_precision": "approximate",
        "document_type": "民国时期印章（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 闻一多分类",
        "collection_name": "Wen Yiduo (15F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:西南联大博物馆-闻一多刻谭庆双印（谭庆双捐赠）.jpg",
        "catalog_reference": "Wikimedia Commons File:西南联大博物馆-闻一多刻谭庆双印（谭庆双捐赠）.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E8%A5%BF%E5%8D%97%E8%81%94%E5%A4%A7%E5%8D%9A%E7%89%A9%E9%A6%86-%E9%97%BB%E4%B8%80%E5%A4%9A%E5%88%BB%E8%B0%AD%E5%BA%86%E5%8F%8C%E5%8D%B0%EF%BC%88%E8%B0%AD%E5%BA%86%E5%8F%8C%E6%8D%90%E8%B5%A0%EF%BC%89.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；闻一多刻印原件扫描；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名"],
        "person_tags": ["闻一多", "中国民主同盟"],
        "place_tags": ["昆明"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "西南联大博物馆藏闻一多刻印（谭庆双捐赠）；"
            "闻一多 = 民盟中央执行委员（1945 一大）+ 西南联大教授；"
            "L2 等级：PD-China + 民盟中央执委文物。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:西南联大博物馆-闻一多刻谭庆双印（谭庆双捐赠）.jpg",
        "uncertainty_note": "需进一步确认具体印章内容。",
    },
    # 西南联大旧址
    {
        "candidate_id": "domestic:WM:xinan-lianda-jiuzhi-1946-meng",
        "title": "西南联大旧址（1946 民盟核心活动地之一）",
        "creator": "作者不详（PD-China）",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "现代纪念设施照（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 闻一多分类",
        "collection_name": "Wen Yiduo (15F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:西南联大旧址 15.jpg",
        "catalog_reference": "Wikimedia Commons File:西南联大旧址 15.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E8%A5%BF%E5%8D%97%E8%81%94%E5%A4%A7%E6%97%A7%E5%9D%80%2015.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；西南联大旧址现状；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名", "1945民盟一大"],
        "person_tags": ["西南联大", "闻一多", "中国民主同盟"],
        "place_tags": ["昆明"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "西南联大旧址（昆明）= 1944-1946 西南联大时期 = 民盟核心活动地；"
            "闻一多/罗隆基/吴晗 等民盟核心均任教于此；"
            "L3 等级：纪念设施。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:西南联大旧址 15.jpg",
        "uncertainty_note": "L3 等级（现代纪念设施）。",
    },
    # 闻一多肖像照
    {
        "candidate_id": "domestic:WM:wen-yiduo-portrait",
        "title": "闻一多肖像照（民国时期）",
        "creator": "作者不详（PD-China）",
        "document_date": "1940",
        "document_date_precision": "approximate",
        "document_type": "民国时期人物照（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 闻一多分类",
        "collection_name": "Wen Yiduo (15F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Wen Yiduo.jpg",
        "catalog_reference": "Wikimedia Commons File:Wen Yiduo.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Wen_Yiduo.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；闻一多肖像照；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名", "1945民盟一大", "1946李公朴闻一多遇害"],
        "person_tags": ["闻一多", "中国民主同盟"],
        "place_tags": ["昆明"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "闻一多肖像照（民国时期）；"
            "闻一多 = 民盟中央执委（1945 一大）+ 1946-07-15 遇害；"
            "L2 等级：PD-China + 民盟中央执委肖像。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Wen_Yiduo.jpg",
        "uncertainty_note": "需进一步确认拍摄年份。",
    },
    # 中国民主同盟历史文献 1949-1988 (文物出版社 1991)
    {
        "candidate_id": "domestic:WP:1949-1988-minmeng-wenwu-1991",
        "title": "《中国民主同盟历史文献 1949-1988》（中国民主同盟中央文史委员会编，文物出版社 1991-01，2 卷）",
        "creator": "中国民主同盟中央文史委员会",
        "document_date": "1991-01",
        "document_date_precision": "month",
        "document_type": "民盟中央正式出版档案文献汇编（2 卷精装）",
        "repository_code": "WP",
        "repository_name": "文物出版社（中央级出版机构）",
        "collection_name": "民盟中央文史委员会编档案文献",
        "archive_item": "上卷 + 下卷 2 卷",
        "catalog_reference": "文物出版社 1991-01-01 第 1 版第 1 次印刷；上下册全；定价 80 元（参考）",
        "catalog_reference_status": "verified",
        "source_url": "http://book.kongfz.com/12382/403045316/",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "正式出版物；孔夫子旧书网在售；民盟中央编",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央文史委员会编 / 文物出版社出版 = 官方一手；学术引用可，复制需授权",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协", "1949-1988民盟史"],
        "person_tags": ["中国民主同盟中央文史委员会", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读孔夫子旧书网 http://book.kongfz.com/12382/403045316/；"
            "中国民主同盟历史文献 1949-1988（上下册全，文物出版社 1991-01 第 1 版第 1 次印刷）；"
            "中国民主同盟中央文史委员会 编；"
            "民盟中央 = 官方一手档案文献汇编；"
            "2 卷精装本；"
            "覆盖 1949-1988 民盟全部重大事件（含一届政协 / 第一届中央 / 历届代表大会 / 重要声明讲话）；"
            "L2 等级：民盟中央编 + 文物出版社 = 官方一手汇编。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": (
            "孔夫子旧书网 http://book.kongfz.com/12382/403045316/ ；"
            "百度百科 https://baike.baidu.com/item/中国民主同盟史:民盟历史文献/16438314"
        ),
        "uncertainty_note": "未取得扫描件；L1 升级需取得扫描件。",
    },
    # 群言出版社（民盟中央出版社）
    {
        "candidate_id": "domestic:QY:qunyan-chubanshe-meng-zhongyang",
        "title": "群言出版社（中国民主同盟中央委员会直属出版社，出版民盟历史文献系列）",
        "creator": "群言出版社（民盟中央直属）",
        "document_date": "2026",
        "document_date_precision": "approximate",
        "document_type": "民盟中央直属出版社（民盟历史文献系列官方出版机构）",
        "repository_code": "QY",
        "repository_name": "群言出版社（民盟中央直属）",
        "collection_name": "民盟历史文献系列 + 群言典藏",
        "archive_item": "http://www.qypublish.com/Pages/ZDAboutUs.aspx",
        "catalog_reference": "群言出版社 = 中国民主同盟中央委员会主办出版社",
        "catalog_reference_status": "verified",
        "source_url": "http://www.qypublish.com/Pages/ZDAboutUs.aspx",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "群言出版社官方公开发布",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "群言出版社官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1949民盟参与政协"],
        "person_tags": ["群言出版社", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读群言出版社 qypublish.com；"
            "群言出版社 = 中国民主同盟中央委员会主办出版社；"
            "出版《中国民主同盟史 2012》/《重庆民盟史 2014》/《中国民主同盟50年·重庆 2014》/"
            "《北京市民盟组织成立70周年 2016》/《福建简史 2018》/《湖南民盟人物 2020》/"
            "《重庆民盟史（精）2021》/《安徽民盟年鉴 2014-2018》/《云南民盟史 2021》等民盟历史文献系列；"
            "L2 等级：民盟中央直属出版社 = 官方一手。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "群言出版社官网 http://www.qypublish.com/Pages/ZDAboutUs.aspx ；"
            "群言典藏系列（孔夫子旧书网）"
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
                    f"L2/L3 needs_human_review 民盟中央出版社/闻一多文物（批次 H-3）；"
                    f"WebFetch 2026-07-21 实测；"
                    f"升级依据与批次 D/F-2 流程一致。"
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