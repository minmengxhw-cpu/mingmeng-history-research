#!/usr/bin/env python3
"""Register 抗战文献数据平台 (modernhistory.org.cn) as a L3 platform anchor.

WebFetch 2026-07-20 测试发现：
- 首页 http://www.modernhistory.org.cn/ WebFetch 返回空内容（重 JS SPA，需登录/机构 IP）
- 高级搜索 https://www.modernhistory.org.cn/search?keyword=民盟 WebFetch 返回空内容
- WebSearch 多源印证：亚洲最大免费公益数据平台，5000万页文献，1万种期刊，1000种报纸，13.5万册图书
- 红色文献专题数据库近 200 种
- 访问方式：全网免费浏览，注册后可免费下载（每月不超过 2000 页）
- 主办：中国社会科学院近代史研究所（中国历史研究院近代史研究所）

This script registers ONE L3 needs_human_review platform-level anchor record
covering the entire platform (5000万页 literature across 图书/期刊/报纸/档案/专题).
L1 upgrade requires cheer institutional access (注册账号 + institutional IP).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:MH:platform-anchor-modernhistory-2026",
        "title": "抗战文献数据平台聚合锚点（5000万页 / 1万期刊 / 1000种报纸 / 红色文献专题 200种）",
        "creator": "中国社会科学院近代史研究所（中国历史研究院近代史研究所）",
        "document_date": "2026",
        "document_date_precision": "approximate",
        "document_type": "官方学术数字图书馆（finding aid 聚合锚点）",
        "repository_code": "MH",
        "repository_name": "抗战文献数据平台（中国社会科学院近代史研究所运营）",
        "collection_name": "亚洲最大免费公益数据平台",
        "catalog_reference": "modernhistory.org.cn 平台聚合锚点",
        "catalog_reference_status": "verified",
        "source_url": "https://www.modernhistory.org.cn/",
        "source_url_role": "finding_aid",
        "access_mode": "login",
        "access_note": "全网免费浏览，注册账号后可免费下载（每月不超过 2000 页）。机构 IP 访问完整内容。WebFetch 实测首页与搜索页均返回空内容（重 JS SPA + 注册访问限制）。",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "官方学术平台，免费注册访问；具体文献下载受平台订阅条款",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大"],
        "person_tags": ["中国民主同盟", "中国共产党"],
        "place_tags": ["重庆", "上海", "延安"],
        "evidence_note": (
            "WebSearch 2026-07-20 多源印证：抗战文献数据平台 = 抗日战争与近代中日关系文献数据平台，"
            "网址 www.modernhistory.org.cn，亚洲最大免费公益数据平台，国家社科基金抗日战争研究专项工程。"
            "文献总量逾 5000 万页 = 图书 13.5 万余册 + 报纸 1000 余种 + 期刊 1 万余种 + 中外文档案 20 余种 + 图片/视频/音频。"
            "上线时间 2017-09 试运行 / 2018-09 正式上线。"
            "红色文献专题数据库近 200 种（1930s-1940s 关键时段含中国民主同盟 / 中国民主政团同盟相关原刊与档案）。"
            "WebFetch 2026-07-20 实测首页 + 高级搜索 URL 均返回空内容（SPA + 注册访问限制）。"
            "提供 1941/1942/1943/1944/1945 关键时点民盟-相关文献检索入口。"
            "Agent 远程无法直接取得扫描件；需 cheer 注册账号或 institutional IP 访问后逐条检索。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "平台 https://www.modernhistory.org.cn/ ；"
            "高级搜索 URL https://www.modernhistory.org.cn/search?keyword=民盟 （WebFetch 空）；"
            "WebSearch 多源：CCPS https://www.ccps.gov.cn/bmpd/tshwhg/kfhqzy/201902/t20190202_129068.shtml ；"
            "齐鲁工业大学图书馆 https://lib.qlu.edu.cn/2023/0519/c1343a223163/page.htm ；"
            "沈阳工学院图书馆 https://tsg.situ.edu.cn/info/1043/3190.htm ；"
            "中国抗战胜利网 http://www.1937china.com/views/xsyj/xsyj_kzwx_sjpt.html"
        ),
        "uncertainty_note": (
            "WebFetch 实测平台首页 + 高级搜索 URL 均返回空内容（SPA / 注册访问 / institutional IP 限制）；"
            "代理 Agent 远程无法取得扫描件；"
            "升级 L1/L2 需 cheer 在该平台注册账号 + institutional IP 后逐条检索并下载民盟-相关文献。"
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
                    "L3 抗战文献数据平台聚合锚点（5000万页文献 / 1万期刊 / 1000种报纸 / 红色文献专题库 200种）；"
                    "Agent WebFetch 实测首页 + 搜索页均空（SPA + 注册/institutional IP 限制）；"
                    "需 cheer 注册账号 + institutional IP 访问后逐条检索民盟-相关文献；"
                    "升级 L1/L2 需取得具体期刊扫描件。"
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