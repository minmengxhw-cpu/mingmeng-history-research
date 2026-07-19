#!/usr/bin/env python3
"""Register institution-backed newspaper database leads without fabricating item hits."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "data" / "domestic" / "source_registry.json"

LEADS = [
    {
        "source_id": "domestic:source:shanghai_modern_newspapers",
        "source_name": "中国近代报纸资源全库",
        "institution": "上海图书馆；复旦大学图书馆公开数据库说明入口",
        "source_type": "近代报纸全文与版面数据库",
        "authority_level": "馆藏报纸数字化检索入口；具体影像和复制权利按机构权限核验",
        "official_url": "https://library.fudan.edu.cn/e8/8e/c42799a518286/page.htm",
        "record_or_search_url": "https://www.cnbksy.com/",
        "material_types": ["《中央日报》1928—1949", "《大公报》1902—1949", "《民国日报》1916—1947", "近代报纸版面"],
        "shanghai_relevance": "极高",
        "access_mode": "机构订阅或馆内访问；公开说明可核对收录范围",
        "rights_status": "需按机构订阅和具体图像条款核实",
        "verification_note": "2026-07-19公开机构说明明确列出《中央日报》1928—1949、《大公报》1902—1949和《民国日报》1916—1947；可用于检索1947-10-28中央社《政府宣布民盟非法》及1947-11-06解散公告相关报面，但本轮未取得具体版面。",
        "checked_at": "2026-07-19",
        "status": "verified_entry",
    },
    {
        "source_id": "domestic:source:shantou_historical_newspapers",
        "source_name": "繙云历史文献库",
        "institution": "汕头大学图书馆",
        "source_type": "馆藏近代报纸全文与高清版面数据库",
        "authority_level": "与国家图书馆合作的报纸数字化访问入口；具体版面需机构权限核验",
        "official_url": "https://www.lib.stu.edu.cn/database/2184",
        "record_or_search_url": "https://www.lib.stu.edu.cn/database/2184",
        "material_types": ["《中央日报》", "《大公报》", "《民国日报》"],
        "shanghai_relevance": "高",
        "access_mode": "学校本地镜像或机构网络访问",
        "rights_status": "需按汕头大学图书馆和合作数据库规则核实",
        "verification_note": "2026-07-19官方图书馆页面说明该库提供《中央日报》《大公报》《民国日报》图文对照和高清DPI图档；本轮未取得1947-10-27/28或1947-11-06具体报面，保留为可执行访问入口。",
        "checked_at": "2026-07-19",
        "status": "verified_entry",
    },
]


def main() -> None:
    rows = json.loads(PATH.read_text(encoding="utf-8"))
    by_id = {row["source_id"]: row for row in rows}
    for lead in LEADS:
        by_id[lead["source_id"]] = lead
    PATH.write_text(json.dumps(list(by_id.values()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources": len(by_id), "added_or_refreshed": [lead["source_id"] for lead in LEADS]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
