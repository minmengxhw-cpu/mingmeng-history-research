#!/usr/bin/env python3
"""Build a bounded MiniMax review packet from local OCR triage results."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--local-triage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    ledger_path = args.ledger if args.ledger.is_absolute() else Path.cwd() / args.ledger
    triage_path = args.local_triage if args.local_triage.is_absolute() else Path.cwd() / args.local_triage
    db_path = args.db if args.db.is_absolute() else Path.cwd() / args.db
    with ledger_path.open(encoding="utf-8", newline="") as handle:
        ledger = {int(row["page_id"]): row for row in csv.DictReader(handle)}
    triage = json.loads(triage_path.read_text(encoding="utf-8"))
    page_ids = [int(item["page_id"]) for item in triage.get("pages", [])]

    packets = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for item in triage.get("pages", []):
            page_id = int(item["page_id"])
            row = conn.execute(
                "SELECT p.text,d.title,d.date_guess,p.page_label FROM pages p JOIN documents d ON d.id=p.document_id WHERE p.id=?",
                (page_id,),
            ).fetchone()
            local_result = item.get("result", {})
            local_text = local_result.get("raw_response", "") if isinstance(local_result, dict) else str(local_result)
            packets.append(
                {
                    "page_id": page_id,
                    "title": row["title"] if row else ledger[page_id].get("title", ""),
                    "date_guess": row["date_guess"] if row else ledger[page_id].get("date_guess", ""),
                    "page_label": row["page_label"] if row else ledger[page_id].get("page_label", ""),
                    "confidence": ledger.get(page_id, {}).get("ocr_mean_confidence", ""),
                    "review_priority": ledger.get(page_id, {}).get("review_priority", ""),
                    "local_qwen_triage": local_text[:6000],
                    "ocr_text_excerpt": (row["text"] if row else "")[:5000],
                }
            )

    system = """你是民盟史料项目的批次复核协调器。你只处理输入包中的页面，不得补造史实，不得把 OCR 猜测改写成原文。请给出严格 JSON，顶层字段为 batch_summary、pages、next_batch。每个 pages 元素必须包含 page_id、final_priority（P0/P1/P2）、search_usable、needs_original_image、article_boundary_action、suspicious_fields、recommended_local_action、citation_ready（固定 false）。目标是把本地 Qwen 的初筛结果转化为可执行的复核队列；任何无法由 OCR 文本确认的内容都标记为 needs_original_image=true。"""
    user = """请审核下面这批跨时期国内 OCR 页面。特别注意不要只围绕 1947 年民盟解散，要保留 1941 和 1948 材料的研究价值。请按原图复核优先级排序，并给出下一批建议页 ID；不要修改数据库。

输入页面：
""" + json.dumps(packets, ensure_ascii=False, indent=2)
    output = [
        {"role": "system", "content": system},
        {"role": "user", "content": user + "\n页面 ID：" + ", ".join(str(page_id) for page_id in page_ids)},
    ]
    output_path = args.output if args.output.is_absolute() else Path.cwd() / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(packets), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
