# AGENTS.md — 民盟历史文献研究库

> 这是给 Codex / Claude / 其他 AI agent 接手本项目时的入口文件。
> 先读这个，再读 `README.md` 和 `docs/_changelog.md`。

## 项目一句话

基于 1941–1950 年中国民主同盟相关境外一手档案搭建研究工作台：抓取、校验、翻译、全文检索、引用、事件线索、研究卡片和史料长编导出。Python 标准库 HTTP server + SQLite。

## 当前关键状态

- 索引规模以本地 `data/research_index.sqlite` 为准；最近一次统计为 6 源 768 篇文档。
- 数据库文件不进 git，GitHub 只保存代码、原始文本快照、脚本和文档；数据库备份走 `data/backups/` 或单独同步。
- 翻译覆盖以 `translations` 表为准；正式引用核心段落前仍需人工校订。

## 工作流必读

1. **改翻译前先看 `data/translation_glossary.csv`**——所有 FRUS 标准译名都在这里。新加人物/机构请加到 CSV。
2. **改翻译用 `scripts/postedit_argos_translations.py`**，而不是直接 `UPDATE translations`。它会同步刷新 FTS 索引。
3. **Argos 常见误译的中文→中文规范化字典在 `scripts/translate_missing_pages_argos.py` 的 `glossary_postedit` 函数里**，是项目的"事实标准"。新发现的误译模式（如"斯图亚特"→"司徒雷登"）加在那里。
4. **改完跑 `scripts/build_translation_quality_report.py`**，确认改善方向。
5. **单条人工校订走 `/review/<page_id>`**（前端）或直接改 `translations` 表 + 同步 `translation_fts`。

## 数据模型要点

- `documents` → `pages` → `translations` 三级；FTS 索引：`page_fts`（英文）、`translation_fts`（中文）。
- 翻译状态字段 `translations.status`：`machine-draft` / `local-postedit` / `sample-review-needed` / `human-reviewed`。**人工校订过的请把 status 置为 `human-reviewed`**。
- `translation_quality_issues` 表由 `build_translation_quality_report.py` 重建（DROP + CREATE）。

## 推荐入口

```bash
python3 app.py                     # 启动本地服务 http://127.0.0.1:8765
python3 scripts/build/build_translation_quality_report.py
python3 scripts/oneshot/gen_sourcebook.py frus
```

## 提交规范

- 用 git。**不要提交 SQLite (`data/research_index.sqlite`)**；它是本地事实状态，但已经通过 `.gitignore` 排除。
- Commit message 中文/英文都可，第一行简短描述，正文列出 quality report 的 delta（前/后对比）。
- 大批量翻译改动单独成 commit，与代码改动分开。
- Git 作者统一使用 `小班 <bot@users.noreply.github.com>`，不要出现个人真名或其他机器人署名。

## 已知坑

- `Service` 不能作为 `John S. Service` 的术语表条目——会和 "Foreign Service" 等常用短语冲突，已改用 `John Service` / `John S. Service` 两条全名映射。
- `Generalissimo`→`委员长` 不能机械替换——FRUS 里 "Marshal Li Chi-shen" 译成"元帅李济深"是对的，与 Generalissimo（蒋介石）不同。需要人工辨别。
- `T. V. Soong` 的 "宋大夫" / "宋博士" 在某些上下文是 Argos 的误译，但 "宋博士" 也可能指别人——慎用。
- 不要 `git add data/.venv data/ocr_smoke_test data/frus_epub_tmp`，已在 `.gitignore`。

## 最近一次接力提示

- 先看 `git status --short --branch`，确认是否有本地未提交改动。
- 首页、平台卡、长编生成器和数据库口径经常联动，改一处后要同步验证 README、dashboard 和首页显示。
- 下一步优先级：身份与文档口径统一、史料长编导出入口、DRNH 自动摘要质量分层、Kew/HKPRO/Sinica 外部档案推进。
