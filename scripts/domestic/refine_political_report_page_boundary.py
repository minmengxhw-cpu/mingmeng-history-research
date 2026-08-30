#!/usr/bin/env python3
"""Record the audited continuous page boundary for the 1945 political report."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data/domestic/candidates.jsonl"
TARGET = "domestic:MMHIST:political-report-1945"


def main() -> None:
    rows = []
    found = False
    for line in CANDIDATES.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("candidate_id") == TARGET:
            row["evidence_note"] = (
                "正文连续页已核读：公开扫描 PDF 第101—117页（扫描书内第71—87页）均为《中国民主同盟临时全国代表大会政治报告》正文；"
                "第101页标题和日期为1945年10月11日，第117页为报告末页。第118页起进入《中国民主同盟临时全国代表大会宣言》，故不并入政治报告。"
            )
            row["evidence_locator"] = (
                "PDF第101—117页；扫描书内第71—87页；第101页正文首页、第117页末页；"
                "第118页起为下一件《中国民主同盟临时全国代表大会宣言》。"
            )
            row["uncertainty_note"] = (
                "该记录证据来自1983年正式汇编公开扫描，不替代1945年大会原始印本或同期发表版；"
                "报告署名、原始形成/发表载体和版本异文仍待互校。"
            )
            row["checked_at"] = "2026-07-19"
            row["review_note"] = (
                "已完成报告正文连续页界审计；保持L2/needs_human_review，待与大会原件、同期发表版或其他正式汇编核对后再决定是否接受。"
            )
            found = True
        rows.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    if not found:
        raise SystemExit(f"candidate not found: {TARGET}")
    CANDIDATES.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"updated {TARGET}")


if __name__ == "__main__":
    main()
