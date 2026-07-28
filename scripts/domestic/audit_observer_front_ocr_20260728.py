#!/usr/bin/env python3
"""Audit the bounded Observer front/contents OCR batch before SQLite import."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISSUES = ROOT / "work/domestic/OBSERVER_V3_ISSUE_MANIFEST_20260728.jsonl"
PAGES = ROOT / "work/domestic/OBSERVER_FRONT_OCR_MANIFEST_20260728.jsonl"
OUT_JSON = ROOT / "work/domestic/OBSERVER_FRONT_OCR_QA_20260728.json"
OUT_MD = ROOT / "work/domestic/OBSERVER_FRONT_OCR_QA_20260728.md"
CONF_RE = re.compile(r"平均置信度：([0-9.]+)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    issues = load(ISSUES)
    pages = load(PAGES)
    errors: list[str] = []
    page_stats: list[dict] = []
    issue_by_number = {int(row["issue_number"]): row for row in issues}
    page_by_issue: dict[int, list[dict]] = defaultdict(list)
    for row in pages:
        issue = int(row["issue_number"])
        page_by_issue[issue].append(row)
        path = ROOT / row["ocr_markdown"]
        if not path.is_file():
            errors.append(f"{row['record_id']}: missing OCR markdown")
            continue
        actual = sha256(path)
        if actual != row.get("ocr_markdown_sha256"):
            errors.append(f"{row['record_id']}: OCR markdown SHA256 mismatch")
        text = path.read_text(encoding="utf-8")
        match = CONF_RE.search(text)
        confidence = float(match.group(1)) if match else None
        recognized = text.split("## 识别文本", 1)[-1].split("## 明细", 1)[0].strip()
        if not recognized:
            errors.append(f"{row['record_id']}: empty recognized text")
        if confidence is None or confidence < 0.80:
            errors.append(f"{row['record_id']}: confidence below 0.80")
        if row.get("citation_ready") is not False:
            errors.append(f"{row['record_id']}: citation_ready must remain false")
        issue_manifest = issue_by_number.get(issue)
        if not issue_manifest:
            errors.append(f"{row['record_id']}: issue missing from boundary manifest")
        elif row.get("source_pdf_sha256") != issue_manifest.get("derived_issue_sha256"):
            errors.append(f"{row['record_id']}: derived PDF SHA mismatch")
        page_stats.append({
            "record_id": row["record_id"],
            "issue_number": issue,
            "page_label": row["page_label"],
            "confidence": confidence,
            "recognized_chars": len(recognized),
            "ocr_markdown": row["ocr_markdown"],
        })
    for issue in range(1, 13):
        labels = {row["page_label"] for row in page_by_issue.get(issue, [])}
        if labels != {"front-01", "front-02"}:
            errors.append(f"issue {issue}: expected front-01/front-02, got {sorted(labels)}")

    confidences = [row["confidence"] for row in page_stats if row["confidence"] is not None]
    result = {
        "gate": "PASS" if not errors else "FAIL",
        "issues": len(issues),
        "ocr_pages": len(pages),
        "verified_pages": len(page_stats),
        "confidence": {
            "min": min(confidences) if confidences else None,
            "mean": sum(confidences) / len(confidences) if confidences else None,
            "max": max(confidences) if confidences else None,
        },
        "errors": errors,
        "pages": page_stats,
        "import_policy": "review_only; citation_ready=false; needs_human_review=true",
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# 《观察》第三卷封面/目录 OCR QA（2026-07-28）",
        "",
        f"- 门控：`{result['gate']}`",
        f"- 期数：{len(issues)}；OCR 页：{len(pages)}；已核验：{len(page_stats)}",
        f"- 平均置信度：{result['confidence']['mean']:.4f}",
        f"- 最低/最高置信度：{result['confidence']['min']:.4f} / {result['confidence']['max']:.4f}",
        "- 入库政策：仅作为 review-only 检索草稿；`citation_ready=false`、`needs_human_review=true`。",
        "",
    ]
    if errors:
        lines.extend(["## 错误", "", *[f"- {error}" for error in errors], ""])
    else:
        lines.extend(["## 结论", "", "24 页文件存在、SHA256 一致、置信度门槛通过、每期封面/目录配对完整，可进入 review-only SQLite 入库。", ""])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"gate": result["gate"], "pages": len(page_stats), "errors": len(errors), "qa": str(OUT_MD)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
