"""T1 快照测试 —— T2 拆分 app.py 时的护栏。

只对"当前环境下能拿到稳定 200 响应"的路由做快照:/sourcebooks 和 /domestic。
其余 4 条(首页、/dashboard、/timeline、文档详情页)在没有真实
data/research_index.sqlite 的环境下,2026-08-02 修复 do_GET/do_POST 顶层
异常兜底之前会直接断开连接(见 conftest.py 顶部说明),拿不到任何响应体;
修复之后会返回干净的 500 页面,但依然不是真实内容,没有东西可以做有意义的
快照,所以一并 skip,只确认返回的是预期的 500(而不是断连、也不是意外的 200)。

**这意味着当前这份快照覆盖面是不完整的**——T2 拆分 app.py 时,这四条路由
的重构没有回归网保护。这一点已经写进 T1 报告,需要用户决定要不要先补一个
真实/测试用的 research_index.sqlite 再进 T2。

规范化规则:只替换 asset_version() 产生的 `?v=<mtime整数>` 查询参数(它是
文件 mtime,每次 checkout 都会变,和页面内容本身无关);不做其它模糊匹配,
避免把真实内容变化也悄悄掩盖掉。
"""
from __future__ import annotations

import re

import pytest

from tests._http import fetch

SNAPSHOT_DIR = __import__("pathlib").Path(__file__).resolve().parent / "snapshots"

_ASSET_VERSION_RE = re.compile(r"(/static/(?:style|fonts)\.css\?v=)\d+")


def _normalize(html: str) -> str:
    return _ASSET_VERSION_RE.sub(r"\1NORMALIZED", html)


def _assert_snapshot(name: str, html: str) -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_path = SNAPSHOT_DIR / f"{name}.html"
    normalized = _normalize(html)
    if not snap_path.exists():
        snap_path.write_text(normalized, encoding="utf-8")
        pytest.skip(f"{name} 快照此前不存在,已首次生成基线({snap_path}),本次不做比较")
    baseline = snap_path.read_text(encoding="utf-8")
    assert normalized == baseline, (
        f"{name} 的渲染结果与已提交的快照基线不一致 —— "
        f"如果这是 T2 拆分导致的,必须先排查是不是拆错了;"
        f"如果是本来就打算改的行为,需要另开工单说明再更新快照。"
    )


def test_sourcebooks_snapshot(live_server):
    status, body = fetch(live_server, "/sourcebooks")
    assert status == 200
    _assert_snapshot("sourcebooks", body)


def test_domestic_snapshot(live_server):
    status, body = fetch(live_server, "/domestic")
    assert status == 200
    _assert_snapshot("domestic", body)


@pytest.mark.parametrize(
    "name,path",
    [
        ("home", "/"),
        ("dashboard", "/dashboard"),
        ("timeline", "/timeline"),
    ],
)
def test_db_dependent_snapshot_skipped(live_server, db_missing_reason, name, path):
    """首页/dashboard/timeline 目前必然因数据库缺失而拿不到真实内容,记录 skip 原因,
    不假装它们已经被快照覆盖。数据库补上之后,把这个测试换成真正的 _assert_snapshot。
    """
    status, body = fetch(live_server, path)
    if db_missing_reason:
        assert status == 500, (
            f"{path} 预期数据库缺失时返回 500 兜底页,实际是 {status} —— "
            "说明数据库状态或 do_GET 异常处理发生了变化,需要人工排查。"
        )
        assert body is not None and "Traceback" not in body
        pytest.skip(f"{path} 因数据库缺失只拿到 500 兜底页,当前无法生成真实内容的快照基线: {db_missing_reason}")
    pytest.fail(
        f"{path} 数据库已健全但仍走了这条 skip 分支(状态 {status})—— "
        "说明数据库状态发生了变化,请把这条测试换成真正的 _assert_snapshot 逻辑。"
    )
