#!/usr/bin/env python3
"""Register 批次 E-A: Wikimedia Commons 上 2 张中国民主同盟历史扫描件（公有领域 PD-China）。

WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/Category:China_Democratic_League：

1. 《中共代表团撤离前委托民盟代管房产的信》(1946)
   - 来源：cppcc.people.com.cn/BIG5/35948/9974422.html（中国政协官方页面）
   - 公开发行 PD-China | JPEG 64KB | 220×308
   - 直接下载：upload.wikimedia.org/wikipedia/commons/7/70/...

2. 《中共及民盟的地方组织抗议政府解散民盟》(1947)
   - 来源：cppcc.people.com.cn/BIG5/35948/9974424.html（中国政协官方页面）
   - 描述：A 1947 newspaper clipping showing reports and statements from local CCP and
     China Democratic League organizations protesting the Kuomintang's illegal dissolution
     of the Democratic League on October 27, 1947.
   - 公开发行 PD-China | JPEG 106KB | 400×335
   - 直接下载：upload.wikimedia.org/wikipedia/commons/f/ff/...

等级：L2 needs_human_review（公有领域 + 中国政协官方源）
升级 L1 需 cheer 取原件高分辨率扫描（cppcc.people.com.cn 源页）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:WM:1946-zhonggong-weituo-minmeng-daiguanfangchan-xin",
        "title": "《中共代表团撤离前委托民盟代管房产的信》(1946)",
        "creator": "中共代表团（来源 cppcc.people.com.cn 中国政协官方）",
        "document_date": "1946",
        "document_date_precision": "year",
        "document_type": "民国时期档案扫描件（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 中国民主同盟分类",
        "collection_name": "China Democratic League (Wikimedia Commons Category)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:中共代表团撤离前委托民盟代管房产的信.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:中共代表团撤离前委托民盟代管房产的信.jpg；"
            "来源：中国政协 cppcc.people.com.cn/BIG5/35948/9974422.html"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://upload.wikimedia.org/wikipedia/commons/7/70/%E4%B8%AD%E5%85%B1%E4%BB%A3%E8%A1%A8%E5%9B%A2%E6%92%A4%E7%A6%BB%E5%89%8D%E5%A7%94%E6%89%98%E6%B0%91%E7%9B%9F%E4%BB%A3%E7%AE%A1%E6%88%BF%E4%BA%A7%E7%9A%84%E4%BF%A1.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "公有领域 PD-China；JPEG 64KB 220×308；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域（中国法律下版权已过期）；Wikimedia Commons 标注",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946政治协商会议", "1947民盟解散"],
        "person_tags": ["中共代表团", "中国民主同盟"],
        "place_tags": ["南京", "重庆"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/File:中共代表团撤离前委托民盟代管房产的信.jpg；"
            "文件元数据：日期 1946；来源 cppcc.people.com.cn/BIG5/35948/9974422.html（中国政协官方页面）；"
            "公有领域 PD-China；JPEG 64KB 220×308；"
            "L2 等级：公有领域 + 中国政协官方源。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/File:中共代表团撤离前委托民盟代管房产的信.jpg (元数据)；"
            "https://upload.wikimedia.org/wikipedia/commons/7/70/... (直接下载)；"
            "http://cppcc.people.com.cn/BIG5/35948/9974422.html (中国政协源)"
        ),
        "uncertainty_note": (
            "分辨率仅 220×308 较小；L1 升级需 cppcc.people.com.cn 源页取高分辨率原件。"
        ),
    },
    {
        "candidate_id": "domestic:WM:1947-zhonggong-minmeng-kangyi-zhengfu-jiesan-minmeng",
        "title": "《中共及民盟的地方组织抗议政府解散民盟》(1947 报纸剪报)",
        "creator": "中共及民盟地方组织（来源 cppcc.people.com.cn 中国政协官方）",
        "document_date": "1947",
        "document_date_precision": "year",
        "document_type": "民国时期报纸剪报扫描件（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 中国民主同盟分类",
        "collection_name": "China Democratic League (Wikimedia Commons Category)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:中共及民盟的地方组织抗议政府解散民盟.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:中共及民盟的地方组织抗议政府解散民盟.jpg；"
            "来源：中国政协 cppcc.people.com.cn/BIG5/35948/9974424.html"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://upload.wikimedia.org/wikipedia/commons/f/ff/%E4%B8%AD%E5%85%B1%E5%8F%8A%E6%B0%91%E7%9B%9F%E7%9A%84%E5%9C%B0%E6%96%B9%E7%BB%84%E7%BB%87%E6%8A%97%E8%AE%AE%E6%94%BF%E5%BA%9C%E8%A7%A3%E6%95%A3%E6%B0%91%E7%9B%9F.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "公有领域 PD-China；JPEG 106KB 400×335；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域（中国法律下版权已过期）；Wikimedia Commons 标注",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1947民盟解散"],
        "person_tags": ["中共", "中国民主同盟", "国民党"],
        "place_tags": ["南京"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/File:中共及民盟的地方组织抗议政府解散民盟.jpg；"
            "文件元数据：日期 1947；来源 cppcc.people.com.cn/BIG5/35948/9974424.html（中国政协官方页面）；"
            "描述：A 1947 newspaper clipping showing reports and statements from local CCP and "
            "China Democratic League organizations protesting the Kuomintang's illegal dissolution "
            "of the Democratic League on October 27, 1947. "
            "公有领域 PD-China；JPEG 106KB 400×335；"
            "L2 等级：公有领域 + 中国政协官方源 + 关键历史时点（1947-10-27 民盟被迫解散声明）。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/File:中共及民盟的地方组织抗议政府解散民盟.jpg (元数据)；"
            "https://upload.wikimedia.org/wikipedia/commons/f/ff/... (直接下载)；"
            "http://cppcc.people.com.cn/BIG5/35948/9974424.html (中国政协源)"
        ),
        "uncertainty_note": (
            "分辨率 400×335 中等；L1 升级需 cppcc.people.com.cn 源页取高分辨率原件。"
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
                    "L2 needs_human_review Wikimedia Commons 公有领域 PD-China 历史扫描件；"
                    "来源：中国政协 cppcc.people.com.cn 官方页面；"
                    "WebFetch 2026-07-20 实测；"
                    "L1 升级需 cppcc.people.com.cn 源页取高分辨率原件。"
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