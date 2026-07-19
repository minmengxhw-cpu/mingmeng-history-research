#!/usr/bin/env python3
"""Record a page-level review of the official MMZY 1945 congress narrative."""

import json
from pathlib import Path

PATH = Path("data/domestic/candidates.jsonl")
TARGET = "domestic:MMZY:1945-first-congress-page"

def main() -> None:
    changed = 0
    rows = []
    for raw in PATH.read_text(encoding="utf-8").splitlines():
        item = json.loads(raw)
        if item.get("candidate_id") == TARGET:
            item["evidence_note"] = (
                "已核对民盟中央官方专题页：1945-10-01至10-12在重庆特园召开临时全国代表大会，"
                "推选代表63人、实到48人；页面记载大会通过政治报告、临时全国代表大会宣言和纲领，"
                "并说明《组织规程》涉及组织原则、中央与地方机构以及盟员入盟和退盟办法。"
            )
            item["evidence_locator"] = (
                "官方专题页正文中的日期、地点、人数、文件名称和组织规程内容；"
                "https://www.mmzy.org.cn/mmzt/sydzt/lcdbdh/34517.aspx"
            )
            item["uncertainty_note"] = (
                "该页面发布日期为2012-11-23，是民盟中央后期历史叙述，不是1945年大会原始文件影像；"
                "《组织规程》全文、原刊/印本页码、档号和底本仍待取得。"
            )
            item["review_note"] = (
                "Codex于2026-07-19完成官方专题页内容核对；补充了大会日期、人数和《组织规程》内容范围，"
                "保持L4、needs_human_review，不进入一手核心证据。"
            )
            changed += 1
        rows.append(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
    if changed != 1:
        raise SystemExit(f"expected one target, changed={changed}")
    tmp = PATH.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(rows) + "\n", encoding="utf-8")
    tmp.replace(PATH)
    print(f"updated={changed}")

if __name__ == "__main__":
    main()
