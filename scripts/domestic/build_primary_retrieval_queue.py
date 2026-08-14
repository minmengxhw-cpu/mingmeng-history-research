#!/usr/bin/env python3
"""Build a metadata-only queue for the nine open domestic primary gaps.

This command joins event coverage, evidence-chain ``missing_primary`` targets,
candidate metadata and official access-audit records. It never reads source
body text, never downloads a file, and never promotes a candidate to a closed
primary-evidence state.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COVERAGE = ROOT / "data/domestic/event_coverage.json"
DEFAULT_CHAIN = ROOT / "data/domestic/topic_evidence_chain.json"
DEFAULT_CANDIDATES = ROOT / "data/domestic/candidates.jsonl"
DEFAULT_ACCESS_AUDIT = ROOT / "data/domestic/primary_evidence_access_audit.json"
DEFAULT_OUTPUT = ROOT / "data/domestic/primary_retrieval_queue.json"

ITEM_EVIDENCE_TYPES = {"digital_image", "official_document"}
CATALOGUE_EVIDENCE_TYPES = {"catalogue", "official_description", "printed_finding_aid"}
LEVEL_SCORE = {"L1": 40, "L2": 30, "L3": 20, "L4": 10, "L0": 5, "LX": 0}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_candidates(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        candidate_id = str(item.get("candidate_id") or "").strip()
        if candidate_id:
            rows[candidate_id] = item
    return rows


def chain_by_event(value: Any) -> dict[str, dict[str, Any]]:
    if isinstance(value, dict):
        return {str(key): row for key, row in value.items() if isinstance(row, dict)}
    if isinstance(value, list):
        return {
            str(row.get("event_id")): row
            for row in value
            if isinstance(row, dict) and row.get("event_id")
        }
    return {}


def route_status(candidate: dict[str, Any], audit: dict[str, Any] | None) -> tuple[str, str]:
    if audit and audit.get("access_status") == "official_viewer_locked":
        return "OFFICIAL_VIEWER_LOCKED", "官方查看器可达但需要授权"
    evidence_type = str(candidate.get("evidence_type") or "")
    availability = str(candidate.get("online_availability") or "")
    access_mode = str(candidate.get("access_mode") or "")
    source_url = str(candidate.get("source_url") or "")
    if evidence_type in ITEM_EVIDENCE_TYPES and availability == "full_item_online" and source_url.startswith("http"):
        return "PUBLIC_ITEM_CANDIDATE", "公开原件/影像候选，需核字节和页级 provenance"
    if access_mode in {"login", "reading_room", "offline"}:
        return "ACCESS_REQUEST_REQUIRED", "需登录、现场或机构权限"
    if evidence_type in CATALOGUE_EVIDENCE_TYPES or availability == "catalogue_only_online":
        return "CATALOGUE_OR_FINDING_AID", "目录/说明/索引线索，不是正文原件"
    if availability == "surrogate_online":
        return "PUBLIC_SURROGATE", "公开替代本或转录，需回追原件"
    if source_url.startswith("http") and access_mode == "open":
        return "PUBLIC_NAVIGATION_LEAD", "公开导航或后期叙述，需回追一手来源"
    return "UNRESOLVED_LEAD", "候选来源尚未形成可核验取得路径"


def route_score(candidate: dict[str, Any], status: str) -> int:
    score = {
        "PUBLIC_ITEM_CANDIDATE": 100,
        "OFFICIAL_VIEWER_LOCKED": 95,
        "ACCESS_REQUEST_REQUIRED": 80,
        "PUBLIC_SURROGATE": 65,
        "CATALOGUE_OR_FINDING_AID": 45,
        "PUBLIC_NAVIGATION_LEAD": 30,
        "UNRESOLVED_LEAD": 10,
    }.get(status, 0)
    score += LEVEL_SCORE.get(str(candidate.get("authenticity_level_accepted") or candidate.get("authenticity_level_proposed") or ""), 0)
    if str(candidate.get("relevance_grade_accepted") or candidate.get("relevance_grade_proposed") or "") == "core":
        score += 20
    if str(candidate.get("review_status") or "") == "accepted":
        score += 5
    return score


def route_candidate(candidate: dict[str, Any], audit: dict[str, Any] | None) -> dict[str, Any]:
    status, label = route_status(candidate, audit)
    source_url = str(candidate.get("source_url") or "")
    route = {
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "title": str(candidate.get("title") or ""),
        "repository_code": str(candidate.get("repository_code") or ""),
        "repository_name": str(candidate.get("repository_name") or ""),
        "catalog_reference": str(candidate.get("catalog_reference") or ""),
        "source_url": source_url if source_url.startswith("http") else "",
        "source_url_role": str(candidate.get("source_url_role") or ""),
        "evidence_type": str(candidate.get("evidence_type") or ""),
        "access_mode": str(candidate.get("access_mode") or ""),
        "online_availability": str(candidate.get("online_availability") or ""),
        "authenticity_level": str(candidate.get("authenticity_level_accepted") or candidate.get("authenticity_level_proposed") or ""),
        "relevance": str(candidate.get("relevance_grade_accepted") or candidate.get("relevance_grade_proposed") or ""),
        "review_status": str(candidate.get("review_status") or ""),
        "route_status": status,
        "route_label": label,
        "route_score": route_score(candidate, status),
        "access_audit_status": str((audit or {}).get("access_status") or ""),
        "body_read": False,
    }
    return route


def next_action(retrieval_class: str) -> str:
    return {
        "AUTHORIZED_VIEWER_REQUIRED": "由有权限账户取得允许保存的官方影像；记录授权范围、文件 SHA256、页码和人工复核。",
        "PUBLIC_ITEM_VERIFICATION": "下载或打开公开原件候选，核对来源身份、文件字节、页数和页级 provenance。",
        "ACCESS_REQUEST_REQUIRED": "向馆藏机构申请登录、现场阅览或复制许可；取得前保持开放缺口。",
        "CATALOGUE_OR_SURROGATE_REVIEW": "把目录/转录作为定位线索，继续追索完整原件或同期影像。",
        "ORIGINAL_ROUTE_UNRESOLVED": "补充馆藏档号、稳定入口和权利状态；不得把后期叙述升级为原件。",
    }.get(retrieval_class, "保持开放并补齐取得路径。")


def build_queue(coverage: list[dict[str, Any]], chains: dict[str, dict[str, Any]], candidates: dict[str, dict[str, Any]], audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    topics: list[dict[str, Any]] = []
    route_counts: Counter[str] = Counter()
    missing_targets = 0
    missing_candidate_ids: list[str] = []
    for item in coverage:
        event_id = str(item.get("event_id") or "")
        chain = chains.get(event_id, {})
        layers = chain.get("layers") if isinstance(chain.get("layers"), dict) else {}
        missing = layers.get("missing_primary", []) if isinstance(layers, dict) else []
        if not isinstance(missing, list):
            missing = []
        candidate_ids = [str(value) for value in item.get("domestic_candidate_ids", [])]
        route_rows = []
        for candidate_id in candidate_ids:
            candidate = candidates.get(candidate_id)
            if not candidate:
                missing_candidate_ids.append(candidate_id)
                continue
            route_rows.append(route_candidate(candidate, audits.get(candidate_id)))
        route_rows.sort(key=lambda row: (-int(row["route_score"]), row["candidate_id"]))
        audited_routes = [row for row in route_rows if row.get("access_audit_status")]
        ordinary_routes = [row for row in route_rows if not row.get("access_audit_status")]
        route_rows = audited_routes + ordinary_routes[: max(0, 12 - len(audited_routes))]
        for row in route_rows:
            route_counts[row["route_status"]] += 1
        missing_target_rows = []
        for target in missing:
            if not isinstance(target, dict):
                continue
            missing_targets += 1
            statuses = {row["route_status"] for row in route_rows}
            if "OFFICIAL_VIEWER_LOCKED" in statuses:
                retrieval_class = "AUTHORIZED_VIEWER_REQUIRED"
            elif "PUBLIC_ITEM_CANDIDATE" in statuses:
                retrieval_class = "PUBLIC_ITEM_VERIFICATION"
            elif "ACCESS_REQUEST_REQUIRED" in statuses:
                retrieval_class = "ACCESS_REQUEST_REQUIRED"
            elif statuses & {"PUBLIC_SURROGATE", "CATALOGUE_OR_FINDING_AID", "PUBLIC_NAVIGATION_LEAD"}:
                retrieval_class = "CATALOGUE_OR_SURROGATE_REVIEW"
            else:
                retrieval_class = "ORIGINAL_ROUTE_UNRESOLVED"
            missing_target_rows.append(
                {
                    "target": str(target.get("target") or ""),
                    "why_it_matters": str(target.get("why_it_matters") or ""),
                    "status": str(target.get("status") or "open"),
                    "retrieval_class": retrieval_class,
                    "next_action": next_action(retrieval_class),
                    "candidate_route_count": len(route_rows),
                }
            )
        topics.append(
            {
                "event_id": event_id,
                "event_name": str(item.get("event_name") or ""),
                "primary_evidence_status": str(item.get("primary_evidence_status") or ""),
                "missing_primary": missing_target_rows,
                "candidate_routes": route_rows,
                "body_read": False,
            }
        )
    return {
        "schema": "domestic_primary_retrieval_queue.v1",
        "generated_at": str(date.today()),
        "scope": "九个国内专题的开放主证据目标",
        "policy": "候选路由只用于追索；不把目录、转录、后期叙述或锁定查看器升级为原件闭环。",
        "topic_count": len(topics),
        "open_target_count": missing_targets,
        "route_status_counts": dict(sorted(route_counts.items())),
        "missing_candidate_ids": sorted(set(missing_candidate_ids)),
        "body_read": False,
        "formal_db_written": False,
        "auto_download": False,
        "auto_promote_primary_closed": False,
        "topics": topics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--chain", type=Path, default=DEFAULT_CHAIN)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--access-audit", type=Path, default=DEFAULT_ACCESS_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    coverage = read_json(args.coverage)
    chains = chain_by_event(read_json(args.chain))
    candidates = read_candidates(args.candidates)
    audit_payload = read_json(args.access_audit)
    audits = {
        str(row.get("candidate_id")): row
        for row in audit_payload.get("records", [])
        if isinstance(row, dict) and row.get("candidate_id")
    }
    result = build_queue(coverage, chains, candidates, audits)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("schema", "topic_count", "open_target_count", "route_status_counts", "body_read", "formal_db_written")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
