#!/usr/bin/env python3
"""Register 1942–1943 Min Meng–related entries from 上海民主党派志资料长编.

This adds three L3 (unpublished compilation / finding aid) records citing
concrete 1942 / 1943 民盟-相关 biographical entries found in the Shanghai
Democratic Parties Gazetteer manuscript (党派分志验收稿 资料长编).

Raw layer path (read-only):
    /Users/cheer/民盟/研究室文件/党派分志20200708/资料长编/
        民盟 第五章 20201018.doc   (史良)
        民盟 人物 20201018.doc      (尚丁, 刘思慕)

Local text extracts (used as evidence_locator pointers, not surrogates):
    /tmp/zlc_民盟 第五章 20201018.txt
    /tmp/zlc_民盟 人物 20201018.txt

Each record is L3 (formally compiled but unpublished) with
review_status = "needs_human_review". Upgrade to L2 requires Shanghai
Gazetteer Office official publication; upgrade to L1 requires primary
archival cross-verification (out of scope per 资料长编 alone).

This script does NOT change the 1942 / 1943 zero-candidate baseline
of accepted records — those are still missing primary sources. It adds
research-aid anchors that future page-image or published-gazetteer hits
can hang from.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RAW_BASE = "/Users/cheer/民盟/研究室文件/党派分志20200708/资料长编"
TXT_BASE = "/tmp"
TODAY = "2026-07-19"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:SHDPZ:zlc-chapter5-line571-shi-liang-1942-join",
        "title": "史良 1942 年加入民盟条目（《上海民主党派志》资料长编 第五章）",
        "creator": "上海市地方志办公室／民主党派分志验收稿",
        "document_date": "2020-10-18",
        "document_date_precision": "day",
        "document_type": "上海民主党派志验收稿资料长编收录的史良入盟时间条目",
        "repository_code": "SHDPZ",
        "repository_name": "上海市地方志办公室／上海民主党派志验收稿",
        "collection_name": "上海民主党派志 资料长编 第五章 民盟代表人士",
        "archive_item": "资料长编/民盟 第五章 20201018.doc 第571行",
        "catalog_reference": "上海民主党派志验收稿（2020，未出版）资料长编 第五章 民盟代表人士 史良条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": (
            "raw 层文件 " + RAW_BASE + "/民盟 第五章 20201018.doc；"
            "验收稿未公开出版；本地转换文本 " + TXT_BASE + "/zlc_民盟 第五章 20201018.txt；"
            "需上海市地方志办公室正式出版后升级 L2"
        ),
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部验收稿，上海市地方志办公室持有版权；引用需注明出处",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["史良", "中国民主同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "条目正文：『史良是著名救国会七君子中唯一女性。1942年加入民盟，"
            "1945年起任民盟中央委员、常委。民盟总部被迫解散后，她担任民盟华东"
            "执行部主任委员，指导并资助民盟华东地区的地下斗争。』"
            "提供 1942 年史良加入民盟的关键节点。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": (
            "raw/" + RAW_BASE + "/民盟 第五章 20201018.doc 第571行；"
            "本地转换文本 /tmp/zlc_民盟 第五章 20201018.txt 第571行"
        ),
        "uncertainty_note": (
            "验收稿为内部未出版稿，需上海市地方志办公室正式出版后才能升级 L2；"
            "1942 年具体月份、介绍人、入盟手续等需对照民盟中央档案（重庆）"
            "确认；现仅作检索词来源与事件时间点线索，不作 L1。"
        ),
    },
    {
        "candidate_id": "domestic:SHDPZ:zlc-characters-line527-shang-ding-1943-join",
        "title": "尚丁 1943 年参加中国民主同盟条目（《上海民主党派志》资料长编 人物）",
        "creator": "上海市地方志办公室／民主党派分志验收稿",
        "document_date": "2020-10-18",
        "document_date_precision": "day",
        "document_type": "上海民主党派志验收稿资料长编收录的尚丁入盟时间条目",
        "repository_code": "SHDPZ",
        "repository_name": "上海市地方志办公室／上海民主党派志验收稿",
        "collection_name": "上海民主党派志 资料长编 人物 民盟代表人士",
        "archive_item": "资料长编/民盟 人物 20201018.doc 第527行",
        "catalog_reference": "上海民主党派志验收稿（2020，未出版）资料长编 人物 民盟代表人士 尚丁条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": (
            "raw 层文件 " + RAW_BASE + "/民盟 人物 20201018.doc；"
            "验收稿未公开出版；本地转换文本 " + TXT_BASE + "/zlc_民盟 人物 20201018.txt；"
            "需上海市地方志办公室正式出版后升级 L2"
        ),
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部验收稿，上海市地方志办公室持有版权；引用需注明出处",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["尚丁", "黄炎培", "中国民主同盟"],
        "place_tags": ["上海", "重庆"],
        "evidence_note": (
            "条目正文：『尚丁，本名孙锡纲，江苏丹徒人，1943年参加中国民主同盟，"
            "曾任黄炎培秘书，民盟中央委员，民盟上海市委常委、副主委，"
            "第六届上海市政协委员，第七届上海市政协常委，中华职教社第五、六届理事。』"
            "提供 1943 年尚丁入盟的关键节点与民盟组织线索。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": (
            "raw/" + RAW_BASE + "/民盟 人物 20201018.doc 第527行；"
            "本地转换文本 /tmp/zlc_民盟 人物 20201018.txt 第527行"
        ),
        "uncertainty_note": (
            "验收稿为内部未出版稿，需上海市地方志办公室正式出版后才能升级 L2；"
            "1943 年具体月份、入盟手续尚需对照民盟中央档案（重庆）确认；"
            "现仅作检索词来源与事件时间点线索，不作 L1。"
        ),
    },
    {
        "candidate_id": "domestic:SHDPZ:zlc-characters-line79-liu-simou-1942-return",
        "title": "刘思慕 1942 年春回国条目（《上海民主党派志》资料长编 人物）",
        "creator": "上海市地方志办公室／民主党派分志验收稿",
        "document_date": "2020-10-18",
        "document_date_precision": "day",
        "document_type": "上海民主党派志验收稿资料长编收录的刘思慕 1942 年春回国条目",
        "repository_code": "SHDPZ",
        "repository_name": "上海市地方志办公室／上海民主党派志验收稿",
        "collection_name": "上海民主党派志 资料长编 人物 民盟代表人士",
        "archive_item": "资料长编/民盟 人物 20201018.doc 第79行",
        "catalog_reference": "上海民主党派志验收稿（2020，未出版）资料长编 人物 民盟代表人士 刘思慕条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": (
            "raw 层文件 " + RAW_BASE + "/民盟 人物 20201018.doc；"
            "验收稿未公开出版；本地转换文本 " + TXT_BASE + "/zlc_民盟 人物 20201018.txt；"
            "需上海市地方志办公室正式出版后升级 L2"
        ),
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部验收稿，上海市地方志办公室持有版权；引用需注明出处",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["刘思慕", "中国民主同盟"],
        "place_tags": ["重庆", "上海"],
        "evidence_note": (
            "条目正文：『1938年秋，刘思慕赴香港，在胡愈之等创办的国际新闻社香港分社"
            "担任国际问题方面专栏作家，同时为迁港的《世界知识》写稿。"
            "1940夏，应邀去印度尼西亚的雅加达担任华侨报纸《天声日报》主笔。"
            "1942年春回国后，他先后任《力报》、《广西日报》总主笔，"
            "撰写的《敌寇的动向》、《第二战场的谜》等军事论文和国内国际系列战局评述，"
            "备受各方关注，在国内名噪一时。』"
            "提供 1942 年春刘思慕回国的关键节点（后任民盟上海市支部临工会委员，"
            "1950 年因故未到职）。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": (
            "raw/" + RAW_BASE + "/民盟 人物 20201018.doc 第79行；"
            "本地转换文本 /tmp/zlc_民盟 人物 20201018.txt 第79行"
        ),
        "uncertainty_note": (
            "验收稿为内部未出版稿，需上海市地方志办公室正式出版后才能升级 L2；"
            "刘思慕 1942 回国后是否当年加入民盟需对照民盟中央档案确认；"
            "现仅作 1942 时间点与人物活动线索，不作 L1。"
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
                    "L3 上海民主党派志验收稿（未出版）资料长编记录级；"
                    "提供 1942/1943 民盟-相关人物时间点线索；"
                    "不入 core accepted 队列；待上海市地方志办公室正式出版或 1983 历史文献"
                    "互证后可升级 L2；不入 L1。"
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
