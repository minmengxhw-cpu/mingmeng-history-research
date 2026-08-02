"""smoke/snapshot 两个测试文件共用的小请求封装。

之所以单独抽出来:早期 app.py 在数据库缺失时不会返回带状态码的响应,而是
直接断开连接(见 conftest.py 顶部说明)。2026-08-02 修复 do_GET/do_POST
顶层异常兜底后,这种场景已经变成正常的 500 响应,但保留这层 (None, None)
兜底——万一未来又出现真正的连接级异常(超时/服务没起来),调用方仍然不用
每处都写 try/except,只判断 status 是否为 None 即可。
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
