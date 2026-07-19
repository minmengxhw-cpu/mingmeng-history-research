#!/usr/bin/env python3
"""Attach the local page-review paths to the Minxian article card."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "data/domestic/candidates.jsonl"
TARGET = "domestic:NLC:minxian-v1n9-democracy-vs-nondemocracy-1944-11-20"

rows = [json.loads(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
for row in rows:
    if row.get("candidate_id") == TARGET:
        row["evidence_locator"] += (
            "; work/domestic/minxian_1944_v1n9_pages/page-16.png至page-20.png"
        )
        row["evidence_note"] += " 本轮已逐页目视核对PDF第16—20页，确认文章页界闭合。"
        row["review_note"] = "已完成文章级原刊影像记录审核并接受；全文转录、异体字校对和原页署名仍待完成。"
        break
else:
    raise SystemExit(f"missing candidate: {TARGET}")

PATH.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
print(TARGET)

