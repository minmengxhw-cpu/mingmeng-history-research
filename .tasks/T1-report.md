# T1 建立回归网 —— 完成报告

分支:`chore/t1-test-net`(本地已提交,commit `0a59ad0`;**push 到 GitHub 被阻塞,见下方「阻塞项」**)

## 改了哪些文件

新增:
- `requirements.txt`(30 行)、`requirements-dev.txt`(5 行)—— 全仓扫 `import` 语句核实,不是抄 README
- `pytest.ini`(3 行)
- `tests/__init__.py`(0 行)
- `tests/_launch_server.py`(38 行)—— 复用 app.py 现有的 `Handler`/`ReusableThreadingHTTPServer` 类在随机端口起服务,**未修改 app.py 任何一行**
- `tests/_http.py`(18 行)—— 请求封装,统一处理"连接被重置"这种没有状态码的场景
- `tests/conftest.py`(101 行)—— `live_server` / `db_missing_reason` 两个 fixture
- `tests/test_smoke.py`(85 行)、`tests/test_snapshot.py`(77 行)
- `tests/snapshots/sourcebooks.html`、`tests/snapshots/domestic.html`(快照基线)
- `.github/workflows/ci.yml`(17 行)

修改:
- `.gitignore` +1 行(`.pytest_cache/`)

全部文件均 ≤ 101 行,没有超标的。

## 验收项逐条结果

| 验收项 | 结果 |
|---|---|
| `pytest` 全绿 | ✅ 本机实测 `4 passed, 7 skipped, 0 failed`(跑了 3 次,含"故意破坏快照基线确认真的会 FAIL"的对抗测试,恢复后回到 4 passed) |
| `tests/snapshots/` 已生成并提交 | ✅ 但只有 2 个文件(`sourcebooks.html`、`domestic.html`),不是 6 个 —— 原因见下 |
| CI 在 GitHub 上跑通(绿勾) | ⚠️ **未验证** —— 代码已写好(`.github/workflows/ci.yml`),但 push 被阻塞(见下),没法在 GitHub 上实际触发一次运行去确认绿勾 |
| 当前快照覆盖了几个路由、哪些页面因数据缺失被 skip | 见下方详细说明 |

## 快照覆盖情况(重要,直接影响 T2 能不能安全进行)

要求覆盖 6 条路由:首页、`/dashboard`、`/sourcebooks`、文档详情页、`/timeline`、国内史料页(`/domestic`)。

**实测结果:只有 2 条(`/sourcebooks`、`/domestic`)在当前环境下能拿到真实 200 响应并生成了字节级快照,其余 4 条(首页、`/dashboard`、`/timeline`、文档详情页)全部 skip。**

根因(已用 `python3 app.py` + curl 现场复现,不是猜的):

1. app.py 实际连接的数据库路径是 `data/research_index.sqlite`(见 app.py 第 21 行 `DB_PATH = ROOT / "data" / "research_index.sqlite"`),**这个文件在 `.gitignore` 里被排除,从未提交到仓库**。全新 clone(包括这次 CI)拿到的仓库里根本没有这个文件。
2. 现有的 `scripts/build/build_research_index.py` 只能重建 `sources`/`documents`/`pages`/`page_fts` 四张表(仅覆盖 FRUS 一个平台),缺 `domestic_candidates`、`domestic_sources`、`translations`、`document_classifications`、`research_events` 等后续新增的表 —— 也就是说**即使跑一遍这个脚本,也拿不到一个能撑起首页/dashboard 的完整数据库**。
3. app.py 里 `home()`、`dashboard()`、`timeline()`、`doc_page()` 这几个函数的**第一条 SQL 语句都没有 try/except 保护**(例如 `home()` 第一行就是 `c.execute("SELECT count(*) FROM documents")`)。数据库缺表时抛出的 `sqlite3.OperationalError` 会一直往上抛到 `http.server` 的默认异常处理,**它不会返回 500 或任何响应体,而是直接把 TCP 连接断开**(已用 curl 实测:`HTTP_CODE:000`,连状态码都拿不到)。
4. 只有两个例外:
   - `/sourcebooks`(`sourcebooks_page()`)**完全不查数据库**,只读文件系统(`workspace/*.pdf`、`output/research_packages/*.zip`,且都做了 `.exists()`/`.is_file()` 判断),所以任何环境下都能正常渲染。
   - `/domestic`(`domestic_page()`)是**唯一**对 `sqlite3.OperationalError` 做了 try/except 的路由,缺表时会优雅退化成一个"国内史料表尚未初始化,请先运行 scripts/domestic/ingest_domestic.py"的正常 200 提示页 —— 这条快照测的是退化页面的文案,不是真实史料内容。

我把这个发现和判断逻辑写进了 `tests/conftest.py` 顶部的大段注释和 `test_smoke.py`/`test_snapshot.py` 里,以及 `.gitignore` 的原有条目里能看到(第 55-62 行本来就排除了 `research_index.sqlite*`)。测试对这四条路由的处理是:**先探测数据库缺失的具体原因,确认真的是"缺表"而不是别的 bug,再 skip 并把原因打印出来** —— 不是简单粗暴地 try/except 吞掉所有异常。

## 发现但未处理的问题(留给后续工单,没有顺手改)

1. **`home()`/`dashboard()`/`timeline()`/`doc_page()` 缺少 `sqlite3.OperationalError` 保护**,和 `domestic_page()` 的写法不一致 —— 这是"看起来是 bug 但改了会变行为"的典型情况,按工单要求记录、不修。
2. **`main()` 硬编码端口 `127.0.0.1:8765`**,本机实测这个端口正被另一个不相关的进程占用。我在测试里用了绕过方案(直接 import app.py 复用类,不调用硬编码的 `main()`),但如果以后要在别的地方(部署、本地开发)启动 app.py,这个硬编码端口仍然是个真实的脆弱点。
3. `build_research_index.py` 已经与线上 schema(至少缺 5 张表)脱节,不确定这是遗留脚本还是有别的建库流程在别处 —— 需要原作者确认。

## 阻塞项 —— 需要你处理才能继续(重要,已停下等确认)

**push 到 GitHub 失败,不是网络问题,是权限问题。** 已排查清楚:

- `~/.ssh/mingmeng-history-research` 这个 deploy key **在这个仓库上根本没有被注册**(SSH 认证直接被拒,不是权限不够,是完全不认这个 key)。
- `~/.ssh/id_ed25519`(我这台机器的默认个人 key)**已经注册为这个仓库的 deploy key,但是只读**,GitHub 明确返回 `Permission to ... denied to deploy key`。
- 之前我在第一次汇报里说"部署密钥读写权限没问题"——**这个结论是错的,我道歉**。当时测的是 `git ls-remote`/`git clone`,而这个仓库是公开仓库,匿名 HTTPS 就能读,我这台机器全局配置里有一条 `url.https://github.com/.insteadOf=git@github.com:` 的重写规则,把我所有 SSH 形式的 URL 都悄悄改写成了匿名 HTTPS——读操作全部"成功"是因为压根没用到那个 key,不代表它真的有权限。这个是我的测试方法问题,现在已经用 `ssh://` 显式 URL 绕开重写规则重新验证过,结论以这份报告为准。

**需要你二选一(我等你的选择,不会替你决定)**:

- **A. 把已注册的只读 key 改成可写**:GitHub 仓库 → Settings → Deploy keys,找公钥指纹 `SHA256:...`(对应下面这段公钥)对应的条目,勾选"Allow write access"保存。
  ```
  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN07+E5YHIStY2g2xtTc1BTx1dvq2xKvfg/LBvGdECkV zq@qq-Redmi-Book-Pro-16-2024
  ```
- **B. 加一个新的可写 deploy key**:我可以现在生成一个新密钥对,把公钥发你,你贴到 Settings → Deploy keys → Add deploy key,勾"Allow write access"。

选好之后告诉我,我马上重新推送 `chore/t1-test-net` 分支,并在 GitHub 上确认一次 CI 是否真的跑绿(不是只看代码写没写,是真的看 Actions 页面的结果)。

## 另一个需要你拍板的事(不是阻塞 push,但阻塞 T2 的安全性)

上面「快照覆盖情况」里说的很清楚:**目前的回归网只覆盖 2/6 条路由**,首页/dashboard/timeline/文档详情页这四条因为没有真实数据库,T2 拆分它们时**没有任何东西能证明拆完输出没变**。工单原话是"没有 T1 建立的回归网,你无法证明拆完之后页面还和原来一样"——现在这四条恰恰就是这个状态。

在你确认 push 权限的同时,建议顺带想一下这个:
- 你手上或者线上部署的地方,有没有一份真实的 `data/research_index.sqlite`? 如果有,发给我(或告诉我在哪能拿到),我可以补全剩下 4 条路由的快照,回归网覆盖率从 2/6 提到 6/6。
- 如果暂时没有,我也可以先这样进 T2(拆分时对这四条路由格外小心、逐行核对,而不是靠快照自动校验),但这样风险明显更高,建议你知情后再决定要不要接受这个风险。

## 回滚方式

本次改动全部是新增文件 + `.gitignore` 加一行,没有改动任何现有文件的内容。回滚:
```
git branch -D chore/t1-test-net   # 本地分支还没推上去,直接删即可
```
如果之后已经 push 到远程,回滚方式是在 GitHub 上直接关闭/不合并对应 PR,不会影响 `main` 分支。
