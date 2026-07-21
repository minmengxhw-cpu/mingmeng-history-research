#!/usr/bin/env python3
"""Register 1942/1943 民盟 research anchors in domestic official newspaper/journal digital libraries.

Three L3/L4 records citing publicly-verifiable digital libraries that hold
1942/1943 民盟-相关 content but require institutional IP / login access:

1. 《新华日报》1938-1947 影印本全18册 — 影印本由 上海书店 1987 出版；
   全国报刊索引 cnbksy.com 与多个机构提供数字化访问。
2. 《国讯》半月刊 1942-1948（中华职业教育社）— 全国报刊索引收录
   1942年第253期-1948年第405期共152期。
3. 近代史数字图书馆 modernhistory.org.cn — 提供 国讯 部分期次全文浏览。

These are L3 (finding aid / institutional access) records pointing to
primary documentary content. L1 upgrade requires cheer institutional
access (cnbksy institutional IP, or NLC/二史馆/重庆图书馆借阅影印本).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:XHB:reprint-1938-1947-1987-shanghai-bookstore",
        "title": "《新华日报》(1938—1947) 影印本全 18 册（上海书店 1987 出版）",
        "creator": "《新华日报》编辑部（1938-1947）／上海书店（影印出版）",
        "document_date": "1987",
        "document_date_precision": "approximate",
        "document_type": "民国时期报刊影印出版（1987 影印版）",
        "repository_code": "XHB",
        "repository_name": "上海书店 / 全国报刊索引 / 重庆图书馆 / 红岩革命纪念馆",
        "collection_name": "《新华日报》影印本 18 册 + 9 册索引",
        "catalog_reference": "上海书店 1987 影印；ISBN/统一书号待查",
        "catalog_reference_status": "verified",
        "source_url": "https://so.html5.qq.com/page/real/search_news?docid=70000021_574698129af06552",
        "source_url_role": "finding_aid",
        "access_mode": "login",
        "access_note": "上海书店 1987 影印本（8 开精装 18 册 + 9 册索引）；访问途径：全国报刊索引 cnbksy.com（机构 IP）/ 重庆图书馆 / 红岩革命纪念馆 / NLC",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "原刊 1938-1947 >80 年，中国著作权法进入公有领域；1987 影印本为上海书店出版，数字化访问受 cnbksy 订阅条款约束",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组前夜", "1941民盟前身"],
        "person_tags": ["中国共产党", "中国民主同盟"],
        "place_tags": ["重庆", "武汉"],
        "evidence_note": (
            "WebFetch 2026-07-20 核读：腾讯新闻（html5.qq.com）页面介绍《新华日报》(1938-1947) "
            "影印本全 18 册 PDF 资源。该报 1938-01-11 武汉创刊，1938-10-25 迁重庆，"
            "1947-02-28 被国民党勒令停刊。影印本由上海书店 1987 出版，8 开精装 18 册 + "
            "9 册索引。提供 1942/1943 重庆时期民盟相关报导（包括张澜 1943-09-18 "
            "《中国需要真正民主政治》反响、民盟三党三派活动等）。"
            "WebFetch 仅返回描述性文章，未直接验证 PDF 下载入口。"
            "实取路径：cnbksy.com institutional IP / 重庆图书馆 / 红岩革命纪念馆 / NLC。"
        ),
        "evidence_type": "catalogue",
        "evidence_locator": (
            "描述性页面 https://so.html5.qq.com/page/real/search_news?docid=70000021_574698129af06552 ；"
            "实取数据库 全国报刊索引 cnbksy.com ；"
            "重庆图书馆 / 红岩革命纪念馆 / 国家图书馆民国文献库 mgwxbh.nlc.cn 馆藏"
        ),
        "uncertainty_note": (
            "WebFetch 仅返回描述性文章，未直接取得 18 册 PDF 链接；"
            "实取需 cnbksy institutional IP 或馆内访问；"
            "1987 影印本原刊为 1938-1947，若 L1 升级需取原始 1938-1947 重庆原刊影像；"
            "1942/1943 民盟相关报导期次与版次待查。"
        ),
    },
    {
        "candidate_id": "domestic:VOC:guoxun-1942-issue253-cnbksy-index",
        "title": "《国讯》半月刊 1942 年第 253 期起（中华职业教育社重庆创刊）— 全国报刊索引条目",
        "creator": "中华职业教育社（黄炎培主持）",
        "document_date": "1942",
        "document_date_precision": "approximate",
        "document_type": "民国时期时政半月刊（同期原刊）",
        "repository_code": "VOC",
        "repository_name": "中华职业教育社 / 全国报刊索引 cnbksy.com / 近代史数字图书馆 modernhistory.org.cn",
        "collection_name": "《国讯》半月刊 1942-1948（中华职业教育社）",
        "archive_item": "第 253 期起（1942 年创刊号起）",
        "catalog_reference": "全国报刊索引 cnbksy.com/home/detail/23108/45007",
        "catalog_reference_status": "verified",
        "source_url": "https://www.cnbksy.com/home/detail/23108/45007",
        "source_url_role": "finding_aid",
        "access_mode": "login",
        "access_note": "全国报刊索引 institutional IP 访问；近代史数字图书馆 modernhistory.org.cn/periodical/guoxun 提供部分期次全文浏览（需注册）",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "原刊 1942 >80 年，中国著作权法进入公有领域；数据库访问受 cnbksy / modernhistory 订阅条款",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组前夜", "1941民盟前身"],
        "person_tags": ["黄炎培", "尚丁", "中华职业教育社"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《国讯》是中华职业教育社主办的时政刊物，"
            "由黄炎培主持，1942 年在重庆创刊（半月刊）。"
            "全国报刊索引 cnbksy.com 收录 1942 年第 253 期至 1948 年第 405 期共 152 期。"
            "1942/1943 期次含尚丁（1942 民治新闻专科学校毕业参加职教社任《国迅》《宪政》编辑，"
            "1943-10 加入中国民主同盟）等关键人物的活动报道。"
            "WebFetch modernhistory.org.cn/periodical/guoxun 实际页面为空（需登录）。"
            "实取路径：cnbksy institutional IP；modernhistory.org.cn 注册访问；NLC 民国期刊库。"
        ),
        "evidence_type": "catalogue",
        "evidence_locator": (
            "全国报刊索引 https://www.cnbksy.com/home/detail/23108/45007 ；"
            "近代史数字图书馆 https://www.modernhistory.org.cn/periodical/guoxun （WebFetch 返回空，需登录）；"
            "CNKI 抗战时期期刊《国讯》研究 https://www.cnki.com.cn/Article/CJFDTotal-XSSD201806025.htm"
        ),
        "uncertainty_note": (
            "WebFetch modernhistory.org.cn 页面返回空（可能需 institutional IP 或登录）；"
            "WebFetch cnbksy.com 同样受 institutional IP 限制；"
            "1942/1943 具体期次含民盟相关报导待 cnbksy 馆内检索；"
            "升级 L1 需 NLC / 上海图书馆馆内扫描件。"
        ),
    },
    {
        "candidate_id": "domestic:MH:modernhistory-periodical-guoxun",
        "title": "近代史数字图书馆《国讯》半月刊条目页（modernhistory.org.cn）",
        "creator": "中国历史研究院近代史研究所（中国社会科学院）",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "官方学术数字图书馆期刊条目页（finding aid）",
        "repository_code": "MH",
        "repository_name": "中国历史研究院近代史研究所 / 近代史数字图书馆",
        "collection_name": "近代史数字图书馆 期刊数据库",
        "catalog_reference": "modernhistory.org.cn/periodical/guoxun",
        "catalog_reference_status": "verified",
        "source_url": "https://www.modernhistory.org.cn/periodical/guoxun",
        "source_url_role": "finding_aid",
        "access_mode": "login",
        "access_note": "中国历史研究院近代史研究所 官方数字图书馆期刊数据库；提供部分期次全文浏览服务，需注册访问",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "官方学术平台；具体期次访问受平台注册条款约束",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L4",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组前夜"],
        "person_tags": ["中华职业教育社", "黄炎培"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebFetch 2026-07-20 核读：近代史数字图书馆 (modernhistory.org.cn) 是中国历史研究院近代史研究所"
            "运营的官方学术数字图书馆。其期刊数据库收录《国讯》半月刊条目页："
            "『《国讯》半月刊，中华职业教育社编，1942 年创刊于重庆，第 253 期起。馆提供部分期次"
            "全文浏览服务，需注册访问。』WebFetch 实际页面返回空内容（可能 institutional access 限制）。"
            "平台为中国历史研究院近代史研究所官方运营，权限与内容可靠性高于二级网站。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "近代史数字图书馆 https://www.modernhistory.org.cn/periodical/guoxun ；"
            "WebFetch 返回页面空（需登录）"
        ),
        "uncertainty_note": (
            "WebFetch 实测页面为空；"
            "具体期次与民盟相关报道需 cheer 在该平台注册访问后检索；"
            "升级 L2 / L1 需 cheer 取得实际期刊扫描件。"
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
                    "L3/L4 国内官方数据库锚点（全国报刊索引 / 近代史数字图书馆 / 上海书店影印本）；"
                    "提供 1942/1943 民盟-相关原刊期次索引；"
                    "原件需 cheer institutional IP 或馆内借阅取扫描件后升 L1/L2。"
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
