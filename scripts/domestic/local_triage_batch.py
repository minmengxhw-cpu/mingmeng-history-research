#!/usr/bin/env python3
"""Use a local Ollama model to triage selected OCR pages without changing the corpus."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"


def prompt_for(row: sqlite3.Row, text: str) -> str:
    return f"""你是民盟史料 OCR 复核初筛器。你只能根据下面给出的 OCR 文本判断，不能补写原文、不能把猜测当事实，也不能宣布页面已经可以逐字引用。

请只返回一个 JSON 对象，字段必须是：
page_id（整数）、search_usable（true/false）、likely_ocr_problems（字符串数组）、suspicious_names_or_dates（字符串数组）、article_boundary_guess（字符串）、recommended_action（字符串）、citation_ready（固定为 false）。

判断重点：
1. 是否仍能用于检索定位；
2. 是否存在明显的倒序、栏序混乱、缺行、繁简/异体字问题；
3. 人名、日期、数字、标题是否需要回看原图；
4. 文章起止和续页关系能否从文本初步判断。

页面元数据：
page_id={row['id']}
题名={row['title']}
日期={row['date_guess'] or ''}
页码={row['page_label'] or ''}

OCR文本：
{text[:12000]}
"""


def clean_model_output(raw: str) -> str:
    raw = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", raw)
    return "".join(char for char in raw if char in "\n\r\t" or ord(char) >= 32)


def parse_model_output(raw: str) -> object:
    cleaned = clean_model_output(raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
    return {"raw_response": cleaned, "parse_error": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--page-id", type=int, action="append", required=True)
    parser.add_argument("--model", default="qwen3.5:9b")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    db_path = args.db if args.db.is_absolute() else Path.cwd() / args.db
    results = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for page_id in args.page_id:
            row = conn.execute(
                """
                SELECT p.id, p.page_label, p.text, d.title, d.date_guess
                FROM pages p JOIN documents d ON d.id=p.document_id
                WHERE p.id=? AND d.source_platform='domestic'
                """,
                (page_id,),
            ).fetchone()
            if not row:
                raise SystemExit(f"domestic page not found: {page_id}")
            command = [
                "ollama", "run", args.model,
                "--format", "json", "--think=false", "--hidethinking", "--keepalive", "10m",
                prompt_for(row, row["text"]),
            ]
            completed = subprocess.run(command, check=True, capture_output=True, text=True)
            raw = completed.stdout.strip()
            parsed = parse_model_output(raw)
            results.append({"page_id": page_id, "model": args.model, "triaged_at": datetime.now().isoformat(timespec="seconds"), "result": parsed})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"pages": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(results), "model": args.model, "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
