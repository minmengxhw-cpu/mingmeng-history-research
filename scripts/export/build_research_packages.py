#!/usr/bin/env python3
"""Build per-platform research packages.

Each package contains:
- the platform research-paper PDF if present
- sourcebook PDF(s) if present
- a document-list CSV exported from the local SQLite index
- a manifest JSON
"""

from __future__ import annotations

import csv
import json
import shutil
import sqlite3
import zipfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "research_index.sqlite"
OUT_ROOT = ROOT / "output" / "research_packages"
PAPER_DIR = ROOT / "output" / "pdf"
SOURCEBOOK_DIR = ROOT / "workspace"


PLATFORMS = {
    "frus": "美国对外关系文件集",
    "drnh": "国民政府档案",
    "cia": "美国中央情报局解密档案",
    "hathitrust": "HathiTrust 数字典藏",
    "wilson": "威尔逊中心数字档案",
    "hoover": "胡佛研究所档案",
    "newspapersg": "NewspaperSG 南洋报刊",
}


def paper_path(platform: str) -> Path:
    return PAPER_DIR / f"mingmeng-{platform}-paper.pdf"


def sourcebook_paths(platform: str) -> list[Path]:
    if not SOURCEBOOK_DIR.exists():
        return []
    paths: list[Path] = []
    for path in sorted(SOURCEBOOK_DIR.glob("民盟史料长编_*.pdf")):
        key = path.name.rsplit("_", 1)[-1].removesuffix(".pdf")
        if key == platform:
            paths.append(path)
    return paths


def export_document_list(conn: sqlite3.Connection, platform: str, out_csv: Path) -> int:
    rows = conn.execute(
        """
        SELECT d.doc_key, d.title, d.date_guess, d.url,
               COALESCE(dc.grade, '') AS grade,
               COALESCE(dc.score, '') AS score,
               COALESCE(dc.reason, '') AS reason,
               (SELECT count(*) FROM pages p WHERE p.document_id=d.id) AS pages,
               (
                 SELECT count(*)
                 FROM pages p
                 JOIN translations t ON t.page_id=p.id AND t.language='zh-CN'
                 WHERE p.document_id=d.id
               ) AS zh_pages
        FROM documents d
        LEFT JOIN document_classifications dc ON dc.document_id=d.id
        WHERE d.source_platform=?
          AND COALESCE(dc.grade, '') <> '前台不展示'
        ORDER BY d.date_guess, d.doc_key
        """,
        (platform,),
    ).fetchall()
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["doc_key", "title", "date", "grade", "score", "pages", "zh_pages", "url", "reason"])
        for row in rows:
            writer.writerow(
                [
                    row["doc_key"],
                    row["title"],
                    row["date_guess"],
                    row["grade"],
                    row["score"],
                    row["pages"],
                    row["zh_pages"],
                    row["url"],
                    row["reason"],
                ]
            )
    return len(rows)


def build_platform(conn: sqlite3.Connection, platform: str, label: str) -> dict[str, object]:
    package_dir = OUT_ROOT / platform
    package_dir.mkdir(parents=True, exist_ok=True)

    files: list[dict[str, object]] = []
    p_pdf = paper_path(platform)
    if p_pdf.exists():
        dst = package_dir / p_pdf.name
        shutil.copy2(p_pdf, dst)
        files.append({"kind": "paper_pdf", "path": dst.name, "bytes": dst.stat().st_size})

    for sb in sourcebook_paths(platform):
        dst = package_dir / sb.name
        shutil.copy2(sb, dst)
        files.append({"kind": "sourcebook_pdf", "path": dst.name, "bytes": dst.stat().st_size})

    csv_path = package_dir / f"{platform}_documents.csv"
    doc_count = export_document_list(conn, platform, csv_path)
    files.append({"kind": "document_list_csv", "path": csv_path.name, "bytes": csv_path.stat().st_size})

    manifest = {
        "platform": platform,
        "label": label,
        "generated_at": date.today().isoformat(),
        "document_count": doc_count,
        "files": files,
        "notes": "Generated from local research_index.sqlite. Original archive PDFs/texts remain in the platform data directories.",
    }
    manifest_path = package_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    files.append({"kind": "manifest_json", "path": manifest_path.name, "bytes": manifest_path.stat().st_size})

    zip_path = OUT_ROOT / f"民盟研究资料包_{platform}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(package_dir.iterdir()):
            if path.is_file():
                zf.write(path, arcname=f"{platform}/{path.name}")

    manifest["zip_path"] = str(zip_path)
    manifest["zip_bytes"] = zip_path.stat().st_size
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    summaries = [build_platform(conn, key, label) for key, label in PLATFORMS.items()]
    conn.close()

    index_path = OUT_ROOT / "研究资料包索引.json"
    index_path.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in summaries:
        print(f"{item['platform']}: {item['document_count']} docs -> {item['zip_path']}")


if __name__ == "__main__":
    main()
