#!/usr/bin/env python3
"""Download the missing public NLC 民憲 scans from the Commons category."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "domestic" / "press_scans"

ITEMS = [
    ("NLC404-00J001436-85443", "民憲_第一卷第二期", "民憲 1944–1945年第一卷第二期.pdf"),
    ("NLC404-00J001436-85444", "民憲_第一卷第三期", "民憲 1944–1945年第一卷第三期.pdf"),
    ("NLC404-00J001436-85445", "民憲_第一卷第四期", "民憲 1944–1945年第一卷第四期.pdf"),
    ("NLC404-00J001436-85446", "民憲_第一卷第五期", "民憲 1944–1945年第一卷第五期.pdf"),
    ("NLC404-00J001436-85448", "民憲_第一卷第七期", "民憲 1944–1945年第一卷第七期.pdf"),
    ("NLC404-00J001436-85449", "民憲_第一卷第八期", "民憲 1944–1945年第一卷第八期.pdf"),
    ("NLC404-00J001436-85452", "民憲_第一卷第十一期", "民憲 1944–1945年第一卷第十一期.pdf"),
    ("NLC404-00J001436-85453", "民憲_第一卷第十二期", "民憲 1944–1945年第一卷第十二期.pdf"),
    ("NLC404-00J001436-85454", "民憲_第二卷第一期", "民憲 1944–1945年第二卷第一期.pdf"),
    ("NLC404-00J001436-85455", "民憲_第二卷第二期", "民憲 1944–1945年第二卷第二期.pdf"),
    ("NLC404-00J001436-85456", "民憲_第二卷第三期", "民憲 1944–1945年第二卷第三期.pdf"),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for ident, label, remote_filename in ITEMS:
        path = OUT / f"{ident}_{label}.pdf"
        if path.exists() and path.stat().st_size > 100_000:
            data = path.read_bytes()
            results.append({"id": ident, "path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": sha256(data), "status": "existing"})
            continue
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(f"{ident} {remote_filename}")
        request = urllib.request.Request(url, headers={"User-Agent": "mingmeng-history-research/1.0 (local archival research)"})
        last_error = ""
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    data = response.read()
                path.write_bytes(data)
                results.append({"id": ident, "path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": sha256(data), "status": "downloaded"})
                break
            except urllib.error.HTTPError as exc:
                last_error = f"HTTP {exc.code}"
                if attempt == 3:
                    results.append({"id": ident, "path": str(path.relative_to(ROOT)), "status": "failed", "error": last_error})
                else:
                    time.sleep(10 * (attempt + 1))
            except Exception as exc:  # network state can vary between public mirrors
                last_error = type(exc).__name__
                if attempt == 3:
                    results.append({"id": ident, "path": str(path.relative_to(ROOT)), "status": "failed", "error": last_error})
                else:
                    time.sleep(10 * (attempt + 1))
        time.sleep(3)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
