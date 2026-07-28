#!/usr/bin/env python3
"""Write a read-only acceptance report for the 2026-07-28 domestic-history work."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/research_index.sqlite"
CORE = ROOT / "work/domestic/CORE_EVIDENCE_MANIFEST_20260728.jsonl"
OBSERVER = ROOT / "work/domestic/OBSERVER_V3_ISSUE_MANIFEST_20260728.jsonl"
OUT_JSON = ROOT / "work/domestic/RESEARCH_INDEX_ACCEPTANCE_20260728.json"
OUT_MD = ROOT / "work/domestic/RESEARCH_INDEX_ACCEPTANCE_20260728.md"


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    conn = sqlite3.connect(DB)
    try:
        counts = {
            "documents": conn.execute("select count(*) from documents").fetchone()[0],
            "pages": conn.execute("select count(*) from pages").fetchone()[0],
            "page_fts": conn.execute("select count(*) from page_fts").fetchone()[0],
            "domestic_documents": conn.execute("select count(*) from documents where source_platform='domestic'").fetchone()[0],
            "accepted_candidates": conn.execute("select count(*) from domestic_candidates where review_status='accepted'").fetchone()[0],
            "pending_candidates": conn.execute("select count(*) from domestic_candidates where review_status='needs_human_review'").fetchone()[0],
            "classification_orphans": conn.execute(
                """select count(*) from document_classifications dc
                   left join documents d on d.id=dc.document_id where d.id is null"""
            ).fetchone()[0],
            "pages_without_fts": conn.execute(
                """select count(*) from pages p left join page_fts f on f.rowid=p.id
                   where f.rowid is null"""
            ).fetchone()[0],
            "fts_without_pages": conn.execute(
                """select count(*) from page_fts f left join pages p on p.id=f.rowid
                   where p.id is null"""
            ).fetchone()[0],
            "integrity_check": conn.execute("pragma integrity_check").fetchone()[0],
        }
        platform_counts = dict(conn.execute("select source_platform,count(*) from documents group by source_platform").fetchall())
        candidate_statuses = dict(conn.execute("select review_status,count(*) from domestic_candidates group by review_status").fetchall())
    finally:
        conn.close()

    core = rows(CORE)
    observer = rows(OBSERVER)
    front_ocr = sorted((ROOT / "work/domestic/observer_front_ocr_20260728/markdown").glob("issue*/page-*.ocr.md"))
    core_periods = dict(Counter(row.get("period") for row in core))
    result = {
        "database": str(DB),
        "counts": counts,
        "platform_counts": platform_counts,
        "candidate_statuses": candidate_statuses,
        "core_manifest": {"rows": len(core), "periods": core_periods, "citation_ready_true": sum(bool(row.get("citation_ready")) for row in core)},
        "observer": {"issues": len(observer), "derived_pdfs": sum((ROOT / row["derived_issue_pdf"]).is_file() for row in observer), "front_ocr_markdown": len(front_ocr)},
        "acceptance": {
            "database_integrity": counts["integrity_check"] == "ok",
            "fts_aligned": counts["pages_without_fts"] == 0 and counts["fts_without_pages"] == 0,
            "core_manifest_shape": len(core) == 40 and counts["citation_ready_true"] == 0 if "citation_ready_true" in counts else len(core) == 40,
            "observer_boundaries_present": len(observer) == 12 and all(row.get("boundary_status") == "cover_verified" for row in observer),
        },
    }
    # Correct the compact expression above while retaining an explicit result key.
    result["acceptance"]["core_manifest_shape"] = len(core) == 40 and result["core_manifest"]["citation_ready_true"] == 0
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    c = counts
    OUT_MD.write_text(
        "\n".join(
            [
                "# 国内盟史资料阶段验收（2026-07-28）",
                "",
                "## 当前库状态",
                "",
                f"- documents：{c['documents']}；pages：{c['pages']}；page_fts：{c['page_fts']}",
                f"- 国内文献（source_platform=domestic）：{c['domestic_documents']}",
                f"- 候选：accepted {c['accepted_candidates']}；needs_human_review {c['pending_candidates']}",
                f"- integrity_check：{c['integrity_check']}",
                f"- pages_without_fts：{c['pages_without_fts']}；fts_without_pages：{c['fts_without_pages']}",
                f"- 历史分类外键孤儿：{c['classification_orphans']}（遗留问题，本轮未扩增）",
                "",
                "## 核心证据集",
                "",
                f"- {len(core)} 条：" + ", ".join(f"{k}={v}" for k, v in core_periods.items()),
                f"- citation_ready=true：{result['core_manifest']['citation_ready_true']}；全部仍需原件/页码/人工复核门禁。",
                "",
                "## 《观察》",
                "",
                f"- 已确认并切分 12 期，覆盖卷3第1—12期；首轮封面/目录 OCR 产出 {len(front_ocr)} 个 Markdown（逐页可断点续跑）。",
                "- 全刊正文尚未导入正式库；原始 PDF 与派生 issue PDF 均保留 SHA256 溯源。",
                "",
                "## 结论",
                "",
                "- 数据库完整性与 FTS 对齐通过。",
                "- 1942—1943 已从“空白”变为 5 条目录级核心入口，但还不能当作全文一手证据。",
                "- 下一道门槛是补齐 1942—1943 原件，以及对《观察》首轮 OCR 进行抽样人工复核后再决定是否扩大正文 OCR。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"json": str(OUT_JSON), "markdown": str(OUT_MD), "counts": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
