#!/usr/bin/env python3
"""2x2 tiled OCR from an existing page image (staging only).

Used to improve dense low-confidence whole-page OCR (e.g. 天津大公报).
Does not write formal SQLite; no citation_ready / human_verified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FORMAL_DB = ROOT / "data/research_index.sqlite"
FORMAL_FROZEN = "822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3"
CST = timezone(timedelta(hours=8))
_OCR = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.now(CST).isoformat(timespec="seconds")


def relpath(path: Path) -> str:
    p = path if path.is_absolute() else (ROOT / path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def get_ocr():
    global _OCR
    if _OCR is None:
        from paddleocr import PaddleOCR

        _OCR = PaddleOCR(lang="ch")
    return _OCR


def run_paddle(image: Path) -> tuple[list[tuple[str, float]], float]:
    ocr = get_ocr()
    result = ocr.predict(str(image)) if hasattr(ocr, "predict") else ocr.ocr(str(image))
    lines: list[tuple[str, float]] = []
    if result is None:
        return [], 0.0
    if isinstance(result, list) and result and isinstance(result[0], dict):
        for page in result:
            texts = page.get("rec_texts") or []
            scores = page.get("rec_scores") or []
            for t, s in zip(texts, scores if scores else [0.0] * len(texts)):
                t = (t or "").strip()
                if t:
                    lines.append((t, float(s or 0.0)))
    else:
        pages = result if isinstance(result, list) else [result]
        for page in pages:
            if not page:
                continue
            for item in page:
                if not item or len(item) < 2:
                    continue
                rec = item[1]
                if isinstance(rec, (list, tuple)) and len(rec) >= 2:
                    t, s = str(rec[0]).strip(), float(rec[1] or 0.0)
                    if t:
                        lines.append((t, s))
    mean = sum(c for _, c in lines) / len(lines) if lines else 0.0
    return lines, mean


def compute_tiles(w: int, h: int, cols: int, rows: int, overlap: float):
    base_w, base_h = w / cols, h / rows
    ov_w, ov_h = base_w * overlap, base_h * overlap
    tiles = []
    for r in range(rows):
        for c in range(cols):
            x0 = int(round(c * base_w - (ov_w if c > 0 else 0)))
            x1 = int(round((c + 1) * base_w + (ov_w if c < cols - 1 else 0)))
            y0 = int(round(r * base_h - (ov_h if r > 0 else 0)))
            y1 = int(round((r + 1) * base_h + (ov_h if r < rows - 1 else 0)))
            tiles.append(
                {
                    "index": r * cols + c,
                    "row": r,
                    "col": c,
                    "bbox": [max(0, x0), max(0, y0), min(w, x1), min(h, y1)],
                }
            )
    return tiles


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=Path, required=True, help="TARGET.json")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--rows", type=int, default=2)
    ap.add_argument("--overlap", type=float, default=0.08)
    args = ap.parse_args()

    out = args.out if args.out.is_absolute() else ROOT / args.out
    out = out.resolve()
    tiles_dir = out / "tiles"
    ocr_dir = out / "ocr_md"
    for d in (tiles_dir, ocr_dir):
        d.mkdir(parents=True, exist_ok=True)

    target_path = args.target if args.target.is_absolute() else ROOT / args.target
    target = json.loads(target_path.read_text(encoding="utf-8"))
    img_rel = target["existing_image"]
    img = (ROOT / img_rel).resolve()
    if not img.exists():
        raise SystemExit(f"missing image {img}")

    from PIL import Image

    full = Image.open(img)
    w, h = full.size
    page_sha = sha256_file(img)
    tiles = compute_tiles(w, h, args.cols, args.rows, args.overlap)
    short = target["sha256"][:12]
    all_lines: list[tuple[str, float]] = []
    tile_recs: list[dict[str, Any]] = []
    t0 = time.time()

    for t in tiles:
        x0, y0, x1, y1 = t["bbox"]
        crop = full.crop((x0, y0, x1, y1))
        tile_path = tiles_dir / f"{short}__p1_r{t['row']}c{t['col']}.png"
        crop.save(tile_path)
        tile_sha = sha256_file(tile_path)
        lines, mean = run_paddle(tile_path)
        md_path = ocr_dir / f"{short}__p1_r{t['row']}c{t['col']}.md"
        body = [
            "---",
            f"tile_index: {t['index']}",
            f"row: {t['row']}",
            f"col: {t['col']}",
            f"bbox: {t['bbox']}",
            f"line_count: {len(lines)}",
            f"mean_confidence: {round(mean, 4)}",
            f"tile_image_sha256: {tile_sha}",
            "citation_ready: false",
            "human_verified: false",
            "---",
            "",
        ]
        for text, conf in lines:
            body.append(f"{text}  <!-- conf={conf:.4f} -->")
        md_path.write_text("\n".join(body) + "\n", encoding="utf-8")
        all_lines.extend(lines)
        tile_recs.append(
            {
                "index": t["index"],
                "row": t["row"],
                "col": t["col"],
                "bbox": t["bbox"],
                "image_path": relpath(tile_path),
                "image_sha256": tile_sha,
                "ocr_md_path": relpath(md_path),
                "ocr_md_sha256": sha256_file(md_path),
                "line_count": len(lines),
                "mean_confidence": round(mean, 4),
            }
        )
        print(
            f"  tile r{t['row']}c{t['col']} lines={len(lines)} conf={mean:.3f}",
            flush=True,
        )

    mean_all = sum(c for _, c in all_lines) / len(all_lines) if all_lines else 0.0
    merged = ocr_dir / f"{short}__p1_TILED_MERGED.md"
    mbody = [
        "---",
        f"source_sha256: {target['sha256']}",
        f"canonical_path: {target['canonical_path']}",
        f"page_index: {target.get('page_index', 0)}",
        f"mode: tiled_{args.cols}x{args.rows}",
        f"overlap: {args.overlap}",
        f"page_image: {img_rel}",
        f"page_image_sha256: {page_sha}",
        f"line_count: {len(all_lines)}",
        f"mean_confidence: {round(mean_all, 4)}",
        "citation_ready: false",
        "human_verified: false",
        "formal_db_apply: false",
        "---",
        "",
    ]
    for text, conf in all_lines:
        mbody.append(f"{text}  <!-- conf={conf:.4f} -->")
    merged.write_text("\n".join(mbody) + "\n", encoding="utf-8")

    wall = round(time.time() - t0, 2)
    row = {
        "sha256": target["sha256"],
        "canonical_path": target["canonical_path"],
        "page_index": target.get("page_index", 0),
        "printed_page": "unknown",
        "mode": f"tiled_{args.cols}x{args.rows}",
        "dpi": 110,
        "page_image_path": img_rel,
        "page_image_sha256": page_sha,
        "ocr_md_path": relpath(merged),
        "ocr_md_sha256": sha256_file(merged),
        "line_count": len(all_lines),
        "mean_confidence": round(mean_all, 4),
        "wall_seconds": wall,
        "model": "PaddleOCR/PP-OCRv6_medium lang=ch",
        "status": "PAGE_TILED_OCR_COMPLETE",
        "tile_grid": {"cols": args.cols, "rows": args.rows, "overlap": args.overlap},
        "tiles": tile_recs,
        "citation_ready": False,
        "human_verified": False,
        "formal_db_apply": False,
        "completed_at": now_iso(),
        "prior_whole_page_lines": 468,
        "prior_whole_page_conf": 0.4246,
    }
    man = out / "TILED_OCR_MANIFEST.jsonl"
    with man.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    formal = sha256_file(FORMAL_DB) if FORMAL_DB.exists() else None
    status = {
        "task": out.name,
        "finished_at": now_iso(),
        "ok": 1,
        "hold": 0,
        "line_count": len(all_lines),
        "mean_confidence": round(mean_all, 4),
        "wall_seconds": wall,
        "formal_db_sha": formal,
        "formal_unchanged": formal == FORMAL_FROZEN,
    }
    (out / "TILED_STATUS.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
