#!/usr/bin/env python3
"""Render and hash the 1946 PCC sourcebook target pages.

This is a local, metadata-only review aid. It verifies the source PDF SHA256,
renders only the six title pages plus explicitly listed adjacent pages, rotates
the scan for human reading, and writes a manifest under ``work/``. It never
changes the formal SQLite database, source PDF, citation flags, or research
packet contents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = ROOT / "data" / "domestic" / "pcc_1946_sourcebook_targets.json"
DEFAULT_OUTPUT = ROOT / "work" / "domestic" / "pcc_1946_sourcebook_render_20260814"
PDFFTOPPM_OVERRIDE = Path(
    "<local-user>/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def executable(name: str, fallback: Path | None = None) -> str:
    found = shutil.which(name)
    if found:
        return found
    if fallback and fallback.is_file():
        return str(fallback)
    raise RuntimeError(f"required executable not found: {name}")


def render_page(pdf: Path, pdf_page: int, output_dir: Path, dpi: int, pdftoppm: str, sips: str) -> dict[str, Any]:
    raw_prefix = output_dir / f"pdf-{pdf_page:03d}-raw"
    raw_png = raw_prefix.with_suffix(".png")
    rotated_png = output_dir / f"pdf-{pdf_page:03d}-r270.png"
    for existing in (raw_png, rotated_png):
        if existing.exists():
            raise RuntimeError(f"refusing to overwrite existing render: {existing}")
    subprocess.run(
        [
            pdftoppm,
            "-f",
            str(pdf_page),
            "-l",
            str(pdf_page),
            "-r",
            str(dpi),
            "-png",
            "-singlefile",
            str(pdf),
            str(raw_prefix),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    subprocess.run(
        [sips, "-r", "270", str(raw_png), "--out", str(rotated_png)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return {
        "pdf_page": pdf_page,
        "raw_image": str(raw_png.relative_to(ROOT)),
        "rotated_image": str(rotated_png.relative_to(ROOT)),
        "rotated_image_sha256": sha256(rotated_png),
        "rotated_image_bytes": rotated_png.stat().st_size,
        "visual_review_status": "pending",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    if args.dpi < 72:
        raise SystemExit("--dpi must be at least 72")

    source_map = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    source_path = ROOT / str(source_map["source_file"])
    if not source_path.is_file():
        raise SystemExit(f"source PDF not found: {source_path}")
    actual_sha = sha256(source_path)
    if actual_sha != source_map.get("source_sha256"):
        raise SystemExit(
            f"source SHA256 mismatch: expected {source_map.get('source_sha256')}, got {actual_sha}"
        )
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit(f"refusing to write into non-empty output directory: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)

    pdftoppm = executable("pdftoppm", PDFFTOPPM_OVERRIDE)
    sips = executable("sips", Path("/usr/bin/sips"))
    page_targets: dict[int, list[dict[str, str]]] = {}
    for target in source_map.get("targets", []):
        target_id = str(target.get("id") or "")
        start_page = int(target["pdf_page_start"])
        page_targets.setdefault(start_page, []).append({"target_id": target_id, "role": "title_start"})
        for adjacent in target.get("adjacent_pdf_pages", []):
            page_targets.setdefault(int(adjacent), []).append({"target_id": target_id, "role": "adjacent_boundary"})

    pages = [
        render_page(source_path, pdf_page, args.output, args.dpi, pdftoppm, sips)
        for pdf_page in sorted(page_targets)
    ]
    for page in pages:
        page["targets"] = page_targets[int(page["pdf_page"])]

    manifest = {
        "schema": "domestic_sourcebook_render_manifest.v1",
        "source_id": source_map.get("source_id"),
        "source_file": source_map.get("source_file"),
        "source_sha256": actual_sha,
        "page_count": source_map.get("page_count"),
        "render_dpi": args.dpi,
        "rotation": "270deg",
        "renderer": {"pdftoppm": pdftoppm, "sips": sips},
        "body_read": False,
        "formal_db_written": False,
        "citation_ready": False,
        "visual_review_status": "pending",
        "pages": pages,
    }
    manifest_path = args.output / "PAGE_RENDER_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "output": str(manifest_path.relative_to(ROOT)),
                "page_count": len(pages),
                "source_sha256": actual_sha,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
