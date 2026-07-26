#!/usr/bin/env python3
"""Build manual Codex closeout artifacts; read-only against the SQLite database."""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/domestic"


def load(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def confidence(row):
    return row.get("mean_confidence") or row.get("mean_confidence_manifest") or 0


def decision(row):
    if row["file_id"] == "P3-023":
        return "PENDING_CODEX_REVIEW"
    if row["file_id"] in {"P3-GXMM-SH", "P3-GXMM-TJ"}:
        return "REJECT_OCR" if float(confidence(row)) < 0.5 else "REVIEW_ORIGINAL"
    return "GO_SEARCH_DRAFT" if float(confidence(row)) >= 0.85 else "REVIEW_ORIGINAL"


def build_candidates(rows):
    out = []
    for row in rows:
        d = decision(row)
        pages = int(row.get("page_count") or row.get("pdf_pages_actual") or 0)
        chunks = row.get("chunk_paths") or row.get("ocr_output_paths") or []
        out.append({
            "candidate_id": f"CLAUDE-B-{row['file_id']}",
            "file_id": row["file_id"],
            "source_path": row.get("rel_path"),
            "source_sha256": row.get("sha256"),
            "source_kind": row.get("priority_source_kind", "press_scan"),
            "batch": row.get("batch"),
            "pdf_pages": pages,
            "num_chunks": len(chunks),
            "chunk_paths": chunks,
            "ocr_lines_total": row.get("ocr_lines") or row.get("ocr_lines_actual_total"),
            "mean_confidence": confidence(row),
            "recommended_action": d,
            "citation_ready": False,
            "needs_human_review": True,
            "approved_for_upgrade": False,
            "dry_run_status": "pending_codex_review" if d == "PENDING_CODEX_REVIEW" else ("skipped_quality" if d in {"REVIEW_ORIGINAL", "REJECT_OCR"} and row["file_id"] in {"P3-GXMM-SH", "P3-GXMM-TJ"} else "planned"),
            "skip_reason": "cheer_only_high_resolution_rescan" if row["file_id"] in {"P3-GXMM-SH", "P3-GXMM-TJ"} else ("orphan_pending_codex_review" if d == "PENDING_CODEX_REVIEW" else None),
            "estimated_new_documents": 1,
            "estimated_new_pages": pages,
            "estimated_new_page_fts": pages,
        })
    return out


def search_regression():
    keywords = [
        "成立宣言", "中国民主政团同盟", "民盟改组", "民盟一大", "临时全国代表大会", "民主宪政",
        "政治协商会议", "国民大会", "非法化", "十月三十一日", "三中全会", "新政协",
        "多党合作", "共同纲领", "张澜", "沈钧儒", "黄炎培", "张君劢", "陈启天", "李公朴",
        "闻一多", "香港", "上海", "延安", "南京", "北平", "沈阳", "民盟", "中国民主同盟",
        "五五宪草", "人民主权", "反对一党独裁", "教授联署", "恢复活动", "五一号召", "下关惨案",
        "政治报告", "民主政团", "重庆谈判", "新政协筹备",
    ]
    db = sqlite3.connect(ROOT / "data/research_index.sqlite")
    rows = []
    try:
        for kw in keywords:
            try:
                fts = db.execute("select count(*) from page_fts where page_fts match ?", (kw,)).fetchone()[0]
            except sqlite3.Error as exc:
                fts = f"ERROR:{exc}"
            like = db.execute("select count(*) from pages where text like ?", (f"%{kw}%",)).fetchone()[0]
            rows.append({"keyword": kw, "fts_hits": fts, "like_hits": like})
        counts = {name: db.execute(f"select count(*) from {name}").fetchone()[0] for name in ("documents", "pages", "page_fts")}
        integrity = db.execute("pragma integrity_check").fetchone()[0]
    finally:
        db.close()
    return {"integrity_check": integrity, "counts": counts, "queries_total": len(rows), "results": rows}


def main():
    rows = load(WORK / "CLAUDE_B_OCR_MANIFEST_NORMALIZED_ALL_20260726.jsonl")
    candidates = build_candidates(rows)
    with (WORK / "CLAUDE_B_IMPORT_CANDIDATE_MANIFEST_20260726.jsonl").open("w", encoding="utf-8") as fh:
        for row in candidates:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    total_pages = sum(int(r["estimated_new_pages"]) for r in candidates)
    planned = [r for r in candidates if r["dry_run_status"] == "planned"]
    skipped = [r for r in candidates if r["dry_run_status"] != "planned"]
    dryrun = {
        "mode": "dry-run-only",
        "sqlite_touched": False,
        "baseline": {"documents": 928, "pages": 1428, "page_fts": 1428},
        "candidates": len(candidates),
        "planned_documents": len(planned),
        "planned_pages": sum(r["estimated_new_pages"] for r in planned),
        "planned_page_fts": sum(r["estimated_new_page_fts"] for r in planned),
        "skipped": len(skipped),
        "skip_breakdown": {},
        "citation_ready": 0,
        "backup_command": "cp -p data/research_index.sqlite data/research_index.sqlite.20260726_manual.pre.bak",
        "rollback_command": "cp -p data/research_index.sqlite.20260726_manual.pre.bak data/research_index.sqlite",
    }
    for row in skipped:
        reason = row["skip_reason"] or row["dry_run_status"]
        dryrun["skip_breakdown"][reason] = dryrun["skip_breakdown"].get(reason, 0) + 1
    (WORK / "CLAUDE_B_IMPORT_DRYRUN_20260726.json").write_text(json.dumps(dryrun, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    regression = search_regression()
    (WORK / "CLAUDE_B_SEARCH_REGRESSION_20260726.json").write_text(json.dumps(regression, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (WORK / "CLAUDE_B_OCR_DECISIONS_20260726.csv").open("w", encoding="utf-8", newline="") as fh:
        fields = ["file_id", "batch", "pages", "mean_confidence", "decision", "citation_ready", "needs_human_review", "source_path"]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({"file_id": row["file_id"], "batch": row.get("batch"), "pages": row.get("page_count") or row.get("pdf_pages_actual"), "mean_confidence": confidence(row), "decision": decision(row), "citation_ready": False, "needs_human_review": True, "source_path": row.get("rel_path")})

    md = [
        "# Codex 手动 OCR 收口报告（2026-07-26）", "",
        "## 结论", "", "本轮由 Codex 本地手动完成 manifest 规范化、113/114 卷尾段登记和只读 dry-run；未修改 SQLite。", "",
        f"- OCR manifest：{len(rows)} 条（原 59 条 + P3-113/P3-114 2 条）",
        f"- 计划检索草稿：{len(planned)} 个文件，{sum(r['estimated_new_pages'] for r in planned)} 页",
        f"- 跳过/待审：{len(skipped)} 个文件，总候选页数 {total_pages}",
        "- citation_ready：0；全部 needs_human_review=true",
        f"- SQLite：{regression['integrity_check']}，documents/pages/page_fts = {regression['counts']['documents']}/{regression['counts']['pages']}/{regression['counts']['page_fts']}",
        f"- 检索回归：{regression['queries_total']} 条，分别记录 FTS 与 LIKE",
        "", "## 禁止项执行情况", "", "未执行 SQLite INSERT/UPDATE，未执行正式 apply，未 commit，未 push。",
        "", "## 产物", "", "- `CLAUDE_B_OCR_MANIFEST_NORMALIZED_ALL_20260726.jsonl`", "- `CLAUDE_B_OCR_MANIFEST_P3-113-114_20260726.jsonl`", "- `CLAUDE_B_OCR_DECISIONS_20260726.csv`", "- `CLAUDE_B_IMPORT_DRYRUN_20260726.json`", "- `CLAUDE_B_SEARCH_REGRESSION_20260726.json`", "", "状态：`WAITING_FOR_CODEX_ACCEPTANCE`。",
    ]
    (WORK / "CLAUDE_B_IMPORT_DRYRUN_20260726.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (WORK / "CLAUDE_B_LONG_TASK_FINAL_20260726.json").write_text(json.dumps({"status": "complete", "mode": "manual_codex_local", "dryrun": dryrun, "regression": regression, "sqlite_touched": False}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (WORK / "CLAUDE_B_LONG_TASK_FINAL_20260726.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "planned": len(planned), "skipped": len(skipped), "pages": total_pages, "regression_queries": regression["queries_total"], "sqlite_touched": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
