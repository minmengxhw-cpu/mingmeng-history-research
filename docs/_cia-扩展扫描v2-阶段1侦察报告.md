# CIA 卷扩展扫描 v2 · 阶段 1 侦察报告

> 民盟历史文献研究库 · CIA 卷查漏补缺 第 2 轮 · 2026-06-03
> 在 CIA 漏抓 27 篇阶段 1（commit e833398）之外的关键词扩展扫描

## 一、方法

原有 CIA 卷 62 篇主要靠 "China Democratic League" 单关键词命中。本轮扩展用 19 个新关键词：

### 1.1 民盟核心人物威氏拼音（11 个）
- Shih Liang（史良）、Tao Hsing-chih（陶行知）、Ma Yin-chu（马寅初）、Huang Yen-pei（黄炎培）、Hu Yu-chih（胡愈之）
- Tu Pin-cheng（杜斌丞）、Li Kung-pu（李公朴）、Wen I-to（闻一多）、Chang Tung-sun（张东荪）、Chu Yun-shan（储安平）
- Kao Ch'ung-min（高崇民，民盟东北总支部）

### 1.2 概念 / 事件关键词（8 个）
- Federation of Chinese Democratic Parties（中国民主政团同盟，民盟前身）
- "third force" China / "third party" Chiang Kai-shek
- "Political Consultative" 1946（政协）
- "minor parties" China / "Democratic Parties" Peiping
- Coalition Government China 1946 / Chinese minor parties Communist

## 二、结果

### 2.1 命中分布
- 总候选：200 个新 identifier（已去除已知 80 个：62 主集 + 27 漏抓 + 部分重叠）
- 1941-1957 时段窗口内：**126 个候选**
- 按年分布：

| 年份 | 候选数 | 民盟史关联 |
|---|---:|---|
| 1946 | 2 | 政协 + 国共内战初期 |
| 1947 | 4 | 1947-10 民盟非法化前夕 |
| 1948 | 10 | 1948-01 香港临三中全会重建 |
| 1949 | 6 | 新政协筹备 + 民盟参加 |
| 1950 | 16 | 民盟参加新政权 + 朝战 |
| 1951 | **26** | 思想改造 / 抗美援朝 |
| 1952 | 14 | 三反五反 / 民主党派整风 |
| 1953-1957 | 48 | 反右前夕 / 双百 |

### 2.2 强信号 vs 弱信号

| 关键词类型 | 命中含义 | 数量 |
|---|---|---:|
| 民盟核心人物威氏拼音（强信号）| 上下文必涉民盟 | 9 篇（Shih Liang +3、Hu Yu-chih +6）|
| 概念关键词（弱信号）| 可能涉民盟，但泛指国共博弈也命中 | 117 篇 |

### 2.3 1946-1949 关键期 22 候选清单（详见 CSV）

主要分布：
- "minor parties" China：2 篇
- "third force" China：3 篇
- Coalition Government China 1946：14 篇
- "third party" Chiang Kai-shek：1 篇
- Federation of Chinese Democratic Parties：2 篇

## 三、阶段 2 工作量预估

| 步骤 | 工作量 |
|---|---|
| 下 126 候选的 djvu.txt OCR（每篇约 5-15 KB）| 5-10 分钟 |
| LLM 精读判民盟相关度（DeepSeek，5 并发）| 5-8 分钟 |
| 真涉民盟篇下载 metadata + PDF 入库 | 10-15 分钟 |
| 写补全报告 + commit | 5 分钟 |
| **合计** | **30-40 分钟** |

## 四、当前阻塞

archive.org 在本侦察期间持续抽风（SSL 证书 hostname mismatch + connection timeout），与之前 CIA 漏抓 27 篇阶段 2 时遇到的问题相同。

阶段 2 脚本 `/tmp/cia_ext_llm.py` 已就绪，含 OCR 缓存（`/tmp/cia-ext-ocr/`），archive.org 恢复后单次重跑即可完成全部 126 篇精读。

## 五、初步学术判断（基于关键词命中分布）

1. **强信号 9 篇** 几乎必涉民盟（Shih Liang / Hu Yu-chih 是民盟核心人物，CIA 档中提及他们的篇 100% 涉民盟）
2. **1946-1949 关键期 22 候选** 中估计真涉民盟约 **8-15 篇**（"Coalition Government" / "third force" 等概念命中率约 35-65%）
3. **1950-1957 时段 104 候选** 主体可能是"民主党派整体"评估，民盟单独命中预计 **20-40 篇**
4. **预期补 CIA 卷 30-60 篇**（实际数取决于 LLM 精读结果）

## 六、阶段 2 待办

- ✅ 2026-06-05 已完成 1946-1949 关键期 22 篇 OCR 下载与阶段 2 复核，详见 `docs/_cia-扩展扫描v2-阶段2关键期复核报告.md`
- ⏳ 真涉民盟篇下载 PDF + metadata 入库到 `data/cia_meng/extended_batch2/`
- ⏳ 写 CIA 卷 v2.2 论文修订（含本轮 30-60 篇新增）

## 七、已落产物

| 文件 | 内容 |
|---|---|
| `scripts/probe/probe_cia_extended_v2.py` | 19 关键词扫描器 |
| `data/cia_extended_v2_candidates.csv` | **126 篇候选清单**（identifier / title / date / matched_keywords / ia_detail_url）|
| `scripts/build/cia_extended_v2_llm_review.py` | OCR + 精读复核脚本；有 API key 时走 LLM，无 API key 时走本地规则复核 |
| `data/cia_extended_v2_llm_review.csv` | 1946-1949 关键期 22 篇阶段 2 复核结果 |
| `data/cia_extended_v2_ocr_cache/` | 1946-1949 关键期 22 篇 OCR 缓存 |
| `docs/_cia-扩展扫描v2-阶段1侦察报告.md` | 本报告 |
| `docs/_cia-扩展扫描v2-阶段2关键期复核报告.md` | 阶段 2 关键期复核报告 |

---

> 卡片集编辑准则：材料有出处，事实有依据；疑点有标注，判断有边界；线索能追踪，问题能深化；整理能入库，研究能成文。
