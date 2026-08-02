#!/usr/bin/env python3
"""Triage newly re-OCRed candidate Markdown files with the local Ollama model."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

from local_triage_batch import parse_model_output, prompt_for


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--candidate", action="append", required=True, help="page_id=path/to/ocr.md")
    parser.add_argument("--model", default="qwen3.5:9b")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    db_path = args.db if args.db.is_absolute() else Path.cwd() / args.db
    results = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for value in args.candidate:
            page_id_text, path_text = value.split("=", 1)
            page_id = int(page_id_text)
            path = Path(path_text)
            if not path.is_absolute():
                path = Path.cwd() / path
            row = conn.execute(
                "SELECT p.id,p.page_label,d.title,d.date_guess FROM pages p JOIN documents d ON d.id=p.document_id WHERE p.id=? AND d.source_platform='domestic'",
                (page_id,),
            ).fetchone()
            if not row:
                raise SystemExit(f"domestic page not found: {page_id}")
            text = path.read_text(encoding="utf-8", errors="replace")
            command = ["ollama", "run", args.model, "--format", "json", "--think=false", "--hidethinking", "--keepalive", "10m", prompt_for(row, text)]
            completed = subprocess.run(command, check=True, capture_output=True, text=True)
            results.append({"page_id": page_id, "candidate_path": str(path), "model": args.model, "triaged_at": datetime.now().isoformat(timespec="seconds"), "result": parse_model_output(completed.stdout)})
    output = args.output if args.output.is_absolute() else Path.cwd() / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"pages": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(results), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
