#!/usr/bin/env python3
"""Build a MiniMax packet for comparing re-OCR candidates with local Qwen triage."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--local-triage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    triage_path = args.local_triage if args.local_triage.is_absolute() else Path.cwd() / args.local_triage
    db_path = args.db if args.db.is_absolute() else Path.cwd() / args.db
    triage = json.loads(triage_path.read_text(encoding="utf-8"))
    packets = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for item in triage.get("pages", []):
            page_id = int(item["page_id"])
            row = conn.execute(
                "SELECT p.page_label,d.title,d.date_guess,f.matched_terms FROM pages p JOIN documents d ON d.id=p.document_id LEFT JOIN page_fts f ON f.rowid=p.id WHERE p.id=?",
                (page_id,),
            ).fetchone()
            path = Path(item["candidate_path"])
            text = path.read_text(encoding="utf-8", errors="replace")
            packets.append(
                {
                    "page_id": page_id,
                    "title": row["title"] if row else "",
                    "date_guess": row["date_guess"] if row else "",
                    "page_label": row["page_label"] if row else "",
                    "old_confidence": "",
                    "new_ocr_metadata": "\n".join(text.splitlines()[:12]),
                    "local_qwen_review": item.get("result", {}).get("raw_response", ""),
                    "new_ocr_excerpt": text[:9000],
                }
            )
    system = """你是国内民盟史料 OCR 版本比较审核器。请只根据输入的旧页元数据、本地 Qwen 初筛和新 PaddleOCR 草稿给出结构化建议，不补造史实，不把推测写成原文。返回 JSON，顶层字段为 batch_summary、pages、import_decision。每个 pages 元素包含 page_id、candidate_quality（improved/mixed/worse）、search_value、needs_original_image、recommended_import（true/false）、reason、required_human_checks、citation_ready（固定 false）。recommended_import=true 只表示可以作为新的检索草稿候选，不表示可以引用。"""
    user = "请比较以下三页的新旧 OCR。平均置信度不是唯一标准，要同时看关键历史词、连续段落、乱码比例和版面顺序。对不能确认的词一律列为 required_human_checks。\n\n" + json.dumps(packets, ensure_ascii=False, indent=2)
    output = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    output_path = args.output if args.output.is_absolute() else Path.cwd() / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(packets), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
