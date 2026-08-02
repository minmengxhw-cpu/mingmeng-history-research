#!/usr/bin/env python3
"""在随机端口启动现有 app Handler，供测试进程使用。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as app_module  # noqa: E402


def main() -> None:
    server = app_module.ReusableThreadingHTTPServer(
        ("127.0.0.1", 0), app_module.Handler
    )
    print(f"PORT={server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
