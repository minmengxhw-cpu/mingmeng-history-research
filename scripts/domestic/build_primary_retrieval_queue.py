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
import sqlite3
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COVERAGE = ROOT / "data/domestic/event_coverage.json"
DEFAULT_CHAIN = ROOT / "data/domestic/topic_evidence_chain.json"
DEFAULT_CANDIDATES = ROOT / "data/domestic/candidates.jsonl"
DEFAULT_ACCESS_AUDIT = ROOT / "data/domestic/primary_evidence_access_audit.json"
DEFAULT_DB = ROOT / "data/research_index.sqlite"
DEFAULT_EVENT_LINKS = ROOT / "data/domestic/citation_event_links.json"
DEFAULT_OUTPUT = ROOT / "data/domestic/primary_retrieval_queue.json"

ITEM_EVIDENCE_TYPES = {"digital_image", "official_document"}
CATALOGUE_EVIDENCE_TYPES = {"catalogue", "official_description", "printed_finding_aid"}
LEVEL_SCORE = {"L1": 40, "L2": 30, "L3": 20, "L4": 10, "L0": 5, "LX": 0}
TARGET_ANCHORS = (
    (("1941", "成立"), ("成立宣言", "成立会议", "光明报")),
    (("1944", "改组"), ("改组", "更名", "改稱", "重组")),
    (("1945", "大会"), ("临时全国代表大会", "政治报告", "大会宣言", "纲领")),
    (("1946", "政协"), ("政协", "政治协商", "旧政协", "参政会", "赴京")),
    (("1946", "国民大会"), ("国民大会", "国大", "不参加", "拒绝参加")),
    (("1946", "李公朴"), ("李公朴", "闻一多", "民主周刊", "遇害", "抗议")),
    (("1947", "解散"), ("解散", "非法", "停止政治活动", "张群", "俞济时", "政府公函", "公函")),
    (("1948", "三中全会"), ("三中全会", "五一", "共同纲领")),
    (("1949", "新政协"), ("新政协", "筹备", "代表名单", "北上")),
)


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


def read_formal_index(path: Path) -> tuple[dict[str, dict[str, Any]], bool]:
    """Read only formal document/page counts for candidate IDs.

    This is deliberately an overlay: it records what is already present in
    the formal database, but never reads page text and never changes the
    database.  A missing or incomplete database returns ``({}, False)`` so a
    clean checkout can still build the metadata-only queue.
    """
    if not path.is_file():
        return {}, False
    try:
        resolved = path.resolve()
        with sqlite3.connect(f"file:{resolved}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            required = {"domestic_candidates", "documents", "pages", "page_provenance"}
            existing = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if not required <= existing:
                return {}, False
            rows = connection.execute(
                """
                SELECT
                    dc.candidate_id,
                    dc.ingested_document_id,
                    d.doc_key,
                    p.id AS page_id,
                    p.page_label,
                    pp.page_id AS provenance_page_id,
                    pp.citation_ready,
                    pp.needs_human_review,
                    pp.review_status,
                    pp.human_review_note,
                    pp.source_file,
                    pp.source_sha256
                FROM domestic_candidates dc
                LEFT JOIN documents d ON d.id=dc.ingested_document_id
                LEFT JOIN pages p ON p.document_id=d.id
                LEFT JOIN page_provenance pp ON pp.page_id=p.id
                ORDER BY dc.candidate_id, p.id
                """
            ).fetchall()
    except sqlite3.Error:
        return {}, False

    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate_id = str(row["candidate_id"])
        item = grouped.setdefault(
            candidate_id,
            {
                "formal_ingested_document_id": row["ingested_document_id"],
                "formal_doc_key": str(row["doc_key"] or ""),
                "formal_pages": [],
            },
        )
        if row["page_id"] is None:
            continue
        strict = (
            int(row["citation_ready"] or 0) == 1
            and int(row["needs_human_review"] or 0) == 0
            and str(row["review_status"] or "") == "human_verified"
            and bool(str(row["human_review_note"] or "").strip())
        )
        item["formal_pages"].append(
            {
                "page_id": int(row["page_id"]),
                "page_label": str(row["page_label"] or ""),
                "provenance_present": row["provenance_page_id"] is not None,
                "source_anchored": bool(
                    str(row["source_file"] or "").strip()
                    and len(str(row["source_sha256"] or "").strip()) == 64
                ),
                "strict_citation": strict,
            }
        )

    index: dict[str, dict[str, Any]] = {}
    for candidate_id, item in grouped.items():
        pages = list(item["formal_pages"])
        page_count = len(pages)
        strict_count = sum(bool(page["strict_citation"]) for page in pages)
        provenance_count = sum(bool(page["provenance_present"]) for page in pages)
        anchored_count = sum(bool(page["source_anchored"]) for page in pages)
        if item["formal_ingested_document_id"] is None:
            status = "NOT_INGESTED"
        elif page_count == 0:
            status = "FORMAL_METADATA_ONLY"
        elif strict_count > 0:
            status = "FORMAL_STRICT_PAGES_PRESENT"
        else:
            status = "FORMAL_PAGES_REVIEW_ONLY"
        index[candidate_id] = {
            "formal_ingested_document_id": item["formal_ingested_document_id"],
            "formal_doc_key": item["formal_doc_key"],
            "formal_page_count": page_count,
            "formal_strict_citation_page_count": strict_count,
            "formal_provenance_page_count": provenance_count,
            "formal_anchored_page_count": anchored_count,
            "formal_pages": pages,
            "formal_page_ids": [page["page_id"] for page in pages],
            "formal_strict_page_ids": [page["page_id"] for page in pages if page["strict_citation"]],
            "formal_ingest_status": status,
        }
    return index, True


def read_event_link_pages(path: Path, db_path: Path) -> tuple[dict[str, list[dict[str, Any]]], bool]:
    """Resolve existing topic page links against formal page metadata.

    The event-link file is a navigation-only manifest.  This overlay reads
    only document keys, page labels and provenance flags; it never reads
    ``pages.text`` and never changes the formal database.  A resolved page is
    shown as an existing topic entry, not as proof that a ``missing_primary``
    target is closed.
    """
    if not path.is_file() or not db_path.is_file():
        return {}, False
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError):
        return {}, False
    links = payload.get("links", []) if isinstance(payload, dict) else []
    if not isinstance(links, list):
        return {}, False
    link_keys = sorted(
        {
            (str(link.get("doc_key") or ""), str(link.get("page_label") or ""))
            for link in links
            if isinstance(link, dict)
            and str(link.get("doc_key") or "")
            and str(link.get("page_label") or "")
        }
    )
    if not link_keys:
        return {}, True
    try:
        resolved = db_path.resolve()
        with sqlite3.connect(f"file:{resolved}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            required = {"documents", "pages", "page_provenance"}
            existing = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if not required <= existing:
                return {}, False
            where = " OR ".join("(d.doc_key=? AND p.page_label=?)" for _ in link_keys)
            params = [value for pair in link_keys for value in pair]
            rows = connection.execute(
                f"""
                SELECT
                    p.id AS page_id,
                    p.page_label,
                    d.doc_key,
                    pp.page_id AS provenance_page_id,
                    pp.citation_ready,
                    pp.needs_human_review,
                    pp.review_status,
                    pp.human_review_note,
                    pp.source_file,
                    pp.source_sha256
                FROM pages p
                JOIN documents d ON d.id=p.document_id
                LEFT JOIN page_provenance pp ON pp.page_id=p.id
                WHERE {where}
                ORDER BY d.doc_key, p.id
                """,
                params,
            ).fetchall()
    except (OSError, sqlite3.Error):
        return {}, False

    resolved_pages: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        strict = (
            int(row["citation_ready"] or 0) == 1
            and int(row["needs_human_review"] or 0) == 0
            and str(row["review_status"] or "") == "human_verified"
            and bool(str(row["human_review_note"] or "").strip())
        )
        key = (str(row["doc_key"] or ""), str(row["page_label"] or ""))
        resolved_pages[key] = {
            "page_id": int(row["page_id"]),
            "page_label": str(row["page_label"] or ""),
            "doc_key": str(row["doc_key"] or ""),
            "provenance_present": row["provenance_page_id"] is not None,
            "source_anchored": bool(
                str(row["source_file"] or "").strip()
                and len(str(row["source_sha256"] or "").strip()) == 64
            ),
            "strict_citation": strict,
            "status": "strict_citation" if strict else "review_only",
        }

    by_event: dict[str, list[dict[str, Any]]] = {}
    for link in links:
        if not isinstance(link, dict):
            continue
        event_id = str(link.get("event_id") or "")
        page = resolved_pages.get(
            (str(link.get("doc_key") or ""), str(link.get("page_label") or ""))
        )
        if not event_id or page is None:
            continue
        item = dict(page)
        item.update(
            {
                "navigation_title": str(link.get("navigation_title") or ""),
                "rationale": str(link.get("rationale") or ""),
            }
        )
        by_event.setdefault(event_id, []).append(item)
    for event_id, items in by_event.items():
        deduped: dict[int, dict[str, Any]] = {}
        for item in items:
            deduped[int(item["page_id"])] = item
        by_event[event_id] = [deduped[page_id] for page_id in sorted(deduped)]
    return by_event, True


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


def target_match(candidate: dict[str, Any], target_text: str, event_name: str = "") -> tuple[bool, list[str]]:
    haystack = " ".join(
        str(candidate.get(key) or "")
        for key in (
            "title",
            "document_date",
            "document_type",
            "evidence_note",
            "event_tags",
            "person_tags",
            "catalog_reference",
        )
    )
    target_context = f"{target_text} {event_name}"
    anchors: tuple[str, ...] = ()
    for markers, values in TARGET_ANCHORS:
        if all(marker in target_context for marker in markers):
            anchors = values
            break
    hits = [value for value in anchors if value in haystack]
    return bool(hits), hits


def is_finding_aid(candidate: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(candidate.get(key) or "")
        for key in ("title", "document_type", "evidence_type")
    ).lower()
    return any(marker in haystack for marker in ("索引", "目录", "finding_aid", "catalogue"))


def route_status(candidate: dict[str, Any], audit: dict[str, Any] | None, target_text: str, event_name: str = "") -> tuple[str, str, bool, list[str]]:
    direct, match_terms = target_match(candidate, target_text, event_name)
    if not direct:
        return "RELATED_CONTEXT_ONLY", "与目标相关但不是直接取得路径", direct, match_terms
    if audit and audit.get("access_status") == "official_viewer_locked":
        return "OFFICIAL_VIEWER_LOCKED", "官方查看器可达但需要授权", direct, match_terms
    evidence_type = str(candidate.get("evidence_type") or "")
    availability = str(candidate.get("online_availability") or "")
    access_mode = str(candidate.get("access_mode") or "")
    source_url = str(candidate.get("source_url") or "")
    if is_finding_aid(candidate) or evidence_type in CATALOGUE_EVIDENCE_TYPES or availability == "catalogue_only_online":
        return "CATALOGUE_OR_FINDING_AID", "目录/说明/索引线索，不是正文原件", direct, match_terms
    if evidence_type in ITEM_EVIDENCE_TYPES and availability == "full_item_online" and source_url.startswith("http"):
        level = str(candidate.get("authenticity_level_accepted") or candidate.get("authenticity_level_proposed") or "")
        if level == "L1":
            return "PUBLIC_ITEM_CANDIDATE", "公开原刊/影像候选，需核字节和页级 provenance", direct, match_terms
        return "PUBLIC_SURROGATE", "公开数字副本候选，但原件层级仍需核对", direct, match_terms
    if access_mode in {"login", "reading_room", "offline"}:
        return "ACCESS_REQUEST_REQUIRED", "需登录、现场或机构权限", direct, match_terms
    if availability == "surrogate_online":
        return "PUBLIC_SURROGATE", "公开替代本或转录，需回追原件", direct, match_terms
    if source_url.startswith("http") and access_mode == "open":
        return "PUBLIC_NAVIGATION_LEAD", "公开导航或后期叙述，需回追一手来源", direct, match_terms
    return "UNRESOLVED_LEAD", "候选来源尚未形成可核验取得路径", direct, match_terms


def route_score(candidate: dict[str, Any], status: str) -> int:
    score = {
        "PUBLIC_ITEM_CANDIDATE": 100,
        "OFFICIAL_VIEWER_LOCKED": 95,
        "ACCESS_REQUEST_REQUIRED": 80,
        "PUBLIC_SURROGATE": 65,
        "CATALOGUE_OR_FINDING_AID": 45,
        "PUBLIC_NAVIGATION_LEAD": 30,
        "RELATED_CONTEXT_ONLY": 5,
        "UNRESOLVED_LEAD": 10,
    }.get(status, 0)
    score += LEVEL_SCORE.get(str(candidate.get("authenticity_level_accepted") or candidate.get("authenticity_level_proposed") or ""), 0)
    if str(candidate.get("relevance_grade_accepted") or candidate.get("relevance_grade_proposed") or "") == "core":
        score += 20
    if str(candidate.get("review_status") or "") == "accepted":
        score += 5
    return score


def formal_overlay(candidate_id: str, formal_index: dict[str, dict[str, Any]] | None, formal_index_available: bool) -> dict[str, Any]:
    if not formal_index_available:
        return {
            "formal_ingest_status": "NOT_CHECKED",
            "formal_ingested_document_id": None,
            "formal_doc_key": "",
            "formal_page_count": 0,
            "formal_strict_citation_page_count": 0,
            "formal_provenance_page_count": 0,
            "formal_anchored_page_count": 0,
            "formal_pages": [],
            "formal_page_ids": [],
            "formal_strict_page_ids": [],
        }
    return dict(
        formal_index.get(
            candidate_id,
            {
                "formal_ingest_status": "FORMAL_NOT_FOUND",
                "formal_ingested_document_id": None,
                "formal_doc_key": "",
                "formal_page_count": 0,
                "formal_strict_citation_page_count": 0,
                "formal_provenance_page_count": 0,
                "formal_anchored_page_count": 0,
                "formal_pages": [],
                "formal_page_ids": [],
                "formal_strict_page_ids": [],
            },
        )
    )


def route_candidate(
    candidate: dict[str, Any],
    audit: dict[str, Any] | None,
    target_text: str,
    event_name: str = "",
    formal_index: dict[str, dict[str, Any]] | None = None,
    formal_index_available: bool = False,
) -> dict[str, Any]:
    status, label, direct, match_terms = route_status(candidate, audit, target_text, event_name)
    source_url = str(candidate.get("source_url") or "")
    candidate_id = str(candidate.get("candidate_id") or "")
    route = {
        "candidate_id": candidate_id,
        "title": str(candidate.get("title") or ""),
        "repository_code": str(candidate.get("repository_code") or ""),
        "repository_name": str(candidate.get("repository_name") or ""),
        "catalog_reference": str(candidate.get("catalog_reference") or ""),
        "document_date": str(candidate.get("document_date") or ""),
        "document_date_precision": str(candidate.get("document_date_precision") or ""),
        "document_date_role": str(candidate.get("document_date_role") or ""),
        "event_context_date": str(candidate.get("event_context_date") or ""),
        "event_context_date_precision": str(candidate.get("event_context_date_precision") or ""),
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
        "target_match": direct,
        "target_match_terms": match_terms,
        "access_audit_status": str((audit or {}).get("access_status") or ""),
        "body_read": False,
    }
    route.update(formal_overlay(candidate_id, formal_index, formal_index_available))
    return route


def next_action(retrieval_class: str) -> str:
    return {
        "AUTHORIZED_VIEWER_REQUIRED": "由有权限账户取得允许保存的官方影像；记录授权范围、文件 SHA256、页码和人工复核。",
        "PUBLIC_ITEM_VERIFICATION": "下载或打开公开原件候选，核对来源身份、文件字节、页数和页级 provenance。",
        "ACCESS_REQUEST_REQUIRED": "向馆藏机构申请登录、现场阅览或复制许可；取得前保持开放缺口。",
        "CATALOGUE_OR_SURROGATE_REVIEW": "把目录/转录作为定位线索，继续追索完整原件或同期影像。",
        "ORIGINAL_ROUTE_UNRESOLVED": "补充馆藏档号、稳定入口和权利状态；不得把后期叙述升级为原件。",
    }.get(retrieval_class, "保持开放并补齐取得路径。")


def next_action_with_formal_overlay(
    retrieval_class: str,
    route_rows: list[dict[str, Any]],
    event_link_pages: list[dict[str, Any]] | None = None,
) -> str:
    strict_pages = sum(int(row.get("formal_strict_citation_page_count") or 0) for row in route_rows)
    formal_pages = sum(int(row.get("formal_page_count") or 0) for row in route_rows)
    event_link_rows = [row for row in (event_link_pages or []) if isinstance(row, dict)]
    event_link_strict_pages = sum(int(bool(row.get("strict_citation"))) for row in event_link_rows)
    if retrieval_class in {"AUTHORIZED_VIEWER_REQUIRED", "ACCESS_REQUEST_REQUIRED"}:
        action = next_action(retrieval_class)
        if formal_pages > 0:
            return action + "现有正式库页只能作同期交叉材料，不能替代该权限路径所指向的原件。"
        return action
    if strict_pages > 0:
        return "已有正式库严格引用页：先核对这些页与开放目标的版本/原件关系；不要重复下载或 OCR，未闭环部分继续追索原件。"
    if event_link_strict_pages > 0:
        return (
            f"已有专题导航关联的严格页（{event_link_strict_pages}页）：先核对这些页与开放目标的版本/原件关系；"
            "严格页不自动关闭主证据缺口，不要重复下载或 OCR，未闭环部分继续追索原件。"
        )
    if event_link_rows:
        return (
            f"已有专题导航关联页（{len(event_link_rows)}页），但尚未全部通过严格引用门禁；"
            "先核对页级 provenance，不要重复下载或 OCR，未闭环部分继续追索原件。"
        )
    if formal_pages > 0:
        return "已有正式库页但尚未通过严格引用门禁：先做页级 provenance 和人工复核，不要重复下载或 OCR。"
    return next_action(retrieval_class)


def must_keep_route(row: dict[str, Any]) -> bool:
    """Keep a high-value archive lead even when ordinary routes are capped.

    A topic may have dozens of newspaper and web candidates.  Exact archive
    references and exact official-compilation page leads are more useful for
    closing a primary gap than another duplicate public article, so they must
    remain visible in the metadata-only queue.  This does not promote the
    route or read its body.
    """
    return bool(
        row.get("target_match") is True
        and str(row.get("catalog_reference") or "").strip()
        and (
            (
                row.get("route_status") == "CATALOGUE_OR_FINDING_AID"
                and str(row.get("repository_code") or "") in {"SHAC", "NJSH"}
            )
            or (
                row.get("route_status") == "PUBLIC_SURROGATE"
                and str(row.get("repository_code") or "") == "MMHIST"
            )
        )
    )


def build_queue(
    coverage: list[dict[str, Any]],
    chains: dict[str, dict[str, Any]],
    candidates: dict[str, dict[str, Any]],
    audits: dict[str, dict[str, Any]],
    formal_index: dict[str, dict[str, Any]] | None = None,
    formal_index_available: bool = False,
    event_link_pages: dict[str, list[dict[str, Any]]] | None = None,
    event_link_index_available: bool = False,
) -> dict[str, Any]:
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
        topic_event_link_pages = list((event_link_pages or {}).get(event_id, []))
        missing_target_rows = []
        topic_routes_by_id: dict[str, dict[str, Any]] = {}
        for target in missing:
            if not isinstance(target, dict):
                continue
            missing_targets += 1
            target_text = str(target.get("target") or target.get("label") or "")
            route_rows = []
            for candidate_id in candidate_ids:
                candidate = candidates.get(candidate_id)
                if not candidate:
                    missing_candidate_ids.append(candidate_id)
                    continue
                route_rows.append(
                    route_candidate(
                        candidate,
                        audits.get(candidate_id),
                        target_text,
                        str(item.get("event_name") or ""),
                        formal_index,
                        formal_index_available,
                    )
                )
            route_rows.sort(key=lambda row: (-int(row["route_score"]), row["candidate_id"]))
            audited_routes = [row for row in route_rows if row.get("access_audit_status")]
            ordinary_routes = [row for row in route_rows if not row.get("access_audit_status")]
            route_rows = audited_routes + ordinary_routes[: max(0, 12 - len(audited_routes))]
            kept_ids = {row["candidate_id"] for row in route_rows}
            for row in sorted(
                (candidate for candidate in ordinary_routes if must_keep_route(candidate)),
                key=lambda candidate: (-int(candidate["route_score"]), candidate["candidate_id"]),
            ):
                if row["candidate_id"] not in kept_ids:
                    route_rows.append(row)
                    kept_ids.add(row["candidate_id"])
            for row in route_rows:
                route_counts[row["route_status"]] += 1
                topic_routes_by_id.setdefault(row["candidate_id"], row)
            direct_statuses = {
                row["route_status"]
                for row in route_rows
                if row.get("target_match") is True
            }
            if "OFFICIAL_VIEWER_LOCKED" in direct_statuses:
                retrieval_class = "AUTHORIZED_VIEWER_REQUIRED"
            elif "PUBLIC_ITEM_CANDIDATE" in direct_statuses:
                retrieval_class = "PUBLIC_ITEM_VERIFICATION"
            elif "ACCESS_REQUEST_REQUIRED" in direct_statuses:
                retrieval_class = "ACCESS_REQUEST_REQUIRED"
            elif direct_statuses & {"PUBLIC_SURROGATE", "CATALOGUE_OR_FINDING_AID", "PUBLIC_NAVIGATION_LEAD"}:
                retrieval_class = "CATALOGUE_OR_SURROGATE_REVIEW"
            else:
                retrieval_class = "ORIGINAL_ROUTE_UNRESOLVED"
            missing_target_rows.append(
                {
                    "target": target_text,
                    "why_it_matters": str(target.get("why_it_matters") or ""),
                    "status": str(target.get("status") or "open"),
                    "retrieval_class": retrieval_class,
                    "next_action": next_action_with_formal_overlay(
                        retrieval_class, route_rows, topic_event_link_pages
                    ),
                    "candidate_route_count": len(route_rows),
                    "formal_page_count": sum(int(row.get("formal_page_count") or 0) for row in route_rows),
                    "formal_strict_citation_page_count": sum(
                        int(row.get("formal_strict_citation_page_count") or 0) for row in route_rows
                    ),
                }
            )
        topics.append(
            {
                "event_id": event_id,
                "event_name": str(item.get("event_name") or ""),
                "primary_evidence_status": str(item.get("primary_evidence_status") or ""),
                "missing_primary": missing_target_rows,
                "event_link_pages": topic_event_link_pages,
                "event_link_strict_page_count": sum(
                    int(bool(page.get("strict_citation")))
                    for page in topic_event_link_pages
                    if isinstance(page, dict)
                ),
                "candidate_routes": sorted(
                    topic_routes_by_id.values(),
                    key=lambda row: (-int(row["route_score"]), row["candidate_id"]),
                )[:24],
                "body_read": False,
            }
        )
    return {
        "schema": "domestic_primary_retrieval_queue.v3",
        "generated_at": str(date.today()),
        "scope": "九个国内专题的开放主证据目标",
        "policy": "候选路由只用于追索；不把目录、转录、后期叙述或锁定查看器升级为原件闭环。",
        "topic_count": len(topics),
        "open_target_count": missing_targets,
        "route_status_counts": dict(sorted(route_counts.items())),
        "missing_candidate_ids": sorted(set(missing_candidate_ids)),
        "formal_index": {
            "available": formal_index_available,
            "metadata_only": True,
            "body_read": False,
            "formal_db_written": False,
            "candidate_count": len(formal_index or {}) if formal_index_available else 0,
        },
        "event_link_index": {
            "available": event_link_index_available,
            "metadata_only": True,
            "body_read": False,
            "formal_db_written": False,
            "event_count": len(event_link_pages or {}) if event_link_index_available else 0,
            "page_count": sum(len(rows) for rows in (event_link_pages or {}).values())
            if event_link_index_available
            else 0,
        },
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
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--event-links", type=Path, default=DEFAULT_EVENT_LINKS)
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
    formal_index, formal_index_available = read_formal_index(args.db)
    event_link_pages, event_link_index_available = read_event_link_pages(args.event_links, args.db)
    result = build_queue(
        coverage,
        chains,
        candidates,
        audits,
        formal_index=formal_index,
        formal_index_available=formal_index_available,
        event_link_pages=event_link_pages,
        event_link_index_available=event_link_index_available,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "schema",
                    "topic_count",
                    "open_target_count",
                    "route_status_counts",
                    "formal_index",
                    "event_link_index",
                    "body_read",
                    "formal_db_written",
                )
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
