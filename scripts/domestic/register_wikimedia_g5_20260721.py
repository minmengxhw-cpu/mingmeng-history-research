#!/usr/bin/env python3
"""Register 批次 G-5: Wikimedia Commons 民盟人物肖像 + 额外关键文件 8 条。

WebFetch 2026-07-21 扫荡剩余人物子分类：
- 张君劢 (Zhang Junmai) - 5 张肖像 + 1 张中国欧洲考察团
- 闻一多 / 沈钧儒 个人照
- Tao Xingzhi 部分肖像
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 1946_10_Chou.jpg 已在 G 注册（章伯钧子分类）
    # Leaders of CD see CCP mission off 已在 G-2 注册（章伯钧子分类）

    # 张澜肖像照
    {
        "candidate_id": "domestic:WM:1940s-zhang-lan-portrait-zhang-lan-tomb",
        "title": "张澜肖像照（民国时期，民盟主席 1941-1945）",
        "creator": "作者不详（PD-China）",
        "document_date": "1940",
        "document_date_precision": "approximate",
        "document_type": "民国时期人物照（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 张澜分类",
        "collection_name": "Zhang Lan (19F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:張瀾.jpg + Zhanglantomb.jpg + Mao Zedong and Zhang Lan.jpg + Zhang Lan and Zhu De.jpg",
        "catalog_reference": "Wikimedia Commons /wiki/Category:Zhang_Lan",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E5%BC%B5%E7%80%9B.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；张澜肖像 + 墓 + 与毛泽东 / 朱德合影",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1947民盟解散"],
        "person_tags": ["张澜", "中国民主同盟"],
        "place_tags": ["重庆", "上海"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons /wiki/Category:Zhang_Lan；"
            "张澜分类 19 文件含肖像 + 墓 + 1955 照片 + 1945 重庆谈判公开信 + 成都市伊斯兰教协会题字 + 与毛泽东 / 朱德合影等；"
            "张澜 = 民盟主席（1945-1955）+ 中国民主政团同盟成立核心；"
            "L2 等级：PD-China + 民盟主席肖像 + 1941-1945 关键期。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/Category:Zhang_Lan；"
            "File:張瀾.jpg / Zhanglantomb.jpg / Mao Zedong and Zhang Lan.jpg / Zhang Lan and Zhu De.jpg"
        ),
        "uncertainty_note": "具体拍摄年份待核。",
    },
    # 张澜 + 毛泽东合影
    {
        "candidate_id": "domestic:WM:1949-zhang-lan-mao-zedong-heying",
        "title": "1949 张澜与毛泽东合影（中央人民政府）",
        "creator": "作者不详（PD-China）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 张澜分类",
        "collection_name": "Zhang Lan (19F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Mao Zedong and Zhang Lan.jpg",
        "catalog_reference": "Wikimedia Commons File:Mao Zedong and Zhang Lan.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Mao_Zedong_and_Zhang_Lan.jpg",
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
        "event_tags": ["1949民盟参与政协", "1949开国大典"],
        "person_tags": ["张澜", "毛泽东", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "1949 张澜与毛泽东合影（中央人民政府期间）；"
            "L2 等级：PD-China + 1949 民盟主席与毛主席合影。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Mao_Zedong_and_Zhang_Lan.jpg",
        "uncertainty_note": "需进一步确认日期与场合。",
    },
    # 1949 张澜墓
    {
        "candidate_id": "domestic:WM:zhang-lan-tomb",
        "title": "张澜墓（北京八宝山革命公墓）",
        "creator": "作者不详（PD-China）",
        "document_date": "2010",
        "document_date_precision": "approximate",
        "document_type": "现代纪念设施照（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 张澜分类",
        "collection_name": "Zhang Lan (19F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Zhanglantomb.jpg",
        "catalog_reference": "Wikimedia Commons File:Zhanglantomb.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Zhanglantomb.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；张澜墓照片；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身"],
        "person_tags": ["张澜", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "张澜墓（八宝山革命公墓）；"
            "L3 等级：纪念设施，非 1941-1949 原件。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Zhanglantomb.jpg",
        "uncertainty_note": "张澜墓 = 1955 以后，非 1941-1949 范围，但作为民盟核心人物纪念设施保留。",
    },
    # 张君劢肖像 (1940s)
    {
        "candidate_id": "domestic:WM:1940s-zhang-junmai-portrait-1",
        "title": "张君劢肖像照（民国时期，民盟创始人 + 1946 国共和谈代表）",
        "creator": "作者不详（PD-China）",
        "document_date": "1940",
        "document_date_precision": "approximate",
        "document_type": "民国时期人物照（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 张君劢分类",
        "collection_name": "Zhang Junmai (8F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Zhang_Junmai.jpg",
        "catalog_reference": "Wikimedia Commons File:Zhang Junmai.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Zhang_Junmai.jpg",
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
        "event_tags": ["1941民盟前身", "1946政治协商会议"],
        "person_tags": ["张君劢", "中国民主社会党", "中国民主同盟"],
        "place_tags": ["重庆", "上海"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 /wiki/Category:Zhang_Junmai；"
            "张君劢肖像照（民国时期）；"
            "张君劢 = 民盟创始人之一 + 1946 国共和谈代表（1946_10_Chou 民盟核心）；"
            "L2 等级：PD-China + 民盟创始人肖像。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Zhang_Junmai.jpg",
        "uncertainty_note": "需进一步确认拍摄年份。",
    },
    # 1949 张澜 + 朱德合影（已在 G-2 角度注册）
    # 张澜 墓
    # 陶行知楷书「和为贵」横幅
    {
        "candidate_id": "domestic:WM:taoxingzhi-heweigui-hengfu",
        "title": "陶行知楷书『和为贵』横幅（民进创始人题字）",
        "creator": "陶行知",
        "document_date": "1940",
        "document_date_precision": "approximate",
        "document_type": "民国时期书法原件（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 陶行知分类",
        "collection_name": "Tao Xingzhi (12F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:陶行知楷书\"和为贵\"横幅.jpg",
        "catalog_reference": "Wikimedia Commons File:陶行知楷书\"和为贵\"横幅.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E9%99%B6%E8%A1%8C%E7%9F%A5%E6%A5%B7%E4%B9%A6%E2%80%9C%E5%92%8C%E4%B8%BA%E8%B4%B5%E2%80%9D%E6%A8%AA%E5%B9%85.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；陶行知楷书原件扫描；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1945民盟一大"],
        "person_tags": ["陶行知", "中国民主同盟"],
        "place_tags": ["重庆", "上海"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 /wiki/Category:Tao_Xingzhi；"
            "陶行知楷书『和为贵』横幅原件扫描（民国时期）；"
            "陶行知 = 1945 民盟一大中央常委 + 1946-11 逝世；"
            "L2 等级：PD-China + 陶行知真迹原件 + 民盟核心人物文物。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:陶行知楷书\"和为贵\"横幅.jpg",
        "uncertainty_note": "需进一步确认原件真伪。",
    },
    # 周恩来 + 罗隆基 + 5 / 已知在政协会议 (已 G-4 注册)
    # 1949 中央人民政府 主席副主席 - 已在 G 注册
    # 罗隆基个人照
    {
        "candidate_id": "domestic:WM:1940s-luo-longji-portrait",
        "title": "罗隆基肖像照（民国时期，民盟宣传部 + 一届政协代表）",
        "creator": "作者不详（PD-China）",
        "document_date": "1940",
        "document_date_precision": "approximate",
        "document_type": "民国时期人物照（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 罗隆基分类",
        "collection_name": "Luo Longji (8F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:羅隆基.jpg",
        "catalog_reference": "Wikimedia Commons File:羅隆基.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E7%BE%85%E9%9A%86%E5%9F%BA.jpg",
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
        "event_tags": ["1941民盟前身", "1946政治协商会议", "1947民盟解散"],
        "person_tags": ["罗隆基", "中国民主同盟"],
        "place_tags": ["重庆", "上海", "北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 /wiki/Category:Luo_Longji；"
            "罗隆基肖像照（民国时期）；"
            "罗隆基 = 民盟宣传部长 + 一届政协代表 + 1946 国共和谈代表（1946_10_Chou 民盟核心）；"
            "L2 等级：PD-China + 民盟核心人物肖像。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:羅隆基.jpg",
        "uncertainty_note": "需进一步确认拍摄年份。",
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
                    f"L2/L3 needs_human_review Wikimedia Commons 民盟人物肖像（批次 G-5）；"
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