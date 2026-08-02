#!/usr/bin/env python3
"""Build an explicit, non-promoting MMDA original-acquisition queue.

This combines previously verified MMDA detail metadata with the current local
P1 intake queue. It intentionally creates only a work queue: no original file,
OCR object, formal database row, or citation-ready claim is created here.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BROWSER = ROOT / "work/domestic/mmda_browser_verified_20260722.jsonl"
DEFAULT_P1 = ROOT / "work/domestic/mmda_p1_intake_20260730/P1_INTAKE_MANIFEST.jsonl"
DEFAULT_OUT = ROOT / "work/domestic/mmda_p1_intake_20260730/MMDA_1942_1943_ORIGINAL_PENDING_QUEUE.jsonl"
DEFAULT_REPORT = ROOT / "work/domestic/mmda_p1_intake_20260730/MMDA_1942_1943_ORIGINAL_PENDING_REPORT.json"
BASE_URL = "http://www.minmeng1941.cn"


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid JSONL: {path}:{line_no}: {exc}") from exc
        if isinstance(row, dict):
            rows.append(row)
    return rows


def phase_of(value: Any) -> str | None:
    text = str(value or "").strip()
    if text.startswith("1942"):
        return "1942"
    if text.startswith("1943"):
        return "1943"
    return None


def url_for(path_value: Any) -> str | None:
    path = str(path_value or "").strip()
    if not path:
        return None
    return f"{BASE_URL}{path}" if path.startswith("/") else path


def browser_row(row: dict[str, Any]) -> dict[str, Any] | None:
    phase = phase_of(row.get("document_date"))
    if phase not in {"1942", "1943"}:
        return None
    pdf_path = row.get("pdf_path")
    preview_path = row.get("preview_path")
    if not pdf_path and not preview_path:
        return None
    return {
        "queue_id": row.get("record_id"),
        "phase": phase,
        "title": row.get("title"),
        "creator": row.get("creator"),
        "document_date": row.get("document_date"),
        "document_type": row.get("document_type"),
        "location": row.get("place_tags", []),
        "catalog_reference": row.get("catalog_reference"),
        "source_url": row.get("listing_url"),
        "pdf_path": pdf_path,
        "preview_path": preview_path,
        "pdf_url": url_for(pdf_path),
        "preview_url": url_for(preview_path),
        "source_evidence": "detail_metadata_verified_in_prior_login_session",
        "prior_file_status": row.get("file_status"),
        "acquisition_status": "ORIGINAL_PENDING",
        "citation_ready": False,
        "human_verified": False,
        "needs_browser_action": True,
        "next_action": "在已授权浏览器中打开详情/预览并下载原件；保存后计算 SHA，再进入 OCR staging",
        "do_not_promote": True,
        "uncertainty_note": row.get("uncertainty_note"),
    }


def p1_row(row: dict[str, Any]) -> dict[str, Any] | None:
    phase = phase_of(row.get("document_date"))
    if phase not in {"1942", "1943"}:
        return None
    candidate_id = row.get("candidate_id")
    return {
        "queue_id": candidate_id,
        "phase": phase,
        "title": row.get("title"),
        "creator": None,
        "document_date": row.get("document_date"),
        "document_type": "MMDA catalogue item",
        "location": [],
        "catalog_reference": row.get("catalog_reference"),
        "source_url": row.get("source_url"),
        "pdf_path": None,
        "preview_path": None,
        "pdf_url": None,
        "preview_url": None,
        "source_evidence": "catalogue_only_no_local_original",
        "prior_file_status": row.get("local_intake_status"),
        "acquisition_status": "ORIGINAL_PENDING",
        "citation_ready": False,
        "human_verified": bool(row.get("human_verified", False)),
        "needs_browser_action": True,
        "next_action": "在已授权浏览器中打开目录详情，记录可见原件路径/下载结果；不得凭标题推断正文",
        "do_not_promote": True,
        "uncertainty_note": "当前只有目录元数据，未取得原件、页图或正文。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser-manifest", type=Path, default=DEFAULT_BROWSER)
    parser.add_argument("--p1-manifest", type=Path, default=DEFAULT_P1)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    candidates: list[dict[str, Any]] = []
    for row in read_jsonl(args.browser_manifest):
        item = browser_row(row)
        if item:
            candidates.append(item)
    for row in read_jsonl(args.p1_manifest):
        item = p1_row(row)
        if item:
            candidates.append(item)

    deduped: dict[str, dict[str, Any]] = {}
    for item in candidates:
        key = str(item["queue_id"])
        if key in deduped:
            # Keep the richer detail record if both sources refer to one item.
            if deduped[key]["source_evidence"] == "catalogue_only_no_local_original":
                deduped[key] = item
        else:
            deduped[key] = item

    rows = sorted(deduped.values(), key=lambda item: (item["phase"], item["queue_id"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    by_phase: dict[str, int] = {"1942": 0, "1943": 0}
    by_evidence: dict[str, int] = {}
    for row in rows:
        by_phase[row["phase"]] += 1
        key = row["source_evidence"]
        by_evidence[key] = by_evidence.get(key, 0) + 1
    report = {
        "report": "MMDA_1942_1943_ORIGINAL_PENDING_QUEUE_20260730",
        "generated_on": date.today().isoformat(),
        "rows": len(rows),
        "phase_counts": by_phase,
        "source_evidence_counts": by_evidence,
        "original_files_present": 0,
        "citation_ready": 0,
        "formal_db_written": False,
        "raw_source_manifests_modified": False,
        "rule": "metadata and paths are acquisition leads only; original bytes, SHA, page provenance and OCR review are required before promotion",
        "inputs": [str(args.browser_manifest), str(args.p1_manifest)],
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
