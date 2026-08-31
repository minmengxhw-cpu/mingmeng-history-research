"""T1 回归网的公共 fixture。

关键前提(2026-08-01 实测确认,写在这里避免以后有人忘了):
app.py 运行时连接的 `data/research_index.sqlite` 被 .gitignore 排除,不在
版本控制里,repo 里现有的 `scripts/build/build_research_index.py` 也只能
重建 FRUS 一个平台的三张表(sources/documents/pages),缺 domestic_candidates
等后续新增的表。也就是说:**在一台全新 clone 的机器上(包括这次 CI),
这个数据库文件根本不存在**。

2026-08-02 对抗性审查修复:app.py 的 do_GET/do_POST 之前没有顶层异常兜底,
数据库缺表时 sqlite3.OperationalError 会一直往上抛,http.server 的默认异常
处理不会返回任何 HTTP 响应,而是直接把连接断开(客户端拿到的是连接错误,不是
带 500 状态码的响应体)。现在 do_GET/do_POST 已经加了 try/except,任何路由
处理函数抛出的未预期异常都会被统一转成一个干净的 500 页面(不回传服务端
traceback),所以**数据库缺失现在表现为 500,而不是连接被重置**。

所以这份测试网的策略是:
  1. 能拿到 200 响应 → 按响应内容正常断言(特征字符串 / 无 Traceback)。
  2. 拿到 500 且确认是 research_index.sqlite 缺失/缺表导致的
     → skip 真实内容校验,只确认 500 页面本身干净(不泄露 traceback),
     不算测试失败。
  3. 拿到非 200/500 的响应,或 500 但排除了"数据库缺失"这个已知原因
     → 视为真失败,不允许吞掉。
"""
from __future__ import annotations

import socket
import subprocess
import sys
import sqlite3
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "research_index.sqlite"

# app.py 里各页面实际会触碰到、且当前没有 try/except 保护的表,任何一张缺失
# 都足以解释"连接被重置"这个现象。清单来自对 app.py 全文 grep 校验,不是猜的。
CORE_TABLES = {"documents", "pages", "translations"}

# 公开代码仓库不携带研究 corpus。以下模块验证的是挂载数据后的真实
# 国内研究层；在 data/research_index.sqlite 不存在时，必须明确 skip，
# 不能把“未挂载”误报为代码失败。带数据运行 CI 时不触发这些 skip。
CORPUS_DEPENDENT_MODULES = frozenset(
    {
        "test_academic_crosswalk_snapshot.py",
        "test_academic_metadata_fallback.py",
        "test_authorized_original_intake.py",
        "test_domestic_foreign_parity_acceptance.py",
        "test_primary_subtarget_support.py",
        "test_public_domestic_boundary.py",
        "test_research_topics.py",
        "test_research_topics_issue8_11.py",
        "test_sibling_collection_intake.py",
        "test_source_admission.py",
        "test_source_admission_queue.py",
        "test_unified_research_platform_gate.py",
    }
)


def _db_missing_reason() -> str | None:
    """返回“数据库缺失/缺核心表”的原因说明;数据库健全则返回 None。"""
    if not DB_PATH.exists():
        return f"{DB_PATH.relative_to(REPO_ROOT)} 不存在(该路径在 .gitignore 中,repo 未提供可重建它的完整脚本)"
    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            existing = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")
            }
        finally:
            conn.close()
    except sqlite3.Error as exc:
        return f"{DB_PATH.relative_to(REPO_ROOT)} 无法打开: {exc}"
    missing = CORE_TABLES - existing
    if missing:
        return f"{DB_PATH.relative_to(REPO_ROOT)} 存在但缺表: {sorted(missing)}"
    return None


@pytest.fixture(scope="session")
def db_missing_reason() -> str | None:
    """None = 数据库健全;否则是可读的缺失原因,供测试 skip 时打印。"""
    return _db_missing_reason()


def pytest_collection_modifyitems(config, items):
    """Skip corpus assertions only when the external corpus is not mounted.

    The public checkout deliberately contains code and synthetic fixtures, not
    the private research database or metadata snapshots.  This keeps a clean
    clone's CI honest while preserving the full test suite for a data-mounted
    research checkout.
    """
    reason = _db_missing_reason()
    if not reason:
        return
    marker = pytest.mark.skip(reason=f"外部研究 corpus 未挂载：{reason}")
    for item in items:
        module_name = Path(str(item.fspath)).name
        if module_name in CORPUS_DEPENDENT_MODULES:
            item.add_marker(marker)


def _free_port_hint() -> int:
    """仅用于日志展示,真实端口以子进程打印的 PORT= 行为准。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server():
    """以子进程方式启动 app.py(通过 tests/_launch_server.py 复用其
    Handler/ReusableThreadingHTTPServer,监听随机端口),测完自动关掉。
    不会以任何方式修改 app.py 源码或其 DB_PATH。
    """
    launcher = REPO_ROOT / "tests" / "_launch_server.py"
    proc = subprocess.Popen(
        [sys.executable, str(launcher)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    port = None
    deadline = time.time() + 10
    try:
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if line.startswith("PORT="):
                port = int(line.removeprefix("PORT="))
                break
        if port is None:
            proc.terminate()
            raise RuntimeError("tests/_launch_server.py 没有在 10 秒内打印 PORT=,启动失败")
        yield f"http://127.0.0.1:{port}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
