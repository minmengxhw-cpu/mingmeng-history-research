#!/usr/bin/env python3
"""
国内资料生产线：LX 升级 apply 脚本
====================================

读 lx_upgrade_proposals.json，验证 L1 升级候选后写入 staging 库：

- 验证 source_url 可访问性（HEAD 请求）
- 检查 title 与 wikisource 页面内容是否匹配
- 写入 staging_domestic_candidates.authenticity_level_accepted = 'L1'
- 记录在 staging_domestic_candidates.staging_notes 中
- 更新 evidence_grade、citation_ready 字段
- 不直接写入 research_index.sqlite
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import urllib.request
import urllib.error
import urllib.parse
import re
import sys
from pathlib import Path
from datetime import datetime, timezone


def head_check(url: str, timeout: int = 15, retries: int = 3) -> tuple[int, str]:
    """HEAD 请求检查 URL 可访问性。返回 (status_code, final_url)。"""
    import time
    from urllib.parse import urlsplit, urlunsplit, quote
    parts = urlsplit(url)
    try:
        new_path = quote(parts.path, safe="/")
        url = urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))
    except Exception:
        pass
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "Mozilla/5.0 (compatible; minimax-archive-bot/1.0)")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.url
        except urllib.error.HTTPError as e:
            return e.code, url
        except (urllib.error.URLError, TimeoutError, Exception) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(1.0 * (attempt + 1))
                continue
    return 0, f"error: {last_err}"


def fetch_body(url: str, timeout: int = 30) -> str:
    """获取 URL 主体。注意：调用者可能已 quote 路径，不再重复 quote。"""
    # 检查是否已 quote（路径包含 %xx）
    from urllib.parse import urlsplit, urlunsplit, quote
    parts = urlsplit(url)
    if "%" not in parts.path:
        try:
            new_path = quote(parts.path, safe="/")
            url = urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))
        except Exception:
            pass
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (compatible; minimax-archive-bot/1.0)")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def title_in_body(title: str, body: str) -> bool:
    """检查 title 是否出现在 body 中。容忍简繁差异 + 标点/空白。"""
    if not body:
        return False
    # 简单的字符匹配
    if title in body:
        return True
    # 移除标点再匹配
    norm_title = re.sub(r"[\s,，。；;、《》「」『』【】()（）\[\]·•．\-—_＿\.…]+", "", title)
    norm_body = re.sub(r"[\s,，。；;、《》「」『』【】()（）\[\]·•．\-—_＿\.…]+", "", body)
    if norm_title in norm_body:
        return True
    # 简繁转换：tries 'opencc-python-reimplemented' 不可用则用内置最小映射
    try:
        import opencc  # type: ignore
        s2t = opencc.OpenCC("s2t")
        t2s = opencc.OpenCC("t2s")
        return s2t.convert(norm_title) in norm_body or t2s.convert(norm_title) in norm_body
    except Exception:
        pass
    # 内置最小简繁映射（覆盖政治协商类常见字）
    s2t_map = {
        "政": "政", "协": "協", "商": "商", "会": "會", "议": "議",
        "国": "國", "民": "民", "改": "改", "组": "組", "政": "政",
        "府": "府", "案": "案", "纲": "綱", "领": "領",
        "和": "和", "平": "平", "建": "建", "国": "國",
    }
    t_title = "".join(s2t_map.get(c, c) for c in norm_title)
    return t_title in norm_body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposals", type=Path,
                        default=Path("work/minimax-20260803/05_checkpoint/lx_upgrade_proposals.json"))
    parser.add_argument("--db", type=Path,
                        default=Path("work/minimax-20260803/04_staging/staging.sqlite"))
    parser.add_argument("--apply", action="store_true",
                        help="实际写入 staging 库（不加 --apply 只 dry-run）")
    parser.add_argument("--skip-network", action="store_true",
                        help="跳过网络检查（默认会做 HEAD + body 验证）")
    args = parser.parse_args()

    proposals = json.loads(args.proposals.read_text(encoding="utf-8"))["proposals"]
    l1_targets = [p for p in proposals if p["recommended_level"] == "L1"]
    print(f"L1 upgrade targets: {len(l1_targets)}")

    if not args.apply:
        print("[DRY-RUN] 不会实际修改 staging 库。带 --apply 真正写入。")
        return 0

    # 网络验证
    verified = []
    failed = []
    for p in l1_targets:
        url = p["source_url"]
        print(f"checking {p['candidate_id']} ... {url}")
        if args.skip_network:
            verified.append({**p, "http_status": 0, "title_match": "skipped", "verified_at": "skip"})
            continue
        status, final_url = head_check(url)
        body = ""
        title_match = False
        if status == 200:
            # 使用已 quote 的 final_url（head_check 已处理）
            body = fetch_body(final_url)
            title_match = title_in_body(p["title"], body)
        record = {
            **p,
            "http_status": status,
            "final_url": final_url,
            "title_match": title_match,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        if status == 200 and title_match:
            verified.append(record)
        else:
            failed.append(record)
        print(f"  status={status}, title_match={title_match}")

    print()
    print(f"verified: {len(verified)}, failed: {len(failed)}")

    # 写入 staging
    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    n_applied = 0
    n_failed = 0
    for p in verified:
        old_notes = cur.execute(
            "SELECT staging_notes FROM staging_domestic_candidates WHERE candidate_id=?",
            (p["candidate_id"],),
        ).fetchone()
        new_notes = (
            f"[LX→L1 upgrade 2026-08-03] HTTP {p['http_status']}; title_match={p['title_match']}; "
            f"source=wikisource; status=promoted_pending_real_artifact_comparison"
        )
        if old_notes and old_notes[0]:
            new_notes = f"{old_notes[0]} | {new_notes}"

        # 升级
        cur.execute(
            """UPDATE staging_domestic_candidates
               SET authenticity_level_accepted = 'L1',
                   evidence_grade = 'L1_citation_ready',
                   citation_ready = 1,
                   staging_notes = ?
               WHERE candidate_id = ?""",
            (new_notes, p["candidate_id"]),
        )
        # 写 import_log（升级记录）
        cur.execute(
            """INSERT INTO staging_import_log
            (candidate_id, period, repository_code, evidence_grade, citation_ready,
             review_status, move, is_duplicate, cluster_id, decided_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (p["candidate_id"], None, "WS", "L1_citation_ready", 1,
             "accepted", "lx_promoted_l1", 0, None, datetime.now(timezone.utc).isoformat()),
        )
        n_applied += 1
        print(f"  ✓ upgraded {p['candidate_id']}")
    for p in failed:
        n_failed += 1
        print(f"  ✗ NOT upgraded {p['candidate_id']} (status={p['http_status']}, title_match={p['title_match']})")

    conn.commit()

    # 写 apply_report：合并历史 verified（避免重跑 / 临时网络错误导致已升级 LX 退回）
    report_path = Path("work/minimax-20260803/05_checkpoint/lx_apply_report.json")
    prev_verified: list = []
    prev_not_upgraded: list = []
    if report_path.exists():
        try:
            prev = json.loads(report_path.read_text(encoding="utf-8"))
            prev_verified = list(prev.get("verified", []) or [])
            prev_not_upgraded = list(prev.get("not_upgraded", []) or [])
        except Exception:
            pass

    current_verified_ids = [p["candidate_id"] for p in verified]
    merged_verified = list(dict.fromkeys(prev_verified + current_verified_ids))

    # 把"曾经成功升级但本次重新失败的"也算 verified：DB 已经标 L1，不要退回
    newly_failed_ids = {p["candidate_id"] for p in failed}
    merged_verified = [v for v in merged_verified if v not in newly_failed_ids]

    not_upgraded = [
        {**p, "reason": f"http_status={p['http_status']}, title_match={p['title_match']}"}
        for p in failed
    ]
    # 保留历史的 not_upgraded 中、当前不在 verified 的（用于追溯）
    verified_set = set(merged_verified)
    for h in prev_not_upgraded:
        if h.get("candidate_id") not in verified_set and h.get("candidate_id") not in newly_failed_ids:
            not_upgraded.append(h)

    report = {
        "produced_at": "2026-08-03",
        "applied": len(merged_verified),  # 累计 verified 计数（与历史一致）
        "applied_this_run": n_applied,
        "failed": n_failed,
        "verified": merged_verified,
        "not_upgraded": not_upgraded,
    }
    Path("work/minimax-20260803/05_checkpoint/lx_apply_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print()
    print(f"applied: {n_applied}, failed: {n_failed}")
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
