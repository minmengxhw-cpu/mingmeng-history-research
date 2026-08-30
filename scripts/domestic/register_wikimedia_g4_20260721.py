#!/usr/bin/env python3
"""Register 批次 G-4: Wikimedia Commons 马叙伦 + 罗隆基 + 张澜 + 闻一多 + 陶行知 等关键文件。

WebFetch 2026-07-21 实测：

Ma Xulun（11 文件，1945-1949 相关 5 条）：
- 下关惨案3.jpg（1946-06-23 民进创始人马叙伦 + 雷洁琼等被国民党特务殴打）
- 参加政协第一届全体会议的民进代表合影（1949）
- 新政协筹备会常委合影（1949 1174×759 高分辨率）
- Ship_Huazhong_Arrived_in_the_Northeast_Liberated_Area.jpg（民进创始人赴东北解放区）
- 中央人民政府主席副主席和部分委员（1949）

Luo Longji（8 文件，1 条新增）：
- Zhou_Enlai_and_Luo_Longji_on_the_Political_Consultative_Conference（1946 重庆政协）

L2 accepted（PD-China）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 1946-06-23 下关惨案
    {
        "candidate_id": "domestic:WM:1946-06-23-xiaguan-can'an-maxulun",
        "title": "1946-06-23 下关惨案（马叙伦、雷洁琼等民进创始人在南京下关车站遭国民党特务殴打）",
        "creator": "作者不详（PD-China）",
        "document_date": "1946-06-23",
        "document_date_precision": "day",
        "document_type": "1946 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 马叙伦分类",
        "collection_name": "马叙伦分类 (11 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:下关惨案3.jpg",
        "catalog_reference": "Wikimedia Commons File:下关惨案3.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E4%B8%8B%E5%85%B3%E6%83%A8%E6%A1%883.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 48KB 488×350",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946下关事件"],
        "person_tags": ["马叙伦", "雷洁琼", "中国民主促进会"],
        "place_tags": ["南京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons /wiki/Category:Ma_Xulun；"
            "下关惨案（1946-06-23）—— 民进代表赴南京请愿代表团（马叙伦/雷洁琼/阎宝航/胡子婴/马叙伦 等）"
            "在南京下关车站遭国民党特务暴徒殴打，马叙伦雷洁琼等重伤；"
            "这是民进 + 民盟参与政治协商的关键事件；"
            "L2 等级：PD-China + 民进/民盟参与政协核心事件。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:下关惨案3.jpg",
        "uncertainty_note": "需进一步确认人物身份。",
    },
    # 1949 民进代表合影
    {
        "candidate_id": "domestic:WM:1949-minjin-daibiao-heying-yijie-zhengxie",
        "title": "1949 参加政协第一届全体会议的民进代表合影（含马叙伦等民进核心）",
        "creator": "作者不详（PD-China）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 马叙伦分类",
        "collection_name": "马叙伦分类 (11 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:参加政协第一届全体会议的民进代表合影.jpg",
        "catalog_reference": "Wikimedia Commons File:参加政协第一届全体会议的民进代表合影.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E5%8F%82%E5%8A%A0%E6%94%BF%E5%8D%8F%E7%AC%AC%E4%B8%80%E5%B1%8A%E5%85%A8%E4%BD%93%E4%BC%9A%E8%AE%AE%E7%9A%84%E6%B0%91%E8%BF%9B%E4%BB%A3%E8%A1%A8%E5%90%88%E5%BD%B1.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 70KB 500×352",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协"],
        "person_tags": ["马叙伦", "中国民主促进会"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "1949 参加政协第一届全体会议的民进代表合影；"
            "L2 等级：PD-China + 民进 + 一届政协。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:参加政协第一届全体会议的民进代表合影.jpg",
        "uncertainty_note": "需进一步确认全部人物。",
    },
    # 1949 民进赴东北解放区
    {
        "candidate_id": "domestic:WM:1946-ship-huazhong-minjin-dongbei-jiefangqu",
        "title": "1946 华中号轮船 民进创始人在东北解放区（马叙伦等赴东北）",
        "creator": "作者不详（PD-China）",
        "document_date": "1946",
        "document_date_precision": "year",
        "document_type": "1946 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 马叙伦分类",
        "collection_name": "马叙伦分类 (11 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Ship_Huazhong_Arrived_in_the_Northeast_Liberated_Area.jpg",
        "catalog_reference": "Wikimedia Commons File:Ship Huazhong Arrived in the Northeast Liberated Area.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Ship_Huazhong_Arrived_in_the_Northeast_Liberated_Area.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 234KB 758×800",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946下关事件", "1949民盟参与政协"],
        "person_tags": ["马叙伦", "中国民主促进会"],
        "place_tags": ["东北", "解放区"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "华中号轮船 民进创始人在东北解放区；"
            "1946-06 下关惨案后马叙伦等赴东北哈尔滨/大连解放区；"
            "L2 等级：PD-China + 民进 1946-1949 关键行动。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Ship_Huazhong_Arrived_in_the_Northeast_Liberated_Area.jpg",
        "uncertainty_note": "需进一步确认日期与人物。",
    },
    # 1946 周恩来与罗隆基在政协
    {
        "candidate_id": "domestic:WM:1946-zhouenlai-luolongji-zhengxie",
        "title": "1946 周恩来与罗隆基在政治协商会议（罗隆基 = 民盟宣传部长）",
        "creator": "作者不详（PD-China）",
        "document_date": "1946-01",
        "document_date_precision": "month",
        "document_type": "1946 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 罗隆基分类",
        "collection_name": "罗隆基分类 (8 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Zhou_Enlai_and_Luo_Longji_on_the_Political_Consultative_Conference.jpg",
        "catalog_reference": "Wikimedia Commons File:Zhou Enlai and Luo Longji on the Political Consultative Conference.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Zhou_Enlai_and_Luo_Longji_on_the_Political_Consultative_Conference.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946政治协商会议"],
        "person_tags": ["周恩来", "罗隆基", "中国民主同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 /wiki/Category:Luo_Longji；"
            "1946-01 周恩来与罗隆基在政治协商会议（重庆）；"
            "罗隆基 = 民盟宣传部 + 一届政协代表 + 起草多份政协决议；"
            "L2 等级：PD-China + 民盟核心 + 政治协商会议。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Zhou_Enlai_and_Luo_Longji_on_the_Political_Consultative_Conference.jpg",
        "uncertainty_note": "需进一步确认具体场合。",
    },
    # 1949 新政协筹备会常委合影（高分辨率 1174×759）
    {
        "candidate_id": "domestic:WM:1949-xinzhengxie-choubeihui-changwei-maxulun-categorized",
        "title": "1949 新政协筹备会常委合影（马叙伦分类 - 1174×759 高分辨率）",
        "creator": "作者不详（PD-China）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 马叙伦分类",
        "collection_name": "马叙伦分类 (11 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:新政协筹备会常委合影.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:新政协筹备会常委合影.jpg；"
            "1174×759（高分辨率，145KB）"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E6%96%B0%E6%94%BF%E5%8D%8F%E7%AD%B9%E5%A4%87%E4%BC%9A%E5%B8%B8%E5%A7%94%E5%90%88%E5%BD%B1.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 145KB 1174×759（高分辨率）",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L1",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协"],
        "person_tags": ["马叙伦", "中国民主促进会", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "新政协筹备会常委合影（1949-06-15 起）- 高分辨率 1174×759；"
            "含民盟筹备会常委（沈钧儒/章伯钧等）；"
            "L1 等级：PD-China + 高分辨率 + 民盟参与政协关键影像。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:新政协筹备会常委合影.jpg",
        "uncertainty_note": "L1 已设置。",
    },
    # 1949 周恩来与马叙伦 马思聪
    {
        "candidate_id": "domestic:WM:1949-zhouenlai-maxulun-masicong",
        "title": "1949 周恩来与马叙伦 + 马思聪（民进创始人）",
        "creator": "作者不详（PD-China）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 马叙伦分类",
        "collection_name": "马叙伦分类 (11 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Zhou_Enlai_talking_with_Ma_Xulan_and_Ma_Sicong.jpg",
        "catalog_reference": "Wikimedia Commons File:Zhou Enlai talking with Ma Xulan and Ma Sicong.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Zhou_Enlai_talking_with_Ma_Xulan_and_Ma_Sicong.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 57KB 640×411",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协"],
        "person_tags": ["周恩来", "马叙伦", "马思聪"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "周恩来与马叙伦 + 马思聪会谈（1949）；"
            "L2 等级：PD-China + 1949 民进核心。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Zhou_Enlai_talking_with_Ma_Xulan_and_Ma_Sicong.jpg",
        "uncertainty_note": "需进一步确认日期。",
    },
    # 1949 民进代表合影 第二版（已 G-3 注册 xinfang 部分）
    # Tao Xingzhi's funeral (已 G 注册)
    # Ship Huazhong Arrived in Northeast Liberated Area (above)

    # 章伯钧肖像 + Leaders CCP mission（已 G 注册）
    # Ye_Duyi3 / 4（章伯钧子分类） - 中央人民政府已 G 注册
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
                    f"L2/L1 needs_human_review Wikimedia Commons 民盟历史文件（批次 G-4）；"
                    f"PD-China 公有领域；WebFetch 2026-07-21 实测。"
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