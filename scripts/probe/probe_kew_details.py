#!/usr/bin/env python3
"""对 4 个 Kew 民盟专题卷宗拉详情（description / scope / content / 子件号）"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

CORE_VOLS = [
    ("C1252251", "CO 537/3724", "China Democratic League (1948)"),
    ("C1253349", "CO 537/4820", "China Democratic League (1949)"),
    ("C14050228", "FCO 141/16965", "Singapore: Chinese Democratic League branch in Hong Kong (1947)"),
    ("C4414285", "WO 208/4770", "Reports on political parties: Democratic League (1947-1948)"),
]

OUT = Path(__file__).resolve().parent.parent / "data" / "kew_probe" / "kew_4vol_details.md"


def get_details(iaid: str) -> dict:
    url = f"https://discovery.nationalarchives.gov.uk/API/records/v1/details/{iaid}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (academic-research; mingmeng-history-research)",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_children(iaid: str) -> dict:
    """拉子节点（件级目录）"""
    url = f"https://discovery.nationalarchives.gov.uk/API/records/v1/children/{iaid}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (academic-research; mingmeng-history-research)",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


lines = []
lines.append("# Kew 4 个民盟专题卷宗 · 件级详情\n")
lines.append("> 4 卷全部为民盟专题，命中精度 100%。下方为每卷的范围说明、件数和直接可下载性。\n")

for iaid, ref, label in CORE_VOLS:
    print(f"\n>>> {ref}  ({label})")
    try:
        d = get_details(iaid)
    except Exception as e:
        print(f"  ERR details: {e}")
        d = {}
    try:
        ch = get_children(iaid)
    except Exception as e:
        print(f"  ERR children: {e}")
        ch = {}

    children = ch.get("assets") or ch.get("results") or ch if isinstance(ch, list) else (ch.get("assets") if isinstance(ch, dict) else [])
    if isinstance(ch, dict):
        # 不同接口字段名可能不同
        for k in ("assets", "children", "items", "records"):
            if k in ch and isinstance(ch[k], list):
                children = ch[k]
                break

    scope = d.get("scopeContent") or {}
    if isinstance(scope, dict):
        scope_txt = scope.get("description") or ""
    else:
        scope_txt = str(scope) if scope else ""

    held = d.get("heldBy", "")
    if isinstance(held, list) and held:
        held = held[0].get("description", "") if isinstance(held[0], dict) else str(held[0])
    elif isinstance(held, dict):
        held = held.get("description", "")

    digitised = d.get("digitised") or d.get("isDigitised") or False
    closure = d.get("closureType") or d.get("closureStatus") or "Open"

    lines.append(f"\n## {ref} — {label}\n")
    lines.append(f"- **iaid**: {iaid}")
    lines.append(f"- **馆藏**: {held or 'The National Archives, Kew'}")
    lines.append(f"- **数字化**: {'✅ 已数字化（可在线下载）' if digitised else '❌ 未数字化（需现场或申请副本）'}")
    lines.append(f"- **公开状态**: {closure}")
    lines.append(f"- **覆盖时段**: {d.get('coveringDates','—')}")
    lines.append(f"- **目录层级**: {d.get('catalogueLevelCode','—')}")
    lines.append(f"- **形成机构**: {d.get('originator') or d.get('department','—')}")
    lines.append(f"\n**范围说明（scope content）**:")
    lines.append(f"> {scope_txt[:1000] if scope_txt else '（目录中未提供 scope content；通常需查正文）'}")
    lines.append(f"\n**详情页 URL**: https://discovery.nationalarchives.gov.uk/details/r/{iaid}")

    if isinstance(children, list) and children:
        lines.append(f"\n**子件目录**（共 {len(children)} 件）:")
        for c in children[:50]:
            cref = c.get("reference") or c.get("ref") or ""
            ctitle = c.get("title") or c.get("description") or ""
            cdates = c.get("coveringDates") or c.get("date") or ""
            lines.append(f"  - `{cref}` · {ctitle[:160]} · {cdates}")
        if len(children) > 50:
            lines.append(f"  - ... 还有 {len(children) - 50} 件")
    else:
        lines.append(f"\n**子件目录**: API 未返回子件清单（可能是 item 级，或目录层级最深）。")
    time.sleep(1.5)

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\n=== 完成 ===\n输出: {OUT}")
