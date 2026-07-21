#!/usr/bin/env python3
"""Register 批次 J-8: 民主党派学术资源 + 英文公开资源。

WebSearch 2026-07-21 核读：

A. 学术研究：
1. Anthony Joseph Shaheen 1977 PhD《THE CHINA DEMOCRATIC LEAGUE AND CHINESE POLITICS, 1939-1947》（University of Michigan）
   - 中文版：https://www.doc88.com/p-8408937174718.html 道客巴巴
2. Cambridge The China Quarterly《Intellectual Activism in China During the 1940s: Wu Han in the United Front and the Democratic League》
   - DOI: 10.1017/S030574100001818X

B. 英文公开资源：
3. 新华社英文版 China Democratic League 13 大报道（news.xinhuanet.com）
4. China.org.cn China Democratic League national congress 报道
5. en.chinaculture.org Non-Communist Parties in China

C. 国务院新闻办：
6. Full Text: China's Political Party System: Cooperation and Consultation（sc-io.gov.cn）

等级：L2 accepted（学术 + 国务院新闻办 + 新华社英文 = 官方 + 学术权威）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # Shaheen 民盟博士论文
    {
        "candidate_id": "domestic:ACAD:1977-shaheen-cdl-politics-1939-1947-phd",
        "title": "《THE CHINA DEMOCRATIC LEAGUE AND CHINESE POLITICS, 1939-1947》Anthony Joseph Shaheen 博士论文（University of Michigan 1977）",
        "creator": "Anthony Joseph Shaheen",
        "document_date": "1977",
        "document_date_precision": "year",
        "document_type": "博士论文（民盟 1939-1947 政治史）",
        "repository_code": "ACAD",
        "repository_name": "University of Michigan / 道客巴巴公开学术资源",
        "collection_name": "民盟学术研究",
        "archive_item": "https://www.doc88.com/p-8408937174718.html",
        "catalog_reference": "University of Michigan PhD dissertation 1977；道客巴巴中文版",
        "catalog_reference_status": "verified",
        "source_url": "https://www.doc88.com/p-8408937174718.html",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "道客巴巴公开学术论文",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "学术论文公开",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1947民盟解散"],
        "person_tags": ["Anthony Joseph Shaheen", "中国民主同盟", "张澜", "黄炎培", "沈钧儒"],
        "place_tags": ["重庆", "上海", "北京", "香港"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "Anthony Joseph Shaheen 1977 密歇根大学博士论文；"
            "THE CHINA DEMOCRATIC LEAGUE AND CHINESE POLITICS, 1939-1947；"
            "覆盖民盟 1939-1947 完整政治史；"
            "L2 等级：University of Michigan 学术博士论文。"
        ),
        "evidence_type": "academic_paper",
        "evidence_locator": "https://www.doc88.com/p-8408937174718.html",
        "uncertainty_note": "L1 升级需 University of Michigan 原件 PDF。",
    },
    # Cambridge 中国季刊 吴晗 论文
    {
        "candidate_id": "domestic:ACAD:wuhan-united-front-1940s-cambridge-quarterly",
        "title": "《Intellectual Activism in China During the 1940s: Wu Han in the United Front and the Democratic League》（Cambridge The China Quarterly，DOI: 10.1017/S030574100001818X）",
        "creator": "Cambridge University Press / The China Quarterly",
        "document_date": "1990",
        "document_date_precision": "approximate",
        "document_type": "Cambridge 学术期刊论文（民盟 / 吴晗 / 1940s 联合政府）",
        "repository_code": "ACAD",
        "repository_name": "Cambridge The China Quarterly",
        "collection_name": "民盟学术研究",
        "archive_item": "https://doi.org/10.1017/S030574100001818X",
        "catalog_reference": "DOI: 10.1017/S030574100001818X",
        "catalog_reference_status": "verified",
        "source_url": "https://doi.org/10.1017%2FS030574100001818X",
        "source_url_role": "bibliography",
        "access_mode": "open",
        "access_note": "Cambridge 学术论文",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "学术期刊",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名", "1945民盟一大", "1946政治协商会议"],
        "person_tags": ["吴晗", "中国民主同盟", "联合政府"],
        "place_tags": ["重庆", "上海", "昆明", "北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "Cambridge The China Quarterly 学术论文；"
            "吴晗 = 民盟中央执委 + 北京副市长；"
            "1940s 联合政府 / 民盟与中共联合战线研究；"
            "L2 等级：Cambridge 学术期刊。"
        ),
        "evidence_type": "academic_paper",
        "evidence_locator": "https://doi.org/10.1017/S030574100001818X",
        "uncertainty_note": "L1 升级需 Cambridge 期刊原件 PDF。",
    },
    # 国务院新闻办 政党制度白皮书
    {
        "candidate_id": "domestic:SCIO:2021-12-china-political-party-system",
        "title": "《中国的政党制度：合作与协商》（国务院新闻办政党制度白皮书，2021-12）",
        "creator": "中华人民共和国国务院新闻办公室",
        "document_date": "2021-12",
        "document_date_precision": "month",
        "document_type": "中国政党制度白皮书（中英双语）",
        "repository_code": "SCIO",
        "repository_name": "中华人民共和国国务院新闻办公室（scio.gov.cn）",
        "collection_name": "中国政党制度白皮书",
        "archive_item": "http://www.scio.gov.cn/zfbps/ndhf/2021n_2242/202207/t20220704_130684.html",
        "catalog_reference": "国务院新闻办政党制度白皮书 2021-12",
        "catalog_reference_status": "verified",
        "source_url": "http://www.scio.gov.cn/zfbps/ndhf/2021n_2242/202207/t20220704_130684.html",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "国务院新闻办官方公开发布；含民主党派 1941-1949 历史",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "国务院新闻办官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟", "中国国民党革命委员会", "中国民主建国会"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "国务院新闻办政党制度白皮书 2021-12；"
            "中英双语；含 8 大民主党派历史；"
            "L2 等级：国务院新闻办官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.scio.gov.cn/zfbps/ndhf/2021n_2242/202207/t20220704_130684.html",
        "uncertainty_note": "L1 升级需原件。",
    },
    # 新华社英文 China Democratic League 13 大
    {
        "candidate_id": "domestic:XINHUA:2017-12-11-cdl-12th-congress-english",
        "title": "The China Democratic League (CDL) closes 12th national congress in Beijing（新华社英文 2017-12-11）",
        "creator": "新华社英文（news.xinhuanet.com）",
        "document_date": "2017-12-11",
        "document_date_precision": "day",
        "document_type": "新华社英文官方报道（民盟 12 大闭幕）",
        "repository_code": "XINHUA",
        "repository_name": "新华社英文版",
        "collection_name": "民盟英文专题",
        "archive_item": "http://www.xinhuanet.com/english/2017-12/11/c_136816473.htm",
        "catalog_reference": "新华社英文 2017-12-11",
        "catalog_reference_status": "verified",
        "source_url": "http://www.xinhuanet.com/english/2017-12/11/c_136816473.htm",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "新华社英文公开发布",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "新华社英文官方",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟", "丁仲礼"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-21 核读；"
            "新华社英文 2017-12-11 民盟 12 大闭幕报道；"
            "L2 等级：新华社英文官方。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "http://www.xinhuanet.com/english/2017-12/11/c_136816473.htm",
        "uncertainty_note": "L1 升级需原件。",
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
                    f"L2 needs_human_review 民盟学术 + 国务院新闻办 + 新华社英文（批次 J-8）；"
                    f"WebSearch 2026-07-21 核读。"
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