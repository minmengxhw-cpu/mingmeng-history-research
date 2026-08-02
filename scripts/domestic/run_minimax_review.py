#!/usr/bin/env python3
"""Run MiniMax CLI on a prepared messages file and persist the raw response locally."""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--messages-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="MiniMax-M3")
    parser.add_argument("--max-tokens", type=int, default=4000)
    args = parser.parse_args()
    result = subprocess.run(
        [
            "mmx", "text", "chat",
            "--model", args.model,
            "--messages-file", str(args.messages_file),
            "--max-tokens", str(args.max_tokens),
            "--output", "json",
            "--non-interactive", "--quiet",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    output_path = args.output if args.output.is_absolute() else Path.cwd() / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        f"# MiniMax 复核建议\n\n生成时间：{datetime.now().isoformat(timespec='seconds')}\n\n"
        f"模型：`{args.model}`\n\n## 原始返回\n\n{result.stdout}\n",
        encoding="utf-8",
    )
    print(f"saved {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
