#!/usr/bin/env python3
"""Register 批次 H-2: mmzy.org.cn 中国民主同盟中央委员会官网官方一手资源。

WebFetch 2026-07-21 实测 mmzy.org.cn + gmw.cn 2022-12-22：

A. 民盟中央 mmzy.org.cn 官方一手：
1. 民盟概况 / 民盟中央领导机构（2026 现任）= 民盟中央官方权威发布
2. 历届中央委员会 = 第一届（1945-10）到第五届 + 中国民主政团同盟中央执行委员会（1941）
3. 中国民主同盟章程 = 民盟中央官方发布
4. 组织结构 = 民盟中央官方发布

B. 光明日报 gmw.cn 民盟历史报道：
- 2022-12-22 关于中国民主同盟的报道（《光明日报》第 02 版，新华社北京 12 月 21 日电）

等级：L2 needs_human_review proposed（民盟中央官方 + 光明日报官方源）
升级 L1 需具体原始文献
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # A1. 民盟中央领导机构（2026 现任）
    {
        "candidate_id": "domestic:MMC:lingdao-jiegou-2026",
        "title": "民盟第十三届中央委员会现任领导机构名单（mmzy.org.cn 民盟中央官方，2026）",
        "creator": "中国民主同盟中央委员会",
        "document_date": "2026-01",
        "document_date_precision": "month",
        "document_type": "民盟中央官方网站一手权威发布",
        "repository_code": "MMC",
        "repository_name": "中国民主同盟中央委员会官网（mmzy.org.cn）",
        "collection_name": "民盟概况 / 民盟中央领导机构",
        "archive_item": "https://www.mmzy.org.cn/mmgk/1186/default.aspx",
        "catalog_reference": "mmzy.org.cn/mmgk/1186/default.aspx 民盟第十三届中央委员会现任领导机构",
        "catalog_reference_status": "verified",
        "source_url": "https://www.mmzy.org.cn/mmgk/1186/default.aspx",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "民盟中央官方公开发布；含 13 届 4 中全会补选名单（2026-01）",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1945民盟一大"],
        "person_tags": ["丁仲礼", "王光谦", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 mmzy.org.cn/mmgk/1186/default.aspx；"
            "民盟第十三届中央委员会现任领导机构名单："
            "主席丁仲礼 / 常务副主席王光谦 + 副主席田刚等 11 人 + 70 常委 + 281 中央委员；"
            "2026-01 13 届 4 中全会补选丁洪/吕小兵/沈维孝为常委 + 王亚愚等 11 人为中央委员；"
            "L2 等级：民盟中央官方公开发布 = 官方一手权威。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.mmzy.org.cn/mmgk/1186/default.aspx",
        "uncertainty_note": "L1 升级需具体民盟中央文件原件。",
    },
    # A2. 历届中央委员会索引
    {
        "candidate_id": "domestic:MMC:lijie-zhongyang-weiyuanhui-index",
        "title": "民盟历届中央委员会索引页（第一届 1945 到第十二届，含 1941 中国民主政团同盟中央执行委员会）",
        "creator": "中国民主同盟中央委员会",
        "document_date": "2026",
        "document_date_precision": "approximate",
        "document_type": "民盟中央官方网站一手权威发布",
        "repository_code": "MMC",
        "repository_name": "中国民主同盟中央委员会官网（mmzy.org.cn）",
        "collection_name": "历届中央委员会",
        "archive_item": "https://www.mmzy.org.cn/mmgk/1193/default.aspx",
        "catalog_reference": "mmzy.org.cn/mmgk/1193/default.aspx 民盟历届中央委员会列表",
        "catalog_reference_status": "verified",
        "source_url": "https://www.mmzy.org.cn/mmgk/1193/default.aspx",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "民盟中央官方公开发布；含完整历届中央委员会索引（第一届到第十二届 + 中国民主政团同盟中央执行委员会）；具体届次详情页 404（路径失效）但索引页可用",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1945民盟一大", "1949民盟参与政协"],
        "person_tags": ["黄炎培", "张澜", "沈钧儒", "杨明轩", "史良", "胡愈之", "楚图南", "费孝通", "中国民主同盟"],
        "place_tags": ["重庆", "上海", "北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 mmzy.org.cn/mmgk/1193/default.aspx；"
            "民盟历届中央委员会索引页（官方一手）："
            "中国民主政团同盟中央执行委员会（1941）+ 第一届（1945-10）+ 第二届（1946）+ "
            "第三届（1947）+ 第四届 + 第五届（1958）+ 第六至十二届；"
            "涵盖 1941-1949 全部关键时点；"
            "具体届次详情子页 404（路径失效）但索引页可用；"
            "L2 等级：民盟中央官方 = 官方一手。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.mmzy.org.cn/mmgk/1193/default.aspx",
        "uncertainty_note": "具体届次详情页 404；L1 升级需具体届次原件档案。",
    },
    # A3. 民盟章程
    {
        "candidate_id": "domestic:MMC:zhangcheng-latest",
        "title": "中国民主同盟章程（mmzy.org.cn 民盟中央官方最新版）",
        "creator": "中国民主同盟中央委员会",
        "document_date": "2024",
        "document_date_precision": "approximate",
        "document_type": "民盟中央官方网站一手权威发布（章程）",
        "repository_code": "MMC",
        "repository_name": "中国民主同盟中央委员会官网（mmzy.org.cn）",
        "collection_name": "民盟章程",
        "archive_item": "https://www.mmzy.org.cn/mmgk/zhangcheng/default.aspx",
        "catalog_reference": "mmzy.org.cn/mmgk/zhangcheng/default.aspx 民盟章程",
        "catalog_reference_status": "verified",
        "source_url": "https://www.mmzy.org.cn/mmgk/zhangcheng/default.aspx",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "民盟中央官方公开发布",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 mmzy.org.cn；"
            "中国民主同盟章程（民盟中央官方最新版）；"
            "民盟章程含 1941 成立 + 1944 改组 + 1945 一大等历史条款；"
            "L2 等级：民盟中央官方一手。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.mmzy.org.cn/mmgk/zhangcheng/default.aspx",
        "uncertainty_note": "L1 升级需具体届次章程原件。",
    },
    # A4. 组织结构
    {
        "candidate_id": "domestic:MMC:zuzhi-jiegou",
        "title": "中国民主同盟组织结构（mmzy.org.cn 民盟中央官方）",
        "creator": "中国民主同盟中央委员会",
        "document_date": "2026",
        "document_date_precision": "approximate",
        "document_type": "民盟中央官方网站一手权威发布",
        "repository_code": "MMC",
        "repository_name": "中国民主同盟中央委员会官网（mmzy.org.cn）",
        "collection_name": "组织结构",
        "archive_item": "https://www.mmzy.org.cn/mmgk/1162/default.aspx",
        "catalog_reference": "mmzy.org.cn/mmgk/1162/default.aspx 民盟组织结构",
        "catalog_reference_status": "verified",
        "source_url": "https://www.mmzy.org.cn/mmgk/1162/default.aspx",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "民盟中央官方公开发布",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1945民盟一大"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "中国民主同盟组织结构（民盟中央官方）；"
            "含专门委员会 + 各类部门；"
            "L2 等级：民盟中央官方一手。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.mmzy.org.cn/mmgk/1162/default.aspx",
        "uncertainty_note": "L1 升级需具体组织结构原件。",
    },
    # B. 光明日报 2022-12-22 民盟报道
    {
        "candidate_id": "domestic:GMD:2022-12-22-minmeng-baodao",
        "title": "《光明日报》2022-12-22 关于中国民主同盟的报道（新华社北京 12 月 21 日电，第 02 版）",
        "creator": "新华社 / 光明日报",
        "document_date": "2022-12-22",
        "document_date_precision": "day",
        "document_type": "光明日报官方历史报道",
        "repository_code": "GMD",
        "repository_name": "光明日报（gmw.cn）",
        "collection_name": "民主党派专题报道",
        "archive_item": "https://news.gmw.cn/2022-12/22/content_36249069.htm",
        "catalog_reference": "《光明日报》2022-12-22 第 02 版；孙宗鹤 编辑",
        "catalog_reference_status": "verified",
        "source_url": "https://news.gmw.cn/2022-12/22/content_36249069.htm",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "光明日报官方公开发布；含 1941 成立 / 1944 改组 / 1949 一届政协等关键时点简述",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "光明日报官方发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 news.gmw.cn/2022-12/22/content_36249069.htm；"
            "《光明日报》2022-12-22 第 02 版关于中国民主同盟报道；"
            "1941-03-19 重庆秘密成立中国民主政团同盟；1944-09 改名为中国民主同盟；"
            "抗日战争和解放战争时期民盟与中共合作反帝反封建反官僚资本；"
            "新中国成立后参与政治协商、民主监督、参政议政；"
            "L2 等级：光明日报官方 = 中共党报官方一手。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://news.gmw.cn/2022-12/22/content_36249069.htm",
        "uncertainty_note": "L1 升级需光明日报纸本原件。",
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
                    f"L2 needs_human_review 民盟中央/光明日报官方一手资源（批次 H-2）；"
                    f"WebFetch 2026-07-21 实测；"
                    f"升级依据与批次 D 流程一致。"
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