#!/usr/bin/env python3
"""Build a conservative, non-destructive period-correction candidate layer.

Only explicit years present in local manifest paths/titles are extracted.  The
source historical_phase is never overwritten and no formal SQLite is opened
for writing.  Candidates with no explicit evidence remain HOLD.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "work/domestic/phase0_reconciliation_20260730/PAGE_ASSETS.jsonl"
OUT = ROOT / "work/domestic/period_correction_candidates_20260730"

YEAR_RE = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")
ROC_RE = re.compile(r"民国\s*(\d{1,3})\s*年")


def year_evidence(text: str) -> list[dict]:
    evidence: list[dict] = []
    for match in YEAR_RE.finditer(text):
        year = int(match.group(1))
        if 1900 <= year <= 2099:
            evidence.append({"year": year, "kind": "gregorian_explicit", "text": match.group(1)})
    for match in ROC_RE.finditer(text):
        year = 1911 + int(match.group(1))
        if 1912 <= year <= 2010:
            evidence.append({"year": year, "kind": "republic_era_derived", "text": match.group(0)})
    return evidence


def main() -> int:
    if not INPUT.exists():
        raise SystemExit(f"missing input: {INPUT}")
    grouped: dict[str, dict] = {}
    for line in INPUT.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = str(row.get("canonical_document_key") or row.get("object_id") or "unknown")
        item = grouped.setdefault(
            key,
            {
                "canonical_document_key": key,
                "source_phases": Counter(),
                "observed_years": Counter(),
                "evidence": [],
                "paths": set(),
                "titles": set(),
            },
        )
        source_phase = str(row.get("historical_phase") or "unknown")
        item["source_phases"][source_phase] += 1
        path = str(row.get("local_path") or "")
        title = str(row.get("title") or "")
        item["paths"].add(path)
        item["titles"].add(title)
        for source, text in (("local_path", path), ("title", title)):
            for ev in year_evidence(text):
                record = {"source": source, **ev}
                item["evidence"].append(record)
                item["observed_years"][ev["year"]] += 1

    candidates: list[dict] = []
    for key, item in sorted(grouped.items()):
        years = item["observed_years"]
        if len(years) == 1:
            year = next(iter(years))
            kinds = {x["kind"] for x in item["evidence"] if x["year"] == year}
            confidence = "HIGH" if kinds == {"gregorian_explicit"} else "MEDIUM"
            status = "CANDIDATE_REVIEW"
            proposed = str(year)
            reason = "explicit year in local path/title"
        elif len(years) > 1:
            confidence = "LOW"
            status = "HOLD_CONFLICT"
            proposed = None
            reason = "multiple explicit years in one canonical object"
        else:
            confidence = "NONE"
            status = "HOLD_NO_DATE_EVIDENCE"
            proposed = None
            reason = "no explicit Gregorian or Republic-era year in local path/title"
        candidates.append(
            {
                "canonical_document_key": key,
                "source_phase": item["source_phases"].most_common(1)[0][0],
                "source_phase_counts": dict(item["source_phases"]),
                "proposed_period": proposed,
                "confidence": confidence,
                "status": status,
                "reason": reason,
                "evidence": item["evidence"],
                "paths": sorted(x for x in item["paths"] if x),
                "titles": sorted(x for x in item["titles"] if x),
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "PERIOD_CORRECTION_CANDIDATES.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in candidates)
    )
    status_counts = Counter(x["status"] for x in candidates)
    confidence_counts = Counter(x["confidence"] for x in candidates)
    report = {
        "report": "DOMESTIC_PERIOD_CORRECTION_CANDIDATES_20260730",
        "input": str(INPUT),
        "canonical_documents": len(candidates),
        "status_counts": dict(status_counts),
        "confidence_counts": dict(confidence_counts),
        "non_destructive": True,
        "formal_db_written": False,
        "rule": "extract explicit Gregorian/Republic-era years from local path/title only",
    }
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    md = [
        "# 国内资料年代纠偏候选层",
        "",
        "本层只提取本地 manifest 文件名/标题中的明确年份；不修改原始队列、不修改正式库。",
        "",
        f"- canonical 文献对象：{len(candidates)}",
        f"- 可审阅候选：{status_counts.get('CANDIDATE_REVIEW', 0)}",
        f"- 冲突待处理：{status_counts.get('HOLD_CONFLICT', 0)}",
        f"- 无日期证据：{status_counts.get('HOLD_NO_DATE_EVIDENCE', 0)}",
        f"- 正式库写入：{report['formal_db_written']}",
        "",
        "## 使用规则",
        "",
        "`HIGH` 仅表示文件名/标题含明确公历年份，不等同于内容核验；`MEDIUM` 表示由民国纪年换算而来。任何年代写入 citation-ready 层前仍需保留原始字符串、SHA 和页级证据。",
    ]
    (OUT / "REPORT.md").write_text("\n".join(md) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
