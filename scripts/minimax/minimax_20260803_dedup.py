#!/usr/bin/env python3
"""
国内资料生产线：去重报告（Phase 1.2）
=====================================

复用 codex 时期已有的去重逻辑，但用于国内资料库的整库扫描。

去重维度：
1. candidate_id 完全相等 — 已在 KEEP_FIELDS 唯一索引
2. URL normalize（去掉 tracking query、fragment、trailing slash）
3. catalog_reference + repository_code 相同
4. archive_fonds + archive_series + archive_file 完全相等
5. title + document_date + repository_code 组合（去除标点/空格）
6. source_url 相同 + period 相同

输出：
  work/minimax-20260803/02_manifests/duplicate_report.csv
  work/minimax-20260803/02_manifests/duplicate_clusters.json

逻辑原则：
- 第一次出现的 candidate_id 视为 canonical
- 其余等价记录写入 duplicate_report.csv，并标记 keep_policy
- 是否真正需要 OCR 取决于：
  - canonical 没有 full_item_online 时，等价记录中仍可作为 supplementary OCR
  - canonical 已有 PDF/OCR 时，等价记录标为 "skip_ocr_dupe"

"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


def normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        u = urlparse(url.strip())
    except Exception:
        return url
    # 去掉 fragment
    fragment = ""
    # 去掉常见 tracking 参数
    drop_params = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                   "ref", "fbclid", "gclid", "mc_cid", "mc_eid"}
    drop_params |= {k.lower() for k in drop_params}
    qs = parse_qsl(u.query, keep_blank_values=False)
    qs = [(k, v) for k, v in qs if k.lower() not in drop_params]
    new_query = urlencode(qs, doseq=True)
    path = u.path.rstrip("/") or "/"
    # 去掉尾部 index.html / default.aspx
    path = re.sub(r"/(index|default)\.(html|aspx|htm|php)$", "", path, flags=re.IGNORECASE)
    return urlunparse((u.scheme.lower(), u.netloc.lower(), path, u.params, new_query, fragment))


def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    s = re.sub(r"[\s\u3000]+", "", title)
    s = re.sub(r"[\s,，。；;、《》「」『』【】()（）\[\]【】·•．\-—_＿\.…]+", "", s)
    return s.lower()


def extract_page_from_catalog(catalog: str | None) -> str | None:
    """从 catalog_reference 中提取页码信息，如'第5页'。"""
    if not catalog:
        return None
    m = re.search(r"第\s*(\d+)\s*页", catalog)
    if m:
        return m.group(1)
    return None


def dedupe_key(c: dict) -> list[tuple]:
    """返回候选可能匹配的等价键组。每条都有 (dim, key) 元组。

    重要原则：同一 source_url（同一份 PDF / 同一原件）内的不同文章不能所以仅靠 URL 合并。
    """
    keys = []
    cid = c.get("candidate_id")
    if cid:
        keys.append(("candidate_id", cid.strip()))
    url = normalize_url(c.get("source_url"))
    # 注意：url 单独不作为主键。使用 url + 内部定位（page / date）粒度
    cat = c.get("catalog_reference")
    repo = c.get("repository_code")
    norm_title = normalize_title(c.get("title"))
    date = c.get("document_date")
    page = extract_page_from_catalog(cat) if cat else None

    # 复合键：catalog_reference + repository_code
    if cat and repo:
        keys.append(("catalog", f"{repo.strip()}::{cat.strip()}"))
    # 档号组合：仅当有完整档号时使用
    if c.get("archive_fonds") and c.get("archive_series"):
        keys.append(("archive", f"{str(c['archive_fonds']).strip()}::{str(c['archive_series']).strip()}::{str(c.get('archive_file') or '').strip()}"))
    # title + date + repo
    if norm_title and date and repo:
        keys.append(("title_date_repo", f"{repo}::{date}::{norm_title}"))
    # catalog + page（同一汇编的不同页码 = 不同文章）
    if cat and repo and page:
        keys.append(("catalog_page", f"{repo.strip()}::{page}::{norm_title[:30] if norm_title else ''}"))
    # url + date + page（同一 PDF / 同一原件不同日期/页码应分开）
    if url and date:
        keys.append(("url_date", f"{url}::{date}::{page or ''}"))
    elif url and page:
        keys.append(("url_page", f"{url}::{page}"))
    return keys


def jaccard(a: str, b: str) -> float:
    """字符集合相似度，用于标题近似去重。"""
    if not a or not b:
        return 0.0
    sa = set(a)
    sb = set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def build_clusters(candidates: list[dict]) -> list[list[dict]]:
    """基于等价键聚合到簇；候选可能同时出现在多个键维度上。"""
    node_parent: dict[str, str] = {}

    def find(x: str) -> str:
        while node_parent.get(x, x) != x:
            node_parent[x] = node_parent.get(node_parent[x], node_parent[x])
            x = node_parent[x]
        return x

    def union(a: str, b: str):
        ra, rb = find(a), find(b)
        if ra != rb:
            node_parent[ra] = rb

    node_lookup: dict[str, dict] = {}
    for c in candidates:
        cid = c.get("candidate_id")
        if not cid:
            continue
        node_lookup[cid] = c
        for dim, key in dedupe_key(c):
            bucket_key = f"#{dim}={key}"
            if bucket_key not in node_parent:
                node_parent[bucket_key] = bucket_key
            union(bucket_key, cid)

    # 按根聚类
    clusters: dict[str, list[dict]] = defaultdict(list)
    for cid in node_lookup:
        root = find(cid)
        clusters[root].append(node_lookup[cid])

    # 标题近似去重（仅在同库同年内）
    extra_keys: dict[str, str] = {}
    for c in candidates:
        cid = c.get("candidate_id")
        if not cid:
            continue
        title = normalize_title(c.get("title"))
        date = c.get("document_date") or ""
        repo = c.get("repository_code") or ""
        # 只对 page 字段都缺失或同页码的 (同一汇编 + 同一日期 + 同一页码) 的候选做近似合并
        page = extract_page_from_catalog(c.get("catalog_reference"))
        if title and len(title) >= 10 and date and repo and page:
            extra_keys[cid] = f"fuzzy::{repo}::{date}::{page}::{title[:30]}"

    fuzzy_groups: dict[str, list[str]] = defaultdict(list)
    for cid, key in extra_keys.items():
        fuzzy_groups[key].append(cid)

    extra_clusters = {}
    for key, cids in fuzzy_groups.items():
        if len(cids) < 2:
            continue
        # 计算近似匹配度
        titles = [normalize_title(c.get("title")) for c in (node_lookup[c] for c in cids)]
        for i in range(len(cids)):
            for j in range(i + 1, len(cids)):
                if jaccard(titles[i], titles[j]) >= 0.95:
                    union(cids[i], cids[j])

    # 重新聚类
    final: dict[str, list[dict]] = defaultdict(list)
    for cid in node_lookup:
        root = find(cid)
        final[root].append(node_lookup[cid])

    return [v for v in final.values() if len(v) > 1]


def ocr_already_canonical(canonical: dict, members: list[dict]) -> dict:
    """检查 canonical 与簇成员是否已经有 OCR/PDF 证据。"""
    has_ocr = False
    has_pdf = False
    for m in members:
        if m.get("online_availability") == "full_item_online":
            has_pdf = True
        elif m.get("online_availability") in {"surrogate_online", "catalogue_only_online"}:
            has_ocr = True
    return {
        "canonical_has_full_online": has_pdf,
        "any_member_has_surrogate": has_ocr and not has_pdf,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("work/minimax-20260803/01_inventory/inventory_full.jsonl"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("work/minimax-20260803/02_manifests"),
    )
    args = parser.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    rows = [json.loads(line) for line in args.inventory.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(rows)} inventory rows")

    # 预先合并：保留 _period 字段
    candidates = []
    for r in rows:
        c = dict(r)
        c["period"] = c.get("_period")
        candidates.append(c)

    clusters = build_clusters(candidates)
    print(f"Found {len(clusters)} duplicate clusters")

    # 写 csv
    csv_path = out / "duplicate_report.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "cluster_id", "canonical_candidate_id", "duplicate_candidate_id",
            "equal_dim", "canonical_title", "duplicate_title",
            "canonical_period", "duplicate_period",
            "canonical_repo", "duplicate_repo",
            "canonical_l1_l4", "duplicate_l1_l4",
            "canonical_availability", "duplicate_availability",
            "has_diff_archive", "diff_archive_note",
            "keep_policy",
        ])
        cluster_meta = []
        for idx, cluster in enumerate(clusters, start=1):
            # 选择 canonical：优先 reviewed_by=human + authenticity_level_accepted 最高
            def rank(c):
                rank_priority = {
                    "L1": 7, "L0": 7, "L2": 6, "L3": 5, "L4": 4, "LX": 3, None: 0, "": 0,
                }
                r = rank_priority.get(c.get("authenticity_level_accepted") or c.get("authenticity_level_proposed"), 0)
                if c.get("online_availability") == "full_item_online":
                    r += 0.5
                if c.get("review_status") == "accepted":
                    r += 0.25
                if c.get("online_availability") == "surrogate_online":
                    r += 0.1
                return r

            cluster_sorted = sorted(cluster, key=rank, reverse=True)
            canonical = cluster_sorted[0]
            duplicates = cluster_sorted[1:]
            equal_dim = []
            for c in cluster:
                keys = dict(dedupe_key(c))
                if canonical.get("source_url") and normalize_url(c.get("source_url")) == normalize_url(canonical.get("source_url")):
                    equal_dim.append("url")
                if c.get("archive_fonds") == canonical.get("archive_fonds") and c.get("archive_series") == canonical.get("archive_series"):
                    equal_dim.append("archive")
                if canonical.get("title") and normalize_title(c.get("title")) == normalize_title(canonical.get("title")):
                    equal_dim.append("title")
            equal_dim_str = "|".join(sorted(set(equal_dim))) or "fuzzy_jaccard>=0.95"

            for dup in duplicates:
                # 是否档号不同
                same_archive = (
                    dup.get("archive_fonds") == canonical.get("archive_fonds")
                    and dup.get("archive_series") == canonical.get("archive_series")
                    and dup.get("archive_file") == canonical.get("archive_file")
                )
                if not same_archive and (dup.get("archive_fonds") or canonical.get("archive_fonds")):
                    diff_note = f"fonds/series differs: dup={dup.get('archive_fonds')}/{dup.get('archive_series')}/{dup.get('archive_file')} vs canonical={canonical.get('archive_fonds')}/{canonical.get('archive_series')}/{canonical.get('archive_file')}"
                elif dup.get("title") != canonical.get("title"):
                    diff_note = "title differs but other keys match"
                else:
                    diff_note = "no diff in archive fields"

                # keep_policy
                if canonical.get("online_availability") == "full_item_online":
                    keep_policy = "skip_ocr_dupe"  # canonical 已有数字件，不重复 OCR
                elif canonical.get("online_availability") == "surrogate_online":
                    keep_policy = "skip_ocr_dupe_or_link_only"
                else:
                    keep_policy = "review_for_ocr_dedup"

                w.writerow([
                    f"DCL-{idx:04d}",
                    canonical.get("candidate_id"),
                    dup.get("candidate_id"),
                    equal_dim_str,
                    (canonical.get("title") or "")[:80],
                    (dup.get("title") or "")[:80],
                    canonical.get("_period"),
                    dup.get("_period"),
                    canonical.get("repository_code"),
                    dup.get("repository_code"),
                    canonical.get("authenticity_level_accepted") or canonical.get("authenticity_level_proposed"),
                    dup.get("authenticity_level_accepted") or dup.get("authenticity_level_proposed"),
                    canonical.get("online_availability"),
                    dup.get("online_availability"),
                    "no" if same_archive else "yes",
                    diff_note,
                    keep_policy,
                ])
            cluster_meta.append({
                "cluster_id": f"DCL-{idx:04d}",
                "size": len(cluster),
                "canonical_candidate_id": canonical.get("candidate_id"),
                "canonical_title": canonical.get("title"),
                "canonical_period": canonical.get("_period"),
                "canonical_repo": canonical.get("repository_code"),
                "members": [
                    {"candidate_id": c.get("candidate_id"),
                     "title": c.get("title"),
                     "period": c.get("_period"),
                     "repo": c.get("repository_code"),
                     "level": c.get("authenticity_level_accepted") or c.get("authenticity_level_proposed"),
                     "availability": c.get("online_availability"),
                     "review_status": c.get("review_status")}
                    for c in cluster
                ],
            })

    # 写 clusters.json（精简版）
    cluster_json = out / "duplicate_clusters.json"
    cluster_json.write_text(
        json.dumps({
            "produced_at": "2026-08-03",
            "inventory_input": str(args.inventory),
            "total_clusters": len(clusters),
            "total_duplicates": sum(len(c) - 1 for c in clusters),
            "clusters": cluster_meta,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 汇总
    print(f"clusters: {len(clusters)}")
    print(f"total duplicates: {sum(len(c) - 1 for c in clusters)}")
    print(f"csv: {csv_path}")
    print(f"json: {cluster_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
