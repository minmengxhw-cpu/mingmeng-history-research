#!/usr/bin/env python3
"""Build a read-only morning acceptance snapshot for the overnight batches."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/domestic"
MINIMAX = WORK / "minimax_domestic_evidence_v2_month_20260729"
GROK = WORK / "grok_domestic_collection_month_20260729"
OUT_DIR = WORK / "overnight_20260729"
BASELINE_DB_SHA = "822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3"


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": str(exc)}


def count_jsonl(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "rows": 0, "parse_errors": 0}
    rows = 0
    errors = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows += 1
            try:
                json.loads(line)
            except Exception:
                errors += 1
    return {"exists": True, "rows": rows, "parse_errors": errors}


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    db = ROOT / "data/research_index.sqlite"
    db_sha = sha256(db)

    minimax_status = load_json(MINIMAX / "00_control/MONTH_STATUS.json")
    grok_status = load_json(GROK / "00_control/MONTH_STATUS.json")

    checks = {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "formal_sqlite": {
            "path": str(db),
            "baseline_sha256": BASELINE_DB_SHA,
            "current_sha256": db_sha,
            "unchanged": db_sha == BASELINE_DB_SHA,
        },
        "minimax": {
            "status": minimax_status,
            "p2_checkpoint_exists": (MINIMAX / "09_reports/P2_CHECKPOINT.md").exists(),
            "variant_manifest": count_jsonl(
                MINIMAX / "04_variant_ocr/V2_VARIANT_MANIFEST.jsonl"
            ),
            "selected_pointers": count_jsonl(
                MINIMAX
                / "05_machine_validation/V2_SELECTED_OCR_POINTERS.jsonl"
            ),
            "validation_1500": count_jsonl(
                MINIMAX / "05_machine_validation/V2_VALIDATION_1500.jsonl"
            ),
            "problem_72": count_jsonl(
                MINIMAX / "05_machine_validation/V2_PROBLEM_72_FINAL.jsonl"
            ),
            "variant_remaining": count_jsonl(
                MINIMAX
                / "05_machine_validation/V2_VARIANT_WORKLIST_REMAINING.jsonl"
            ),
            "p3_checkpoint_exists": (MINIMAX / "09_reports/P3_CHECKPOINT.md").exists(),
            "p3_evidence_candidates": count_jsonl(
                MINIMAX / "06_period_evidence/EVIDENCE_CANDIDATES_300.jsonl"
            ),
        },
        "grok": {
            "status": grok_status,
            "p3_checkpoint_exists": (GROK / "06_reports/P3_CHECKPOINT.md").exists(),
            "final_report_exists": (
                GROK / "06_reports/MONTH_FINAL_REPORT.md"
            ).exists(),
            "p3_acquisition": count_jsonl(
                GROK / "03_acquisition/P3_ACQUISITION_MANIFEST.jsonl"
            ),
            "minimax_handoff": count_jsonl(
                GROK / "05_minimax_handoff/MINIMAX_OCR_INGEST_QUEUE.jsonl"
            ),
            "no_ocr_fulltext": count_jsonl(
                GROK / "05_minimax_handoff/NO_OCR_NEEDED_FULLTEXT.jsonl"
            ),
            "metadata_only": count_jsonl(
                GROK / "05_minimax_handoff/METADATA_ONLY_QUEUE.jsonl"
            ),
            "access_hold": count_jsonl(
                GROK / "05_minimax_handoff/ACCESS_OR_RIGHTS_HOLD.jsonl"
            ),
            "p5_status": load_json(
                GROK / "07_temporal_primary_audit/P5_STATUS.json"
            ),
            "p5_checkpoint_exists": (
                GROK / "07_temporal_primary_audit/P5_CHECKPOINT.md"
            ).exists(),
            "p5_temporal_audit": count_jsonl(
                GROK / "07_temporal_primary_audit/P5_TEMPORAL_AUDIT_962.jsonl"
            ),
            "p5_clean_candidates": count_jsonl(
                GROK / "07_temporal_primary_audit/P5_CLEAN_CANDIDATE_VIEW.jsonl"
            ),
        },
    }

    json_path = OUT_DIR / "MORNING_SNAPSHOT_20260730.json"
    md_path = OUT_DIR / "MORNING_SNAPSHOT_20260730.md"
    json_path.write_text(
        json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    mm = checks["minimax"]
    gr = checks["grok"]
    md = f"""# 夜间任务晨间快照

- 生成时间：{checks['generated_at']}
- 正式 SQLite 未变化：{checks['formal_sqlite']['unchanged']}
- MiniMax 状态：{minimax_status.get('state', 'UNKNOWN')}
- MiniMax 阶段：{minimax_status.get('phase', 'UNKNOWN')}
- MiniMax P2 checkpoint：{mm['p2_checkpoint_exists']}
- MiniMax validation 行数：{mm['validation_1500']['rows']}
- MiniMax 72 问题页行数：{mm['problem_72']['rows']}
- MiniMax 剩余 variant：{mm['variant_remaining']['rows']}
- MiniMax P3 checkpoint：{mm['p3_checkpoint_exists']}
- MiniMax P3 证据候选：{mm['p3_evidence_candidates']['rows']}
- Grok 状态：{grok_status.get('state', 'UNKNOWN')}
- Grok 阶段：{grok_status.get('phase', 'UNKNOWN')}
- Grok P3 checkpoint：{gr['p3_checkpoint_exists']}
- Grok P3 获取清单：{gr['p3_acquisition']['rows']}
- Grok MiniMax OCR 交接：{gr['minimax_handoff']['rows']}
- Grok免 OCR 全文：{gr['no_ocr_fulltext']['rows']}
- Grok元数据队列：{gr['metadata_only']['rows']}
- Grok访问/权利 HOLD：{gr['access_hold']['rows']}
- Grok P5 状态：{gr['p5_status'].get('state', 'UNKNOWN')}
- Grok P5 checkpoint：{gr['p5_checkpoint_exists']}
- Grok P5 审计行数：{gr['p5_temporal_audit']['rows']}
- Grok P5 清洁候选：{gr['p5_clean_candidates']['rows']}

本文件仅为自动只读快照，不代表 Codex 正式验收。正式入库、Git 和发布仍需后续验收。
"""
    md_path.write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
