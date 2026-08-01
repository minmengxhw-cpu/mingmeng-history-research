"""smoke/snapshot 两个测试文件共用的小请求封装。

之所以单独抽出来:app.py 在数据库缺失时不会返回带状态码的响应,而是直接
断开连接(见 conftest.py 顶部说明)。requests 库对这种情况抛的是
`requests.exceptions.ConnectionError`,这里统一捕获成 `(None, None)`,
调用方只需要判断 status 是否为 None,不用每处都写 try/except。
"""
from __future__ import annotations

import requests


def fetch(base_url: str, path: str, timeout: float = 10.0) -> tuple[int | None, str | None]:
    """返回 (status_code, body)。请求本身失败(连接被重置等)时返回 (None, None)。"""
    try:
        resp = requests.get(f"{base_url}{path}", timeout=timeout)
    except requests.exceptions.RequestException:
        return None, None
    return resp.status_code, resp.text
