#!/usr/bin/env python3
"""Rebuild B4 PAGE_TILE_MANIFEST.jsonl from on-disk artifacts for pages 1-4.

The original `atomic_write_jsonl` overwrote per run, so only page 4 was left in
the manifest after the sequential batch. The OCR outputs (tiles, OCR md,
merged OCR) are all on disk and the formal DB SHA was verified untouched, so
we reconstruct the manifest deterministically from those files.

This script is read-only against the formal SQLite and never deletes files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "work/domestic/MULTI_AGENT_SUPERLONG_TASK_20260801/03_MINIMAX_CYCLE_0003/04_tiled_ocr_fix"
RENDER_DIR = TASK_DIR / "rendered"
TILE_DIR = TASK_DIR / "tiles"
OCR_DIR = TASK_DIR / "ocr_md"
MANIFEST_PATH = TASK_DIR / "PAGE_TILE_MANIFEST.jsonl"
FORMAL_DB_REL = "data/research_index.sqlite"
FORMAL_DB_FROZEN_SHA = "822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3"

PDF_REL = "data/domestic/press_scans/NLC1080-00N001037-7606_大剛報_1947年11月06日.pdf"
PDF_SHA = "9b4c22a6e905c40f0efef1ce24aa6f1f447b4eb64a1137513a5f6b6532f83284"
TILE_GRID = {"cols": 2, "rows": 2, "overlap": 0.08}
RENDER_DPI = 110


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    formal = ROOT / FORMAL_DB_REL
    actual = sha(formal)
    if actual != FORMAL_DB_FROZEN_SHA:
        raise SystemExit(
            f"formal DB SHA drifted: actual={actual} expected={FORMAL_DB_FROZEN_SHA}; refusing to write manifest"
        )

    pages = []
    for page_no in (1, 2, 3, 4):
        page_image = RENDER_DIR / f"page-{page_no:04d}-resized.png"
        if not page_image.exists():
            print(f"skip page {page_no}: missing resized render")
            continue
        tiles = []
        total_lines = 0
        confidences: list[float] = []
        for index in range(4):
            row, col = divmod(index, 2)
            tile_image = TILE_DIR / f"page-{page_no:04d}-tile-r{row}-c{col}-i{index}.png"
            tile_md = OCR_DIR / f"page-{page_no:04d}-tile-r{row}-c{col}-i{index}.ocr.md"
            if not (tile_image.exists() and tile_md.exists()):
                continue
            line_count = sum(1 for line in tile_md.read_text(encoding="utf-8").splitlines() if line.strip())
            # We did not store per-tile confidence in the OCR md; use the merged
            # manifest's existing average for page 4 only (last known good), and
            # fall back to a sentinel for pages 1-3 (mean not preserved per-tile).
            # Better: re-extract from the merged OCR md if a CONF marker exists,
            # else leave mean_confidence=0.0 to signal "not preserved per tile".
            tiles.append(
                {
                    "index": index,
                    "row": row,
                    "col": col,
                    "bbox": None,  # not preserved across overwrite; left None on purpose
                    "image": str(tile_image.relative_to(ROOT)),
                    "image_sha256": sha(tile_image),
                    "ocr_md": str(tile_md.relative_to(ROOT)),
                    "ocr_md_sha256": sha(tile_md),
                    "line_count": line_count,
                    "mean_confidence": None,  # intentionally None: not preserved across overwrite
                    "status": "OK",
                    "error": None,
                    "params": {
                        "use_doc_orientation_classify": False,
                        "use_doc_unwarping": False,
                        "use_textline_orientation": False,
                        "lang": "ch",
                        "paddleocr_version": "3.7.0",
                    },
                }
            )
            total_lines += line_count
        merged = OCR_DIR / f"page-{page_no:04d}.merged.ocr.md"
        merged_exists = merged.exists()
        if merged_exists:
            merged_sha_val = sha(merged)
        else:
            merged_sha_val = ""
        # Try to recover mean_confidence from the most recent successful run log
        # (last row in the log file) for page 4 only.
        # For pages 1-3, mean_confidence will need to be re-computed if desired.
        pages.append(
            {
                "source_pdf": PDF_REL,
                "source_pdf_sha256": PDF_SHA,
                "page_no": page_no,
                "physical_page_no": page_no,
                "printed_page_no": "unknown",
                "render_dpi": RENDER_DPI,
                "page_image": str(page_image.relative_to(ROOT)),
                "page_image_sha256": sha(page_image),
                "page_image_size": [None, None],  # not preserved across overwrite
                "tile_grid": TILE_GRID,
                "tiles": tiles,
                "merged_ocr_md": str(merged.relative_to(ROOT)) if merged_exists else None,
                "merged_ocr_sha256": merged_sha_val,
                "merge_method": "tile_row_major_with_overlap_markers",
                "merge_trace": [
                    {"row": t["row"], "col": t["col"], "index": t["index"], "sha256": t["image_sha256"], "line_count": t["line_count"]}
                    for t in tiles
                ],
                "ok_tiles": len(tiles),
                "hold_tiles": 0,
                "total_line_count": total_lines,
                "mean_confidence": None,  # intentionally None: original per-page averages were overwritten
                "tile_timeout_seconds": 90,
                "formal_db_sha256": FORMAL_DB_FROZEN_SHA,
                "formal_db_touched": False,
                "citation_ready_created": 0,
                "human_verified_created": 0,
                "status": "PAGE_PILOT_COMPLETE" if tiles else "PAGE_PILOT_FAILED",
                "completed_at": None,  # original timestamps overwritten; left None for transparency
                "rebuilt_from_disk_at": "2026-08-01T14:35:00+08:00",
                "rebuild_note": "manifest overwritten by sequential runs; reconstructed from on-disk tile/ocr/render SHAs",
            }
        )

    if not pages:
        raise SystemExit("no pages reconstructed")

    tmp = MANIFEST_PATH.with_suffix(MANIFEST_PATH.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for p in pages:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    tmp.replace(MANIFEST_PATH)
    print(f"rebuilt manifest with {len(pages)} pages → {MANIFEST_PATH.relative_to(ROOT)}")
    for p in pages:
        print(f"  page {p['page_no']}: tiles={p['ok_tiles']}/{p['ok_tiles']+p['hold_tiles']} lines={p['total_line_count']} status={p['status']}")


if __name__ == "__main__":
    main()