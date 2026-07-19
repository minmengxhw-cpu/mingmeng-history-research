#!/usr/bin/env python3
"""Accept SAAC item-surrogate candidates whose official page and image URLs were checked."""

import json
from pathlib import Path


PATH = Path("data/domestic/candidates.jsonl")
UPDATES = {
    "domestic:SAAC:catalog-06-06_09": {
        "note": "国家档案局官方条目页明确标示《中华人民共和国中央人民政府公告（1949年10月1日）》，页面提供官方影像直链，已核对条目页与影像入口。",
        "locator": "条目页 https://www.saac.gov.cn/daj/gqzt/content/06/06_09.html；官方影像 https://www.saac.gov.cn/daj/gqzt/img/a06/09/01.jpg",
    },
    "domestic:SAAC:catalog-02-02_05": {
        "note": "国家档案局官方条目页明确标示《沈钧儒在新政治协商会议筹备会开幕典礼上的讲话（1949年6月15日）》，页面提供两张官方影像直链，已核对条目页、日期和影像入口。",
        "locator": "条目页 https://www.saac.gov.cn/daj/gqzt/content/02/02_05.html；官方影像 https://www.saac.gov.cn/daj/gqzt/img/a02/02-05/01.jpg、https://www.saac.gov.cn/daj/gqzt/img/a02/02-05/02.jpg",
    },
    "domestic:SAAC:catalog-05-05_83": {
        "note": "国家档案局官方条目页明确标示《中华人民共和国中央人民政府主席、副主席及全体委员名单（1949年9月30日）》，页面提供两张官方影像直链，已核对条目页、日期和影像入口。",
        "locator": "条目页 https://www.saac.gov.cn/daj/gqzt/content/05/05_83.html；官方影像 https://www.saac.gov.cn/daj/gqzt/img/a05/83/01.jpg、https://www.saac.gov.cn/daj/gqzt/img/a05/83/02.jpg",
    },
}


def main() -> None:
    found = set()
    lines = []
    for raw in PATH.read_text(encoding="utf-8").splitlines():
        row = json.loads(raw)
        cid = row.get("candidate_id")
        if cid in UPDATES:
            u = UPDATES[cid]
            row["evidence_note"] = u["note"]
            row["evidence_type"] = "digital_image"
            row["evidence_locator"] = u["locator"]
            row["uncertainty_note"] = "官方条目页未公开完整全宗号、案卷号和页码；影像复制权利仍需按国家档案局规则核对。L1表示官方数字替身已定位，不表示已取得无条件原件复制授权。"
            row["review_status"] = "accepted"
            row["review_note"] = "Codex核对官方条目页标题、形成日期和官方影像直链；按项目规则接受为L1官方数字替身。完整档号、页码和复制权利未公开部分保留为限制。"
            row["check_outcome"] = "pass"
            row["authenticity_level_accepted"] = "L1"
            row["relevance_grade_accepted"] = row.get("relevance_grade_proposed", "core")
            row["reviewed_at"] = "2026-07-18"
            row["reviewed_by"] = "codex"
            found.add(cid)
        lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    missing = set(UPDATES) - found
    if missing:
        raise SystemExit(f"missing candidate IDs: {sorted(missing)}")
    tmp = PATH.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(PATH)
    print(f"accepted={len(found)}")


if __name__ == "__main__":
    main()
