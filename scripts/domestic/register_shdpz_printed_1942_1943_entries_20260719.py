#!/usr/bin/env python3
"""Register 1942–1943 Min Meng entries from 印刷厂 党派分志验收稿正文 (Shanghai gazetteer body, 2020).

Three L3 records citing biographical entries in the unpublished Shanghai
民主党派志 acceptance manuscript (印刷厂 党派分志验收稿正文 20200701) that
provide concrete 1942 / 1943 Min Meng membership / relationship milestones
with monthly precision (e.g. 尚丁 1943-10 加入中国民主同盟).

Compared to 资料长编 (research compilation), 印刷厂 党派分志验收稿正文 is
the formal gazetteer body — closer to L2 quality but still unpublished.
We classify as L3 (unpublished finding aid) until the Shanghai Gazetteer
Office publishes.

Cross-verification opportunity: 尚丁 1943-10 (printed gazetteer) ↔ 尚丁 1943
(资料长编) — exact-month refinement possible.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RAW_PDF = "/Users/cheer/民盟/研究室文件/党派分志20200708/印刷厂 党派分志验收稿正文20200701.pdf"
TODAY = "2026-07-19"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:SHDPZ:printed-page816-su-yanbin-1943-11-join",
        "title": "苏延宾 1943 年 11 月参加中国民主同盟条目（《上海民主党派志》印刷厂验收稿正文）",
        "creator": "上海市地方志办公室／民主党派分志验收稿",
        "document_date": "2020-07-01",
        "document_date_precision": "day",
        "document_type": "上海民主党派志印刷厂验收稿正文收录的苏延宾入盟时间条目",
        "repository_code": "SHDPZ",
        "repository_name": "上海市地方志办公室／上海民主党派志验收稿",
        "collection_name": "上海民主党派志 印刷厂验收稿正文 第二篇 中国民主同盟 人物传略",
        "archive_item": "印刷厂 党派分志验收稿正文20200701.pdf 第816页",
        "catalog_reference": "上海民主党派志验收稿（2020-07，未出版）印刷厂正文 第二篇 民盟 人物传略 苏延宾条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": (
            "raw 层文件 " + RAW_PDF + " 第816页；"
            "验收稿未公开出版；"
            "需上海市地方志办公室正式出版后升级 L2"
        ),
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部验收稿，上海市地方志办公室持有版权",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["苏延宾", "中国民主同盟"],
        "place_tags": ["上海"],
        "evidence_note": (
            "条目正文：『苏延宾（1909.10—1993.9）……1943 年11 月，参加中国民主同盟。"
            "1948 年成立民盟上海执行部，任委员兼秘书主任。解放前夕开展护厂活动。"
            "1949 年1 月被上海淞沪警备司令部逮捕，后经营救获释转道香港去北京。』"
            "提供 1943-11 苏延宾加入民盟的精确月份节点，及 1948 民盟上海执行部关键人事信息。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_PDF + " 第816页",
        "uncertainty_note": (
            "验收稿未公开出版；1943-11 月份精度由印刷厂正文提供（vs 资料长编可能仅 1943）；"
            "1948 民盟上海执行部人事信息需与民盟中央档案互证。"
        ),
    },
    {
        "candidate_id": "domestic:SHDPZ:printed-page840-shang-ding-1943-10-join",
        "title": "尚丁 1943 年 10 月加入中国民主同盟条目（《上海民主党派志》印刷厂验收稿正文）",
        "creator": "上海市地方志办公室／民主党派分志验收稿",
        "document_date": "2020-07-01",
        "document_date_precision": "day",
        "document_type": "上海民主党派志印刷厂验收稿正文收录的尚丁入盟时间条目（精确到月）",
        "repository_code": "SHDPZ",
        "repository_name": "上海市地方志办公室／上海民主党派志验收稿",
        "collection_name": "上海民主党派志 印刷厂验收稿正文 第二篇 中国民主同盟 人物传略",
        "archive_item": "印刷厂 党派分志验收稿正文20200701.pdf 第840页",
        "catalog_reference": "上海民主党派志验收稿（2020-07，未出版）印刷厂正文 第二篇 民盟 人物传略 尚丁条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": (
            "raw 层文件 " + RAW_PDF + " 第840页；"
            "验收稿未公开出版；"
            "需上海市地方志办公室正式出版后升级 L2"
        ),
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部验收稿，上海市地方志办公室持有版权",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["尚丁", "黄炎培", "中国民主同盟"],
        "place_tags": ["上海"],
        "evidence_note": (
            "条目正文：『尚丁（1921.1—2009.9）……1938 年8 月考入军委会战时干部训练团，"
            "1939 年5 月毕业。1941 年7 月，参加由郭沫若、田汉领导的铁血剧团。"
            "1942 年民治新闻专科学校毕业，参加中华职业教育社，担任《国迅》杂志编辑、"
            "《宪政》月刊编辑，1944 年9 月加入中国人民救国会，1945 年任国迅书店经理、"
            "民盟机关报《民主报》经理兼社论委员……1943 年10 月加入中国民主同盟。』"
            "提供 1943-10 尚丁加入民盟的精确月份节点（资料长编 SHDPZ 写『1943』无月份，"
            "印刷厂正文补足至 1943-10）。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_PDF + " 第840页",
        "uncertainty_note": (
            "验收稿未公开出版；1943-10 月份精度由印刷厂正文提供；"
            "需以中华职业教育社档案或尚丁本人回忆录互证。"
        ),
    },
    {
        "candidate_id": "domestic:SHDPZ:printed-page820-zhou-gucheng-federation-consultant-1942",
        "title": "周谷城 1942 年后被聘为民主政团同盟顾问条目（《上海民主党派志》印刷厂验收稿正文）",
        "creator": "上海市地方志办公室／民主党派分志验收稿",
        "document_date": "2020-07-01",
        "document_date_precision": "day",
        "document_type": "上海民主党派志印刷厂验收稿正文收录的周谷城聘为民主政团同盟顾问条目",
        "repository_code": "SHDPZ",
        "repository_name": "上海市地方志办公室／上海民主党派志验收稿",
        "collection_name": "上海民主党派志 印刷厂验收稿正文 第二篇 中国民主同盟 人物传略",
        "archive_item": "印刷厂 党派分志验收稿正文20200701.pdf 第820页",
        "catalog_reference": "上海民主党派志验收稿（2020-07，未出版）印刷厂正文 第二篇 民盟 人物传略 周谷城条目",
        "catalog_reference_status": "unpublished",
        "access_mode": "offline",
        "access_note": (
            "raw 层文件 " + RAW_PDF + " 第820页；"
            "验收稿未公开出版；"
            "需上海市地方志办公室正式出版后升级 L2"
        ),
        "medium": "digital",
        "online_availability": "not_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "内部验收稿，上海市地方志办公室持有版权",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组前夜"],
        "person_tags": ["周谷城", "中国民主政团同盟"],
        "place_tags": ["重庆", "上海"],
        "evidence_note": (
            "条目正文：『周谷城（1898.9—1996.11）……1933 年，任暨南大学教授兼历史社会系主任。"
            "1942 年后，任复旦大学教授兼历史系主任和教务长。抗战期间创办社会科学讲习所，"
            "向沦陷区青年宣传爱国主义思想，被日伪机关监视后遭逮捕。保释后，赴重庆复旦大学任教，"
            "被聘为民主政团同盟顾问。』"
            "提供 1942 后周谷城被聘为民主政团同盟顾问的关键节点——民盟早期核心顾问层扩展线索。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "raw/" + RAW_PDF + " 第820页",
        "uncertainty_note": (
            "验收稿未公开出版；"
            "『聘为顾问』具体年份（1942/1943/1944）需对照复旦校史与民盟中央档案确认；"
            "周谷城后任民盟上海市委主委（1980 年）职位见现有 event_coverage。"
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
                    "L3 上海民主党派志印刷厂验收稿正文（未出版）人物传略条目；"
                    "提供 1942/1943 民盟-相关人物时间点（精确到月）；"
                    "不入 accepted 队列；待上海市地方志办公室正式出版或 1983 历史文献"
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
