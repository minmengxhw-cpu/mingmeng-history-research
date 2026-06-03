# 三源统一误收清单 · 阶段性报告

> 民盟历史文献研究库 · 2026-06-03
> 用户清单 #3 误收专项清理完整执行报告

## 一、范围与方法

清理三个最容易混淆的源：CIA / NewspaperSG / HathiTrust，合计 116 + 93 = 209 篇文档候选（DRNH / FRUS / Wilson / Hoover 不在 Democratic League 混淆高发区，本期不纳）。

### 1.1 方法学（两阶段）

阶段 A · **关键词扫描**：基于 `data/excluded_organizations.csv` 黑名单 8 类组织（Taiwan-DSGL、Malayan-DL、Korean-DL、Indo-British-DL、Burmese-DL、Vietnam-DL、Other-non-China-DL、Generic-broadcast），用正则识别命中文档；并扩展"DL≥1 且 China 强信号≤1"作低信号候选。

阶段 B · **LLM 二次精读** + **全文规则验证**：
- DeepSeek-v4-flash 对候选篇做"是否真涉中国民盟"判断
- 由于 LLM 上下文窗口前 5000 字符截断导致**整期港媒误判**（HathiTrust NPCM 系列 CDL 在 OCR 中段 600-1000 行才出现），增加全文规则验证（grep CDL 强信号 vs 国家上下文关键词命中比）做最终确认

## 二、最终结果

### 2.1 三源剔除统计

| 平台 | 候选 | 剔除 | 误判已撤销 | 真实剔除 |
|---|---:|---:|---:|---:|
| NewspaperSG | 93 | 1 | 0 | **1** |
| CIA | 62 | 6 | 3 | **3** |
| HathiTrust | 54 | 3 | 3 | **0** |
| **合计** | **209** | **10** | **6** | **4** |

### 2.2 4 篇真实剔除清单

| 平台 | 文档 ID | 日期 | 类别 | 关键证据 |
|---|---|---|---|---|
| CIA | cia-rdp82-00457r002700170001-7 | 1949-05-06 | Other-non-China-DL | WFDW 命中 4 次 / CDL 强信号=0；实为'世界民主妇女联合会'报告（新发现）|
| CIA | cia-rdp78-01617a003500050003-5 | 1949-11-17 | Malayan-DL | Malaya/Malayan=134 / CDL=1；阶段 1 已剔除清单一致 |
| CIA | cia-rdp78-01617a003700140001-5 | 1950-01-11 | Burmese-DL | Burma/Burmese=136 / CDL=1；实指 AFPFL；阶段 1 已剔除清单一致 |
| NewspaperSG | indiandailymail19490524-1.2.42 | 1949-05-24 | Other-non-China-DL | 报道'民盟'实为广播电台名称 |

### 2.3 已撤销的 LLM 误判（共 6 篇）

LLM 第一次扫描因前 5000 字符截断而误判，全文规则验证后撤销：

- **HathiTrust 3 期港媒**（NPCM19470426 / NPCM19480106 / NPCM19481202）：均为《华侨日报》整期报纸，OCR 总字符 200-250 KB，'Democratic League' 在中段（行 605/688/1018）才出现，LLM 因只看前 5000 字符而误判为"OCR 无 DL"。全文 grep 确认含中国民盟报道，应**保留**。
- CIA Malaya/Burma 2 篇 LLM 第二次给出"keep"（与第一次"exclude"不一致），但全文规则验证支持剔除（CDL=1 vs 国家关键词 130+），保持 exclude 决定。
- CIA WFDW 1 篇 LLM 第二次也给"keep"，但全文规则证 CDL=0 强信号且 WFDW=4，**保持 exclude**。

LLM 判断不稳是已知边界，本平台对剔除决定**叠加全文规则验证**作最终把关。

## 三、对前台的影响

### 3.1 入库路径（用户本地）

```bash
python3 scripts/build/merge_excluded_master.py        # 三源合并到统一清单
python3 scripts/ingest/ingest_excluded_master.py      # 注入 sqlite document_classifications
python3 app.py                                         # 重启服务
```

### 3.2 前台显示变化

- `/excluded` 页面新增 4 篇'前台不展示'文档
- `/sources/cia` 列表中 3 篇 CIA 文档下移到"已剔除"分组
- `/sources/newspapersg` 列表中 1 篇下移
- `/quality` 页面的"疑似非中国民盟"专项提示统计 +4

### 3.3 不动声色保留的 102 篇

CIA 候选 62 - 3 已剔 = 59 篇保留，其中 5 篇之前的低信号但 CDL=1 也保留（如 1947-04 SELANGOR Chinese in Support of...，虽然 Selangor 是马来亚地名，但 CDL 在 OCR 中明确指中国民主同盟 - 雪兰莪分部）。

HathiTrust 54 期全保留（NPCM 整期港媒整期均含民盟相关报道）。

NewspaperSG 92 篇保留（1 篇广播电台名误命中已剔除）。

## 四、方法学产物

| 文件 | 用途 |
|---|---|
| `data/excluded_organizations.csv` | 8 类异国 DL 误收组织黑名单（结构化数据，可扩展）|
| `scripts/build/scan_excluded_organizations.py` | CIA + HathiTrust 扫描脚本（关键词命中 + LLM 复核）|
| `data/excluded_org_scan_candidates.csv` | 关键词候选清单（30 篇）|
| `data/excluded_org_final.csv` | LLM 精读结果（含 keep/exclude/downgrade 分类）|
| `data/excluded_master.csv` | **三源统一最终误收清单（4 篇）**——用户本地 ingest 用 |
| `scripts/build/merge_excluded_master.py` | 三源合并工具 |
| `scripts/ingest/ingest_excluded_master.py` | sqlite 注入工具（用户本地）|

## 五、待长期跟进

- **DRNH 卷误收清理**：DRNH 是国民政府内部档案，'民盟'指代明确，几乎无误收风险，本期不纳。但若未来加入"中国农工民主党""中国民主建国会"等同期民主党派关键词，可能产生新误收，需重做扫描。
- **FRUS 卷误收清理**：FRUS 是美方公开外交档，CDL/DCL 等表述明确，误收风险低；少数文档可能涉 Malayan DL / Korean DL，可作后续巡检题。
- **Wilson / Hoover 卷**：篇数少（24+2=26 篇），人工已逐篇审过，无需机器复核。
- **LLM 判断稳定性**：本次发现 LLM 二次扫描给出与第一次不同决定的现象，需引入"多次跑取一致结果"或"全文规则验证"作冗余机制——已写入 `scan_excluded_organizations.py` 改进版。

---

> 卡片集编辑准则：材料有出处，事实有依据；疑点有标注，判断有边界；线索能追踪，问题能深化；整理能入库，研究能成文。
