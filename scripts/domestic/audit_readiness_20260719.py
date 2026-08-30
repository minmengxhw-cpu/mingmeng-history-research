#!/usr/bin/env python3
"""Audit domestic records for a truthful handoff and reproducible ingest."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data/domestic/candidates.jsonl"
REPORT = ROOT / "docs/domestic/收口审计_20260719.md"

REQUIRED = (
    "candidate_id", "title", "repository_code", "repository_name", "catalog_reference",
    "access_mode", "access_note", "rights_status", "authenticity_level_proposed",
    "relevance_grade_proposed", "event_tags", "person_tags", "place_tags", "evidence_note",
    "evidence_type", "uncertainty_note", "checked_at", "checked_by", "review_status",
)
PATH_RE = re.compile(r"(?<![A-Za-z0-9_.-])((?:data|work|index)/[^；，。、\s)]+?\.(?:pdf|png|jpg|jpeg|md|csv|sqlite))")


def main() -> int:
    rows = [json.loads(line) for line in CANDIDATES.read_text(encoding="utf-8").splitlines() if line.strip()]
    status = Counter(row["review_status"] for row in rows)
    levels = Counter(row["authenticity_level_proposed"] for row in rows)
    missing = []
    missing_paths = []
    for row in rows:
        absent = [key for key in REQUIRED if row.get(key) in (None, "")]
        if absent:
            missing.append((row["candidate_id"], absent))
        paths = []
        for raw in PATH_RE.findall(row.get("evidence_locator") or ""):
            candidate = ROOT / raw.rstrip("；，。")
            if not candidate.exists():
                missing_paths.append((row["candidate_id"], raw))

    lines = [
        "# 国内资料库收口审计",
        "",
        "审计日期：2026-07-19  ",
        "审计范围：`data/domestic/candidates.jsonl` 及候选定位中声明的本地文件  ",
        "审计目的：确认当前成果可复查、可重跑、并且不会把记录级接受误写成全文或原件闭环。",
        "",
        "## 数量",
        "",
        f"- 候选：{len(rows)}；状态：{dict(sorted(status.items()))}",
        f"- 证据等级：{dict(sorted(levels.items()))}",
        f"- 必填字段缺失记录：{len(missing)}",
        f"- 定位中明确声明但本地不存在的文件：{len(missing_paths)}",
        f"- accepted 记录：{status.get('accepted', 0)}（统一按记录级通过解释）",
        "",
        "## 结果",
        "",
        "- 候选结构和状态字段通过现有 `validate_candidates.py`；本审计没有修改候选状态。",
        "- accepted 仅表示记录级影像/目录身份、页级定位和审核字段齐全；全文转录、版权、原始形成机关文件仍按各条 `uncertainty_note` 处理。",
        "- `needs_human_review` 是当前主工作队列；不能用总数增长或 accepted 数量替代原始证据闭环。",
    ]
    if missing:
        lines.extend(["", "## 缺失必填字段", "", *[f"- `{cid}`：{', '.join(keys)}" for cid, keys in missing]])
    if missing_paths:
        lines.extend(["", "## 缺失本地文件定位", "", *[f"- `{cid}`：`{path}`" for cid, path in missing_paths]])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(rows), "missing_required": len(missing), "missing_paths": len(missing_paths), "accepted_records": status.get("accepted", 0), "report": str(REPORT)}, ensure_ascii=False))
    return 1 if missing or missing_paths else 0


if __name__ == "__main__":
    raise SystemExit(main())
