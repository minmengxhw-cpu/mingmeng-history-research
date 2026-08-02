# P1 国内资料库网页入口验证

> 截至 2026-08-02 21:47，对照 `MINIMAX_NEXT_STAGE_MASTER_TASK_20260802.md` P1 节，
> 逐项核实工作树修改与功能性。

## 1. 现状

`/domestic/library` 路由、`domestic_library_page()` 函数、首页卡片与导航项已经写进工作树 `app.py` 顶层（diff +96/-6）。
production live server（PID 40248，Aug 2 12:45 启动）尚未重启加载新代码。
测试 fixture `live_server` 会自己 spawn 子进程，所以 pytest 看到的是新版本。

| 验收项 | 状态 | 说明 |
|---|---|---|
| 首页出现 `/domestic/library` 国内资料库卡片 | 代码已就位 | `app.py:967-971`：`<h3>国内资料库</h3>`，`href="/domestic/library"` |
| 新增 `/domestic/library` 路由 | 代码已就位 | `app.py:2373` `def domestic_library_page`；`app.py:7741` `parsed.path == "/domestic/library"` |
| 页面只展示 `source_platform='domestic'` 的正式收录 | 实现正确 | SQL：`WHERE d.source_platform='domestic'` 且 `JOIN documents`，**不**走 `domestic_candidates` |
| 显示文档/页面/来源/当前结果数 | 实现正确 | `<section class="stats">` 输出 total_docs / total_pages / source_count / len(rows) |
| 题名/档号/来源筛选 | 实现正确 | form `?q=`，SQL 命中 `title LIKE ? OR doc_key LIKE ? OR volume_title LIKE ?` |
| `/domestic` 增加返回已收库的入口 | 实现正确 | `app.py:2531` "已收资料库" 按钮链接到 `/domestic/library` |
| 导航增加"已收国内资料" | 实现正确 | `app.py:767` `("library", "i-library", "资料库", [..., ("/domestic/library", "已收国内资料"), ...])` |
| OCR/候选/staging/复核边界说明保留 | 实现正确 | 页面顶部"国内史料层正式收录文档；候选线索、staging 材料和待复核记录不混入本列表"；底部 notice 提到 OCR 用于检索不等于逐字可靠 |

## 2. 测试结果

`PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m pytest -q tests/` → **13 passed** in 0.55s。

新增 `test_domestic_library_smoke` 走 `_require_database` 真实库（不伪造数字），与既有 6 条 smoke 一并通过：

```
tests/test_smoke.py::test_home_smoke PASSED
tests/test_smoke.py::test_dashboard_smoke PASSED
tests/test_smoke.py::test_sourcebooks_smoke PASSED
tests/test_smoke.py::test_doc_detail_smoke PASSED
tests/test_smoke.py::test_timeline_smoke PASSED
tests/test_smoke.py::test_domestic_smoke PASSED
tests/test_smoke.py::test_domestic_library_smoke PASSED
tests/test_snapshot.py::test_home_snapshot PASSED
tests/test_snapshot.py::test_dashboard_snapshot PASSED
tests/test_snapshot.py::test_sourcebooks_snapshot PASSED
tests/test_snapshot.py::test_doc_snapshot PASSED
tests/test_snapshot.py::test_timeline_snapshot PASSED
tests/test_snapshot.py::test_domestic_snapshot PASSED
```

`tests/snapshots/` 6 份 HTML 快照随之更新（diff：dashboard ±2、doc ±2、domestic ±3、home ±6、sourcebooks ±2、timeline ±2）。`tests/test_snapshot.py` 加了一个 `line.rstrip()` 兜底；快照只护栏结构和内容，不护栏空白实现细节。

## 3. Live server 待办事项（**未自动执行**）

`python3 app.py` PID 40248 的 live server 仍跑 Aug 2 12:45 启动的二进制，**不包含 `/domestic/library`**。本任务明确：

> 不删除本地任何文件、数据库、备份、缓存、日志或模型产物。
> 不执行 `git reset --hard`、…不覆盖远端历史。

所以本人**没有**对 PID 40248 执行 `kill -TERM` 或 SIGTERM。要让 production 127.0.0.1:8765 看到新路由：

- 选项 A（推荐）：用户在浏览器侧手动停掉 PID 40248 后 `python3 app.py` 重启。
- 选项 B：在不杀 production 进程的前提下，单独 `python3 tests/_launch_server.py` 起一个独立端口用于回归（CI / 人工隔离测试）。

本人会在 FINAL_ACCEPTANCE.md 中明确登记这条 take-over，让用户决策。

## 4. 安全门

- `git diff --check` 无 whitespace 错误。
- 没有动 SQLite；没有改 `domestic_candidates`；没有写 `citation_ready` 或 `human_verified`。
- 不属于本任务的 `data/domestic/1957_1976_*_20260730/` 等 staging/工作目录**未触碰**。
- 工作树 12 modified + 0 staged，与 master task 第 5 节"只暂存以下明确文件"清单边界一致，未误包含任何其它目录。

## 5. P1 验收门

- [x] `/` 首页卡片已指向 `/domestic/library`
- [x] `/domestic/library` 在 app.py 已注册路由，未对 production live server 强重启
- [x] smoke 测试 13 passed，包含 `test_domestic_library_smoke`
- [x] 候选目录 `/domestic` 与已收资料库互链
- [x] OCR / staging / 复核边界在页面上有显式提示
- [x] 未越权写 SQLite、未触碰候选状态

## 6. 下一步

`/domestic/library` 是否在 production 127.0.0.1:8765 上线，由用户在浏览器侧手动决定重启时机。
本任务其余 P2/P3/P4 产物已在 `minimax_next_stage_20260802/` 中以最小增量的方式承接 w6 outputs。
