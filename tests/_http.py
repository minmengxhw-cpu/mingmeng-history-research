"""测试用的标准库 HTTP 请求封装。"""
from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch(base_url: str, path: str, timeout: float = 15.0) -> tuple[int | None, str | None]:
    """返回 (状态码, UTF-8 响应体)，连接失败时返回 (None, None)。"""
    try:
        request = Request(f"{base_url}{path}", headers={"Connection": "close"})
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except (OSError, URLError):
        return None, None
