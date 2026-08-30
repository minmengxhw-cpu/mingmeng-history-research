#!/usr/bin/env python3
"""Exec Claude with the current CC Switch provider env without printing secrets."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: exec_current_ccswitch_claude.py TASK.md")

    task = Path(sys.argv[1]).resolve()
    db = Path.home() / ".cc-switch/cc-switch.db"
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            """
            SELECT name, settings_config
            FROM providers
            WHERE app_type = 'claude' AND is_current = 1
            LIMIT 1
            """
        ).fetchone()
    if not row:
        raise SystemExit("no current CC Switch Claude provider")

    provider_name, raw_config = row
    if provider_name != "MiniMax":
        raise SystemExit(f"current CC Switch provider is {provider_name!r}, expected 'MiniMax'")

    config = json.loads(raw_config)
    provider_env = config.get("env", {})
    required = {"ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN"}
    missing = sorted(key for key in required if not provider_env.get(key))
    if missing:
        raise SystemExit(f"current MiniMax provider missing required env keys: {missing}")

    env = os.environ.copy()
    env.update({str(key): str(value) for key, value in provider_env.items()})
    prompt = task.read_text(encoding="utf-8")
    argv = [
        "/opt/homebrew/bin/claude",
        "--permission-mode",
        "bypassPermissions",
        "--effort",
        "high",
        "--name",
        task.stem.lower()[:64],
        "-p",
        prompt,
    ]
    os.execvpe(argv[0], argv, env)


if __name__ == "__main__":
    main()
