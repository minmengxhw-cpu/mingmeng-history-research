# 公开发布边界

本仓库是研究平台的代码与流程发布版，不是研究资料分发包。

公开树只保留：

- 应用代码、脚本、测试和 CI 配置；
- 不含正文的流程说明、数据字典和研究方法文档；
- 明确标记为 synthetic 的测试夹具。

以下内容必须留在本机或受控数据盘，不得提交到公开仓库：

- `research_index.sqlite`、staging SQLite 和任何数据库备份；
- 原始扫描、PDF、图片、下载缓存和 OCR 正文；
- `data/` 下的研究数据、译文、队列和本机元数据；
- `work/`、`.tasks/`、`workspace/` 下的收口报告、任务记录和草稿；
- 包含本机路径、正文摘录、访问凭据或私有来源清单的文件。

启动应用时，通过环境变量挂载外部资料：

```bash
MINGMENG_RESEARCH_DB=/path/to/research_index.sqlite \
MINGMENG_DATA_ROOT=/path/to/data \
MINGMENG_WORK_ROOT=/path/to/work \
python3 app.py
```

公开发布前至少执行：

```bash
git ls-files | rg '^(data/|work/|\.tasks/|workspace/)' \
  | rg -v '^(data/\.gitkeep|work/\.gitkeep|\.tasks/\.gitkeep|workspace/\.gitkeep)$'
git grep -n -I -E '/Users/|/private/tmp/|BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY|ghp_|github_pat_|xox[baprs]-'
```

第一条命令应无输出；第二条命令只能在确认是文档中的占位示例后保留结果。
