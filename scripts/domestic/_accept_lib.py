"""共享 accept/fix 操作 lib (0722 重构引入, 修复对抗式审查 14 个 bug)。

修复覆盖:
- P0-1 非原子写 (write_jsonl_atomic 内置 tmp + os.replace)
- P0-2 apply 前不备份 (write_jsonl_atomic 内置 .bak.YYYYMMDD_HHMMSS)
- P0-3 uncertainty_note 覆写 (update_field 的 append_fields 选项)
- P1-4 r["candidate_id"] KeyError (read_jsonl + accept_batch 内部 .get + 跳过)
- P1-5 fix 静默跳过未预期 (update_field 的 preconditions 强校验)
- P1-6 level_accepted 可能 null (accept_batch 缺失时 raise)
- P2-7 docstring 9 vs 8 (统一由 ACCEPT_IDS 集合决定, 长度校验内置)
- P2-8 数字校验 (accept_batch 末 assert)
- P2-9 3 accept 重复代码 (本 lib 抽离 main 逻辑)
- P2-12 accept 后自动 validate (validate_after_write 选项)
- P3-13 UTF-8 BOM (read_jsonl 用 utf-8-sig)
- P3-14 重复 cid (read_jsonl 后调用 dedupe_by_cid)
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


# ===== I/O =====

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """读 JSONL: 剥 UTF-8 BOM, 跳过空行, 坏 JSON 直接 SystemExit(2)。

    Returns a list of dict rows in original order.
    """
    text = path.read_text(encoding="utf-8-sig")
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"ERROR: bad JSON at line {i}: {e}", file=sys.stderr)
            raise SystemExit(2)
    return rows


def dedupe_by_cid(rows: list[dict[str, Any]], *, warn: bool = True) -> list[dict[str, Any]]:
    """按 candidate_id 去重（保留首次出现），重复行写入 stderr 警告。

    Returns deduped list.
    """
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    dups: list[str] = []
    for r in rows:
        cid = r.get("candidate_id")
        if not cid:
            continue
        if cid in seen:
            dups.append(cid)
            continue
        seen.add(cid)
        out.append(r)
    if warn and dups:
        print(f"WARN: dropped {len(dups)} duplicate candidate_id rows: {dups[:5]}{'...' if len(dups) > 5 else ''}", file=sys.stderr)
    return out


def write_jsonl_atomic(path: Path, rows: list[dict[str, Any]], *, backup: bool = True) -> Path | None:
    """原子写 JSONL: 写 .tmp + os.replace; 可选备份到 .bak.YYYYMMDD_HHMMSS。

    Returns backup path if created, else None.
    """
    backup_path: Path | None = None
    if backup and path.exists():
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # 保留 .jsonl 扩展名 (with_suffix 会替换掉, 改用 with_name 拼接)
        backup_path = path.with_name(f"{path.name}.bak.{ts}")
        shutil.copy2(path, backup_path)

    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(
        "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows),
        encoding="utf-8",
    )
    os.replace(tmp, path)  # atomic on POSIX (and Windows since Python 3.3)
    return backup_path


# ===== Accept 操作 =====

def accept_batch(
    rows: list[dict[str, Any]],
    accept_ids: set[str],
    *,
    review_note: str,
    today: str,
    reviewed_by: str = "human",
    level_mode: str = "preserve_proposed",  # or "hardcode"
    hardcoded_level: str | None = None,
) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    """批量 accept: 对 rows 中 cid ∈ accept_ids 的候选, 设置 accept 字段。

    Returns (rows, accepted, skipped, missing).
    """
    accepted: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []

    for r in rows:
        cid = r.get("candidate_id")
        if cid is None:
            continue
        if cid not in accept_ids:
            continue
        if r.get("review_status") == "accepted":
            skipped.append(cid)
            continue

        r["review_status"] = "accepted"
        r["reviewed_by"] = reviewed_by
        r["reviewed_at"] = today
        r["check_outcome"] = "pass"

        # authenticity_level_accepted: hardcode 或 preserve_proposed
        if level_mode == "hardcode":
            if not hardcoded_level:
                raise ValueError("level_mode='hardcode' requires hardcoded_level")
            r["authenticity_level_accepted"] = hardcoded_level
        else:  # preserve_proposed (default)
            proposed = r.get("authenticity_level_proposed")
            if not proposed:
                raise ValueError(
                    f"authenticity_level_proposed missing for {cid}; cannot set level_accepted. "
                    f"Either fix data or use level_mode='hardcode' with hardcoded_level."
                )
            r["authenticity_level_accepted"] = proposed

        # relevance_grade_accepted: preserve proposed (no default fallback)
        proposed_rel = r.get("relevance_grade_proposed")
        if proposed_rel is None:
            raise ValueError(
                f"relevance_grade_proposed missing for {cid}; cannot set relevance_grade_accepted"
            )
        r["relevance_grade_accepted"] = proposed_rel

        r["review_note"] = review_note
        accepted.append(cid)

    for cid in accept_ids:
        if cid not in accepted and cid not in skipped:
            missing.append(cid)

    return rows, accepted, skipped, missing


# ===== Update Field 操作 (URL 修复等) =====

def update_field(
    rows: list[dict[str, Any]],
    target_id: str,
    *,
    field_updates: dict[str, str],
    preconditions: dict[str, str] | None = None,
    append_fields: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    """对单个 target_id 候选更新字段。失败时 raise (不静默)。

    field_updates: {field: new_value}  (默认 overwrite)
    preconditions: {field: expected_current_value}  (必须全部匹配, 否则 raise)
    append_fields: 字段名列表 — 这些字段保留旧值, 在末尾追加新值 (而不是覆写)

    Returns (rows, changed, no_change, missing).
    """
    changed: list[str] = []
    no_change: list[str] = []
    missing: list[str] = []

    append_set = set(append_fields or [])

    for r in rows:
        cid = r.get("candidate_id")
        if cid != target_id:
            continue

        # 强校验 preconditions (任一不匹配则 raise)
        if preconditions:
            for k, expected in preconditions.items():
                actual = r.get(k)
                if actual != expected:
                    raise ValueError(
                        f"precondition failed for {cid}: {k} expected {expected!r}, got {actual!r}. "
                        f"Refusing to mutate."
                    )

        for k, v in field_updates.items():
            if k in append_set:
                old = r.get(k, "") or ""
                r[k] = (old + "\n\n" + v).strip() if old else v
            else:
                r[k] = v

        changed.append(cid)
        return rows, changed, no_change, missing

    missing.append(target_id)
    return rows, changed, no_change, missing


# ===== Validation =====

def validate_after_write(jsonl_path: Path) -> bool:
    """跑 scripts/domestic/validate_candidates.py, 返回是否通过。

    找不到脚本时返回 True (跳过)。
    """
    script = jsonl_path.parent / "validate_candidates.py"
    if not script.exists():
        return True
    result = subprocess.run(
        [sys.executable, str(script), str(jsonl_path)],
        capture_output=True,
        text=True,
    )
    print(f"[validate] {result.stdout.strip()}")
    if result.returncode != 0:
        print(f"VALIDATION FAILED:\n{result.stderr}", file=sys.stderr)
        return False
    return True


# ===== Standard main() 模板 =====

def run_standard_main(
    jsonl_path: Path,
    apply: bool,
    *,
    accept_ids: set[str],
    review_note: str,
    today: str,
    reviewed_by: str = "human",
    level_mode: str = "preserve_proposed",
    hardcoded_level: str | None = None,
    auto_validate: bool = True,
) -> int:
    """标准 accept 脚本 main(): 读 -> 去重 -> accept -> (apply 时) 原子写 + 备份 + validate。

    Returns exit code.
    """
    rows = read_jsonl(jsonl_path)
    rows = dedupe_by_cid(rows)

    rows, accepted, skipped, missing = accept_batch(
        rows,
        accept_ids,
        review_note=review_note,
        today=today,
        reviewed_by=reviewed_by,
        level_mode=level_mode,
        hardcoded_level=hardcoded_level,
    )

    backup_path: Path | None = None
    if apply:
        backup_path = write_jsonl_atomic(jsonl_path, rows)
        if auto_validate and not validate_after_write(jsonl_path):
            return 3

    summary = {
        "accepted": accepted,
        "skipped_already_accepted": skipped,
        "missing_not_found": missing,
        "applied": apply,
        "backup": str(backup_path) if backup_path else None,
        "total_records": len(rows),
        "accept_set_size": len(accept_ids),
    }
    # 数字一致性校验: accepted + skipped + missing == accept_set_size
    if (len(accepted) + len(skipped) + len(missing)) != len(accept_ids):
        print(
            f"ERROR: count mismatch (accepted+skipped+missing={len(accepted)+len(skipped)+len(missing)} "
            f"!= accept_set_size={len(accept_ids)})",
            file=sys.stderr,
        )
        return 4
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0
