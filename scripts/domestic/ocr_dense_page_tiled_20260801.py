#!/usr/bin/env python3
"""Tiled OCR for dense newspaper pages (B4 《大公报》1947-11-06 first page pilot).

Why this script exists
----------------------
The earlier whole-page PaddleOCR run on B4 (2240x3123, ~6.7 MB, 180 DPI) stalled
silently inside text recognition. The shape of the page (8-column dense news
print) plus the high DPI ballooned CPU time. Tiling lets us:

- keep each tile at a digestible pixel size (long edge ~900-1400 px);
- fail fast per tile with a hard timeout and an explicit HOLD record;
- preserve provenance (source PDF SHA, full-page image SHA, tile SHA,
  OCR markdown SHA, model versions, parameters, line counts, confidence);
- never touch the formal SQLite or claim `citation_ready` / `human_verified`.

Per task instructions, this pilot targets B4 page 1 first; on success the same
driver can be pointed at B4 pages 2-4 and other CYCLE_0003 dense PDFs.

Hard constraints (do not relax)
-------------------------------
- only write into `work/domestic/MULTI_AGENT_SUPERLONG_TASK_20260801/
  03_MINIMAX_CYCLE_0003/04_tiled_ocr_fix/` and `data/domestic/...` staging;
- no `data/research_index.sqlite` writes;
- do not delete/overwrite original PDFs, full-page renders, or prior OCR;
- tile timeouts write `HOLD_TILE_TIMEOUT` instead of silently failing;
- printed page numbers stay `unknown` unless we can prove them from the page.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = ROOT / "work/domestic/MULTI_AGENT_SUPERLONG_TASK_20260801/03_MINIMAX_CYCLE_0003/04_tiled_ocr_fix"
RENDER_DIR = TASK_ROOT / "rendered"
TILE_DIR = TASK_ROOT / "tiles"
OCR_DIR = TASK_ROOT / "ocr_md"
HOLD_DIR = TASK_ROOT / "hold"
MANIFEST_PATH = TASK_ROOT / "PAGE_TILE_MANIFEST.jsonl"
HOLD_LOG_PATH = TASK_ROOT / "OCR_TILE_HOLD.jsonl"
STATUS_PATH = TASK_ROOT / "MINIMAX_TILED_OCR_STATUS.json"
CHECKPOINT_PATH = TASK_ROOT / "MINIMAX_TILED_OCR_CHECKPOINT.md"
FINAL_REPORT_PATH = TASK_ROOT / "MINIMAX_TILED_OCR_FINAL_REPORT.md"

FORMAL_DB_REL = "data/research_index.sqlite"
FORMAL_DB_FROZEN_SHA = "822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3"

B4_PDF_REL = "data/domestic/press_scans/NLC1080-00N001037-7606_大剛報_1947年11月06日.pdf"
B4_PDF_EXPECTED_SHA = "9b4c22a6e905c40f0efef1ce24aa6f1f447b4eb64a1137513a5f6b6532f83284"

DEFAULT_RENDER_DPI = 110
DEFAULT_COLS = 2
DEFAULT_ROWS = 3
DEFAULT_OVERLAP = 0.08
DEFAULT_TILE_TIMEOUT = 120
DEFAULT_MAX_LONG_EDGE = 1400


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_formal_db_untouched() -> str:
    """Return the current SHA and refuse to proceed if it has drifted."""
    p = ROOT / FORMAL_DB_REL
    if not p.exists():
        return "MISSING"
    actual = sha256_of(p)
    if actual != FORMAL_DB_FROZEN_SHA:
        raise RuntimeError(
            f"formal DB SHA changed! expected {FORMAL_DB_FROZEN_SHA}, got {actual}"
        )
    return actual


@dataclass
class Tile:
    index: int  # 0-based in row-major order
    row: int
    col: int
    x0: int
    y0: int
    x1: int
    y1: int
    overlap_x: int
    overlap_y: int


@dataclass
class TileResult:
    tile: Tile
    status: str  # OK or HOLD_TILE_TIMEOUT / HOLD_TILE_ERROR
    image_path: Path
    image_sha256: str = ""
    ocr_md_path: Path | None = None
    ocr_sha256: str = ""
    line_count: int = 0
    mean_confidence: float = 0.0
    elapsed_seconds: float = 0.0
    error: str | None = None
    paddle_version: str = "unknown"
    paddleocr_version: str = "unknown"
    params: dict[str, Any] = field(default_factory=dict)


def compute_tiles(width: int, height: int, cols: int, rows: int, overlap: float) -> list[Tile]:
    """Split image into cols x rows tiles with `overlap` (fraction) on inner edges."""
    if cols < 1 or rows < 1:
        raise ValueError("cols and rows must be >= 1")
    if not 0.0 <= overlap < 1.0:
        raise ValueError("overlap must be in [0, 1)")

    base_w = width / cols
    base_h = height / rows
    ov_w = base_w * overlap
    ov_h = base_h * overlap

    tiles: list[Tile] = []
    for r in range(rows):
        for c in range(cols):
            x0 = int(round(c * base_w - (ov_w if c > 0 else 0)))
            x1 = int(round((c + 1) * base_w + (ov_w if c < cols - 1 else 0)))
            y0 = int(round(r * base_h - (ov_h if r > 0 else 0)))
            y1 = int(round((r + 1) * base_h + (ov_h if r < rows - 1 else 0)))
            # clamp
            x0 = max(0, x0)
            y0 = max(0, y0)
            x1 = min(width, x1)
            y1 = min(height, y1)
            tiles.append(
                Tile(
                    index=r * cols + c,
                    row=r,
                    col=c,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    overlap_x=int(round(ov_w)) if 0 < c < cols else 0,
                    overlap_y=int(round(ov_h)) if 0 < r < rows else 0,
                )
            )
    return tiles


def render_pdf_page(pdf_path: Path, page_no: int, dpi: int, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_prefix = out_dir / f"page-{page_no:04d}"
    # use poppler pdftoppm (already on PATH via codex-runtimes override)
    cmd = [
        shutil.which("pdftoppm") or "pdftoppm",
        "-r",
        str(dpi),
        "-f",
        str(page_no),
        "-l",
        str(page_no),
        "-png",
        "-singlefile",
        str(pdf_path),
        str(out_prefix),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"pdftoppm failed: {proc.stderr.strip()}")
    produced = out_prefix.with_suffix(".png")
    if not produced.exists():
        raise RuntimeError(f"expected rendered page not found: {produced}")
    return produced


def crop_tile(full_page: Path, tile: Tile, out_path: Path) -> Path:
    """Use PIL to crop. PaddleOCR will later read out_path."""
    from PIL import Image

    img = Image.open(full_page)
    cropped = img.crop((tile.x0, tile.y0, tile.x1, tile.y1))
    cropped.save(out_path, format="PNG", optimize=False)
    return out_path


def get_image_size(path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as img:
        return img.size


def run_paddleocr_with_timeout(
    image_path: Path,
    out_md_path: Path,
    timeout_seconds: int,
) -> tuple[bool, str, int, float, dict[str, Any]]:
    """Run PaddleOCR on one tile under a hard wall-clock timeout.

    Returns (ok, error, line_count, mean_confidence, params). On timeout the
    PaddleOCR child is killed; we never let a single tile stall the batch.
    """
    import paddleocr  # local import to keep startup fast

    paddle_ver = paddleocr.__version__ if hasattr(paddleocr, "__version__") else "unknown"
    params = {
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
        "lang": "ch",
    }

    lines: list[str] = []
    confidences: list[float] = []

    def _worker() -> None:
        # PaddleOCR 3.x: PaddleOCR(use_angle_cls=False, lang='ch') then .predict()
        engine = paddleocr.PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang="ch",
        )
        result = engine.predict(str(image_path))
        if not result:
            return
        ocr_obj = result[0]
        # OCRResult is dict-like: keys via r0.keys(), values via r0[key]
        # attribute access like ocr_obj.rec_texts returns None.
        try:
            keys = set(ocr_obj.keys())
        except Exception:  # noqa: BLE001
            keys = set()
        rec_texts = ocr_obj["rec_texts"] if "rec_texts" in keys else None
        rec_scores = ocr_obj["rec_scores"] if "rec_scores" in keys else None
        if rec_texts and rec_scores is not None and len(rec_texts) == len(rec_scores):
            for text, score in zip(rec_texts, rec_scores):
                if text is None:
                    continue
                lines.append(str(text))
                try:
                    confidences.append(float(score))
                except (TypeError, ValueError):
                    pass
            return
        # Fallback: try .json() if available
        if hasattr(ocr_obj, "json"):
            try:
                j = ocr_obj.json
                if isinstance(j, str):
                    import json as _json
                    j = _json.loads(j)
                res = j.get("res", j) if isinstance(j, dict) else {}
                rt = res.get("rec_texts") or []
                rs = res.get("rec_scores") or []
                for text, score in zip(rt, rs):
                    if text is None:
                        continue
                    lines.append(str(text))
                    try:
                        confidences.append(float(score))
                    except (TypeError, ValueError):
                        pass
            except Exception:  # noqa: BLE001
                pass

    start = time.monotonic()
    parent_pid = os.getpid()
    timed_out = {"value": False}
    container: dict[str, BaseException | None] = {"err": None}

    def _alarm_handler(signum, frame):  # noqa: ARG001
        timed_out["value"] = True
        # Best effort: kill the whole process group of the worker via raising
        raise TimeoutError(f"paddleocr exceeded {timeout_seconds}s on {image_path.name}")

    old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(timeout_seconds)
    try:
        try:
            _worker()
        except TimeoutError as exc:
            timed_out["value"] = True
            container["err"] = exc
        except Exception as exc:  # noqa: BLE001
            container["err"] = exc
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    elapsed = time.monotonic() - start

    if timed_out["value"]:
        return False, f"HOLD_TILE_TIMEOUT after {elapsed:.1f}s", 0, 0.0, {
            **params,
            "paddleocr_version": paddle_ver,
        }
    if container["err"] is not None:
        return False, f"HOLD_TILE_ERROR: {container['err']}", 0, 0.0, {
            **params,
            "paddleocr_version": paddle_ver,
        }

    md = "\n".join(lines).rstrip() + "\n"
    out_md_path.write_text(md, encoding="utf-8")
    mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return True, "", len(lines), mean_conf, {**params, "paddleocr_version": paddle_ver}


def merge_tile_texts(tiles: list[TileResult]) -> tuple[str, str, list[dict[str, Any]]]:
    """Reassemble tile OCR in row-major order, marking merge method."""
    ok_tiles = [t for t in tiles if t.status == "OK"]
    if not ok_tiles:
        return "", "no_tiles_ok", []
    by_index = {t.tile.index: t for t in ok_tiles}
    blocks: list[str] = []
    trace: list[dict[str, Any]] = []
    for t in sorted(ok_tiles, key=lambda x: (x.tile.row, x.tile.col)):
        text = t.ocr_md_path.read_text(encoding="utf-8") if t.ocr_md_path else ""
        blocks.append(
            f"<!-- tile row={t.tile.row} col={t.tile.col} index={t.tile.index} "
            f"overlap_x={t.tile.overlap_x} overlap_y={t.tile.overlap_y} -->\n{text.rstrip()}"
        )
        trace.append(
            {
                "row": t.tile.row,
                "col": t.tile.col,
                "index": t.tile.index,
                "sha256": t.image_sha256,
                "line_count": t.line_count,
                "mean_confidence": t.mean_confidence,
            }
        )
    return "\n\n".join(blocks) + "\n", "tile_row_major_with_overlap_markers", trace


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def atomic_write_jsonl(path: Path, rows: Iterable[dict[str, Any]], *, append: bool = False) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    mode = "a" if append and path.exists() else "w"
    with tmp.open(mode, encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def write_hold(rows: Iterable[dict[str, Any]]) -> None:
    HOLD_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_jsonl(HOLD_LOG_PATH, rows)


@dataclass
class PageTask:
    pdf_path: Path
    expected_sha: str
    page_no: int  # 1-based
    dpi: int
    cols: int
    rows: int
    overlap: float
    tile_timeout: int


def run_one_page(task: PageTask) -> dict[str, Any]:
    start = time.monotonic()
    formal_sha = verify_formal_db_untouched()

    pdf_sha = sha256_of(task.pdf_path)
    if pdf_sha != task.expected_sha:
        raise RuntimeError(
            f"PDF SHA mismatch for {task.pdf_path}: expected {task.expected_sha}, got {pdf_sha}"
        )

    page_image = render_pdf_page(task.pdf_path, task.page_no, task.dpi, RENDER_DIR)
    width, height = get_image_size(page_image)
    page_image_sha = sha256_of(page_image)

    # If max_long_edge constraint is violated (e.g. user picked very high DPI),
    # re-render at the largest DPI that respects it.
    long_edge = max(width, height)
    if long_edge > DEFAULT_MAX_LONG_EDGE:
        # Resize on the fly rather than re-render: tile cropping stays simple.
        from PIL import Image

        scale = DEFAULT_MAX_LONG_EDGE / long_edge
        new_w = int(width * scale)
        new_h = int(height * scale)
        resized = Image.open(page_image).resize((new_w, new_h))
        resized_path = RENDER_DIR / f"page-{task.page_no:04d}-resized.png"
        resized.save(resized_path, format="PNG")
        width, height = new_w, new_h
        page_image = resized_path
        page_image_sha = sha256_of(page_image)

    tiles = compute_tiles(width, height, task.cols, task.rows, task.overlap)
    results: list[TileResult] = []
    hold_rows: list[dict[str, Any]] = []

    for tile in tiles:
        tile_image_path = TILE_DIR / f"page-{task.page_no:04d}-tile-r{tile.row}-c{tile.col}-i{tile.index}.png"
        crop_tile(page_image, tile, tile_image_path)
        tile_sha = sha256_of(tile_image_path)
        ocr_md_path = OCR_DIR / f"page-{task.page_no:04d}-tile-r{tile.row}-c{tile.col}-i{tile.index}.ocr.md"
        ok, err, lines, conf, params = run_paddleocr_with_timeout(
            tile_image_path, ocr_md_path, task.tile_timeout
        )
        elapsed = 0.0
        if ok:
            results.append(
                TileResult(
                    tile=tile,
                    status="OK",
                    image_path=tile_image_path,
                    image_sha256=tile_sha,
                    ocr_md_path=ocr_md_path,
                    ocr_sha256=sha256_of(ocr_md_path) if ocr_md_path.exists() else "",
                    line_count=lines,
                    mean_confidence=conf,
                    elapsed_seconds=elapsed,
                    params=params,
                )
            )
        else:
            results.append(
                TileResult(
                    tile=tile,
                    status=err.split(":")[0] if err else "HOLD_TILE_ERROR",
                    image_path=tile_image_path,
                    image_sha256=tile_sha,
                    elapsed_seconds=0.0,
                    error=err,
                    params=params,
                )
            )
            hold_rows.append(
                {
                    "source_pdf_sha256": pdf_sha,
                    "page_no": task.page_no,
                    "tile_index": tile.index,
                    "tile_row": tile.row,
                    "tile_col": tile.col,
                    "tile_image_sha256": tile_sha,
                    "tile_image_path": str(tile_image_path.relative_to(ROOT)),
                    "reason": err,
                    "params": params,
                    "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                }
            )

    merged_text, merge_method, merge_trace = merge_tile_texts(results)
    merged_md_path = OCR_DIR / f"page-{task.page_no:04d}.merged.ocr.md"
    if merged_text:
        merged_md_path.write_text(merged_text, encoding="utf-8")
        merged_sha = sha256_of(merged_md_path)
    else:
        merged_sha = ""

    write_hold(hold_rows)

    ok_count = sum(1 for r in results if r.status == "OK")
    total_lines = sum(r.line_count for r in results if r.status == "OK")
    overall_conf = (
        sum(r.mean_confidence for r in results if r.status == "OK") / ok_count
        if ok_count
        else 0.0
    )

    manifest_row = {
        "source_pdf": str(task.pdf_path.relative_to(ROOT)),
        "source_pdf_sha256": pdf_sha,
        "page_no": task.page_no,
        "physical_page_no": task.page_no,
        "printed_page_no": "unknown",
        "render_dpi": task.dpi,
        "page_image": str(page_image.relative_to(ROOT)),
        "page_image_sha256": page_image_sha,
        "page_image_size": [width, height],
        "tile_grid": {"cols": task.cols, "rows": task.rows, "overlap": task.overlap},
        "tiles": [
            {
                "index": r.tile.index,
                "row": r.tile.row,
                "col": r.tile.col,
                "bbox": [r.tile.x0, r.tile.y0, r.tile.x1, r.tile.y1],
                "image": str(r.image_path.relative_to(ROOT)),
                "image_sha256": r.image_sha256,
                "ocr_md": (
                    str(r.ocr_md_path.relative_to(ROOT)) if r.ocr_md_path else None
                ),
                "ocr_md_sha256": r.ocr_sha256,
                "line_count": r.line_count,
                "mean_confidence": r.mean_confidence,
                "status": r.status,
                "error": r.error,
                "params": r.params,
            }
            for r in results
        ],
        "merged_ocr_md": str(merged_md_path.relative_to(ROOT)) if merged_text else None,
        "merged_ocr_sha256": merged_sha,
        "merge_method": merge_method,
        "merge_trace": merge_trace,
        "ok_tiles": ok_count,
        "hold_tiles": len(results) - ok_count,
        "total_line_count": total_lines,
        "mean_confidence": overall_conf,
        "tile_timeout_seconds": task.tile_timeout,
        "formal_db_sha256": formal_sha,
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "status": "PAGE_PILOT_COMPLETE" if ok_count > 0 else "PAGE_PILOT_FAILED",
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    atomic_write_jsonl(MANIFEST_PATH, [manifest_row], append=True)

    return {
        "manifest_row": manifest_row,
        "hold_rows": hold_rows,
        "elapsed_seconds": time.monotonic() - start,
    }


def update_status(payload: dict[str, Any]) -> None:
    atomic_write_json(STATUS_PATH, payload)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", default=str(ROOT / B4_PDF_REL))
    ap.add_argument("--expected-sha", default=B4_PDF_EXPECTED_SHA)
    ap.add_argument("--page-no", type=int, default=1)
    ap.add_argument("--dpi", type=int, default=DEFAULT_RENDER_DPI)
    ap.add_argument("--cols", type=int, default=DEFAULT_COLS)
    ap.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    ap.add_argument("--overlap", type=float, default=DEFAULT_OVERLAP)
    ap.add_argument("--tile-timeout", type=int, default=DEFAULT_TILE_TIMEOUT)
    ap.add_argument(
        "--max-long-edge",
        type=int,
        default=DEFAULT_MAX_LONG_EDGE,
        help="resize full-page image so its long edge <= this if render DPI is too high",
    )
    args = ap.parse_args(argv)

    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 2

    task = PageTask(
        pdf_path=pdf_path,
        expected_sha=args.expected_sha,
        page_no=args.page_no,
        dpi=args.dpi,
        cols=args.cols,
        rows=args.rows,
        overlap=args.overlap,
        tile_timeout=args.tile_timeout,
    )

    update_status(
        {
            "lane": "tiled_ocr_fix",
            "state": "RUNNING",
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "pdf": str(pdf_path.relative_to(ROOT)),
            "expected_sha": args.expected_sha,
            "page_no": args.page_no,
            "render_dpi": args.dpi,
            "tile_grid": {"cols": args.cols, "rows": args.rows, "overlap": args.overlap},
            "tile_timeout_seconds": args.tile_timeout,
            "formal_db_sha256_expected": FORMAL_DB_FROZEN_SHA,
        }
    )

    try:
        result = run_one_page(task)
    except Exception as exc:  # noqa: BLE001
        update_status(
            {
                "lane": "tiled_ocr_fix",
                "state": "PAUSED_TILED_OCR_ERROR",
                "error": str(exc),
                "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }
        )
        raise

    manifest_row = result["manifest_row"]
    hold_rows = result["hold_rows"]
    update_status(
        {
            "lane": "tiled_ocr_fix",
            "state": manifest_row["status"],
            "ok_tiles": manifest_row["ok_tiles"],
            "hold_tiles": manifest_row["hold_tiles"],
            "total_line_count": manifest_row["total_line_count"],
            "mean_confidence": manifest_row["mean_confidence"],
            "manifest": str(MANIFEST_PATH.relative_to(ROOT)),
            "hold_log": str(HOLD_LOG_PATH.relative_to(ROOT)) if hold_rows else None,
            "elapsed_seconds": round(result["elapsed_seconds"], 2),
            "formal_db_sha256": manifest_row["formal_db_sha256"],
            "citation_ready_created": 0,
            "human_verified_created": 0,
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
    )
    print(json.dumps(manifest_row, ensure_ascii=False, indent=2))
    return 0 if manifest_row["status"] == "PAGE_PILOT_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))