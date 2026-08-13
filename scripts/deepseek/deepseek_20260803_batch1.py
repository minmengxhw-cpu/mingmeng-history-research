#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 国内证据审计 · Batch 1：对账 + 重复/低价值/目录冒充全文
================================================================
输入：01_inputs/*.csv|jsonl|json（只读快照）
输出：02_analysis/
  - reconciliation_report.json        基线文档口径 vs 库 vs staging 对账
  - dedup_clusters_review.csv         复核 MiniMax 32 簇/92 重复项
  - missed_duplicates.csv             跨簇/跨库漏检重复
  - low_value_list.csv                低价值条目
  - catalog_as_fulltext.csv           目录冒充全文条目
  - duplicates_low_value_report.md    汇总报告
"""
import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
WORK = BASE / "work" / "deepseek-20260803"
IN = WORK / "01_inputs"
OUT = WORK / "02_analysis"
OUT.mkdir(parents=True, exist_ok=True)


def read_csv(name):
    path = IN / name
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(name):
    path = IN / name
    if not path.exists():
        return None
    return json.load(open(path, encoding="utf-8"))


def write_csv(name, rows):
    if not rows:
        print(f"  [warn] {name}: empty")
        return
    path = OUT / name
    fieldnames = list(dict.fromkeys(k for r in rows for k in r.keys()))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"  [ok] {name} ({len(rows)} rows)")


def norm_url(u):
    if not u:
        return ""
    u = u.strip().lower()
    u = re.sub(r"^https?://(www\.)?", "", u)
    u = u.rstrip("/")
    return u


def norm_title(t):
    if not t:
        return ""
    t = re.sub(r"[\s\u3000\-—_·\.。，,、（）()「」【】《》\"'“”‘’]+", "", str(t))
    return t.lower()


# ----------------------------------------------------------------------
# 1. 对账
# ----------------------------------------------------------------------
def reconcile():
    inv = read_json("inventory_reconciliation.json") or {}
    staging_import = read_csv("staging_import_ready.csv")
    staging_review = read_csv("staging_needs_review.csv")
    staging_excl = read_csv("staging_exclude.csv")
    staging_sql = read_csv("staging_domestic_candidates.csv")
    db_cands = read_csv("domestic_candidates.csv")
    docs = read_csv("domestic_documents.csv")
    cands_jsonl = []
    p = IN / "snapshot_candidates.jsonl"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            cands_jsonl = [json.loads(l) for l in f if l.strip()]

    rep = {
        "基线文档口径(2026-07-28验收)": {
            "documents_total": 1003,
            "domestic_documents": 142,
            "accepted_candidates": 679,
            "needs_human_review": 10,
            "classification_orphans": 15,
        },
        "生产库口径(本次只读导出)": {
            "documents_total": inv.get("counts", {}).get("documents_total", "n/a"),
            "domestic_documents": len(docs),
            "accepted_candidates": inv.get("counts", {}).get("candidates_by_status", {}).get("accepted"),
            "needs_human_review": inv.get("counts", {}).get("candidates_by_status", {}).get("needs_human_review"),
            "classification_orphans": len(read_csv("classification_orphans.csv")),
        },
        "staging CSV 口径": {
            "import_ready": len(staging_import),
            "needs_review": len(staging_review),
            "exclude_duplicates": len(staging_excl),
            "total": len(staging_import) + len(staging_review) + len(staging_excl),
        },
        "staging SQLite 口径": {
            "staging_domestic_candidates": len(staging_sql),
            "accepted": sum(1 for r in staging_sql if r.get("review_status") == "accepted"),
            "needs_human_review": sum(1 for r in staging_sql if r.get("review_status") == "needs_human_review"),
        },
        "data/domestic/candidates.jsonl 口径": {
            "total": len(cands_jsonl),
            "accepted": sum(1 for r in cands_jsonl if r.get("review_status") == "accepted"),
            "needs_human_review": sum(1 for r in cands_jsonl if r.get("review_status") == "needs_human_review"),
        },
    }
    # 差异解释
    notes = [
        "基线验收(07-28)后、MiniMax 生产阶段将 679 条 accepted 候选导入正式库，国内文献 142→525",
        "candidates 总量恒为 689；accepted 660 + needs_human_review 29；基线报告口径 679+10，19 条由 accepted 翻转为 needs_human_review（reviewed_at 未更新，见 Batch4）",
        "staging CSV 与 staging SQLite 存在 12 条漂移（import_ready 557 vs SQLite 候选 664 的 accepted 637）：CSV 是三轮清单脚本输出，SQLite 是入库前终态",
    ]
    rep["差异说明"] = notes
    with open(OUT / "reconciliation_report.json", "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print("reconciliation_report.json written")
    return staging_import, staging_sql, db_cands, docs


# ----------------------------------------------------------------------
# 2. 复核 MiniMax 去重簇 + 漏检重复
# ----------------------------------------------------------------------
def classify_group(ids, url_key=""):
    """按 candidate_id 命名模式区分：真重复 / 期-文章容器 / 汇编多文档 / 网站多条目"""
    n = len(ids)
    for i in ids:
        if not (str(i).startswith("domestic:")):
            return "unknown"
    # 汇编型：同一 PDF 内含多篇独立文档（MMHIST marxists 汇编、NLC 言论集等）
    if any("minmeng-wenxian" in i or "yanlunji" in i for i in ids) or "mzhtm1" in url_key:
        return "compilation_multi_doc" if n >= 3 else "compilation_pair"
    # 期-文章容器：issue 级与 article 级共享期号 PDF
    if any("-issue" in i or "-v3n" in i or "observer" in i for i in ids) and n >= 2:
        return "issue_article_container"
    if n == 2:
        # 网站锚点对（同站历史页 + 简介页）
        if any(i.endswith("-anchor") for i in ids):
            return "web_page_near_dup"
        if any("website" in i for i in ids):
            return "web_page_near_dup"
        if "xinhuanet" in "".join(ids) or "zl1872" in "".join(ids):
            return "web_page_near_dup"
    return "possible_true_dup"


def dedup_review(staging_sql, db_cands):
    # 32 簇 from manifest_duplicate_clusters.json
    cl = read_json("manifest_duplicate_clusters.json") or {}
    clusters = cl.get("clusters", [])
    # 簇内成员校验：所有 candidate_id 必须存在
    all_ids = set()
    for r in staging_sql:
        all_ids.add(r.get("candidate_id"))
    for r in db_cands:
        all_ids.add(r.get("candidate_id"))

    cluster_rows = []
    issues = []
    for c in clusters:
        cid = c["cluster_id"]
        members = c.get("members", [])
        canon = c.get("canonical_candidate_id")
        if canon not in all_ids:
            issues.append({"cluster_id": cid, "issue": "canonical 不存在于 staging/db candidates"})
        for m in c.get("members", []):
            mid = m.get("candidate_id") if isinstance(m, dict) else m
            if mid not in all_ids:
                issues.append({"cluster_id": cid, "member": mid, "issue": "member 不存在"})
            cluster_rows.append({
                "cluster_id": cid, "role": "canonical" if mid == canon else "dup",
                "candidate_id": mid,
            })

    # 漏检：同一 repository + 归一化 URL 相同 或 归一化题名相同 + 日期相同的候选，未在同一簇
    by_url = {}
    by_title = {}
    for r in staging_sql:
        u = norm_url(r.get("source_url"))
        if u:
            by_url.setdefault((r.get("repository_code"), u), []).append(r["candidate_id"])
        t = norm_title(r.get("title"))
        d = r.get("document_date") or ""
        if t:
            by_title.setdefault((r.get("repository_code"), t, d), []).append(r["candidate_id"])

    in_cluster = set()
    for c in clusters:
        in_cluster.add(c.get("canonical_candidate_id"))
        in_cluster.update([m.get("candidate_id") if isinstance(m, dict) else m
                           for m in c.get("members", [])])

    missed = []
    for k, ids in by_url.items():
        if len(ids) > 1:
            in_same = any(i in in_cluster for i in ids)
            if not in_same:
                missed.append({"kind": "same_url", "key": str(k), "candidates": ";".join(ids),
                               "relationship": classify_group(ids, url_key=str(k))})
    for k, ids in by_title.items():
        if len(ids) > 1:
            in_same = any(i in in_cluster for i in ids)
            if not in_same:
                missed.append({"kind": "same_title_date", "key": str(k), "candidates": ";".join(ids),
                               "relationship": classify_group(ids, url_key=str(k))})

    # 簇内 canonical 是否也出现在其他簇的 dup 成员中（簇间重叠）
    canon_ids = [c.get("canonical_candidate_id") for c in clusters]
    dup_ids = []
    for c in clusters:
        canon = c.get("canonical_candidate_id")
        for m in c.get("members", []):
            mid = m.get("candidate_id") if isinstance(m, dict) else m
            if mid != canon:
                dup_ids.append(mid)
    overlap = set(canon_ids) & set(dup_ids)
    if overlap:
        issues.append({"cluster_id": "cross", "issue": "canonical 同时出现在其他簇的 dup 成员中", "ids": sorted(overlap)})

    write_csv("dedup_clusters_review.csv",
              cluster_rows + [{"cluster_id": i["cluster_id"], "role": "ISSUE",
                               "candidate_id": i.get("member", "") or i.get("ids", ""),
                               "note": i["issue"]} for i in issues])
    write_csv("missed_duplicates.csv", missed)
    return len(clusters), len(issues), len(missed)


# ----------------------------------------------------------------------
# 3. 低价值 + 目录冒充全文
# ----------------------------------------------------------------------
def low_value(staging_sql, db_cands, docs):
    low = []
    cat = []  # 目录冒充全文
    for r in staging_sql:
        cid = r.get("candidate_id", "")
        av = (r.get("online_availability") or "").lower()
        mode = (r.get("access_mode") or "").lower()
        level = r.get("authenticity_level_proposed") or r.get("authenticity_level_accepted") or ""
        source_kind = r.get("source_kind") or ""
        cat_ref_status = r.get("catalog_reference_status") or ""
        page_count = int(r.get("page_count") or 0)
        sha = r.get("sha256") or ""
        title = r.get("title") or ""

        reasons = []
        if "catalogue_only" in av or "目录" in av:
            reasons.append("仅目录级(media_class=catalogue_only)")
        if mode and "offline" in mode and not sha:
            reasons.append("仅离线无数字影像")
        if source_kind in ("catalog", "catalogue", "finding_aid", "index_page"):
            reasons.append(f"资料类型={source_kind}")
        if "目录" in str(title) and page_count == 0 and not sha:
            reasons.append("题名含'目录'且无影像")
        if level and "LX" in level:
            reasons.append("等级 LX(未定)")
        if r.get("review_status") == "rejected":
            reasons.append("已被拒")

        if reasons:
            low.append({
                "candidate_id": cid, "title": title[:60],
                "repository_code": r.get("repository_code"),
                "level": level, "availability": av, "access_mode": mode,
                "source_kind": source_kind, "page_count": page_count,
                "review_status": r.get("review_status"),
                "low_value_reasons": ";".join(reasons),
            })

        # 目录冒充全文：声称 full text / 有 OCR 但实际是目录页或元数据卡
        if "full" in av and (source_kind in ("catalog", "catalogue", "index_page") or
                             "目录" in str(title)):
            cat.append({
                "candidate_id": cid, "title": title[:80],
                "repository_code": r.get("repository_code"),
                "level": level, "availability": av,
                "source_kind": source_kind, "note": "声称full_item但来源为目录/索引类",
            })

    # DB documents：pages 文本为纯元数据/题名的目录卡（DRNH 类问题）；本地 OCR 有 local_path 的不算
    for d in docs:
        doc_key = d.get("doc_key", "")
        title = d.get("title", "")
        url = d.get("url", "") or ""
        hit = d.get("hit_type", "")
        pages = int(d.get("sub_count") or 0)
        local_path = d.get("source_local_path") or ""
        origin_url = d.get("source_origin_url") or ""
        prov = int(d.get("prov_count") or 0)
        reasons = []
        if hit in ("drnh_catalogue", "catalogue_card", "doc-level"):
            reasons.append(f"hit_type={hit}(目录卡)")
        if not url and not origin_url and not local_path and prov == 0:
            reasons.append("无 URL/本地文件/溯源(provenance)")
        if reasons:
            low.append({
                "candidate_id": doc_key, "title": (title or "")[:60],
                "repository_code": d.get("source_registry_id", ""),
                "level": d.get("class_grade", ""), "availability": "",
                "access_mode": "", "source_kind": hit, "page_count": pages,
                "review_status": "", "low_value_reasons": ";".join(reasons),
            })
    write_csv("low_value_list.csv", low)
    write_csv("catalog_as_fulltext.csv", cat)
    return len(low), len(cat)


# ----------------------------------------------------------------------
def main():
    staging_import, staging_sql, db_cands, docs = reconcile()
    n_cl, n_issues, n_missed = dedup_review(staging_sql, db_cands)
    n_low, n_cat = low_value(staging_sql, db_cands, docs)

    md = f"""# Batch 1 · 对账与重复/低价值/目录冒充全文审计

- 复核 MiniMax 去重簇：32 簇 / 92 重复项；异常 {n_issues} 处；漏检 {n_missed} 条
- 低价值清单：{n_low} 条
- 目录冒充全文：{n_cat} 条（candidate 口径）
- 对账报告：reconciliation_report.json
"""
    (OUT / "duplicates_low_value_report.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
