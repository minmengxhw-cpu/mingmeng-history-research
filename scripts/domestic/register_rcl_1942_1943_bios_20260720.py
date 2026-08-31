#!/usr/bin/env python3
"""Register 1942/1943 民盟 biographical entries from 民盟代表人士资料汇编 5 篇.

Two new L3 records citing direct 1942/1943 入盟 entries in the 上海民主党派志
资料汇编 (representative personnel compilation) which is part of the
上海地方志办公室 approved but unpublished compilation.

Most important: 刘良模 1942 加入民盟 + 推广《义勇军进行曲》(national anthem).
This is a SIGNIFICANT 1942 民盟-相关 figure previously not captured.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RAW_BASE = "<local-user>/民盟/研究室文件/党派分志20200708/民盟代表人士资料汇编"
TODAY = "2026-07-20"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:RCL:wenliangmo-1942-join-national-anthem",
        "title": "刘良模 1942 年加入民盟条目（《民盟代表人士资料汇编·文化篇》）",
        "creator": "上海市地方志办公室／民盟代表人士资料汇编",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "上海民主党派志验收稿·代表人士资料汇编（文化篇）",
        "repository_code": "RCL",
        "repository_name": "上海市地方志办公室／民盟代表人士资料汇编",
        "collection_name": "民盟代表人士资料汇编·文化篇",
        "archive_item": RAW_BASE + "/文化篇.docx 刘良模条目",
        "catalog_reference": "上海民主党派志验收稿（2020，未出版）民盟代表人士资料汇编·文化篇·刘良模",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": "raw 层文件 " + RAW_BASE + "/文化篇.docx；验收稿未公开出版",
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部验收稿，上海市地方志办公室持有版权",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组前夜", "1941民盟前身"],
        "person_tags": ["刘良模", "聂耳", "田汉", "中国民主同盟"],
        "place_tags": ["上海", "重庆"],
        "evidence_note": (
            "条目正文：『1932 年毕业于沪江大学社会学系。"
            "1942 年加入民盟。积极领导民众传唱国歌凝聚国魂，"
            "推动宣传中国人民英勇抗日的事迹。"
            "1949 年9 月21 日，第一届中国人民政治协商会议召开，"
            "《义勇军进行曲》被确定为中华人民共和国国歌。"
            "刘良模对《义勇军进行曲》的广泛传唱，作出巨大贡献。』"
            "提供 1942 民盟-直接命中：民盟盟员 + 抗战时期推动国歌传唱。"
            "刘良模是 1942 民盟在文化战线的关键人物证据。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_BASE + "/文化篇.docx",
        "uncertainty_note": (
            "验收稿未公开出版→当前等级 L3；"
            "需上海市地方志办公室正式出版或与刘良模档案互证后升级 L2；"
            "1942 入盟具体月份待考。"
        ),
    },
    {
        "candidate_id": "domestic:RCL:textile-engineer-1943-12-join",
        "title": "纺织工程专家 1943 年 12 月加入民盟条目（《民盟代表人士资料汇编·科技篇》）",
        "creator": "上海市地方志办公室／民盟代表人士资料汇编",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "上海民主党派志验收稿·代表人士资料汇编（科技篇）",
        "repository_code": "RCL",
        "repository_name": "上海市地方志办公室／民盟代表人士资料汇编",
        "collection_name": "民盟代表人士资料汇编·科技篇",
        "archive_item": RAW_BASE + "/科技篇.docx 纺织工程专家条目",
        "catalog_reference": "上海民主党派志验收稿（2020，未出版）民盟代表人士资料汇编·科技篇",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": "raw 层文件 " + RAW_BASE + "/科技篇.docx；验收稿未公开出版",
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部验收稿，上海市地方志办公室持有版权",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["重庆", "上海"],
        "evidence_note": (
            "条目正文：『1943 年12 月加入民盟。"
            "参与发起组建中国纺织事业协进会，创立《纺织通报》《染整通报》"
            "等刊物，建立纺织图书馆，编撰《英汉纺织辞典》。』"
            "提供 1943-12 民盟-直接命中（科技界人士入盟）+ 纺织工业组线索。"
            "科技篇条目未注明姓名（资料汇编匿名化或待核全名）。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_BASE + "/科技篇.docx",
        "uncertainty_note": (
            "验收稿未公开出版→当前等级 L3；"
            "纺织工程专家姓名未在资料汇编中出现（可能因汇编匿名化或抄录遗漏）；"
            "需上海市地方志办公室正式出版或与纺织事业协进会档案互证后升级 L2；"
            "1943-12 月份精度待核。"
        ),
    },
    {
        "candidate_id": "domestic:RCL:qian-weichang-1942-phd-meng-vice-chairman",
        "title": "钱伟长 1942 年获多伦多大学博士学位条目（《民盟代表人士资料汇编·领导篇》，1952 入盟，1983-1996 民盟中央副主席）",
        "creator": "上海市地方志办公室／民盟代表人士资料汇编",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "上海民主党派志验收稿·代表人士资料汇编（领导篇）",
        "repository_code": "RCL",
        "repository_name": "上海市地方志办公室／民盟代表人士资料汇编",
        "collection_name": "民盟代表人士资料汇编·领导篇",
        "archive_item": RAW_BASE + "/领导篇.docx 钱伟长条目",
        "catalog_reference": "上海民主党派志验收稿（2020，未出版）民盟代表人士资料汇编·领导篇·钱伟长",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": "raw 层文件 " + RAW_BASE + "/领导篇.docx；验收稿未公开出版",
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部验收稿，上海市地方志办公室持有版权",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名"],
        "person_tags": ["钱伟长", "中国民主同盟"],
        "place_tags": ["重庆", "上海", "多伦多"],
        "evidence_note": (
            "条目正文：『1935 年毕业于清华大学物理系，"
            "1942 年获多伦多大学博士学位。"
            "1952 年加入民盟。1983 年12 月至1996 年11 月任民盟中央副主席。"
            "1992 年12 月至2007 年11 月任民盟中央名誉主席。"
            "创办中国第一个力学系。』"
            "提供 1942 钱伟长获多伦多大学博士学位的关键时点（已有事件 1942 时间点+人物背景）；"
            "钱伟长本人 1952 入盟（晚），但作为民盟中央副主席（1983-1996）和名誉主席，"
            "1942 学位年是关键民盟领导人早期经历。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_BASE + "/领导篇.docx",
        "uncertainty_note": (
            "钱伟长 1942 是学位年非入盟年；本条作为 1942 民盟领导人早期背景；"
            "与现有 钱宝钧 SHDPZ 印刷厂 L3 记录（1942 重返成都金陵大学）+ 资料长编 L3"
            "钱伟长博士毕业到美国 + 印刷厂正文钱伟长条目互证。"
        ),
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
                    "L3 民盟代表人士资料汇编（验收稿未公开出版）人物条目；"
                    "1942/1943 民盟-相关人物时间点与活动记录；"
                    "不入 accepted 队列；待上海市地方志办公室正式出版或人物档案互证后可升级 L2。"
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
        {"added": added, "skipped": skipped, "applied": args.apply, "total_records": len(rows)},
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
