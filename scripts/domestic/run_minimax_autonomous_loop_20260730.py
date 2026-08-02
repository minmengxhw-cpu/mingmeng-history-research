#!/usr/bin/env python3
"""Run bounded MiniMax autonomous cycles through the current CC Switch route.

The supervisor never edits the formal database.  It stops immediately if the
formal database SHA changes or if the agent reports forbidden promotion flags.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/domestic/minimax_autonomous_research_20260730"
CONTROL = WORK / "00_control"
STATE = CONTROL / "STATE.json"
SUPERVISOR_STATE = CONTROL / "SUPERVISOR_STATUS.json"
LOG = CONTROL / "MINIMAX_LOOP.log"
FORMAL_DB = ROOT / "data/research_index.sqlite"
TASK = ROOT / "work/domestic/MINIMAX_AUTONOMOUS_RESEARCH_START_PROMPT_20260730.md"
WRAPPER = ROOT / "scripts/domestic/exec_current_ccswitch_claude.py"
EXPECTED_FORMAL_SHA = "8458c82e3ecc46ad5658b4cc5220b11735b7fd5a9373304882719f2b90913f37"

MAX_WALL_SECONDS = 4 * 3600 + 50 * 60
MAX_ROUNDS = 24
MIN_REMAINING_TO_RESTART = 30 * 60
MAX_NO_PROGRESS_ROUNDS = 2


def now() -> str:
    return datetime.now().astimezone().isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_state() -> dict:
    if not STATE.is_file():
        return {}
    try:
        value = json.loads(STATE.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def progress_signature() -> tuple:
    files = [path for path in WORK.rglob("*") if path.is_file()]
    latest = max((path.stat().st_mtime_ns for path in files), default=0)
    total_bytes = sum(path.stat().st_size for path in files)
    state = read_state()
    return (
        len(files),
        latest,
        total_bytes,
        state.get("state"),
        state.get("cycle"),
        state.get("last_completed_task_id"),
        state.get("next_action"),
    )


def write_supervisor(status: str, **extra: object) -> None:
    CONTROL.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "updated_at": now(),
        "formal_db_sha256": sha256(FORMAL_DB),
        **extra,
    }
    SUPERVISOR_STATE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def forbidden_or_terminal(state: dict) -> str | None:
    current_sha = sha256(FORMAL_DB)
    if current_sha != EXPECTED_FORMAL_SHA:
        return "STOP_FORMAL_DB_SHA_CHANGED"
    if state.get("formal_db_touched") is True:
        return "STOP_AGENT_REPORTED_FORMAL_DB_TOUCHED"
    if int(state.get("citation_ready_created") or 0) != 0:
        return "STOP_CITATION_READY_CREATED"
    if int(state.get("human_verified_created") or 0) != 0:
        return "STOP_HUMAN_VERIFIED_CREATED"
    if state.get("state") in {
        "COMPLETE_WAITING_CODEX_ACCEPTANCE",
        "BLOCKED_GLOBAL",
        "PAUSED_USER",
        "PAUSED_5H_LIMIT",
    }:
        return f"STOP_STATE_{state['state']}"
    return None


def main() -> int:
    CONTROL.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    round_no = 0
    no_progress = 0
    previous = progress_signature()
    write_supervisor(
        "RUNNING",
        started_at=now(),
        max_wall_seconds=MAX_WALL_SECONDS,
        max_rounds=MAX_ROUNDS,
        no_progress_rounds=0,
    )

    while round_no < MAX_ROUNDS:
        elapsed = time.monotonic() - started
        remaining = MAX_WALL_SECONDS - elapsed
        if round_no > 0 and remaining < MIN_REMAINING_TO_RESTART:
            write_supervisor(
                "PAUSED_LOCAL_WALL_LIMIT",
                rounds=round_no,
                elapsed_seconds=round(elapsed, 1),
                remaining_seconds=round(remaining, 1),
            )
            return 0

        state_before = read_state()
        stop_reason = forbidden_or_terminal(state_before)
        if stop_reason:
            write_supervisor(
                stop_reason,
                rounds=round_no,
                agent_state=state_before,
            )
            return 0

        round_no += 1
        with LOG.open("a", encoding="utf-8") as handle:
            handle.write(f"\n===== ROUND {round_no} START {now()} =====\n")
            handle.flush()
            result = subprocess.run(
                [
                    "python3",
                    "-B",
                    str(WRAPPER),
                    str(TASK),
                ],
                cwd=ROOT,
                stdout=handle,
                stderr=subprocess.STDOUT,
                check=False,
            )
            handle.write(
                f"\n===== ROUND {round_no} END {now()} exit={result.returncode} =====\n"
            )

        state_after = read_state()
        stop_reason = forbidden_or_terminal(state_after)
        current = progress_signature()
        if current == previous:
            no_progress += 1
        else:
            no_progress = 0
        previous = current

        write_supervisor(
            "RUNNING" if not stop_reason else stop_reason,
            rounds=round_no,
            last_exit_code=result.returncode,
            no_progress_rounds=no_progress,
            elapsed_seconds=round(time.monotonic() - started, 1),
            agent_state=state_after,
        )

        if stop_reason:
            return 0
        if no_progress >= MAX_NO_PROGRESS_ROUNDS:
            write_supervisor(
                "STOP_NO_PROGRESS",
                rounds=round_no,
                no_progress_rounds=no_progress,
                agent_state=state_after,
            )
            return 2

    write_supervisor(
        "PAUSED_MAX_ROUNDS",
        rounds=round_no,
        elapsed_seconds=round(time.monotonic() - started, 1),
        agent_state=read_state(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
