# 国内研究平台运行验收（2026-08-15）

## 结论

本地阅读器已在 `127.0.0.1:8765` 重新启动，当前 checkout 的国内—海外对齐页面与正式元数据门禁一致：

- `/research/parity`：HTTP 200；9 个专题、9/9 导航可用、9/9 来源地图、204 个来源地图页、0 个 `research_ready`、9 个开放原件目标。
- `/domestic/library?layer=core`：HTTP 200；国内核心可阅入口可打开。
- 页面保留 `body_read=false`，没有把导航、书目交叉表或汇编重刊升级为一手原件闭环。

## 修复内容

清洁 checkout 可能没有未纳入 Git 的 `work/domestic/staging_20260730/domestic_staging.sqlite`。此前网页只从正式 SQLite 中少量可读的学术全文记录重新按关键词匹配，导致页面统计低于已提交的 `data/domestic/academic_topic_crosswalk.json`。

现在：

1. 9 个专题的学术元数据总数优先读取已提交的学术—专题交叉表；这是可复现的书目/结构化元数据计数，不是正文阅读或引用门禁。
2. 当前 checkout 实际携带的详情记录仍按可见行展示；缺失详情时页面明确提示“元数据匹配、详情未携带”，不虚构作者、机构、全文或页码。
3. `research_ready` 仍要求一手证据状态关闭，因此本次修复只恢复导航一致性，不改变一手证据状态。

## 验证证据

- `PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile app.py`：通过。
- `python3 scripts/domestic/build_domestic_parity_matrix_20260813.py --output /tmp/domestic-parity-current.json`：`status=PASS`，9/9 `navigation_ready`，0/9 `research_ready`。
- 随机端口真实 HTTP 回归：对 `/research/parity` 返回 200，页面包含 `9 个导航可用`、`0 个 research_ready`、`body_read=false`。
- 8765 真实 HTTP 回归：`/research/parity` 与 `/domestic/library?layer=core` 均返回 200。
- 当前正式库 manifest：数据库 SHA256 `75312b9c1cfe7d8978f64c572b4c32b7ab443fb507eabfd3b2fce47031d2109e`；1,413 个文档、6,266 个页、220 个严格人工引用页；SQLite 完整性、外键、FTS 和来源 hash 检查通过。
- 当前专题检索队列：81 个页级事件导航关联；队列和主证据矩阵已按当前数据库重建。
- 李闻专题新增 2 条正文-free 原刊追索路线：民盟云南官方盟史出版范围和商业影印目录；两条均为 `navigation_only`，不增加正式库页或严格引用页。
- 1944 改组专题新增 1 条正文-free 官方盟史导航锚点；只用于日期、地点和组织变化的交叉定位，不增加正式库页或严格引用页。

## 未完成项

运行验收不等于内容闭环。1941 成立宣言原刊、1947-10-27 政府公函和 1947-11-06 民盟总部原始公告仍在开放原件队列；现有同期报刊和 1946/1983 汇编页继续按各自证据等级使用。
