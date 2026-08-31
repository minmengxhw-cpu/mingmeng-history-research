#!/usr/bin/env python3
"""Verify that the Git-tracked tree is safe for public release.

This checker inspects tracked paths only.  It does not open an external
research database, parse source bodies, follow URLs, or modify the checkout.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


ALLOWED_PLACEHOLDER_FILES = {"data/.gitkeep"}
FORBIDDEN_PREFIXES = ("data/", "work/", ".tasks/", "workspace/")
FORBIDDEN_SUFFIXES = (".sqlite", ".db", ".pdf", ".docx", ".jpg", ".jpeg", ".png")
FORBIDDEN_TEXT_PATTERNS = (
    ("absolute_user_path", re.compile(r"/Users/cheer(?:/|$)")),
    ("private_temp_path", re.compile(r"/private/tmp/mingmeng(?:/|$)")),
    ("local_checkout_path", re.compile(r"Documents/mm agent")),
    ("private_key", re.compile(r"BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY")),
    ("github_token", re.compile(r"(?:ghp_|github_pat_)[A-Za-z0-9_]+")),
)


def tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def scan(root: Path) -> dict[str, object]:
    paths = tracked_paths(root)
    path_violations: list[dict[str, str]] = []
    binary_violations: list[dict[str, str]] = []
    text_violations: list[dict[str, str]] = []

    for relative in paths:
        if relative in ALLOWED_PLACEHOLDER_FILES:
            continue
        if relative.startswith(FORBIDDEN_PREFIXES):
            path_violations.append({"path": relative, "rule": "private_tree_prefix"})
        if relative.lower().endswith(FORBIDDEN_SUFFIXES):
            binary_violations.append({"path": relative, "rule": "research_binary_suffix"})

        file_path = root / relative
        if not file_path.is_file():
            continue
        raw = file_path.read_bytes()
        if b"\0" in raw:
            continue
        text = raw.decode("utf-8", errors="ignore")
        for rule, pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(text):
                text_violations.append({"path": relative, "rule": rule})

    violations = path_violations + binary_violations + text_violations
    return {
        "schema_version": "public_release_boundary.v1",
        "status": "PASS" if not violations else "FAIL",
        "tracked_file_count": len(paths),
        "path_violations": path_violations,
        "binary_violations": binary_violations,
        "text_violations": text_violations,
        "violation_count": len(violations),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    report = scan(args.root.expanduser().resolve())
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
