#!/usr/bin/env python3
"""Expand whole-page OCR for selected PDF pages (staging only).

Constraints:
- no formal SQLite writes
- no citation_ready / human_verified claims
- default page_index=0 (page 1); list items may set page_index
- printed page stays unknown unless proven
- HOLD on missing path / render / OCR failure
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
DEFAULT_OUT = (
    ROOT
    / "work/domestic/MULTI_AGENT_SUPERLONG_TASK_20260801"
    / "16_MINIMAX_OCR_FROM_GROK_QUEUE_20260801"
    / "W2_EXPAND_P0_PAGE1_B2"
)
FORMAL_DB = ROOT / "data/research_index.sqlite"
FORMAL_FROZEN = "822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3"
CST = timezone(timedelta(hours=8))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.now(CST).isoformat(timespec="seconds")


def render_page(
    pdf: Path, out_png: Path, page_index: int = 0, dpi: int = 110
) -> tuple[int, int]:
    import fitz  # PyMuPDF

    doc = fitz.open(pdf)
    try:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(f"page_index {page_index} out of range (pages={len(doc)})")
        page = doc[page_index]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_png.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(out_png))
        return pix.width, pix.height
    finally:
        doc.close()


_OCR_ENGINE = None


def get_ocr():
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        from paddleocr import PaddleOCR

        _OCR_ENGINE = PaddleOCR(lang="ch")
    return _OCR_ENGINE


def run_paddle(image: Path) -> tuple[list[tuple[str, float]], float]:
    """Return (lines of (text, conf), mean_conf)."""
    ocr = get_ocr()
    if hasattr(ocr, "predict"):
        result = ocr.predict(str(image))
    else:
        result = ocr.ocr(str(image))

    lines: list[tuple[str, float]] = []
    if result is None:
        return [], 0.0

    # New API: list of dict-like page results
    if isinstance(result, list) and result and isinstance(result[0], dict):
        for page in result:
            texts = page.get("rec_texts") or page.get("texts") or []
            scores = page.get("rec_scores") or page.get("scores") or []
            for t, s in zip(texts, scores if scores else [0.0] * len(texts)):
                t = (t or "").strip()
                if t:
                    lines.append((t, float(s or 0.0)))
    else:
        # Classic: [[[box, (text, score)], ...]] or [[box, (text, score)], ...]
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
                elif isinstance(rec, str) and rec.strip():
                    lines.append((rec.strip(), 0.0))

    mean = sum(c for _, c in lines) / len(lines) if lines else 0.0
    return lines, mean


def write_md(lines: list[tuple[str, float]], meta: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "---",
        f"source_sha256: {meta['sha256']}",
        f"canonical_path: {meta['canonical_path']}",
        f"page_index: {meta.get('page_index', 0)}",
        f"printed_page: unknown",
        f"dpi: {meta['dpi']}",
        f"mode: {meta.get('mode', 'whole_page')}",
        f"model: {meta['model']}",
        f"line_count: {meta['line_count']}",
        f"mean_confidence: {meta['mean_confidence']}",
        f"image_sha256: {meta['image_sha256']}",
        f"citation_ready: false",
        f"human_verified: false",
        f"formal_db_apply: false",
        "---",
        "",
    ]
    for t, c in lines:
        body.append(f"{t}  <!-- conf={c:.4f} -->")
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def relpath(path: Path) -> str:
    """Safe repo-relative path (handles absolute/relative inputs)."""
    p = path if path.is_absolute() else (ROOT / path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", type=Path, required=True, help="BATCH_LIST.json")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument(
        "--default-page-index",
        type=int,
        default=0,
        help="page_index used when list item omits page_index (0-based)",
    )
    ap.add_argument(
        "--manifest-name",
        type=str,
        default="EXPAND_OCR_MANIFEST.jsonl",
        help="manifest filename under --out",
    )
    ap.add_argument(
        "--hold-name",
        type=str,
        default="EXPAND_OCR_HOLD.jsonl",
        help="hold filename under --out",
    )
    ap.add_argument(
        "--status-name",
        type=str,
        default="EXPAND_OCR_STATUS.json",
        help="status filename under --out",
    )
    args = ap.parse_args()

    list_path = args.list if args.list.is_absolute() else ROOT / args.list
    out: Path = args.out if args.out.is_absolute() else ROOT / args.out
    out = out.resolve()
    rendered = out / "rendered"
    ocr_md = out / "ocr_md"
    hold_dir = out / "hold"
    for d in (rendered, ocr_md, hold_dir):
        d.mkdir(parents=True, exist_ok=True)

    formal_sha = sha256_file(FORMAL_DB) if FORMAL_DB.exists() else None
    if formal_sha != FORMAL_FROZEN:
        print(f"WARN formal SHA mismatch: {formal_sha} expected {FORMAL_FROZEN}")

    items = json.loads(list_path.read_text(encoding="utf-8"))
    if args.limit:
        items = items[: args.limit]

    manifest_path = out / args.manifest_name
    hold_path = out / args.hold_name
    # resume: skip existing (sha, page_index) in manifest
    done: set[tuple[str, int]] = set()
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                done.add((row["sha256"], int(row.get("page_index", 0))))
            except Exception:
                pass

    model = "PaddleOCR/PP-OCRv6_medium lang=ch"
    ok = hold = skip = 0

    with manifest_path.open("a", encoding="utf-8") as mf, hold_path.open(
        "a", encoding="utf-8"
    ) as hf:
        for i, item in enumerate(items, 1):
            sha = item["sha256"]
            rel = item["canonical_path"]
            page_index = int(item.get("page_index", args.default_page_index))
            pdf = (ROOT / rel).resolve()
            short = sha[:12]
            ptag = f"p{page_index + 1}"
            print(
                f"[{i}/{len(items)}] {Path(rel).name} short={short} page_index={page_index}",
                flush=True,
            )
            if (sha, page_index) in done:
                print("  skip already in manifest", flush=True)
                skip += 1
                continue
            if not pdf.exists():
                rec = {
                    "sha256": sha,
                    "canonical_path": rel,
                    "page_index": page_index,
                    "status": "HOLD_MISSING_FILE",
                    "at": now_iso(),
                }
                hf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                hf.flush()
                hold += 1
                print("  HOLD missing", flush=True)
                continue

            img = rendered / f"{short}__{ptag}_{args.dpi}dpi.png"
            md = ocr_md / f"{short}__{ptag}.md"
            t0 = time.time()
            try:
                w, h = render_page(pdf, img, page_index=page_index, dpi=args.dpi)
                img_sha = sha256_file(img)
                lines, mean = run_paddle(img)
                wall = round(time.time() - t0, 2)
                meta = {
                    "sha256": sha,
                    "canonical_path": rel,
                    "page_index": page_index,
                    "printed_page": "unknown",
                    "mode": "whole_page",
                    "dpi": args.dpi,
                    "image_path": relpath(img),
                    "image_sha256": img_sha,
                    "image_width": w,
                    "image_height": h,
                    "ocr_md_path": relpath(md),
                    "line_count": len(lines),
                    "mean_confidence": round(mean, 4),
                    "wall_seconds": wall,
                    "model": model,
                    "status": "PAGE_OCR_COMPLETE",
                    "citation_ready": False,
                    "human_verified": False,
                    "formal_db_apply": False,
                    "bucket": item.get("bucket"),
                    "completed_at": now_iso(),
                }
                write_md(lines, meta, md)
                meta["ocr_md_sha256"] = sha256_file(md)
                mf.write(json.dumps(meta, ensure_ascii=False) + "\n")
                mf.flush()
                ok += 1
                print(
                    f"  OK lines={len(lines)} conf={mean:.3f} wall={wall}s",
                    flush=True,
                )
            except Exception as e:
                wall = round(time.time() - t0, 2)
                rec = {
                    "sha256": sha,
                    "canonical_path": rel,
                    "page_index": page_index,
                    "status": "HOLD_OCR_ERROR",
                    "error": f"{type(e).__name__}: {e}",
                    "wall_seconds": wall,
                    "at": now_iso(),
                }
                hf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                hf.flush()
                hold += 1
                print(f"  HOLD {rec['error'][:200]}", flush=True)

    formal_after = sha256_file(FORMAL_DB) if FORMAL_DB.exists() else None
    status = {
        "task": out.name,
        "finished_at": now_iso(),
        "ok": ok,
        "hold": hold,
        "skip": skip,
        "default_page_index": args.default_page_index,
        "manifest": relpath(manifest_path),
        "formal_db_sha_before": formal_sha,
        "formal_db_sha_after": formal_after,
        "formal_unchanged": formal_sha == formal_after == FORMAL_FROZEN,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    (out / args.status_name).write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if hold == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
