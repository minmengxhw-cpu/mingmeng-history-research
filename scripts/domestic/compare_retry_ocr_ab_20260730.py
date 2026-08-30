#!/usr/bin/env python3
"""Compare isolated retry OCR outputs with the original OCR drafts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work" / "domestic" / "minimax_two_month_20260730" / "w2"


def text_chars(path: Path) -> int:
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    return len(text.split("## 识别文本", 1)[-1])


def main() -> None:
    triage = [json.loads(line) for line in (OUT / "w1" / "UNREADABLE_TRIAGE.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()] if (OUT / "w1" / "UNREADABLE_TRIAGE.jsonl").exists() else []
    # W1 lives one directory above w2 in this project layout.
    if not triage:
        triage = [json.loads(line) for line in (ROOT / "work/domestic/minimax_two_month_20260730/w1/UNREADABLE_TRIAGE.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    originals = {str(row["page_id"]): row for row in triage}
    comparisons = []
    for manifest in sorted(OUT.glob("retry_ocr_pilot*/RETRY_OCR_MANIFEST.jsonl")):
        row = json.loads(manifest.read_text(encoding="utf-8").splitlines()[0])
        original = originals.get(str(row["page_id"]), {})
        original_path = ROOT / str(original.get("ocr_md_path", ""))
        retry_path = ROOT / row["retry_ocr_md"]
        old_conf = float(original.get("ocr_mean_confidence") or 0)
        new_conf = float(row.get("mean_confidence") or 0)
        comparisons.append(
            {
                "page_id": row["page_id"],
                "source_id": row["source_id"],
                "original_ocr_path": original.get("ocr_md_path", ""),
                "retry_ocr_path": row["retry_ocr_md"],
                "original_mean_confidence": old_conf,
                "retry_mean_confidence": new_conf,
                "confidence_delta": round(new_conf - old_conf, 6),
                "original_text_chars": text_chars(original_path),
                "retry_text_chars": text_chars(retry_path),
                "disposition": "REVIEW_ONLY_NO_AUTO_REPLACEMENT",
            }
        )
    report = {
        "report": "RETRY_OCR_AB_COMPARISON_20260730",
        "pages_compared": len(comparisons),
        "improved_confidence": sum(item["confidence_delta"] > 0 for item in comparisons),
        "reduced_or_equal_confidence": sum(item["confidence_delta"] <= 0 for item in comparisons),
        "auto_replacements": 0,
        "formal_db_written": False,
        "comparisons": comparisons,
        "rule": "confidence delta is a triage signal only; no OCR is promoted without review",
    }
    (OUT / "RETRY_OCR_AB_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
