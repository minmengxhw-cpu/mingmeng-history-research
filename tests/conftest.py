"""T1 回归网公共 fixture。

核心 SQLite 文件和国内 staging SQLite 都是本地研究状态，不进 git。测试在
本地有真实数据库时验证完整页面和快照；在全新 CI clone 中则明确 skip 数据库
依赖项，并把缺失原因显示出来，不把缺失数据伪装成通过。
"""
from __future__ import annotations

import selectors
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "research_index.sqlite"
STAGING_DB_PATH = REPO_ROOT / "work" / "domestic" / "staging_20260730" / "domestic_staging.sqlite"
CORE_TABLES = {"documents", "pages", "translations", "research_events"}


def _missing_reason(path: Path, tables: set[str]) -> str | None:
    if not path.exists():
        return f"{path.relative_to(REPO_ROOT)} 不存在（本地研究数据库不进 git）"
    try:
        with sqlite3.connect(path) as conn:
            existing = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
                )
            }
    except sqlite3.Error as exc:
        return f"{path.relative_to(REPO_ROOT)} 无法打开：{exc}"
    missing = tables - existing
    if missing:
        return f"{path.relative_to(REPO_ROOT)} 缺表：{sorted(missing)}"
    return None


def _db_reason() -> str | None:
    return _missing_reason(DB_PATH, CORE_TABLES)


def _staging_reason() -> str | None:
    return _missing_reason(STAGING_DB_PATH, set())


@pytest.fixture(scope="session")
def db_missing_reason() -> str | None:
    return _db_reason()


@pytest.fixture(scope="session")
def staging_missing_reason() -> str | None:
    return _staging_reason()


@pytest.fixture(scope="session")
def document_key(db_missing_reason: str | None) -> str:
    if db_missing_reason:
        pytest.skip(f"无法取得真实文档键：{db_missing_reason}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT doc_key FROM documents ORDER BY doc_key LIMIT 1"
            ).fetchone()
    except sqlite3.Error as exc:
        pytest.skip(f"读取 documents 失败：{exc}")
    if not row:
        pytest.skip("documents 表为空，无法验证文档详情页")
    return str(row[0])


@pytest.fixture(scope="session")
def live_server():
    """复用 app.py 的 Handler，在随机端口启动隔离测试服务。"""
    launcher = REPO_ROOT / "tests" / "_launch_server.py"
    proc = subprocess.Popen(
        [sys.executable, str(launcher)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    port: int | None = None
    selector = selectors.DefaultSelector()
    assert proc.stdout is not None
    selector.register(proc.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + 15
    try:
        while time.monotonic() < deadline:
            events = selector.select(max(0.1, deadline - time.monotonic()))
            if not events:
                break
            line = proc.stdout.readline().strip()
            if line.startswith("PORT="):
                port = int(line.removeprefix("PORT="))
                break
        if port is None:
            output = ""
            if proc.poll() is not None:
                output = proc.stdout.read(2000)
            raise RuntimeError(f"测试服务未在 15 秒内启动：{output}")
        yield f"http://127.0.0.1:{port}"
    finally:
        selector.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
