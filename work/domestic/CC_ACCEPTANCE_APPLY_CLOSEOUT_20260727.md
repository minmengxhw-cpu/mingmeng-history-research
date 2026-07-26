# CC 工作验收与正式入库收口（2026-07-27）

## 验收结论

CC 资料搜集/OCR 主批次通过有条件验收，并已作为 `ocr_status=pilot`、`needs_human_review` 的检索草稿正式合并入本地 SQLite。任何 OCR 草稿均未升格为可直接引用的校订文本。

### 通过并入库

- 58 个来源文档。
- 3598 个原始 PDF/图像物理页。
- 75 个 SQLite OCR 检索单元：按现存 OCR Markdown/chunk 入库，每个 `page_label` 保留对应物理页范围。
- 第 113 卷《大公报》：232 页，3 chunks，SHA256 `31060177686a64a99f1c8b464d972d3a5271f00c6ee47e8616b5340b8f771c84`。
- 第 114 卷《大公报》：248 页，3 chunks，SHA256 `80d5daea555bfa6e5df03baaa71b4b0dc251510adb89752ab93da3ce932bb0bd`。

### 暂不入库

- `P3-023`：《观察》第 3 卷第 1—12 期；OCR 质量可用于检索，但 issue/article 边界仍是自动猜测，等待逐期核校。
- `P3-GXMM-SH`：旋转变体达到 0.8012，但候选 manifest 仍指向均值 0.5019 的旧 OCR Markdown，路径与置信度不一致；需以旋转版重建独立 provenance 后再审。
- `P3-GXMM-TJ`：旋转变体达到 0.8672，但候选 manifest 仍指向均值 0.4575 的旧 OCR Markdown，路径与置信度不一致；需以旋转版重建独立 provenance 后再审。

## 正式合并

- 导入批次：`cc_accepted_20260727`。
- 导入前：documents/pages/page_fts = `928/1428/1428`。
- 导入后：documents/pages/page_fts = `986/1503/1503`。
- 新增：58 documents、75 pages、75 page_fts。
- `source_platform=domestic`：58/58。
- `PRAGMA integrity_check`：`ok`。
- FTS orphan：0；pages 缺 FTS：0。
- 候选校验：689/689 通过；事件覆盖缺失引用 0；审计 accepted 660。

## 外键说明

`PRAGMA foreign_key_check` 仍报告 15 条 `document_classifications → documents` 历史残留。导入前自动备份中同样是 15 条、相同 rowid；本批次未新增外键问题，暂不扩大范围修复历史分类表。

## 检索提升

| 查询 | 入库前 | 入库后 |
| --- | ---: | ---: |
| 成立宣言 FTS | 5 | 14 |
| 政治协商会议 FTS | 131 | 146 |
| 新政协 FTS | 125 | 128 |
| 中国民主同盟 FTS | 162 | 178 |
| 张澜 LIKE | 19 | 32 |
| 上海 LIKE | 82 | 149 |
| 民盟 LIKE | 152 | 195 |
| 多党合作 FTS | 0 | 1 |

二字中文词在 FTS5 trigram 下仍可能为 0，平台查询时需保留 LIKE/混合检索兜底。

## 回滚与校验

- 自动备份：`data/research_index.sqlite.cc_accepted_20260727.pre.bak`。
- 回滚命令：`cp -p data/research_index.sqlite.cc_accepted_20260727.pre.bak data/research_index.sqlite`。
- 入库后数据库 SHA256：`bba5efa00640f3736e05cd2e8c14927fed9daa8b9888e6b77cd729b0cbd34189`。
- 备份 SHA256：`38d57fa13bc61763ea8f2495b32dd0a1050796ea35a6a7569fa111e2db046075`。

数据库、原始 PDF、OCR 全文和备份均按 `.gitignore` 留在本地，不进入 GitHub。GitHub 仅保存可复现脚本、manifest、验收报告和阶段总结。
