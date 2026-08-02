#!/usr/bin/env python3
"""Stage B P0 OCR pilot wrapper over B4 tiled OCR driver.

Re-uses scripts/domestic/ocr_dense_page_tiled_20260801.py unchanged.
Candidates loaded from w2_stage_b_p0_candidates_20260801.jsonl (same dir).
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

R = Path(__file__).resolve().parents[2]
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import ocr_dense_page_tiled_20260801 as d  # noqa: E402

OUT = R / "work/domestic/MULTI_AGENT_SUPERLONG_TASK_20260801/16_MINIMAX_W2_TEXT_OCR_PILOT_20260801"
T = OUT / "P0_PILOT"
DPI = 110
FORMAL = "822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3"
CAND = H / "w2_stage_b_p0_candidates_20260801.jsonl"
MDL = {"name": "PaddleOCR", "version": "3.7.0", "lang": "ch"}


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _db():
    a = _sha(R / "data/research_index.sqlite")
    assert a == FORMAL, f"formal DB SHA drift: {a}"
    return a


def _render(pdf, n, dpi, out):
    """Per-PDF prefix render to avoid filename collision."""
    import shutil, subprocess
    out.mkdir(parents=True, exist_ok=True)
    pre = out / f"{pdf.stem.replace('/', '_')}__page-{n:04d}"
    cmd = [shutil.which("pdftoppm") or "pdftoppm", "-r", str(dpi),
           "-f", str(n), "-l", str(n), "-png", "-singlefile", str(pdf), str(pre)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"pdftoppm failed: {p.stderr.strip()}")
    o = pre.with_suffix(".png")
    assert o.exists()
    return o


def _row(pom, m, c, rsn, chars):
    """Stage B manifest row spec."""
    return {
        "manifest_row_id": f"POM-{pom:04d}", "page_no": m["page_no"],
        "source_sha256": m["source_pdf_sha256"],
        "source_registry_id": c["source_registry_id"],
        "render_dpi": m["render_dpi"], "render_size": m["page_image_size"],
        "tile_grid": m["tile_grid"], "tile_count_ok": m["ok_tiles"],
        "tile_count_hold": m["hold_tiles"], "tile_hold_reasons": rsn,
        "total_line_count": m["total_line_count"],
        "mean_confidence": round(m["mean_confidence"], 4), "merged_chars": chars,
        "model": MDL, "tile_timeout_seconds": m["tile_timeout_seconds"],
        "extraction_at": m["completed_at"],
        "merged_md_path": m.get("merged_ocr_md"),
        "merged_md_sha256": m.get("merged_ocr_sha256"),
        "page_render_sha256": m["page_image_sha256"],
        "hold": bool(rsn), "hold_reason": rsn[0] if rsn else None,
        "stage_b_batch": "STAGE_B_PILOT_20260801",
        "grok_mapping_ref": f"GROK_P0_SOURCE_MAPPING.jsonl#{c['mapping_id']}",
        "mapping_id": c["mapping_id"],
    }


def main():
    pre = _db()
    rd, td, od, hd = T/"rendered", T/"tiles", T/"ocr_md", T/"hold"
    for x in (rd, td, od, hd):
        x.mkdir(parents=True, exist_ok=True)
    d.RENDER_DIR, d.TILE_DIR, d.OCR_DIR, d.HOLD_DIR = rd, td, od, hd
    d.MANIFEST_PATH, d.HOLD_LOG_PATH = T/"INTERNAL_TILE_MANIFEST.jsonl", hd/"OCR_TILE_HOLD.jsonl"
    d.STATUS_PATH = T / "INTERNAL_TILE_STATUS.json"
    d.render_pdf_page = _render

    mf, hl = OUT / "P0_OCR_PILOT_MANIFEST.jsonl", OUT / "P0_OCR_HOLD.jsonl"
    pom, poh = 0, 0
    cs = [json.loads(l) for l in CAND.read_text().splitlines() if l.strip()]
    for c in cs:
        pdf = R / c["pdf_rel"]
        ps = pdf.stem.replace("/", "_")
        d.TILE_DIR, d.OCR_DIR = td/ps, od/ps
        d.TILE_DIR.mkdir(parents=True, exist_ok=True)
        d.OCR_DIR.mkdir(parents=True, exist_ok=True)
        o = d.run_one_page(d.PageTask(pdf, c["sha256"], 1, DPI, 2, 2, 0.08, 90))
        m = o["manifest_row"]
        chars = (m["merged_ocr_md"] and len(open(m["merged_ocr_md"]).read())) or 0
        rsn = sorted({t["error"] for t in m["tiles"] if t["status"] != "OK"})
        pom += 1
        with mf.open("a", encoding="utf-8") as f:
            f.write(json.dumps(_row(pom, m, c, rsn, chars), ensure_ascii=False) + "\n")
        for t in m["tiles"]:
            if t["status"] != "OK":
                poh += 1
                with hl.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "hold_id": f"POH-{poh:04d}",
                        "source_sha256": m["source_pdf_sha256"],
                        "source_registry_id": c["source_registry_id"],
                        "page_no": m["page_no"], "hold_type": "TILE",
                        "hold_reason": t.get("error", "unknown"),
                        "confidence": t.get("mean_confidence", 0.0),
                        "hold_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "mapping_id": c["mapping_id"],
                    }, ensure_ascii=False) + "\n")
    print(f"db_pre={pre} db_post={_db()} pages={pom} holds={poh}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())