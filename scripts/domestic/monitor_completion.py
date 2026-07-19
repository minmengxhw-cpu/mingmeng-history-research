#!/usr/bin/env python3
"""Local completion monitor for domestic 民盟史资料库 phase work.

Writes machine + human status under work/domestic/.
Does not upgrade evidence levels or invent original-document claims.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOM = ROOT / "data" / "domestic"
WORK = ROOT / "work" / "domestic"

PHASE_REPORTS = {
    "phase0": WORK / "minimax_phase0_audit_20260719.md",
    "phase1": WORK / "minimax_phase1_1941_1945_pursuit_20260719.md",
    "phase2": WORK / "minimax_phase2_1946_articles_20260719.md",
    "phase3": WORK / "minimax_phase3_1947_core_gaps_20260719.md",
    "phase4": WORK / "minimax_phase4_1948_1949_20260719.md",
    "phase2_5_final": WORK / "minimax_phases_2_to_5_final_20260719.md",
    "codex_review": WORK / "codex_unified_review_20260719.md",
}

HARD_GAPS = {
    "B1_1941_guangmingbao_original": {
        "label": "1941《光明報》成立相关原刊影像",
        "candidates": [
            "domestic:HKU:guangmingbao-1941-microform-holdings",
            "domestic:LNU:guangmingbao-index-1941",
        ],
        "closed_if": "never_auto",  # original not auto-closed
    },
    "B4_1946_wenxian_political_report_body": {
        "label": "1946《民主同盟文獻》政治报告正文",
        "candidates": ["domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap"],
        "closed_if": "never_auto",
    },
    "B5_1947_interior_ban_original": {
        "label": "1947-10-27 内政部非法化公函/公报原页",
        "candidates": ["domestic:MMHIST:league-banned-1947-10-27"],
        "closed_if": "never_auto",
    },
    "B6_1947_dissolution_original_print": {
        "label": "1947-11-06 总部解散公告独立印本",
        "candidates": ["domestic:MMHIST:league-dissolution-announcement-1947-11-06"],
        "closed_if": "never_auto",
    },
    "B7_1947_xinminbao_original": {
        "label": "1947-11-04 北平《新民报》原版",
        "candidates": ["domestic:GXMM:xinminbao-professors-statement-1947-11-04"],
        "closed_if": "never_auto",
    },
}

R1_ID = "domestic:MMHIST:formation-declaration-1941"
R2_DIR = WORK / "mmhist_platform_1945_pages"
R2_PAGES = [f"page-{i:03d}.png" for i in range(111, 117)]


def run_py(script: str, *args: str) -> dict:
    cmd = [sys.executable, str(ROOT / "scripts" / "domestic" / script), *args]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (p.stdout or "").strip().splitlines()
    last = out[-1] if out else "{}"
    try:
        payload = json.loads(last)
    except json.JSONDecodeError:
        payload = {"raw": last, "stderr": (p.stderr or "")[:500]}
    payload["_returncode"] = p.returncode
    return payload


def load_candidates() -> list[dict]:
    path = DOM / "candidates.jsonl"
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def check_r1(cands: list[dict]) -> dict:
    row = next((c for c in cands if c.get("candidate_id") == R1_ID), None)
    if not row:
        return {"ok": False, "reason": "missing candidate"}
    note = str(row.get("evidence_note") or "")
    ok = "对时局主张纲领" in note and "中国民主同盟纲领" not in note.split("第38页")[-1][:40]
    # stronger: explicit correct phrase
    ok = "对时局主张纲领" in note and "不是1944年纲领" in note
    return {"ok": ok, "evidence_note_snippet": note[-120:]}


def check_r2() -> dict:
    missing = [name for name in R2_PAGES if not (R2_DIR / name).exists()]
    full = all((R2_DIR / f"page-{i:03d}.png").exists() for i in range(101, 118))
    return {
        "ok": not missing and full,
        "missing_111_116": missing,
        "has_101_117": full,
    }


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    cands = load_candidates()
    by_id = {c["candidate_id"]: c for c in cands}
    status_counts = Counter(c.get("review_status") for c in cands)
    level_counts = Counter(c.get("authenticity_level_proposed") for c in cands)

    reports = {k: p.exists() for k, p in PHASE_REPORTS.items()}

    v_cand = run_py("validate_candidates.py", str(DOM / "candidates.jsonl"))
    v_ev = run_py(
        "validate_event_coverage.py",
        str(DOM / "candidates.jsonl"),
        str(DOM / "event_coverage.json"),
    )
    v_ing = run_py("ingest_domestic.py")
    v_aud = run_py("audit_readiness_20260719.py")

    r1 = check_r1(cands)
    r2 = check_r2()

    a_checks = {
        "phase_reports_all_present": all(reports.values()),
        "validate_candidates_pass": v_cand.get("failed") == 0 and v_cand.get("_returncode") == 0,
        "event_coverage_no_dangling": v_ev.get("missing_candidate_references") == []
        and v_ev.get("_returncode") == 0,
        "ingest_ok": v_ing.get("_returncode") == 0
        and v_ing.get("domestic_candidates") == len(cands),
        "audit_no_missing_required": v_aud.get("missing_required") == 0,
        "audit_no_missing_paths": v_aud.get("missing_paths") == 0,
        "r1_page38_boundary_fixed": r1["ok"],
        "r2_political_report_pages_111_116": r2["ok"],
        "codex_review_report_present": reports.get("codex_review", False),
    }
    a_complete = all(a_checks.values())

    open_gaps = []
    for gid, meta in HARD_GAPS.items():
        open_gaps.append(
            {
                "id": gid,
                "label": meta["label"],
                "status": "OPEN",
                "related_candidates": [
                    {
                        "candidate_id": cid,
                        "review_status": (by_id.get(cid) or {}).get("review_status"),
                        "level": (by_id.get(cid) or {}).get("authenticity_level_proposed"),
                    }
                    for cid in meta["candidates"]
                    if cid in by_id
                ],
            }
        )
    b_open = len(open_gaps) > 0

    payload = {
        "generated_at": now,
        "project_root": str(ROOT),
        "A_LAYER_COMPLETE": a_complete,
        "B_LAYER_OPEN": b_open,
        "a_checks": a_checks,
        "baseline": {
            "candidates": len(cands),
            "review_status": dict(status_counts),
            "evidence_levels": dict(level_counts),
            "accepted": status_counts.get("accepted", 0),
            "needs_human_review": status_counts.get("needs_human_review", 0),
            "sources_ingest": v_ing.get("domestic_sources"),
            "events": v_ev.get("events"),
        },
        "validators": {
            "candidates": v_cand,
            "event_coverage": v_ev,
            "ingest": v_ing,
            "audit": v_aud,
        },
        "reports": reports,
        "r1": r1,
        "r2": r2,
        "hard_gaps_open": open_gaps,
        "message_for_user": (
            "A层阶段执行已完成；B层原件硬缺口仍开放，监控不会虚报闭环。"
            if a_complete and b_open
            else (
                "A层与B层均满足完成定义（罕见）。"
                if a_complete and not b_open
                else "A层尚未全部满足，见 a_checks。"
            )
        ),
    }

    json_path = WORK / "monitor_status_latest.json"
    md_path = WORK / "monitor_status_latest.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# 完成监控状态",
        f"",
        f"- 生成时间：{now}",
        f"- `A_LAYER_COMPLETE`：**{str(a_complete).lower()}**",
        f"- `B_LAYER_OPEN`：**{str(b_open).lower()}**",
        f"- 候选：{len(cands)}；accepted：{status_counts.get('accepted', 0)}；"
        f"needs_human_review：{status_counts.get('needs_human_review', 0)}",
        f"",
        f"## A 层检查",
        f"",
    ]
    for k, v in a_checks.items():
        lines.append(f"- [{'x' if v else ' '}] `{k}`")
    lines += ["", "## B 层硬缺口（仍开放则不可宣称原件闭环）", ""]
    for g in open_gaps:
        lines.append(f"- **{g['id']}**：{g['label']} — `{g['status']}`")
    lines += ["", f"## 用户摘要", "", payload["message_for_user"], ""]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False))
    return 0 if a_complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
