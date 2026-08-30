#!/usr/bin/env python3
"""Register 批次 I-3: saac.gov.cn 剩余 17 件民主党派相关档案。

WebFetch 2026-07-21 实测，已注册 41/93；剩余 ~44 件中筛民主党派直接相关：

Page 01（剩 16 件中筛 4 件）：
- DDE 8: 中央关于邀请民主党派等代表来解放区开政协的指示 (1948-05-01) ⭐
- DDE 15: 毛泽东关于新政协时间地点给李济深等的电报 (1948-08-01) ⭐
- DDE 22: 中央关于交换政协意见的指示 (1948-05-07) ⭐
- DDE 14: 56 名民主人士贺电 (1949-02) 已注册

Page 04（剩 13 件中筛 5 件）：
- DDE 1: 新政治协商会议筹备会关于召开成立会的通知 (1949-06-14) ⭐
- DDE 2: 毛泽东在新政协筹备会开幕典礼上的讲话 (1949-06-15) ⭐
- DDE 3: 朱德在新政协筹备会开幕典礼上的讲话 (1949-06-15) ⭐
- DDE 6: 郭沫若在新政协筹备会开幕典礼上的讲话 (1949-06-15) ⭐
- DDE 8: 陈嘉庚在新政协筹备会开幕典礼上的讲话 (1949-06-15) ⭐

Page 05（剩 15 件中筛 10 件）：
- DDE 1: 政协一届全体会议会场 (1949-09-21) ⭐
- DDE 3: 政协一届全体会议代表签名册 (1949-09-21) ⭐
- DDE 4: 政协一届全体会议开幕式签到簿 (1949-09-21) ⭐
- DDE 5: 政协一届全体会议代表签到 (1949-09-21) ⭐
- DDE 6: 政协一届全体会议程序 (1949-09-21 至 30) ⭐
- DDE 7: 政协一届全体会议主席团名单 (1949-09-21) ⭐
- DDE 8: 毛泽东致开幕词 (1949-09-21) ⭐
- DDE 9: 刘少奇讲话（中共代表） (1949-09-21) ⭐
- DDE 12: 李立三讲话（全总副主席） (1949-09-21) ⭐
- DDE 13: 张治中讲话（特邀代表） (1949-09-21) ⭐
- DDE 14: 程潜讲话（特邀代表） (1949-09-21) ⭐
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

# 19 条剩余民主党派直接相关档案
REMAINING = [
    # Page 01
    {"page": "01", "dde": 8, "date": "1948-05-01",
     "title": "中共中央关于邀请民主党派等代表来解放区开政协的指示（1948-05-01）",
     "context": "中央对民主党派的指示"},
    {"page": "01", "dde": 15, "date": "1948-08-01",
     "title": "毛泽东关于新政协时间地点给李济深等的电报（1948-08-01）",
     "context": "新政协时间地点"},
    {"page": "01", "dde": 22, "date": "1948-05-07",
     "title": "中央关于交换政协意见的指示（1948-05-07）",
     "context": "中央对民主党派政协意见"},
    # Page 04
    {"page": "04", "dde": 1, "date": "1949-06-14",
     "title": "新政治协商会议筹备会关于召开成立会的通知（1949-06-14）",
     "context": "新政协筹备会通知"},
    {"page": "04", "dde": 2, "date": "1949-06-15",
     "title": "毛泽东在新政协筹备会开幕典礼上的讲话（1949-06-15）",
     "context": "毛泽东新政协讲话"},
    {"page": "04", "dde": 3, "date": "1949-06-15",
     "title": "朱德在新政协筹备会开幕典礼上的讲话（1949-06-15）",
     "context": "朱德新政协讲话"},
    {"page": "04", "dde": 6, "date": "1949-06-15",
     "title": "郭沫若在新政协筹备会开幕典礼上的讲话（1949-06-15）",
     "context": "郭沫若新政协讲话"},
    {"page": "04", "dde": 8, "date": "1949-06-15",
     "title": "陈嘉庚在新政协筹备会开幕典礼上的讲话（1949-06-15）",
     "context": "陈嘉庚新政协讲话"},
    # Page 05
    {"page": "05", "dde": 1, "date": "1949-09-21",
     "title": "政协一届全体会议会场（1949-09-21）",
     "context": "政协会场"},
    {"page": "05", "dde": 3, "date": "1949-09-21",
     "title": "政协一届全体会议代表签名册（1949-09-21）",
     "context": "代表签名册"},
    {"page": "05", "dde": 4, "date": "1949-09-21",
     "title": "政协一届全体会议开幕式签到簿（1949-09-21）",
     "context": "开幕式签到"},
    {"page": "05", "dde": 5, "date": "1949-09-21",
     "title": "政协一届全体会议代表签到（1949-09-21）",
     "context": "代表签到"},
    {"page": "05", "dde": 6, "date": "1949-09-21",
     "title": "政协一届全体会议程序（1949-09-21 至 30）",
     "context": "会议程序"},
    {"page": "05", "dde": 7, "date": "1949-09-21",
     "title": "政协一届全体会议主席团名单（1949-09-21）",
     "context": "主席团名单"},
    {"page": "05", "dde": 8, "date": "1949-09-21",
     "title": "毛泽东致开幕词（1949-09-21）",
     "context": "毛泽东开幕词"},
    {"page": "05", "dde": 9, "date": "1949-09-21",
     "title": "刘少奇讲话（中共代表，1949-09-21）",
     "context": "刘少奇中共代表讲话"},
    {"page": "05", "dde": 12, "date": "1949-09-21",
     "title": "李立三讲话（全总副主席，1949-09-21）",
     "context": "李立三全总讲话"},
    {"page": "05", "dde": 13, "date": "1949-09-21",
     "title": "张治中讲话（特邀代表，1949-09-21）",
     "context": "张治中特邀讲话"},
    {"page": "05", "dde": 14, "date": "1949-09-21",
     "title": "程潜讲话（特邀代表，1949-09-21）",
     "context": "程潜特邀讲话"},
]


def make_record(idx: int, item: dict) -> dict:
    page = item["page"]
    dde = item["dde"]
    title = item["title"]
    doc_date = item["date"]
    context = item["context"]

    archive_url = f"https://www.saac.gov.cn/daj/gqzt/{page}_0{dde}.html"
    thumb_url = f"https://www.saac.gov.cn/daj/gqzt/img/a0{page}/s/s{dde:02d}.jpg"

    return {
        "candidate_id": f"domestic:SAAC:51koukou-p{page}-dde{dde:02d}-i3",
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
        "event_tags": ["1948五一口号", "1949新政协筹备", "1949民盟参与政协", "1949开国大典"],
        "person_tags": ["毛泽东", "朱德", "周恩来", "刘少奇", "李济深", "郭沫若", "陈嘉庚", "李立三", "张治中", "程潜"],
        "place_tags": ["北京", "北平"],
        "evidence_note": (
            f"WebFetch 2026-07-21 实测 saac.gov.cn/daj/gqzt/{page}.html；"
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
    for idx, item in enumerate(REMAINING, 1):
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
                    f"L2 needs_human_review 中央档案馆 1948-1949 民主党派相关档案（批次 I-3）；"
                    f"WebFetch 2026-07-21 实测 saac.gov.cn；L1 升级需原件扫描。"
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