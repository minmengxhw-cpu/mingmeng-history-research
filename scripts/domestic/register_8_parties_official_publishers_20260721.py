#!/usr/bin/env python3
"""Register 批次 J-4: 8 大民主党派中央出版社 + 各党派官方传记丛书。

WebSearch 2026-07-21 核读：

A. 团结出版社（民革中央直属）：
- 1987-12-25 成立
- 民革前辈传记丛书 2025-2026 启动（80 周年纪念）
- 辛亥著名人物传记丛书 2011
- 抗日战争与中华民族复兴 2015
- 华人华侨与中国革命和建设 2019

B. 澎湃【会史撷萃】民建诞生 1945-12-16 重庆白象街西南实业大厦
- 黄炎培 / 胡厥文 / 章乃器 / 施复亮 / 孙起孟 5 位发起人
- 主席团：黄炎培 / 胡厥文 / 黄墨涵
- 93 人出席成立大会
- 134 人发起签名

C. 8 大民主党派中央主管出版社
- 民革 → 团结出版社
- 民盟 → 群言出版社（已批次 D/J-2）
- 民建 → 中华工商时报出版社
- 民进 → 开明出版社
- 农工 → 中国医药科技出版社
- 致公 → 中国致公出版社
- 九三 → 学苑出版社
- 台盟 → 台海出版社

等级：L2 accepted（各党派中央直属出版社）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 团结出版社
    {
        "candidate_id": "domestic:MGCH:TJPRESS-minjizhongtian-zhuguan",
        "title": "团结出版社（民革中央直属，1987-12-25 成立，民革前辈传记丛书等）",
        "creator": "中国国民党革命委员会中央委员会（民革中央）",
        "document_date": "1987-12-25",
        "document_date_precision": "day",
        "document_type": "民革中央直属出版社（中央级出版机构）",
        "repository_code": "MGCH",
        "repository_name": "团结出版社（民革中央直属）",
        "collection_name": "民革系列 / 辛亥著名人物传记 / 抗日战争与中华民族复兴 / 华人华侨与中国革命和建设 / 民革前辈传记",
        "archive_item": "http://www.tjpress.com/",
        "catalog_reference": "团结出版社 = 民革中央直属中央级出版机构；1987-12-25 成立",
        "catalog_reference_status": "verified",
        "source_url": "http://www.tjpress.com/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "团结出版社官方公开发布",
        "medium": "hybrid",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民革中央直属出版社",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1948民革成立香港", "1949民盟参与政协"],
        "person_tags": ["团结出版社", "民革中央", "宋庆龄", "李济深", "何香凝"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读团结出版社官网；"
            "团结出版社有限公司（民革中央主管的中央级出版单位）；"
            "1987-12-25 成立；专门出版社会科学 / 民国史 / 传记作品 / 传统文化；"
            "已出版系列：辛亥著名人物传记丛书（2011，20 卷）/ "
            "抗日战争与中华民族复兴（2015，20 卷）/ "
            "华人华侨与中国革命和建设（2019，7 卷）/ "
            "民革前辈传记丛书（2025-2026 启动，纪念民革成立 80 周年）；"
            "L2 等级：民革中央直属出版。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.tjpress.com/",
        "uncertainty_note": "L1 升级需取得具体出版物扫描件。",
    },
    # 民革前辈传记丛书聚合锚点
    {
        "candidate_id": "domestic:MGCH:mengge-qianbei-chuanji-congshu-2025",
        "title": "《民革前辈传记丛书》（团结出版社 2025-2026 启动，纪念民革成立 80 周年）",
        "creator": "中国国民党革命委员会中央委员会宣传部 + 团结出版社",
        "document_date": "2026-02-04",
        "document_date_precision": "month",
        "document_type": "民革中央系列出版（前言传记丛书）",
        "repository_code": "MGCH",
        "repository_name": "团结出版社（民革中央直属）",
        "collection_name": "民革前辈传记丛书",
        "archive_item": "团结出版社 2025-2026 多辑出版",
        "catalog_reference": (
            "团结出版社官网民革书屋推荐书目 "
            "http://www.tjpress.com/folder992/folder995/2021-08-09/7998.html"
        ),
        "catalog_reference_status": "verified",
        "source_url": "http://www.tjpress.com/folder992/folder995/",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "团结出版社民革书屋栏目",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民革中央宣传部 + 团结出版社",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1948民革成立香港"],
        "person_tags": ["民革中央", "团结出版社", "宋庆龄", "李济深", "何香凝"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读团结出版社；"
            "《民革前辈传记丛书》（2025-2026 启动，分辑推出）；"
            "纪念民革成立 80 周年（1948-2028）；"
            "民革中央宣传部主办 + 团结出版社承办；"
            "任贵祥《〈民革前辈传记丛书〉读后》评论；"
            "L2 等级：民革中央系列出版。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "团结出版社 http://www.tjpress.com/folder992/folder995/ ；"
            "座谈会报道 https://new.qq.com/rain/a/20260206A050S100"
        ),
        "uncertainty_note": "L1 升级需取得具体人物传记原件。",
    },
    # 澎湃【会史撷萃】民建诞生
    {
        "candidate_id": "domestic:CJD:1945-minjian-dansheng-chongqing",
        "title": "中国民主建国会诞生（澎湃【会史撷萃】1945-12-16 重庆白象街西南实业大厦）",
        "creator": "中国民主建国会（公众号）",
        "document_date": "1945-12-16",
        "document_date_precision": "day",
        "document_type": "民建中央官方 + 澎湃政务号转载",
        "repository_code": "CJD",
        "repository_name": "中国民主建国会（cndca.org.cn）+ 澎湃新闻",
        "collection_name": "会史撷萃系列",
        "archive_item": "https://www.thepaper.cn/newsDetail_forward_30245299",
        "catalog_reference": "澎湃【会史撷萃(7)】民主建国会诞生 2024",
        "catalog_reference_status": "verified",
        "source_url": "https://www.thepaper.cn/newsDetail_forward_30245299",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "澎湃政务号 + 民建中央官方公众号",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "澎湃政务号 + 民建中央官方公众号",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民建成立"],
        "person_tags": ["黄炎培", "胡厥文", "章乃器", "施复亮", "孙起孟", "中国民主建国会"],
        "place_tags": ["重庆", "白象街", "西南实业大厦"],
        "evidence_note": (
            "WebSearch + WebFetch 2026-07-21 核读澎湃；"
            "【会史撷萃(7)】民主建国会诞生；"
            "1945-12-16 民建在重庆白象街西南实业大厦成立；"
            "5 位发起人：黄炎培 / 胡厥文 / 章乃器 / 施复亮 / 孙起孟；"
            "主席团：黄炎培 / 胡厥文 / 黄墨涵；"
            "93 人出席成立大会；134 人发起签名；"
            "约半数为民族工商业者 / 金融界代表 + 约半数文教界知识分子；"
            "L2 等级：民建中央官方公众号。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.thepaper.cn/newsDetail_forward_30245299",
        "uncertainty_note": "L1 升级需原件。",
    },
    # 民革中央 + 民盟中央 + 民建中央 + ... 8 党派中央直属出版社聚合
    {
        "candidate_id": "domestic:8P:8-dangpai-zhongyang-chubanshe",
        "title": "8 大民主党派中央主管出版社聚合锚点（团结 / 群言 / 中华工商时报 / 开明 / 中国医药科技 / 中国致公 / 学苑 / 台海）",
        "creator": "8 大民主党派中央委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "8 大民主党派中央直属出版社聚合",
        "repository_code": "8P",
        "repository_name": "8 大民主党派中央主管出版社",
        "collection_name": "各党派中央直属出版社",
        "archive_item": "https://www.toutiao.com/article/6660397680549691918",
        "catalog_reference": (
            "民革 → 团结出版社；民盟 → 群言出版社；"
            "民建 → 中华工商时报出版社；民进 → 开明出版社；"
            "农工 → 中国医药科技出版社；致公 → 中国致公出版社；"
            "九三 → 学苑出版社；台盟 → 台海出版社"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://www.toutiao.com/article/6660397680549691918",
        "source_url_role": "finding_aid",
        "access_mode": "open",
        "access_note": "各党派中央直属出版机构汇总",
        "medium": "hybrid",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "各党派中央直属出版社",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1945民盟一大", "1948民革成立香港", "1945民进成立上海", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟", "中国国民党革命委员会", "中国民主建国会", "中国民主促进会", "中国农工民主党", "中国致公党", "九三学社", "台湾民主自治同盟"],
        "place_tags": ["北京", "上海", "重庆", "南京", "广州", "昆明", "香港"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读今日头条汇总；"
            "8 大民主党派中央主办的出版社汇总；"
            "L2 等级：各党派中央直属出版。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.toutiao.com/article/6660397680549691918",
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
                    f"L2 needs_human_review 8 大民主党派中央出版社聚合（批次 J-4）；"
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