#!/usr/bin/env python3
"""Low-cost, event-driven supervisor for the domestic multi-agent task.

Normal operation is model-free. A small Codex handoff is invoked only when a
new checkpoint/terminal event/worker exit/formal SHA change is observed.
The supervisor never writes the formal SQLite and never deletes files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "work/domestic/MULTI_AGENT_SUPERLONG_TASK_20260801/00_CONTROL"
STATUS_PATH = CONTROL / "STATUS.json"
SUPERVISOR_PATH = CONTROL / "SUPERVISOR_STATUS.json"
EVENTS_PATH = CONTROL / "SUPERVISOR_EVENTS.jsonl"
LOG_PATH = CONTROL / "LOW_COST_SUPERVISOR.log"
PROMPT_PATH = CONTROL / "LOW_COST_SUPERVISOR_PROMPT.md"
FORMAL_DB = ROOT / "data/research_index.sqlite"
EXPECTED_FORMAL_SHA = "e4417bd1dfce77772832e0fcee17f5fb33bbd0fc9d1e6b2618932a64e9c8c0a5"
TASK_ROOT = CONTROL.parent


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def screen_sessions() -> list[str]:
    result = subprocess.run(
        ["screen", "-ls"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    names = []
    for line in result.stdout.splitlines():
        token = line.strip().split()[0] if line.strip() else ""
        if "." in token and token.split(".", 1)[1]:
            names.append(token.split(".", 1)[1])
    return sorted(set(names))


def markers() -> list[str]:
    result = []
    for path in TASK_ROOT.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.upper()
        if any(word in name for word in ("CHECKPOINT", "COMPLETE", "FINAL_REPORT", "STATUS")):
            result.append(str(path.relative_to(ROOT)))
    return sorted(result)


def snapshot() -> dict:
    status = read_json(STATUS_PATH)
    sessions = screen_sessions()
    return {
        "observed_at": now(),
        "formal_db_sha256": sha256(FORMAL_DB),
        "task_state": status.get("state"),
        "cycle": status.get("cycle"),
        "last_progress_at": status.get("last_progress_at"),
        "last_checkpoint": status.get("last_checkpoint"),
        "workers": status.get("workers", {}),
        "gates": status.get("gates", {}),
        "screens": sessions,
        "task_markers": markers(),
    }


def stable_view(value: dict) -> dict:
    copy = json.loads(json.dumps(value, ensure_ascii=False))
    copy.pop("observed_at", None)
    return copy


def event_reasons(current: dict, previous: dict | None) -> list[str]:
    reasons = []
    if current["formal_db_sha256"] != EXPECTED_FORMAL_SHA:
        reasons.append("FORMAL_DB_SHA_CHANGED")
    if current.get("task_state") in {"COMPLETE", "BLOCKED", "PAUSED"}:
        reasons.append(f"TASK_STATE_{current.get('task_state')}")
    if previous:
        if current.get("task_state") != previous.get("task_state"):
            reasons.append("TASK_STATUS_CHANGED")
        if current.get("last_checkpoint") != previous.get("last_checkpoint"):
            reasons.append("NEW_CHECKPOINT")
        old_markers = set(previous.get("task_markers", []))
        new_markers = set(current.get("task_markers", [])) - old_markers
        if any("COMPLETE" in Path(path).name.upper() for path in new_markers):
            reasons.append("NEW_COMPLETE_MARKER")
        old_screens = set(previous.get("screens", []))
        exited = old_screens - set(current.get("screens", []))
        if any(name.startswith(("grok-", "minimax-")) for name in exited):
            reasons.append("WORKER_SCREEN_EXITED")
    return sorted(set(reasons))


def append_event(payload: dict) -> None:
    CONTROL.mkdir(parents=True, exist_ok=True)
    with EVENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def invoke_small_agent(reasons: list[str], current: dict) -> int:
    event = json.dumps({"reasons": reasons, "snapshot": current}, ensure_ascii=False, indent=2)
    prompt = PROMPT_PATH.read_text(encoding="utf-8") + f"\n\n## 事件\n```json\n{event}\n```\n"
    CONTROL.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"\n===== SMALL SUPERVISOR START {now()} reasons={reasons} =====\n")
        handle.flush()
        result = subprocess.run(
            [
                "/Users/cheer/.local/bin/codex", "-a", "never",
                "--disable", "plugins", "--disable", "apps",
                "--disable", "memories", "--disable", "computer_use",
                "--disable", "browser_use", "--disable", "image_generation",
                "--disable", "multi_agent", "--disable", "skill_search",
                "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
                "-c", 'model_reasoning_effort="none"', "-m", "gpt-5.4-mini",
                "-s", "workspace-write", "-C", str(ROOT), prompt,
            ],
            cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, check=False,
        )
        handle.write(f"===== SMALL SUPERVISOR END {now()} rc={result.returncode} =====\n")
    return result.returncode


def run_once(invoke: bool) -> dict:
    CONTROL.mkdir(parents=True, exist_ok=True)
    monitor = read_json(SUPERVISOR_PATH)
    previous = monitor.get("last_snapshot")
    current = snapshot()
    reasons = event_reasons(current, previous)
    event_key = hashlib.sha256(
        json.dumps({"reasons": reasons, "snapshot": stable_view(current)}, sort_keys=True).encode()
    ).hexdigest() if reasons else None
    handled = set(monitor.get("handled_event_keys", []))
    action = "NO_EVENT"
    if reasons and event_key not in handled:
        event = {"detected_at": now(), "event_key": event_key, "reasons": reasons, "snapshot": current}
        append_event(event)
        if invoke:
            rc = invoke_small_agent(reasons, current)
            event["small_agent_rc"] = rc
            action = f"SMALL_AGENT_RC_{rc}"
        else:
            action = "EVENT_RECORDED_NO_INVOKE"
        handled.add(event_key)
    payload = {
        "state": "RUNNING" if current["formal_db_sha256"] == EXPECTED_FORMAL_SHA else "BLOCKED_FORMAL_SHA_CHANGE",
        "updated_at": now(),
        "interval_seconds": monitor.get("interval_seconds", 300),
        "model_invocations": int(monitor.get("model_invocations", 0)) + (1 if action.startswith("SMALL_AGENT") else 0),
        "last_action": action,
        "last_reasons": reasons,
        "handled_event_keys": list(handled)[-100:],
        "last_snapshot": current,
    }
    SUPERVISOR_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"action": action, "reasons": reasons, "snapshot": current}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--no-invoke", action="store_true")
    parser.add_argument("--interval", type=int, default=600)
    args = parser.parse_args()
    existing = read_json(SUPERVISOR_PATH)
    existing["interval_seconds"] = args.interval
    if not existing.get("last_snapshot"):
        # Seed without spending a model call on startup.
        first = snapshot()
        existing["last_snapshot"] = first
        existing["state"] = "RUNNING"
        existing["updated_at"] = now()
        existing.setdefault("handled_event_keys", [])
        existing.setdefault("model_invocations", 0)
    SUPERVISOR_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    while True:
        result = run_once(invoke=not args.no_invoke)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if args.once:
            return 0
        time.sleep(max(60, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
