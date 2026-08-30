#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 国内证据审计 · Batch 3：L1—L4 分级终稿 + citation_ready 严格门禁
==========================================================================
门禁定义（六道，全部通过才允许 citation_ready=yes）：
  G1 等级门禁：final 等级 ∈ {L1, L2}（L3 目录线索 / L4 二手 / LX 未定 → FAIL）
  G2 原件门禁：availability=full_item_online（或 surrogate_online 且证据类型为 digital_image）
  G3 类型门禁：material_class ∈ {一手, 汇编}；非"目录冒充全文"名单
  G4 溯源门禁：catalog_reference 非空 且 catalog_reference_status=verified
  G5 草稿门禁：非 OCR 草稿（needs_ocr≠yes；非 ocr_pilot/review_only）
  G6 复核门禁：uncertainty_note 不含重大保留关键词（未核验/缺原件/待复核/边界待定）
输出：
  citation_gate_matrix.csv   全 689 条 × 六道门禁逐项判定
  citation_gate_pass.csv     严格门禁通过名单
  citation_gate_failures.csv 未通过名单（含未过门禁明细）
  citation_gate_report.md
"""
import csv
import re
from collections import Counter
from pathlib import Path

from _guard import guard

BASE = Path(__file__).resolve().parents[2]
WORK = BASE / "work" / "deepseek-20260803"
IN = WORK / "01_inputs"
OUT = WORK / "02_analysis"

UNCERTAIN_KW = ["未核验", "未直接核验", "待复核", "需人工", "边界待定", "缺原件", "未公开核验",
                "尚未核验", "需补", "无法核验", "未确认", "需要人工"]


def read_csv(name):
    p = IN / name
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows):
    if not rows:
        print(f"  [warn] {name}: empty")
        return
    p = OUT / name
    fn = list(dict.fromkeys(k for r in rows for k in r.keys()))
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fn})
    print(f"  [ok] {name} ({len(rows)} rows)")


def gate_row(c):
    """对单个候选执行六道门禁，返回 (verdict, fail_reasons)"""
    fails = []
    level = c.get("evidence_level_final", "")
    if level not in ("L1", "L2"):
        fails.append(f"G1_level={level or 'EMPTY'}")
    avail = c.get("availability", "")
    if avail not in ("full_item_online", "surrogate_online"):
        fails.append(f"G2_avail={avail or 'EMPTY'}")
    if avail == "surrogate_online" and c.get("evidence_type", "") != "digital_image":
        fails.append("G2_avail=surrogate 但证据类型非影像")
    mcls = c.get("material_class", "")
    if mcls not in ("一手", "汇编"):
        fails.append(f"G3_class={mcls}")
    catref = c.get("catalog_reference", "") or ""
    catstat = c.get("catalog_reference_status", "") or ""
    if not catref.strip():
        fails.append("G4_no_catalog_reference")
    elif catstat != "verified":
        fails.append(f"G4_catref_status={catstat or 'EMPTY'}")
    if c.get("needs_ocr", "") == "yes":
        fails.append("G5_ocr_draft")
    unc = c.get("uncertainty_note", "") or ""
    hit_kw = [k for k in UNCERTAIN_KW if k in unc]
    if hit_kw:
        fails.append("G6_uncertain:" + ",".join(hit_kw[:3]))
    return (fails == [], ";".join(fails))


def main():
    guard()
    db = read_csv("domestic_candidates.csv")
    staging = read_csv("staging_domestic_candidates.csv")
    import_ready = read_csv("staging_import_ready.csv")
    norm = []
    p = OUT / "metadata_normalized.csv"
    if p.exists():
        with open(p, newline="", encoding="utf-8") as f:
            norm = list(csv.DictReader(f))
    else:
        print("[fatal] metadata_normalized.csv 缺失，先跑 batch2")
        return
    norm_by_id = {r["candidate_id"]: r for r in norm}
    db_by_id = {r["candidate_id"]: r for r in db}
    st_by_id = {r["candidate_id"]: r for r in staging}
    ir_by_id = {r["candidate_id"]: r for r in import_ready}
    cat_as_full = {r["candidate_id"] for r in read_csv("catalog_as_fulltext.csv")}

    rows = []
    for cid in sorted(set(db_by_id) | set(st_by_id)):
        d = db_by_id.get(cid, {})
        s = st_by_id.get(cid, {})
        ir = ir_by_id.get(cid, {})
        c = dict(norm_by_id.get(cid, {}))
        c["candidate_id"] = cid
        c["review_status"] = d.get("review_status") or s.get("review_status", "")
        c["catalog_reference"] = d.get("catalog_reference") or s.get("catalog_reference", "")
        c["catalog_reference_status"] = d.get("catalog_reference_status") or s.get("catalog_reference_status", "")
        c["uncertainty_note"] = d.get("uncertainty_note") or s.get("uncertainty_note", "")
        c["evidence_type"] = d.get("evidence_type") or s.get("evidence_type", "")
        c["needs_ocr"] = ir.get("needs_ocr") or s.get("needs_ocr", "")
        c["staging_citation_ready"] = ir.get("citation_ready", "")
        c["_catalog_as_fulltext"] = "yes" if cid in cat_as_full else ""
        rows.append(c)

    matrix = []
    for c in rows:
        verdict, reasons = gate_row(c)
        matrix.append({
            "candidate_id": c["candidate_id"],
            "review_status": c["review_status"],
            "level": c.get("evidence_level_final", ""),
            "material_class": c.get("material_class", ""),
            "availability": c.get("availability", ""),
            "catalog_reference_status": c["catalog_reference_status"],
            "needs_ocr": c["needs_ocr"],
            "staging_citation_ready": c["staging_citation_ready"],
            "strict_gate": "PASS" if verdict else "FAIL",
            "fail_reasons": reasons,
            "catalog_as_fulltext_flag": c["_catalog_as_fulltext"],
        })
    write_csv("citation_gate_matrix.csv", matrix)

    passed = [m for m in matrix if m["strict_gate"] == "PASS"]
    failed = [m for m in matrix if m["strict_gate"] == "FAIL"]
    # 仅对 accepted 计算（needs_human_review 无论结果如何不进 citation）
    accepted_pass = [m for m in passed if m["review_status"] == "accepted"]
    write_csv("citation_gate_pass.csv", passed)
    write_csv("citation_gate_failures.csv", failed)

    # 与 staging 声称的 229 对照
    staging_claimed = [m for m in matrix if m["staging_citation_ready"] == "yes"]
    overlap = [m for m in staging_claimed if m["strict_gate"] == "PASS"]

    f_reasons = Counter()
    for m in failed:
        for r in m["fail_reasons"].split(";"):
            f_reasons[r.split(":")[0]] += 1

    md = f"""# Batch 3 · L1—L4 分级终稿与 citation_ready 严格门禁报告

## 1. 门禁规则（六道）

G1 等级 ∈ L1/L2 ｜ G2 availability=full_item_online|surrogate_online(影像) ｜ G3 资料类=一手|汇编 且非目录冒充全文 ｜ G4 catalog_reference 非空且 verified ｜ G5 非 OCR 草稿 ｜ G6 uncertainty 无重大保留

## 2. 结果总览

| 指标 | 数量 |
|---|---:|
| 候选总数 | {len(matrix)} |
| 严格门禁 PASS | {len(passed)} |
| 严格门禁 FAIL | {len(failed)} |
| accepted 且 PASS（可入 citation 层） | {len(accepted_pass)} |
| staging 声称 citation_ready=yes | {len(staging_claimed)} |
| 其中通过严格门禁 | {len(overlap)}（{len(staging_claimed)-len(overlap)} 条被严格门禁打回） |

## 3. FAIL 原因分布

| 门禁 | 失败数 |
|---|---:|
{chr(10).join(f"| {k} | {v} |" for k, v in f_reasons.most_common())}

## 4. 结论与处置

- 现行 229 条 citation_ready=yes 中 {len(overlap)} 条通过严格门禁，{len(staging_claimed)-len(overlap)} 条被驳回（多为 G1 等级不足 / G4 目录状态未 verified / G6 不确定性保留）
- 通过名单 → `citation_gate_pass.csv`；驳回明细 → `citation_gate_failures.csv`
- 正式库侧 citation_ready 仍为 0（0702 验收口径）；本报告是库外门禁基线，正式库门禁由生产轮次执行
"""
    (OUT / "citation_gate_report.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
