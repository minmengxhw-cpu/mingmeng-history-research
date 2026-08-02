#!/usr/bin/env python3
"""Build conservative Phase-2 inventory and OCR HOLD disposition worklists.

This script only writes under work/domestic and never updates the formal DB or
the staging status columns. It converts existing audit evidence into explicit
next actions; it does not infer a source binding or approve a citation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
HOLD_INPUT = ROOT / "work/domestic/ocr_hold_audit_20260730/OCR_HOLD_AUDIT.jsonl"
OUT = ROOT / "work/domestic/phase2_inventory_20260730"
CORE_PHASES = ("1941", "1942-1943", "1944-1945", "1946")
TERM_RULES = (
    ("成立/早期组织", ("成立", "民主政团同盟", "统一建国", "张澜", "重庆")),
    ("政纲/宪政", ("民宪", "宪政", "参政会", "政纲", "政治协商")),
    ("同期报刊", ("光明报", "大公报", "民主报", "新华日报", "言论")),
    ("地方网络", ("上海", "昆明", "重庆", "香港", "西南联大")),
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def phase_for(value: str | None) -> str:
    text = value or ""
    for phase in CORE_PHASES:
        if phase in text:
            return phase
    if "1941" in text:
        return "1941"
    if "1942" in text or "1943" in text:
        return "1942-1943"
    if "1944" in text or "1945" in text:
        return "1944-1945"
    if "1946" in text:
        return "1946"
    return "unknown"


def classify_title(title: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    for label, terms in TERM_RULES:
        if any(term in title for term in terms):
            hits.append(label)
    if not hits:
        return "待主题判定", []
    return hits[0], hits


def display_title(raw: str | None, fallback: str) -> str:
    """Normalize the staging title field for human-facing worklists only."""
    text = raw or fallback
    try:
        value = json.loads(text)
        if isinstance(value, list) and value:
            return str(value[0])
        if isinstance(value, str):
            return value
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    return text


def build_core_inventory() -> dict:
    conn = sqlite3.connect(STAGING)
    conn.row_factory = sqlite3.Row
    docs = conn.execute(
        """
        SELECT id, canonical_document_key, title, dominant_phase,
               source_row_count, page_row_count, file_row_count,
               unique_sha256_count, unique_path_count, evidence_status
        FROM documents
        WHERE dominant_phase IN ('1941','1942-1943','1944-1945','1946')
        ORDER BY dominant_phase, title, canonical_document_key
        """
    ).fetchall()
    pages = conn.execute(
        """
        SELECT p.document_id, p.object_id, p.local_path, p.page_no, p.sha256,
               p.file_kind, p.historical_phase, p.title,
               d.canonical_document_key, d.title AS document_title
        FROM page_assets p JOIN documents d ON d.id=p.document_id
        WHERE d.dominant_phase IN ('1941','1942-1943','1944-1945','1946')
        ORDER BY d.dominant_phase, d.title, p.page_no
        """
    ).fetchall()
    conn.close()

    out_docs: list[dict] = []
    phase_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    pages_by_doc: defaultdict[int, list[dict]] = defaultdict(list)
    for row in pages:
        item = dict(row)
        pages_by_doc[item["document_id"]].append(item)

    for row in docs:
        item = dict(row)
        title = display_title(item.get("title"), item["canonical_document_key"])
        phase = item["dominant_phase"] or phase_for(title)
        topic, topic_hits = classify_title(title)
        doc_pages = pages_by_doc.get(item["id"], [])
        phase_counts[phase] += 1
        topic_counts[topic] += 1
        item.update(
            {
                "title": title,
                "title_display": title,
                "phase": phase,
                "topic_bucket": topic,
                "topic_hits": topic_hits,
                "page_asset_count_live": len(doc_pages),
                "page_sha_count_live": len({p["sha256"] for p in doc_pages if p["sha256"]}),
                "selection_status": "machine_inventory_candidate",
                "selection_rule": "period_in_core_1941_1946; title/topic signal only",
            }
        )
        out_docs.append(item)

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "CORE_DOCUMENT_INVENTORY.jsonl").open("w", encoding="utf-8") as fh:
        for row in out_docs:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    with (OUT / "CORE_PAGE_ASSET_INVENTORY.jsonl").open("w", encoding="utf-8") as fh:
        for row in pages:
            fh.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")

    summary = {
        "report": "DOMESTIC_PHASE2_CORE_INVENTORY_20260730",
        "scope": "1941-1946 canonical documents and page assets in staging",
        "document_rows": len(out_docs),
        "page_asset_rows": len(pages),
        "phase_document_counts": {phase: phase_counts.get(phase, 0) for phase in CORE_PHASES},
        "topic_bucket_counts": dict(sorted(topic_counts.items())),
        "selection_is_not_semantic_approval": True,
        "formal_db_written": False,
        "outputs": [
            str(OUT / "CORE_DOCUMENT_INVENTORY.jsonl"),
            str(OUT / "CORE_PAGE_ASSET_INVENTORY.jsonl"),
        ],
    }
    (OUT / "REPORT.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with (OUT / "CORE_DOCUMENT_INVENTORY.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        fields = ["canonical_document_key", "title", "phase", "topic_bucket", "page_asset_count_live", "evidence_status", "selection_status"]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in out_docs:
            writer.writerow({key: row.get(key, "") for key in fields})

    md = [
        "# 1941—1946 核心资料覆盖表",
        "",
        "本表来自 staging 的 canonical 文献和页资产，仅用于资料建设排序，不代表语义核验或正式引用资格。",
        "",
        f"- 文献对象：{len(out_docs)}",
        f"- 页/文件资产：{len(pages)}",
        "",
        "## 按时期",
        "",
        "| 时期 | 文献对象 |",
        "|---|---:|",
    ]
    for phase in CORE_PHASES:
        count = phase_counts.get(phase, 0)
        md.append(f"| {phase} | {count} |")
    md.extend(["", "## 按主题信号", "", "| 主题 | 文献对象 |", "|---|---:|"])
    for topic, count in sorted(topic_counts.items()):
        md.append(f"| {topic} | {count} |")
    md.extend(["", "## 后续规则", "", "- 先核对原件/SHA/页链，再进入语义证据候选。", "- 目录、网页快照和机器标题信号不得冒充同期原件。", "- 本轮未写入正式数据库。", ""])
    (OUT / "REPORT.md").write_text("\n".join(md), encoding="utf-8")
    return summary


def build_hold_disposition() -> dict:
    rows = [json.loads(line) for line in HOLD_INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    disposition: list[dict] = []
    action_counts: Counter[str] = Counter()
    source_groups: defaultdict[str, list[str]] = defaultdict(list)
    for row in rows:
        reasons = set(row.get("reasons", []))
        candidates = row.get("candidate_paths") or []
        if "UNBOUND_SOURCE_FILE" in reasons:
            if candidates:
                action = "PENDING_EXPLICIT_FILENAME_SHA_MAPPING"
                next_step = "核对候选路径文件是否为同一原件，并取得/记录源文件 SHA；不得因近似名称自动绑定。"
            else:
                action = "PENDING_SOURCE_FILE_RECOVERY"
                next_step = "在原始资料目录或来源系统寻找对应文件；未找到前保持 HOLD。"
        elif "PAGE_IMAGE_NOT_FOUND" in reasons:
            action = "PENDING_PAGE_ASSET_REBIND"
            next_step = "根据 source SHA、页号和派生关系重新定位页图；不能用相邻页替代。"
        else:
            action = "PENDING_MANUAL_EVIDENCE_REVIEW"
            next_step = "核对 provenance、页图、OCR 文本和来源 SHA 后再决定。"
        source = row.get("source_id") or row.get("source_file") or "UNKNOWN"
        source_groups[source].append(row.get("provenance_id", ""))
        action_counts[action] += 1
        disposition.append(
            {
                **row,
                "disposition_id": "HOLD-" + sha256_text(row.get("provenance_id", ""))[:16],
                "disposition_action": action,
                "next_step": next_step,
                "status": "HOLD_NO_AUTO_RESOLUTION",
                "citation_ready": False,
                "human_verified": False,
            }
        )

    with (OUT / "OCR_HOLD_DISPOSITION.jsonl").open("w", encoding="utf-8") as fh:
        for row in disposition:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    report = {
        "report": "DOMESTIC_OCR_HOLD_DISPOSITION_20260730",
        "rows": len(disposition),
        "action_counts": dict(sorted(action_counts.items())),
        "source_groups": len(source_groups),
        "auto_resolved": 0,
        "formal_db_written": False,
        "rule": "explicit worklist only; no source binding or citation approval inferred",
        "output": str(OUT / "OCR_HOLD_DISPOSITION.jsonl"),
    }
    (OUT / "OCR_HOLD_DISPOSITION_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = [
        "# OCR HOLD 逐条处置清单",
        "",
        "本清单只分配修复动作，不自动绑定来源、不补写页图、不提升引用状态。",
        "",
        f"- 总记录：{len(disposition)}",
        f"- 来源组：{len(source_groups)}",
        "",
        "| 处置队列 | 条数 |",
        "|---|---:|",
    ]
    for action, count in sorted(action_counts.items()):
        md.append(f"| {action} | {count} |")
    md.extend(["", "## 复算规则", "", "- 只有源文件、SHA、canonical 文献和页链同时一致，才允许下一轮提出绑定。", "- 无页图或 source SHA 的记录继续 HOLD。", "- 正式库 `citation_ready` 与 `human_verified` 均不在本轮改变。", ""])
    (OUT / "OCR_HOLD_DISPOSITION.md").write_text("\n".join(md), encoding="utf-8")
    return report


def main() -> None:
    core = build_core_inventory()
    holds = build_hold_disposition()
    print(json.dumps({"core": core, "holds": holds}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
