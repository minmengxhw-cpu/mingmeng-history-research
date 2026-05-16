# AGENTS.md — 海外民盟历史文献研究库

> 这是给 Codex / Claude / 其他 AI agent 接手本项目时的入口文件。
> 先读这个，再读 `README.md`，最后读 `docs/research_workbench_progress.md`。

## 项目一句话

基于 FRUS 1941–1950 卷册搭建中国民主同盟史料研究工作台：抓取、校验、翻译、全文检索、引用、事件线索、研究卡片导出。Python + Flask 单文件 app + SQLite。

## 当前关键状态

- 索引规模：299 篇文档，416 个页/段落片段，117 个带官方页码锚点。
- 翻译覆盖：416 个片段 100% 有中文译文，其中 403 个 Argos 机器初稿，13 个早期批量样本。
- 质量提示：见 `docs/translation_quality_report.md`，最新一次 322 条；`/tasks` 路由是优先级队列。

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
.venv/bin/python app.py            # 启动本地服务 http://127.0.0.1:8765
.venv/bin/python scripts/postedit_argos_translations.py
.venv/bin/python scripts/build_translation_quality_report.py
```

## 提交规范

- 用 git。**修改 SQLite (`data/research_index.sqlite`) 也要 commit**，它是项目的事实状态。
- Commit message 中文/英文都可，第一行简短描述，正文列出 quality report 的 delta（前/后对比）。
- 大批量翻译改动单独成 commit，与代码改动分开。

## 已知坑

- `Service` 不能作为 `John S. Service` 的术语表条目——会和 "Foreign Service" 等常用短语冲突，已改用 `John Service` / `John S. Service` 两条全名映射。
- `Generalissimo`→`委员长` 不能机械替换——FRUS 里 "Marshal Li Chi-shen" 译成"元帅李济深"是对的，与 Generalissimo（蒋介石）不同。需要人工辨别。
- `T. V. Soong` 的 "宋大夫" / "宋博士" 在某些上下文是 Argos 的误译，但 "宋博士" 也可能指别人——慎用。
- 不要 `git add data/.venv data/ocr_smoke_test data/frus_epub_tmp`，已在 `.gitignore`。

## 最近一次接力（2026-05-14, Claude）

- Commit `b015b7e`: git baseline，911 files。
- Commit `a4adbaf`: 扩展术语表 ~60 条 + postedit zh-zh 字典扩展；postedit 触动 106 条；english_residue 总数 112→88。
- 下一步：人工校订 `/tasks` 前 20 条高优先级片段。
