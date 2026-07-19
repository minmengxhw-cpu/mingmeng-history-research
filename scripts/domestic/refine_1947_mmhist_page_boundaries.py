#!/usr/bin/env python3
"""Record page-level audits for the 1947 MMHIST documents."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data/domestic/candidates.jsonl"

UPDATES = {
    "domestic:MMHIST:league-dissolution-announcement-1947-11-06": {
        "evidence_note": "正文页已核读：公开扫描 PDF 第385—386页（扫描书内第355—356页）连续为《中国民主同盟被迫发表解散公告》（1947年11月6日）；第385页为标题、日期和正文首页，第386页为公告续页、政府答复条件和中国民主同盟主席张澜署名。",
        "evidence_locator": "PDF第385—386页；扫描书内第355—356页；第385页正文首页、第386页末页及张澜署名。",
        "evidence_type": "digital_image",
        "uncertainty_note": "该记录证据来自1983年正式汇编公开扫描，不替代1947年民盟总部原始印本、同期报刊原版或档案原件；汇编底本、传播载体和文本异文仍待互校。",
        "review_note": "已完成解散公告连续页界审计；保持L2/needs_human_review，待与1947年同期原版、张澜原件或档案记录互校后再决定是否接受。",
    },
    "domestic:MMHIST:league-banned-1947-10-27": {
        "evidence_note": "正文页已核读：公开扫描 PDF 第390页（扫描书内第360页）为《国民党政府宣布民盟为非法团体》，题下注明1947年10月27日；该页为独立正文页，页首有“附录”标识和标题，正文说明内政部发言人宣布及政府取缔口径。",
        "evidence_locator": "PDF第390页；扫描书内第360页；该页独立正文标题、日期和正文。",
        "evidence_type": "digital_image",
        "uncertainty_note": "该记录证据来自1983年正式汇编公开扫描，不替代1947年内政部原始公函、国民政府公报或档案原件；汇编底本、正式发布载体和文本异文仍待互校。",
        "review_note": "已完成非法化公告汇编正文页审计；保持L2/needs_human_review，待与1947年内政部公函、官方公报或档案影像互校后再决定是否接受。",
    },
}


def main() -> None:
    rows = []
    seen = set()
    for line in CANDIDATES.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        candidate_id = row.get("candidate_id")
        if candidate_id in UPDATES:
            row.update(UPDATES[candidate_id])
            row["checked_at"] = "2026-07-19"
            seen.add(candidate_id)
        rows.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    missing = set(UPDATES) - seen
    if missing:
        raise SystemExit(f"candidate(s) not found: {sorted(missing)}")
    CANDIDATES.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"updated {len(seen)} candidates")


if __name__ == "__main__":
    main()
