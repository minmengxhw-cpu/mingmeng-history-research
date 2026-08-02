#!/usr/bin/env python3
"""Low-cost event watcher for the MiniMax/Grok domestic-research loop.

Normal polling is local and model-free.  A small Codex agent is invoked only
for a terminal/safety event or a newly observed COMPLETE marker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "work/domestic/loop_supervisor_20260730"
STATE_PATH = CONTROL / "STATE.json"
EVENTS_PATH = CONTROL / "EVENTS.jsonl"
AGENT_LOG = CONTROL / "SMALL_AGENT.log"
ACTION_PATH = CONTROL / "ACTION.json"
DISPATCH_LOG = CONTROL / "DISPATCH.log"
PROMPT_PATH = ROOT / "work/domestic/LOOP_SUPERVISOR_SMALL_AGENT_PROMPT_20260730.md"
FORMAL_DB = ROOT / "data/research_index.sqlite"
EXPECTED_FORMAL_SHA = "e4257587a8c32695399c3660d499504c8ccbcd7568ac9170b60553f51ddb7159"

MINIMAX_CONTROL = (
    ROOT / "work/domestic/minimax_autonomous_research_20260730/00_control"
)
GROK_CONTROL = ROOT / "work/domestic/grok_next_stage_20260730/00_control"

TERMINAL_STATES = {
    "COMPLETE",
    "COMPLETE_WAITING_CODEX_ACCEPTANCE",
    "BLOCKED_GLOBAL",
    "PAUSED_5H_LIMIT",
    "PAUSED_LOCAL_WALL_LIMIT",
    "PAUSED_MAX_ROUNDS",
    "STOP_NO_PROGRESS",
    "STOP_FORMAL_DB_SHA_CHANGED",
    "STOP_AGENT_REPORTED_FORMAL_DB_TOUCHED",
    "STOP_CITATION_READY_CREATED",
    "STOP_HUMAN_VERIFIED_CREATED",
}


def now() -> str:
    return datetime.now().astimezone().isoformat()


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


def repair_trailing_commas(path: Path) -> bool:
    """Repair only JSON punctuation emitted by a live control writer.

    This is deliberately limited to trailing commas before ``]``/``}`` and
    only runs for the MiniMax control metrics file.  It does not infer or
    rewrite research values; an unparseable file remains unparseable and is
    reported as such on the next snapshot.
    """
    if path != MINIMAX_CONTROL / "METRICS.json" or not path.exists():
        return False
    try:
        raw = path.read_text(encoding="utf-8")
        json.loads(raw)
        return False
    except (OSError, json.JSONDecodeError):
        pass
    try:
        cleaned = re.sub(r",(\s*[}\]])", r"\1", raw)
        json.loads(cleaned)
        tmp = path.with_name(path.name + ".repairing")
        tmp.write_text(cleaned, encoding="utf-8")
        tmp.replace(path)
        append_dispatch_log("REPAIRED_MINIMAX_METRICS_TRAILING_COMMA")
        return True
    except (OSError, json.JSONDecodeError, UnboundLocalError):
        return False


def screen_sessions() -> set[str]:
    result = subprocess.run(
        ["screen", "-ls"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    sessions: set[str] = set()
    for line in result.stdout.splitlines():
        if "\t" not in line or "." not in line:
            continue
        token = line.strip().split()[0]
        sessions.add(token.split(".", 1)[1])
    return sessions


def complete_markers(base: Path) -> list[str]:
    if not base.is_dir():
        return []
    values = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        upper = path.name.upper()
        if "COMPLETE" in upper or "CHECKPOINT" in upper:
            values.append(str(path.relative_to(ROOT)))
    return sorted(values)


def snapshot() -> dict:
    repair_trailing_commas(MINIMAX_CONTROL / "METRICS.json")
    sessions = screen_sessions()
    mini_state = read_json(MINIMAX_CONTROL / "STATE.json")
    mini_metrics = read_json(MINIMAX_CONTROL / "METRICS.json")
    mini_supervisor = read_json(MINIMAX_CONTROL / "SUPERVISOR_STATUS.json")
    grok_state = read_json(GROK_CONTROL / "STATE.json")
    grok_metrics = read_json(GROK_CONTROL / "METRICS.json")
    return {
        "observed_at": now(),
        "formal_db_sha256": sha256(FORMAL_DB),
        "screens": sorted(sessions),
        "minimax": {
            "screen_present": any(name.startswith("minimax-") for name in sessions),
            "screen_names": sorted(
                name for name in sessions if name.startswith("minimax-")
            ),
            "state": mini_state.get("state"),
            "active_task_id": mini_state.get("active_task_id"),
            "last_completed_task_id": mini_state.get("last_completed_task_id"),
            "supervisor_status": mini_supervisor.get("status"),
            "ocr_physical_pages": mini_metrics.get("ocr_physical_pages"),
            "dossiers": mini_metrics.get("dossiers"),
            "relations": mini_metrics.get("relations"),
            "citation_ready_created": mini_state.get("citation_ready_created"),
            "human_verified_created": mini_state.get("human_verified_created"),
            "markers": complete_markers(MINIMAX_CONTROL.parent),
        },
        "grok": {
            "screen_present": any(name.startswith("grok-") for name in sessions),
            "screen_names": sorted(
                name for name in sessions if name.startswith("grok-")
            ),
            "state": grok_state.get("state"),
            "phase": grok_state.get("phase"),
            "gates": grok_state.get("gates"),
            "progress": grok_metrics.get("progress"),
            "markers": complete_markers(GROK_CONTROL.parent),
        },
    }


def load_monitor_state() -> dict:
    value = read_json(STATE_PATH)
    value.setdefault("handled_event_fingerprints", [])
    value.setdefault("small_agent_invocations", 0)
    return value


def write_monitor_state(value: dict) -> None:
    CONTROL.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def event_reasons(current: dict, previous: dict | None) -> list[str]:
    reasons: list[str] = []
    if current["formal_db_sha256"] != EXPECTED_FORMAL_SHA:
        reasons.append("FORMAL_DB_SHA_CHANGED")

    mini = current["minimax"]
    if mini.get("citation_ready_created") not in (None, 0):
        reasons.append("MINIMAX_CITATION_READY_CREATED")
    if mini.get("human_verified_created") not in (None, 0):
        reasons.append("MINIMAX_HUMAN_VERIFIED_CREATED")
    if mini.get("state") in TERMINAL_STATES:
        reasons.append(f"MINIMAX_STATE_{mini.get('state')}")
    if mini.get("supervisor_status") in TERMINAL_STATES:
        reasons.append(f"MINIMAX_SUPERVISOR_{mini.get('supervisor_status')}")

    grok = current["grok"]
    grok_phase = str(grok.get("phase") or "")
    previous_grok = (previous or {}).get("grok", {})
    if (
        grok.get("state") in TERMINAL_STATES
        or grok_phase in TERMINAL_STATES
        or (not grok.get("screen_present") and grok_phase.endswith("_COMPLETE"))
    ) and (
        previous is None
        or previous_grok.get("screen_present")
        or previous_grok.get("phase") != grok_phase
    ):
        reasons.append(f"GROK_TERMINAL_{grok.get('state') or grok.get('phase')}")

    if previous:
        old_mini = previous.get("minimax", {})
        old_grok = previous.get("grok", {})
        if old_mini.get("screen_present") and not mini.get("screen_present"):
            reasons.append("MINIMAX_SCREEN_EXITED")
        if old_grok.get("screen_present") and not grok.get("screen_present"):
            reasons.append("GROK_SCREEN_EXITED")
        new_mini_markers = set(mini.get("markers", [])) - set(
            old_mini.get("markers", [])
        )
        new_grok_markers = set(grok.get("markers", [])) - set(
            old_grok.get("markers", [])
        )
        if any("COMPLETE" in Path(x).name.upper() for x in new_mini_markers):
            reasons.append("MINIMAX_NEW_COMPLETE_MARKER")
        if any("COMPLETE" in Path(x).name.upper() for x in new_grok_markers):
            reasons.append("GROK_NEW_COMPLETE_MARKER")
    return sorted(set(reasons))


def fingerprint(reasons: list[str], current: dict) -> str:
    material: dict = {
        "reasons": reasons,
        "formal_db_sha256": current["formal_db_sha256"],
    }
    if any(reason.startswith("MINIMAX_") for reason in reasons):
        material["minimax"] = {
            "screen": current["minimax"]["screen_present"],
            "screen_names": current["minimax"].get("screen_names"),
            "state": current["minimax"].get("state"),
            "supervisor": current["minimax"].get("supervisor_status"),
            "last_completed": current["minimax"].get("last_completed_task_id"),
            "markers": current["minimax"].get("markers"),
        }
    if any(reason.startswith("GROK_") for reason in reasons):
        material["grok"] = {
            "screen": current["grok"]["screen_present"],
            "screen_names": current["grok"].get("screen_names"),
            "state": current["grok"].get("state"),
            "phase": current["grok"].get("phase"),
            "markers": current["grok"].get("markers"),
        }
    raw = json.dumps(material, ensure_ascii=False, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def invoke_small_agent(reasons: list[str], current: dict) -> int:
    base_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    event = json.dumps(
        {"reasons": reasons, "snapshot": current},
        ensure_ascii=False,
        indent=2,
    )
    prompt = f"{base_prompt}\n\n## 本次触发事件\n\n```json\n{event}\n```\n"
    CONTROL.mkdir(parents=True, exist_ok=True)
    with AGENT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"\n===== SMALL AGENT START {now()} =====\n")
        handle.flush()
        result = subprocess.run(
            [
                "/Users/cheer/.local/bin/codex",
                "-a",
                "never",
                "--disable",
                "plugins",
                "--disable",
                "apps",
                "--disable",
                "memories",
                "--disable",
                "computer_use",
                "--disable",
                "browser_use",
                "--disable",
                "image_generation",
                "--disable",
                "multi_agent",
                "--disable",
                "skill_search",
                "exec",
                "--ignore-user-config",
                "--ignore-rules",
                "--ephemeral",
                "-c",
                'model_reasoning_effort="none"',
                "-m",
                "gpt-5.4-mini",
                "-s",
                "workspace-write",
                "-C",
                str(ROOT),
                prompt,
            ],
            cwd=ROOT,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
        handle.write(f"\n===== SMALL AGENT END {now()} rc={result.returncode} =====\n")
    return result.returncode


def append_dispatch_log(message: str) -> None:
    CONTROL.mkdir(parents=True, exist_ok=True)
    with DISPATCH_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{now()} {message}\n")


def dispatch_action() -> str:
    action = read_json(ACTION_PATH)
    if action.get("action") != "launch":
        return "NO_LAUNCH_ACTION"
    if action.get("dispatched_at"):
        return "ACTION_ALREADY_DISPATCHED"

    provider = action.get("provider")
    task_raw = action.get("task_path")
    session_name = action.get("session_name")
    if provider not in {"grok", "minimax"}:
        return "REJECT_BAD_PROVIDER"
    if not isinstance(task_raw, str) or not isinstance(session_name, str):
        return "REJECT_BAD_ACTION_FIELDS"
    if not re.fullmatch(r"[A-Za-z0-9._-]{8,80}", session_name):
        return "REJECT_BAD_SESSION_NAME"
    if provider == "grok" and not session_name.startswith("grok-"):
        return "REJECT_BAD_GROK_SESSION_NAME"
    if provider == "minimax" and not session_name.startswith("minimax-"):
        return "REJECT_BAD_MINIMAX_SESSION_NAME"

    task_path = (ROOT / task_raw).resolve()
    allowed_root = (CONTROL / "next_tasks").resolve()
    if allowed_root not in task_path.parents or not task_path.is_file():
        return "REJECT_TASK_PATH_OUTSIDE_NEXT_TASKS"

    sessions = screen_sessions()
    if provider == "grok" and any(name.startswith("grok-") for name in sessions):
        return "DEFER_GROK_ALREADY_RUNNING"
    if provider == "minimax" and any(
        name.startswith("minimax-") for name in sessions
    ):
        return "DEFER_MINIMAX_ALREADY_RUNNING"

    if provider == "grok":
        probe = subprocess.run(
            [
                "/Users/cheer/.local/bin/grok",
                "--cwd",
                str(ROOT),
                "--model",
                "grok-4.5",
                "--single",
                "只回复 GROK_LOOP_OK，不调用工具。",
                "--output-format",
                "plain",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=120,
        )
        if probe.returncode != 0 or "GROK_LOOP_OK" not in probe.stdout:
            append_dispatch_log(
                f"GROK_PROBE_FAILED rc={probe.returncode} output={probe.stdout[-1000:]!r}"
            )
            return "BLOCKED_GROK_PROBE"
        command = [
            "screen",
            "-dmS",
            session_name,
            "/Users/cheer/.local/bin/grok",
            "--cwd",
            str(ROOT),
            "--model",
            "grok-4.5",
            "--prompt-file",
            str(task_path),
            "--permission-mode",
            "bypassPermissions",
            "--max-turns",
            "300",
            "--no-alt-screen",
        ]
    else:
        current_state = read_json(MINIMAX_CONTROL / "STATE.json")
        supervisor_state = read_json(MINIMAX_CONTROL / "SUPERVISOR_STATUS.json")
        if (
            current_state.get("state") == "PAUSED_5H_LIMIT"
            or supervisor_state.get("status") == "PAUSED_5H_LIMIT"
        ):
            return "DEFER_MINIMAX_5H_LIMIT"
        command = [
            "screen",
            "-dmS",
            session_name,
            "/usr/bin/python3",
            "-B",
            str(ROOT / "scripts/domestic/exec_current_ccswitch_claude.py"),
            str(task_path),
        ]

    launched = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if launched.returncode != 0:
        append_dispatch_log(
            f"LAUNCH_FAILED provider={provider} rc={launched.returncode} "
            f"output={launched.stdout[-1000:]!r}"
        )
        return f"BLOCKED_{provider.upper()}_LAUNCH"

    time.sleep(3)
    if session_name not in screen_sessions():
        append_dispatch_log(f"SESSION_EXITED_EARLY provider={provider} name={session_name}")
        return f"BLOCKED_{provider.upper()}_EARLY_EXIT"

    action["dispatched_at"] = now()
    action["dispatch_status"] = "RUNNING_CONFIRMED"
    ACTION_PATH.write_text(
        json.dumps(action, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    append_dispatch_log(f"LAUNCHED provider={provider} name={session_name}")
    return f"LAUNCHED_{provider.upper()}"


def run_once(invoke: bool) -> dict:
    monitor = load_monitor_state()
    previous = monitor.get("last_snapshot")
    current = snapshot()
    reasons = event_reasons(current, previous)
    fp = fingerprint(reasons, current) if reasons else None
    handled = set(monitor.get("handled_event_fingerprints", []))
    action = "NO_EVENT"

    if reasons and fp not in handled:
        event = {
            "detected_at": now(),
            "fingerprint": fp,
            "reasons": reasons,
            "snapshot": current,
        }
        CONTROL.mkdir(parents=True, exist_ok=True)
        with EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        if invoke:
            rc = invoke_small_agent(reasons, current)
            event["small_agent_rc"] = rc
            monitor["small_agent_invocations"] = (
                int(monitor.get("small_agent_invocations", 0)) + 1
            )
            if rc == 0:
                action = dispatch_action()
            else:
                action = f"SMALL_AGENT_RC_{rc}"
        else:
            action = "EVENT_RECORDED_DRY_RUN"
        handled.add(fp)

    monitor["updated_at"] = now()
    monitor["last_snapshot"] = current
    monitor["last_action"] = action
    monitor["handled_event_fingerprints"] = list(handled)[-100:]
    write_monitor_state(monitor)
    return {"action": action, "reasons": reasons, "snapshot": current}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    args = parser.parse_args()

    while True:
        result = run_once(invoke=not args.dry_run)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if args.once:
            return 0
        time.sleep(max(args.interval, 30))


if __name__ == "__main__":
    raise SystemExit(main())
