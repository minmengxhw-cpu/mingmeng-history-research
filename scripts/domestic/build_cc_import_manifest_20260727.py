#!/usr/bin/env python3
"""Build the canonical SQLite import manifest for accepted CC OCR drafts.

The PaddleOCR batch outputs do not preserve per-page separators.  Therefore
each Markdown file is imported as one honest retrieval unit whose page_label
records the covered PDF range.  It must not be reported as one SQLite row per
physical PDF page.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/domestic"
SOURCE = WORK / "CLAUDE_PHASE5_IMPORT_CANDIDATE_MANIFEST_20260726.jsonl"
OUTPUT = WORK / "CC_ACCEPTED_IMPORT_MANIFEST_20260727.jsonl"
REPORT = WORK / "CC_ACCEPTED_IMPORT_MANIFEST_20260727.md"
EXCLUDED = {
    "P3-023": "OCR issue/article boundaries are still an automatic guess",
    "P3-GXMM-SH": "low-resolution trial-database image requires original review",
    "P3-GXMM-TJ": "low-resolution trial-database image requires original review",
}


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def page_label(path: Path, physical_pages: int) -> str:
    match = re.search(r"_p(\d{4})-(\d{4})\.ocr\.md$", path.name)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    if physical_pages <= 1:
        return "0001"
    return f"0001-{physical_pages:04d}"


def year_guess(text: str) -> str:
    years = re.findall(r"(?:19)(?:41|44|45|46|47|48|49)", text)
    return years[0] if years else ""


def main() -> int:
    candidates = read_jsonl(SOURCE)
    accepted = []
    errors = []
    for row in candidates:
        file_id = row["file_id"]
        if file_id in EXCLUDED:
            continue
        if row.get("dry_run_status") not in {"planned", "planned_with_review"}:
            errors.append(f"{file_id}: status={row.get('dry_run_status')}")
            continue
        source = ROOT / row["source_path"]
        expected = str(row.get("source_sha256", "")).lower()
        if not source.is_file() or len(expected) != 64 or sha256(source) != expected:
            errors.append(f"{file_id}: source/SHA gate failed")
            continue
        chunks = [ROOT / value for value in row.get("chunk_paths", [])]
        if not chunks or any(not value.is_file() for value in chunks):
            errors.append(f"{file_id}: OCR chunk missing")
            continue
        physical_pages = int(row.get("pdf_pages") or 0)
        title = Path(row["source_path"]).stem
        pages = [
            {
                "page_label": page_label(path, physical_pages),
                "ocr_markdown": str(path.relative_to(ROOT)),
                "mean_confidence": row.get("mean_confidence"),
                "ocr_status": "needs_human_review",
            }
            for path in chunks
        ]
        accepted.append({
            "record_id": f"COLLECTION:{file_id}:ocr-draft-20260727",
            "file_id": file_id,
            "title": title,
            "document_date": year_guess(title),
            "collection": "国内盟史一手资料 OCR 检索草稿",
            "source_kind": "public_scan",
            "source_path": row["source_path"],
            "source_sha256": expected,
            "source_url": "",
            "event_tags": ["国内盟史", "OCR检索草稿"] + ([year_guess(title)] if year_guess(title) else []),
            "physical_pdf_pages": physical_pages,
            "ocr_retrieval_units": len(pages),
            "citation_ready": False,
            "needs_human_review": True,
            "pages": pages,
        })
    if errors:
        raise SystemExit("manifest gate failed:\n- " + "\n- ".join(errors))
    if len(accepted) != 58:
        raise SystemExit(f"expected 58 accepted records, got {len(accepted)}")
    with OUTPUT.open("w", encoding="utf-8") as handle:
        for row in accepted:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    retrieval_units = sum(row["ocr_retrieval_units"] for row in accepted)
    physical_pages = sum(row["physical_pdf_pages"] for row in accepted)
    lines = [
        "# CC OCR 正式入库 Manifest（2026-07-27）",
        "",
        "## 口径",
        "",
        f"- 验收通过：{len(accepted)} 个文档。",
        f"- 原始 PDF/图像物理页：{physical_pages} 页。",
        f"- SQLite 检索单元：{retrieval_units} 条（按 OCR Markdown/chunk，而非伪造逐页记录）。",
        "- 全部保持 `citation_ready=false`、`needs_human_review=true`。",
        "",
        "## 排除",
        "",
    ]
    lines.extend(f"- `{key}`：{value}。" for key, value in EXCLUDED.items())
    lines.extend(["", "## 安全边界", "", "原始扫描件不入 Git；SQLite 正式库按 `.gitignore` 保持本地，GitHub 只提交 manifest、脚本、验收与阶段总结。", ""])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"records": len(accepted), "physical_pages": physical_pages, "retrieval_units": retrieval_units, "excluded": EXCLUDED}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
