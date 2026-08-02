# 语料库删除建议清单（2026-08-02，待确认）

> 原则：只删「无价值 / 范围外 / 已入库的过程产物」；一切与民盟相关的原文素材与入库数据一律保留。
> 请逐类确认，确认后我再执行。所有删除均先备份一份索引清单到 git，可追溯。

---

## A. 确定可删（纯冗余，不涉内容价值）——约 69.4 GB

### A1. `data/*.bak` 数据库备份 —— 288 个 / 69.4 GB ⭐主力
- `machine_review.*` 92 个 / 26.3 GB：7/28-7/29 循环内每 3 秒一个的瞬时快照
- `MONTH_B*` 119 个 / 34.6 GB：同上的月度流程瞬时快照
- `research_index.sqlite.2026*` 66 个 / 6.4 GB：逐 OCR 页面的 80-460MB 备份
- 单个大备份（pre_rebaseline、pre_quarantine 等）12 个 / 2.2 GB
- **保留例外（建议各留 1 个近期回滚点）**：
  - `pre_quarantine_1931_20260802.bak`（458M，本次隔离前）
  - `pre_rebaseline_20260802_e4417bd1.bak`（458M，基线重建前）
  - 其余 286 个全删

### A2. work/ 内 dryrun/隔离测试库 —— 8 个 / 2.9 GB
- `repair_gate_0/isolated_dbs/*` 4 个（各 ~460M）：迁移验证用，验证已通过
- `minimax_two_month/w1/research_index.w1_dryrun.sqlite`（471M）
- `research_layers_acceptance/...dryrun.sqlite`（471M）
- `minimax_autonomous/dryrun/...dryrun.sqlite`（5M）
- `staging_20260730/domestic_staging.sqlite.pre_*.bak` 4 个（各 ~20M，staging 库的旧备份）

### A3. 范围内外语料图 —— 1.37 GB
- `work/domestic/month_20260728/pages/NLC511-012031312030001-21905/`（632M）：大公报 113 卷（1931）
- `work/domestic/month_20260728/pages/NLC511-012031312030001-21906/`（735M）：大公报 114 卷（1931）
- **理由**：即昨日隔离的 1931 大公报（民盟成立前，范围外），已移出前台，原图无需保留

### A4. 小冗余
- `data/domestic/candidates.jsonl.bak.*` 3 个（4MB）：候选表旧备份
- `data/domestic/mingmeng.sqlite`（0 字节空文件）
- `screenlog.0`（50 字节）

**A 类合计约 73.7 GB**

---

## B. 建议保留（价值语料，勿删）

| 对象 | 体量 | 理由 |
|---|---|---|
| `work/domestic/month_20260728/pages/`（除 21905/21906） | ~6.1 GB | 已入库民国报纸/文献的**原始页面图**（新华日报、大刚报、民宪、光明报、观察、历史文献、宣言等），一手素材 |
| `data/domestic/press_scans/` | 455 MB | 已 OCR 入库的一手原始扫描 PDF |
| `data/domestic/grok_*` 各 cycle | ~600 MB | 公开网页快照/PDF（FRUS、政协、民盟文件），原始抓取 |
| `data/domestic/sourcebooks/` | 71 MB | 汇编 |
| `data/newspapersg/images` | 536 MB | 海外华文报纸图片 |
| 各平台 documents/pages/translations | 库内 | 正式语料 |

---

## C. 待你决策（内容相关，我不擅自删）

1. **CIA 平台 26 个已隔离文档**（1950-1982：CURRENT INTELLIGENCE BULLETIN、SMUGGLING OF RUBBER、FACTBOOK 等）——已从前台隐藏，但**物理仍存**。删 or 留？
2. **hathitrust 12 个 1950「建国初期第三方面」**——已隔离，1949 后出范围。删 or 留？
3. **CIA 平台未隔离的 ~50 个 1950-1954 文档**（张澜、沈钧儒、政协、联合政府等后续情况）——标题看与民盟相关，但超 1941-49 时间窗。这类**建议保留**（人物后续史料），除非你明确不要。
4. **`-- page break --` 垃圾页 5 处 + 空页**：doc 374 的 5 页。可清文本或保留（影响极小）。
5. **顶层遗留脚本** `key_events.py / person_archive.py / platforms.py / weixin_bridge.py`（93KB）：早期项目遗留，与 domestic 语料无关。归档 or 删？

---

## 我的建议
- **A 类全部执行**（纯冗余 73.7GB，零内容损失）。
- **C 类默认建议**：1/2 删除（已隔离且范围外）；3 保留；4 清理 page-break 文本；5 归档到 `scripts/legacy/`。

请逐项确认：**A1/A2/A3/A4 是否全删？C1-C5 各如何处置？**

---

## 执行结果（2026-08-02 已执行）

用户确认：**A 类纯冗余全部删除；C 类采纳 4、5；C1/C2/C3 保留不动。**

| 项 | 内容 | 结果 |
|---|---|---|
| A1 | data/*.bak 286 个 | ✅ 已删，释放 68.42 GB（保留 pre_quarantine + pre_rebaseline） |
| A2 | work/ dryrun/隔离测试库 12 项 | ✅ 已删，释放 3.01 GB |
| A3 | 1931 大公报原图 21905/21906 | ✅ 已删，释放 1.43 GB |
| A4 | candidates.jsonl.bak×3、空 mingmeng.sqlite、screenlog | ✅ 已删 |
| C4 | page-break 垃圾页 5 个 | ✅ 已删（pages+fts 同步，5475→5470） |
| C5 | 顶层遗留脚本 ×4 | ✅ 归档至 scripts/legacy/ |
| C1/C2/C3 | CIA 26 / hathitrust 12 / CIA 1950-54 | ⏸ 按用户决定保留（C1/C2 已隔离不出前台） |

- 总释放：**约 73 GB**（data 67→4.5GB，work 9.6→5.4GB）
- 新 SHA：`7af2e27b`（S2 后，新增 bigram FTS 索引表）
- 备份：保留 pre_quarantine_1931 / pre_rebaseline / pre_pagebreak_clean 三份回滚点
