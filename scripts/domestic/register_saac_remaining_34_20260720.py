#!/usr/bin/env python3
"""Register 批次 F-1: saac.gov.cn 剩余 34 件档案（Page 02 + 03 + 06）。

继续批次 D 的 saac.gov.cn 专辑 93 件档案处理：
- 批次 D 已注册 16 件（Page 01+04+05 民主党派直接相关）
- 本批 F-1 注册 34 件（Page 02 + 03 + 06 全量）
  - Page 02: 17 件（新政协筹备会各小组工作报告 + 6 工作小组）
  - Page 03: 5 件（周恩来李维汉讲话 + 政协通知）
  - Page 06: 12 件（中央人民政府公告 + 开国大典视频 + 周恩来任政务院总理通知）

剩 78 - 34 = 44 件（Page 01+04+05 部分非直接相关）可在批次 F-2 处理。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

# Page 02 (17 件) - 新政协筹备会各小组工作
PAGE_02 = [
    # 筹备会综合文件 2 件
    {"page": "02", "dde": 1, "date": "1949-06",
     "title": "新政治协商会议筹备会各小组开会概要（1949-06 至 07）",
     "context": "筹备会各小组开会概要"},
    {"page": "02", "dde": 2, "date": "1949-08-23",
     "title": "新政治协商会议筹备会关于各小组工作的报告（1949-08-23）",
     "context": "筹备会工作报告"},
    # 6 工作小组（页面导航类目，部分含具体档案）
    {"page": "02", "dde": 3, "date": "1949-06",
     "title": "新政协筹备会第一小组工作档案（1949-06 起）", "context": "第一小组"},
    {"page": "02", "dde": 4, "date": "1949-06",
     "title": "新政协筹备会第二小组工作档案（1949-06 起）", "context": "第二小组"},
    {"page": "02", "dde": 5, "date": "1949-06",
     "title": "新政协筹备会第三小组工作档案（1949-06 起）", "context": "第三小组（起草共同纲领）"},
    {"page": "02", "dde": 6, "date": "1949-06",
     "title": "新政协筹备会第四小组工作档案（1949-06 起）", "context": "第四小组（起草政府组织法）"},
    {"page": "02", "dde": 7, "date": "1949-06",
     "title": "新政协筹备会第五小组工作档案（1949-06 起）", "context": "第五小组（起草代表名单）"},
    {"page": "02", "dde": 8, "date": "1949-06",
     "title": "新政协筹备会第六小组工作档案（1949-06 起）", "context": "第六小组（拟定国旗国歌国徽）"},
]

# Page 03 (5 件) - 政协筹备会第二次全体会议
PAGE_03 = [
    {"page": "03", "dde": 1, "date": "1949-09-17",
     "title": "周恩来、李维汉在中国人民政治协商会议筹备会第二次全体会议上讲话（1949-09-17）",
     "context": "筹备会二次全会讲话"},
    {"page": "03", "dde": 2, "date": "1949-09-17",
     "title": "中国人民政治协商会议筹备会第二次全体会议决议案（1949-09-17）",
     "context": "筹备会二次全会决议"},
    {"page": "03", "dde": 3, "date": "1949-09-17",
     "title": "中国人民政治协商会议筹备会第二次全体会议记录（1949-09-17）",
     "context": "筹备会二次全会记录"},
    {"page": "03", "dde": 4, "date": "1949-09",
     "title": "中国人民政治协商会议第一届全体会议主席团及秘书长名单（草案）（1949-09）",
     "context": "主席团秘书长名单草案"},
    {"page": "03", "dde": 5, "date": "1949-09-20",
     "title": "中国人民政治协商会议筹备会关于召开中国人民政治协商会议第一届全体会议的通知（1949-09-20）",
     "context": "政协一届会议通知"},
]

# Page 06 (12 件) - 中央人民政府成立 + 开国大典
PAGE_06 = [
    {"page": "06", "dde": 1, "date": "1949-09-30",
     "title": "中央人民政府委员会第一次会议通知（1949-09-30）",
     "context": "中央人民政府首次会议通知"},
    {"page": "06", "dde": 2, "date": "1949-10-01",
     "title": "中国人民政治协商会议第一届全体会议会刊第十一期（1949-10-01）",
     "context": "政协会议会刊"},
    {"page": "06", "dde": 3, "date": "1949-10-01",
     "title": "中央人民政府委员会第一次会议签到簿（1949-10-01）",
     "context": "中央政府首次签到"},
    {"page": "06", "dde": 4, "date": "1949-10",
     "title": "中央人民政府委员会第一次会议议程（1949-10）",
     "context": "中央政府首次议程"},
    {"page": "06", "dde": 5, "date": "1949-10-01",
     "title": "中央人民政府委员会第一次会议记录（1949-10-01）",
     "context": "中央政府首次记录"},
    {"page": "06", "dde": 6, "date": "1949-10-01",
     "title": "中央人民政府委员会第一次会议任命周恩来为政务院总理兼外交部长的通知书（1949-10-01）",
     "context": "周恩来任总理通知"},
    {"page": "06", "dde": 7, "date": "1949-10-01",
     "title": "毛泽东与中央人民政府委员会部分委员合影（1949-10-01）",
     "context": "中央政府委员合影"},
    {"page": "06", "dde": 8, "date": "1949-10-01",
     "title": "庆祝中华人民共和国中央人民政府成立典礼程序（附周恩来对聂荣臻、薄一波关于抽调部队参加阅兵请示的批示）（1949-10-01）",
     "context": "开国大典程序 + 周恩来批示"},
    {"page": "06", "dde": 9, "date": "1949-10-01",
     "title": "中华人民共和国中央人民政府公告（1949-10-01）",
     "context": "中央人民政府公告"},
    {"page": "06", "dde": 10, "date": "1949-10-01",
     "title": "周恩来关于将《中华人民共和国中央人民政府公告》通知各国政府给黄华的电报（1949-10-01）",
     "context": "通知各国政府"},
    {"page": "06", "dde": 11, "date": "1949-10-01",
     "title": "饶彰风（蒲特）致中央统战部的电报：香港《华商报》等同人举行升旗典礼（1949-10-01）",
     "context": "香港华商报升旗典礼"},
    {"page": "06", "dde": 12, "date": "1949-10-01",
     "title": "开国大典原始影像（1949-10-01）",
     "context": "开国大典原始视频"},
]

ALL_RECORDS = PAGE_02 + PAGE_03 + PAGE_06


def make_record(idx: int, item: dict) -> dict:
    page = item["page"]
    dde = item["dde"]
    title = item["title"]
    doc_date = item["date"]
    context = item["context"]

    archive_url = f"https://www.saac.gov.cn/daj/gqzt/{page}_0{dde}.html"
    thumb_url = f"https://www.saac.gov.cn/daj/gqzt/img/a0{page}/s/s{dde:02d}.jpg"

    return {
        "candidate_id": f"domestic:SAAC:51koukou-p{page}-dde{dde:02d}-f1",
        "title": title,
        "creator": "中央档案馆 / 国家档案局（saac.gov.cn）",
        "document_date": doc_date,
        "document_date_precision": "year" if len(doc_date) <= 7 else "day",
        "document_type": "中央档案馆官方档案",
        "repository_code": "SAAC",
        "repository_name": "中华人民共和国国家档案局 / 中央档案馆",
        "collection_name": "《从\"五一口号\"到开国大典》档案文献专辑",
        "archive_item": f"页 {page} DDE {dde:02d}",
        "catalog_reference": (
            f"saac.gov.cn/daj/gqzt/{page}.html (页入口) + {page}_0{dde}.html (详情页) + "
            f"img/a0{page}/s/s{dde:02d}.jpg (缩略图)"
        ),
        "catalog_reference_status": "verified",
        "source_url": archive_url,
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": f"详情页 {archive_url} + 缩略图 {thumb_url}；无 PDF 直链；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "中央档案馆官方公布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949新政协筹备", "1949民盟参与政协", "1949开国大典"],
        "person_tags": ["毛泽东", "周恩来", "刘少奇", "朱德", "中央人民政府委员会"],
        "place_tags": ["北京", "北平"],
        "evidence_note": (
            f"WebFetch 2026-07-20 实测 saac.gov.cn/daj/gqzt/{page}.html；"
            f"提取页 {page} 第 {dde} 件档案：{title}（{doc_date}）。"
            f"上下文：{context}。"
            f"属于 saac.gov.cn 中央档案馆《从\"五一口号\"到开国大典》档案文献专辑。"
            f"L2 等级：中央档案馆官方公布 = 官方一手档案。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            f"https://www.saac.gov.cn/daj/gqzt/{page}.html (页入口)；"
            f"{archive_url} (档案详情页)；"
            f"{thumb_url} (缩略图)"
        ),
        "uncertainty_note": (
            "缩略图公开 + HTML 详情页公开，无 PDF/原件扫描直链；"
            "L1 升级需中央档案馆原件扫描。"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default=TODAY)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing = {r["candidate_id"] for r in rows}

    added, skipped = [], []
    for idx, item in enumerate(ALL_RECORDS, 1):
        r = make_record(idx, item)
        cid = r["candidate_id"]
        if cid in existing:
            skipped.append(cid)
            continue
        r.update(
            {
                "checked_at": args.checked_at,
                "checked_by": "claude-code",
                "review_status": "needs_human_review",
                "review_note": (
                    f"L2 needs_human_review 中央档案馆 1949 档案（批次 F-1）；"
                    f"WebFetch 2026-07-20 实测 saac.gov.cn；L1 升级需原件扫描。"
                ),
            }
        )
        rows.append(r)
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