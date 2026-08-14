#!/usr/bin/env python3
"""Build a conservative source-admission and OCR-disposition queue.

The input is a metadata-only coverage inventory. The command never opens the
source bodies, never writes the formal SQLite database, and never deletes or
renames local files. It turns existing inventory states into explicit next
actions so that OCR work is not mistaken for research progress.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = ROOT / "data/domestic/source_admission_policy.json"
DEFAULT_INVENTORY = ROOT / "work/domestic/DOMESTIC_COVERAGE_INVENTORY_20260728.csv"
DEFAULT_OUTPUT = ROOT / "work/domestic/source_admission_20260814"

YEAR_RE = re.compile(r"(?:19|20)\d{2}")
CORE_MARKERS = (
    "民盟",
    "民主同盟",
    "光明",
    "大公",
    "民宪",
    "观察",
    "国民政府公报",
    "政协",
    "共同纲领",
)
PHASE_LABELS = {
    "1941": "成立与早期组织",
    "1945": "第一次全国代表大会",
    "1946": "旧政协与拒绝国民大会",
    "1947": "组织受压与解散",
    "1948": "三中全会与转型",
    "1949": "新政协与政权转换",
}


def integer(value: object) -> int:
    try:
        return int(str(value or "0").strip())
    except (TypeError, ValueError):
        return 0


def load_policy(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "domestic_source_admission_policy.v1":
        raise ValueError(f"invalid policy schema: {path}")
    return payload


def load_inventory(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError(f"empty inventory: {path}")
    required = {"source_path", "sha256", "status", "pdf_pages", "indexed_pages", "ocr_draft_pages"}
    missing = sorted(required - set(rows[0]))
    if missing:
        raise ValueError(f"inventory missing columns: {', '.join(missing)}")
    return rows


def load_reconciliation(path: Path | None) -> dict[str, dict[str, Any]]:
    """Load an optional metadata-only page reconciliation report."""

    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "domestic_source_page_reconciliation.v1":
        raise ValueError(f"invalid reconciliation schema: {path}")
    return {
        str(row["source_path"]): row
        for row in payload.get("rows", [])
        if isinstance(row, dict) and row.get("source_path")
    }


def phase_for(path: str) -> tuple[str, str]:
    years = [year for year in YEAR_RE.findall(path) if year in PHASE_LABELS]
    year = years[0] if years else "unknown"
    return year, PHASE_LABELS.get(year, "待主题判定")


def source_form(row: dict[str, str]) -> str:
    explicit = " ".join(
        row.get(key, "") for key in ("text_mode", "source_form", "text_layer_status", "content_mode")
    ).lower()
    if any(marker in explicit for marker in ("electronic_text", "html_text", "text_layer_ready")):
        return "ELECTRONIC_TEXT"
    return "SCAN_OR_UNKNOWN_PDF"


def is_index_only(source_path: str, row: dict[str, str], policy: dict[str, Any]) -> bool:
    marker_list = policy.get("index_rule", {}).get("markers", [])
    # A contents page can be one indexed page inside a valuable periodical.
    # Do not downgrade the whole source merely because ``indexed_titles`` says
    # 目录; only an explicit source-file/finding-aid marker can do that.
    path_haystack = source_path.lower()
    explicit_markers = [*marker_list, "index"]
    return any(str(marker).lower() in path_haystack for marker in explicit_markers)


def status_rule(status: str, policy: dict[str, Any]) -> dict[str, str]:
    for rule in policy.get("status_rules", []):
        if isinstance(rule, dict) and rule.get("status") == status:
            return {str(k): str(v) for k, v in rule.items()}
    return {
        "admission_class": "REVIEW_STATUS_UNMAPPED",
        "ocr_action": "HOLD_UNTIL_STATUS_REVIEW",
        "next_action": "补充来源状态字段后再分流。",
    }


def priority_score(row: dict[str, str], admission_class: str) -> int:
    path = row.get("source_path", "")
    score = {"gazette_scans": 60, "sourcebooks": 55, "press_scans": 50}.get(row.get("source_group", ""), 20)
    score += sum(12 for marker in CORE_MARKERS if marker in path)
    phase, _ = phase_for(path)
    if phase != "unknown":
        score += 10
    if admission_class == "RETAIN_NAVIGATION_ONLY":
        score -= 25
    if admission_class.startswith("HOLD_"):
        score += 5
    return score


def build_rows(
    inventory: list[dict[str, str]],
    policy: dict[str, Any],
    reconciliation: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    by_sha: defaultdict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(inventory):
        digest = row.get("sha256", "").strip().lower()
        if re.fullmatch(r"[0-9a-f]{64}", digest):
            by_sha[digest].append(index)

    output: list[dict[str, Any]] = []
    for index, row in enumerate(inventory):
        source_path = row.get("source_path", "").strip()
        status = row.get("status", "").strip()
        form = source_form(row)
        rule = status_rule(status, policy)
        index_only = is_index_only(source_path, row, policy)
        if index_only:
            admission_class = str(policy["index_rule"]["admission_class"])
            ocr_action = str(policy["index_rule"]["ocr_action"])
            next_action = str(policy["index_rule"]["next_action"])
            reason_codes = ["INDEX_OR_FINDING_AID"]
        else:
            admission_class = rule["admission_class"]
            ocr_action = rule["ocr_action"]
            next_action = rule["next_action"]
            reason_codes = [f"STATUS_{status.upper() or 'UNKNOWN'}"]

        reconciliation_row = (reconciliation or {}).get(source_path, {})
        reconciliation_disposition = str(reconciliation_row.get("disposition", ""))
        if not index_only and reconciliation_disposition in {
            "RECONCILED_CANONICAL_PAGE_CHAIN",
            "RECONCILED_DUPLICATE_COMPLETE_LAYERS",
        }:
            admission_class = "RETAIN_FORMAL_PAGE_CHAIN"
            ocr_action = "NO_REPEAT_OCR_FORMAL_PAGES_EXIST"
            next_action = "页链已与物理页对账；转入定向人工引用复核，不重复 OCR 或整本导入。"
            reason_codes.append("PAGE_RECONCILED_COMPLETE_CANONICAL_LAYER")
        elif not index_only and reconciliation_disposition == "RECONCILED_COMPLETE_OCR_LAYER":
            admission_class = "RETAIN_TARGETED_REVIEW"
            ocr_action = "USE_EXISTING_OCR_TARGETED_REVIEW"
            next_action = "已有完整 OCR 页层；只做目标页视觉核验，按需补建 canonical 页链。"
            reason_codes.append("PAGE_RECONCILED_COMPLETE_OCR_LAYER")

        if form == "ELECTRONIC_TEXT":
            ocr_action = "SKIP_OCR_ELECTRONIC_TEXT"
            reason_codes.append("ELECTRONIC_TEXT_DECLARED")
        elif form == "SCAN_OR_UNKNOWN_PDF":
            reason_codes.append("TEXT_LAYER_NOT_DECLARED")

        digest = row.get("sha256", "").strip().lower()
        duplicate_indexes = by_sha.get(digest, []) if digest else []
        duplicate_status = "UNIQUE_SHA"
        duplicate_group = ""
        if len(duplicate_indexes) > 1:
            duplicate_group = "sha256:" + digest[:16]
            duplicate_status = "SAME_SHA_REVIEW_GROUP"
            reason_codes.append("SAME_SHA_MULTIPLE_PATHS")

        year, phase_label = phase_for(source_path)
        output.append(
            {
                "queue_id": "SAQ-" + hashlib.sha256(source_path.encode("utf-8")).hexdigest()[:16],
                "source_path": source_path,
                "source_group": row.get("source_group", ""),
                "sha256": digest,
                "physical_pages": integer(row.get("pdf_pages")),
                "indexed_pages": integer(row.get("indexed_pages")),
                "ocr_draft_pages": integer(row.get("ocr_draft_pages")),
                "inventory_status": status,
                "reconciliation_disposition": reconciliation_disposition,
                "source_form": form,
                "phase": year,
                "phase_label": phase_label,
                "admission_class": admission_class,
                "ocr_action": ocr_action,
                "duplicate_status": duplicate_status,
                "duplicate_group": duplicate_group,
                "priority_score": priority_score(row, admission_class),
                "reason_codes": reason_codes,
                "next_action": next_action,
                "body_read": False,
                "citation_ready_changed": False,
                "auto_delete": False,
            }
        )
    return sorted(output, key=lambda item: (-int(item["priority_score"]), item["source_path"]))


def write_outputs(rows: list[dict[str, Any]], output_dir: Path, inventory: Path, policy: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = Counter(row["admission_class"] for row in rows)
    ocr_counts = Counter(row["ocr_action"] for row in rows)
    duplicate_groups = len({row["duplicate_group"] for row in rows if row["duplicate_group"]})
    report = {
        "schema": "domestic_source_admission_queue.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_inventory": str(inventory),
        "policy": str(policy),
        "source_rows": len(rows),
        "admission_counts": dict(sorted(counts.items())),
        "ocr_action_counts": dict(sorted(ocr_counts.items())),
        "same_sha_groups": duplicate_groups,
        "body_read": False,
        "formal_db_written": False,
        "auto_delete": False,
        "auto_promote_citation_ready": False,
        "rows": rows,
    }
    (output_dir / "SOURCE_ADMISSION_QUEUE.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (output_dir / "SOURCE_ADMISSION_QUEUE.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    md = [
        "# 国内资料准入与 OCR 分流清单",
        "",
        "本清单只读取元数据覆盖表；不读取正文、不写正式 SQLite、不删除或重命名本地文件。",
        "",
        f"- 来源行：{len(rows)}",
        f"- 同 SHA 复核组：{duplicate_groups}",
        "",
        "## 准入分流",
        "",
        "| 分流 | 数量 |",
        "|---|---:|",
    ]
    md.extend(f"| {key} | {value} |" for key, value in sorted(counts.items()))
    md.extend(["", "## OCR 动作", "", "| 动作 | 数量 |", "|---|---:|"])
    md.extend(f"| {key} | {value} |" for key, value in sorted(ocr_counts.items()))
    md.extend(
        [
            "",
            "## 硬门禁",
            "",
            "- `ELECTRONIC_TEXT` 不重复 OCR；文本层未声明的 PDF 必须先探测文本层。",
            "- `formal_page_complete` 只转人工引用复核，不因已有 OCR 再次整本导入。",
            "- `formal_page_count_anomaly` 先做页链对账，不能用 OCR 数量掩盖冲突。",
            "- 同 SHA 只建立复核组，不自动删除任何副本。",
            "- 任何分流都不改变 `citation_ready`、`human_verified` 或真实性等级。",
            "",
        ]
    )
    (output_dir / "SOURCE_ADMISSION_QUEUE.md").write_text("\n".join(md), encoding="utf-8")
    return {
        "output_dir": str(output_dir),
        "source_rows": len(rows),
        "admission_counts": dict(sorted(counts.items())),
        "ocr_action_counts": dict(sorted(ocr_counts.items())),
        "same_sha_groups": duplicate_groups,
        "body_read": False,
        "formal_db_written": False,
        "auto_delete": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument(
        "--reconciliation",
        type=Path,
        default=None,
        help="optional metadata-only output from reconcile_source_page_counts.py",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    inventory = args.inventory.resolve()
    policy = args.policy.resolve()
    reconciliation = load_reconciliation(args.reconciliation.resolve() if args.reconciliation else None)
    output_dir = args.output_dir.resolve()
    rows = build_rows(load_inventory(inventory), load_policy(policy), reconciliation)
    print(json.dumps(write_outputs(rows, output_dir, inventory, policy), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
