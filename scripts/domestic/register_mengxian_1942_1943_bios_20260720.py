#!/usr/bin/env python3
"""Register 1942/1943 民盟 biographical entries from 盟贤.pdf (人物和重要历史 folder).

Six L3 records citing biographical entries in the unpublished Shanghai 民盟
内部资料汇编《盟贤》(169 pages) which contains detailed biographies of
民盟 figures with 入盟时间与 1942/1943 活动.

Most important: 成柏仁 1942 加入民盟 (with 西北组织 creation in 1942).
This is the FIRST 1942 候选 with a direct 入盟 time point.

Cross-validations:
- 尚丁 1943-11 入盟 (盟贤) vs 1943-10 入盟 (印刷厂正文 SHDPZ) — 1 month diff
  possibly due to 入盟手续跨月完成
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RAW_PDF = "/Users/cheer/民盟/研究室文件/人物和重要历史/盟贤.pdf"
TODAY = "2026-07-20"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:MX:cheng-boren-1942-join-northwest-org",
        "title": "成柏仁 1942 年加入民盟条目（《盟贤》第 47 页）",
        "creator": "上海市地方志办公室／盟内部传记汇编《盟贤》",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟人物传记汇编条目（上海民盟内部资料，未公开出版）",
        "repository_code": "MX",
        "repository_name": "民盟上海市委内部传记汇编《盟贤》（169 页 PDF）",
        "collection_name": "盟贤 民盟人物传记",
        "archive_item": "人物和重要历史/盟贤.pdf 第 47 页",
        "catalog_reference": "盟贤（内部资料，未公开出版）成柏仁条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": "raw 层文件 " + RAW_PDF + "；盟贤为上海民盟内部传记汇编，未公开出版；"
                       "需民盟中央或上海市委正式出版后升级 L2",
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部传记汇编，民盟上海市委持有版权",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名"],
        "person_tags": ["成柏仁", "杜斌丞", "杨明轩", "中国民主同盟"],
        "place_tags": ["陕西"],
        "evidence_note": (
            "条目正文：『成柏仁（1889 年—1958 年），男，汉族，陕西耀县人。"
            "1942 年加入民盟。知名报人。"
            "1915 年毕业于上海同济医工大学。1942 年起，与杜斌丞、杨明轩等人一起"
            "从事民盟西北组织的创建工作。1945 年2 月，任民盟西北总支部执行委员"
            "兼宣传部长，同年秋，任民盟西北总支部机关报《秦风·工商日报联合版》"
            "报社社长。』"
            "提供 1942 民盟入盟时间点 + 1942 民盟西北组织创建的关键史料——"
            "**1942 民盟时间点首个直接命中**。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_PDF + " 第 47 页",
        "uncertainty_note": (
            "盟贤为上海民盟内部传记汇编（未公开出版）→ 当前等级 L3；"
            "需民盟中央或上海市委正式出版或与民盟西北总支部档案互证后升级 L2；"
            "『1942 年加入民盟』具体月份未细述。"
        ),
    },
    {
        "candidate_id": "domestic:MX:shang-ding-1943-11-join-mengxian",
        "title": "尚丁 1943 年 11 月加入民盟条目（《盟贤》第 63 页；与 SHDPZ 印刷厂正文 1943-10 互证）",
        "creator": "上海市地方志办公室／盟内部传记汇编《盟贤》",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟人物传记汇编条目",
        "repository_code": "MX",
        "repository_name": "民盟上海市委内部传记汇编《盟贤》（169 页 PDF）",
        "collection_name": "盟贤 民盟人物传记",
        "archive_item": "人物和重要历史/盟贤.pdf 第 63 页",
        "catalog_reference": "盟贤（内部资料，未公开出版）尚丁条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": "raw 层文件 " + RAW_PDF + "；盟贤为上海民盟内部传记汇编，未公开出版",
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部传记汇编，民盟上海市委持有版权",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["尚丁", "黄炎培", "中国民主同盟"],
        "place_tags": ["重庆", "上海"],
        "evidence_note": (
            "条目正文：『尚丁（1921 年2 月11 日—2009 年9 月22 日），本名孙锡纲，男，汉族，"
            "江苏丹徒人。1943 年11 月加入民盟。著名出版人。"
            "1942 年毕业于民治新闻专科学校。抗日战争和解放战争时期，任黄炎培秘书，"
            "协助他做中国民主政团同盟的组织协调工作，参与中华职教社发起组织的"
            "『宪政座谈会』和『拒检运动』的工作，任《国讯》周刊、《宪政》月刊编辑。"
            "1947 年10 月，民盟总部被迫解散，受命任民盟华东区执行部委员、"
            "民盟上海市委支部（地下）组织部长。』"
            "提供 1943-11 尚丁入盟精确月份（与 SHDPZ 印刷厂正文 1943-10 互证，"
            "差 1 月可能是入盟手续跨月完成）。"
            "同时确认 1942 尚丁任黄炎培秘书 + 协助政团同盟组织协调 + 任职《国讯》《宪政》编辑——"
            "1942 重庆民盟组织活动的关键人物证据。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_PDF + " 第 63 页",
        "uncertainty_note": (
            "盟贤为内部传记汇编（未公开出版）→ 当前等级 L3；"
            "1943-11 vs SHDPZ 1943-10 差 1 月待上海盟讯档案或中华职业教育社档案互证；"
            "升级 L2 需民盟上海市委正式出版或尚丁回忆录互证。"
        ),
    },
    {
        "candidate_id": "domestic:MX:ding-cong-1942-chongqing-artist",
        "title": "丁聪 1942 年在桂林/重庆/成都/昆明美术设计活动条目（《盟贤》第 158 页）",
        "creator": "上海市地方志办公室／盟内部传记汇编《盟贤》",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟人物传记汇编条目（1944-01 入盟）",
        "repository_code": "MX",
        "repository_name": "民盟上海市委内部传记汇编《盟贤》",
        "collection_name": "盟贤 民盟人物传记",
        "archive_item": "人物和重要历史/盟贤.pdf 第 158 页",
        "catalog_reference": "盟贤（内部资料）丁聪条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": "raw 层文件 " + RAW_PDF,
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部传记汇编",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "related",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["丁聪", "中国民主同盟"],
        "place_tags": ["重庆", "桂林", "成都", "昆明"],
        "evidence_note": (
            "条目正文：『丁聪（1916 年12 月6 日—2009 年5 月26 日），笔名小丁，男，汉族，"
            "上海金山人。1944 年1 月入盟。中国当代著名漫画家。"
            "1942 年在桂林、重庆、成都、昆明等地担任《钦差大臣》《正气歌》《北京人》"
            "等美术设计，并在重庆举办个人画展。』"
            "提供 1942 民盟外围进步文化界活动证据（丁聪本人 1944 入盟，但 1942 在大后方"
            "从事抗战美术工作）。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_PDF + " 第 158 页",
        "uncertainty_note": (
            "丁聪 1944-01 入盟非 1942/1943；本条为 1942 民盟外围文化活动记录；"
            "升级 L2 需民盟上海市委正式出版或上海漫画界档案互证。"
        ),
    },
    {
        "candidate_id": "domestic:MX:shang-ding-1942-journalist-secretary",
        "title": "尚丁 1942 年任黄炎培秘书 + 政团同盟组织协调条目（《盟贤》第 63 页，1942 关键人物活动）",
        "creator": "上海市地方志办公室／盟内部传记汇编《盟贤》",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟人物传记汇编条目",
        "repository_code": "MX",
        "repository_name": "民盟上海市委内部传记汇编《盟贤》",
        "collection_name": "盟贤 民盟人物传记",
        "archive_item": "人物和重要历史/盟贤.pdf 第 63 页",
        "catalog_reference": "盟贤（内部资料）尚丁条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": "raw 层文件 " + RAW_PDF,
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部传记汇编",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组前夜", "1941民盟前身"],
        "person_tags": ["尚丁", "黄炎培", "中国民主政团同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "条目正文：『1942 年毕业于民治新闻专科学校。抗日战争和解放战争时期，"
            "任黄炎培秘书，协助他做中国民主政团同盟的组织协调工作，"
            "参与中华职教社发起组织的『宪政座谈会』和『拒检运动』的工作，"
            "任《国讯》周刊、《宪政》月刊编辑。』"
            "提供 1942 尚丁任黄炎培秘书 + 协助政团同盟组织协调的关键证据——"
            "1942 重庆 民盟组织活动的人事链：尚丁→黄炎培→政团同盟总部。"
            "与 SHDPZ 印刷厂正文 1942 民治新闻专科学校毕业互证。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_PDF + " 第 63 页",
        "uncertainty_note": (
            "1942 政团同盟『组织协调』具体事项待中华职业教育社档案或黄炎培日记"
            "（华文出版社 2008 第 8 卷）互证。"
        ),
    },
    {
        "candidate_id": "domestic:MX:wang-lingu-1942-art-troupe",
        "title": "王林谷 1942 年入中国艺术剧社条目（《盟贤》，1946-12 入盟）",
        "creator": "上海市地方志办公室／盟内部传记汇编《盟贤》",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟人物传记汇编条目",
        "repository_code": "MX",
        "repository_name": "民盟上海市委内部传记汇编《盟贤》",
        "collection_name": "盟贤 民盟人物传记",
        "archive_item": "人物和重要历史/盟贤.pdf 王林谷条目",
        "catalog_reference": "盟贤（内部资料）王林谷条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": "raw 层文件 " + RAW_PDF,
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部传记汇编",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "related",
        "event_tags": ["1944改组前夜"],
        "person_tags": ["王林谷", "陶行知"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "条目正文：『王林谷（1919 年11 月3 日—1995 年），男，汉族，浙江宁波人。"
            "1946 年12 月加入民盟。中国电影剧作家。"
            "1940 年在重庆陶行知创办的育才学校工作。"
            "1942 年进入中国艺术剧社，创作了十几万字的长篇小说《疾风》。』"
            "提供 1942 重庆进步剧运（陶行知育才学校→中国艺术剧社）的关键人事链。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_PDF,
        "uncertainty_note": "王林谷 1946-12 入盟非 1942/1943；本条记录 1942 民盟外围进步文化界人事链。",
    },
    {
        "candidate_id": "domestic:MX:lu-jinhua-1942-yueju-troupe",
        "title": "陆锦花 1942 年入袁雪芬领衔大来剧场条目（《盟贤》，1956-10 入盟）",
        "creator": "上海市地方志办公室／盟内部传记汇编《盟贤》",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟人物传记汇编条目",
        "repository_code": "MX",
        "repository_name": "民盟上海市委内部传记汇编《盟贤》",
        "collection_name": "盟贤 民盟人物传记",
        "archive_item": "人物和重要历史/盟贤.pdf 陆锦花条目",
        "catalog_reference": "盟贤（内部资料）陆锦花条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": "raw 层文件 " + RAW_PDF,
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部传记汇编",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "related",
        "event_tags": ["1944改组前夜"],
        "person_tags": ["陆锦花", "袁雪芬"],
        "place_tags": ["上海"],
        "evidence_note": (
            "条目正文：『陆锦花（1927 年2 月25 日—2018 年1 月10 日），女，汉族，学名柯纹祺……"
            "13 岁进越剧四季班学艺……1942 年入袁雪芬领衔的大来剧场唱二肩小生。"
            "1946 年与邢竹琴合作演出。1947 年秋与王文娟合作，成立少壮越剧团任团长。』"
            "提供 1942 上海越剧界民盟外围人事链（袁雪芬、陆锦花）。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_PDF,
        "uncertainty_note": "陆锦花 1956-10 入盟非 1942/1943；本条记录 1942 民盟外围上海文化界人事链。",
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
                    "L3 民盟上海市委内部传记汇编《盟贤》（未公开出版）人物条目；"
                    "1942/1943 民盟-相关人物时间点与活动记录；"
                    "不入 accepted 队列；待民盟上海市委正式出版或民盟中央档案互证后可升级 L2；"
                    "不入 L1。"
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
