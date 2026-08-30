import subprocess
import sys
from pathlib import Path

EXPECTED = "agent/deepseek-domestic-audit-20260803"
BASE = Path(__file__).resolve().parents[2]


def guard():
    try:
        cur = subprocess.run(["git", "-C", str(BASE), "branch", "--show-current"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return
    if cur != EXPECTED:
        sys.exit(f"[guard] 当前分支 {cur!r} ≠ {EXPECTED!r}，拒绝执行，避免写到错误分支。")
