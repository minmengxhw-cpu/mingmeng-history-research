#!/usr/bin/env python3
"""测试专用启动器 —— 不修改 app.py 任何一行。

背景:app.py 的 main() 把端口硬编码成 127.0.0.1:8765(见 app.py 末尾
`ReusableThreadingHTTPServer(("127.0.0.1", 8765), Handler)`),测试用固定端口在
CI/共享开发机上有真实的端口冲突风险(本机实测: 8765 当前就被另一个不相关的
python3 进程占用)。工单要求"随机端口",但又不许改 app.py 的行为。

解决方式:直接 `import app` 把它当模块用,复用它已经定义好的
ReusableThreadingHTTPServer / Handler 两个类自己起一个监听在随机端口(0)的
server,不调用 app.main()、不改 app.py 源码一个字节。DB_PATH 等模块级变量
保持 app.py 原样(不 monkeypatch),即:如果真的存在 data/research_index.sqlite
就用真库,不存在就是 app.py 原本就会遇到的"数据库缺失"场景,交给测试的
skip 逻辑去判断,不在这里伪造数据掩盖。

用法:作为子进程启动,stdout 第一行打印 `PORT=<端口号>` 后开始 serve_forever()。
调用方读到这一行即可拿到实际监听端口;测试结束后用 SIGTERM 结束进程。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as app_module  # noqa: E402


def main() -> None:
    server = app_module.ReusableThreadingHTTPServer(("127.0.0.1", 0), app_module.Handler)
    port = server.server_address[1]
    # 必须 flush,调用方靠这一行拿端口号;不flush在管道缓冲下可能读不到
    print(f"PORT={port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
