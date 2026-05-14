#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
OUT_PATH = EXPORTS / "event_cards_index.md"


def title_from_file(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line.removeprefix("# ").strip()
    except UnicodeDecodeError:
        return path.stem
    return path.stem


def main() -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    files = sorted(
        [path for path in EXPORTS.glob("event_cards_*.md") if path.name != OUT_PATH.name],
        key=lambda path: (path.name.count("_"), path.name),
    )
    lines = [
        "# 事件研究卡片导出目录",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 文件数量：{len(files)}",
        "",
    ]
    groups = [
        ("人物", "event_cards_person_"),
        ("专题", "event_cards_topic_"),
        ("地点", "event_cards_place_"),
        ("机构", "event_cards_organization_"),
    ]
    listed: set[Path] = set()
    for label, prefix in groups:
        group = [path for path in files if path.name.startswith(prefix)]
        if not group:
            continue
        lines.extend([f"## {label}", ""])
        for path in group:
            listed.add(path)
            title = title_from_file(path)
            size_kb = max(1, path.stat().st_size // 1024)
            lines.append(f"- [{title}]({path.name}) · `{path.name}` · {size_kb} KB")
        lines.append("")
    remaining = [path for path in files if path not in listed]
    if remaining:
        lines.extend(["## 其他", ""])
        for path in remaining:
            title = title_from_file(path)
            size_kb = max(1, path.stat().st_size // 1024)
            lines.append(f"- [{title}]({path.name}) · `{path.name}` · {size_kb} KB")
        lines.append("")
    OUT_PATH.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(files)} files)")


if __name__ == "__main__":
    main()
