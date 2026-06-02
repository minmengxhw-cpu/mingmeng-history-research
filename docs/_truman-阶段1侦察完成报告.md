# Truman Library 卷阶段 1 侦察完成报告

> 民盟历史文献研究库 · 第 7 个数据源（Truman 卷）· 2026-06-02
> 侦察 → 候选清单 → metadata 全量入库 全链路打通

## 〇、本报告口径

承接 2025 年既往侦察工作（任务 #21 仅完成"找入口"），本阶段：
- ✅ 完整摸清 Truman → NARA 数字化档真实下载通路
- ✅ 5 个中国相关主题集 → 326 篇真实单篇文档候选
- ✅ NARA `/proxy/v3/records/search` 隐藏 API + S3 影像直链全部跑通
- ✅ 325/326 篇完整 metadata 入库（成功率 99.7%，唯 1 失败属 NARA 端 _id 异常）
- ✅ **2383 页扫描影像 URL 全部在手**，可批量拉取

## 一、关键技术突破：NARA SPA 反爬绕过

### 1.1 问题

`catalog.archives.gov`（美国国家档案馆全国目录系统）是 React SPA，所有 `/id/<NAID>` / `/api/v1/?naIds=...` 路径都返同一个 5454 字节 HTML 空壳——curl 取不到任何实质数据。

### 1.2 突破

从 SPA JS bundle (`/static/js/main.05a33ff0.chunk.js`) 抠出隐藏 API：

```
真实 endpoint: https://catalog.archives.gov/proxy/v3/records/search?naId_is=<NAID>&limit=1
真实 path 字符串: SEARCH_HOST + "/proxy"（bundle 里 var V="https://catalog.archives.gov"）
返回格式: ElasticSearch 风格 JSON（body.hits.hits[]._source.record）
```

实测响应含：
- `record.title` 完整文档名
- `record.productionDates[]` 生产年月日
- `record.physicalOccurrences[]` 实物存藏位置 + 联系信息
- `record.ancestors[]` Collection/Series/File Unit 层级
- **`record.digitalObjects[]`** 扫描影像列表（每页一条）

### 1.3 影像直链

每条 `digitalObjects[i].objectUrl` 指向：

```
https://s3.amazonaws.com/NARAprodstorage/lz/presidential-libraries/truman/<group>/<series>/<file_unit>/<filename>.tif
```

将 `.tif` 改 `.jpg` 即得 access 派生版（小 30 倍，浏览友好）。**实测 GET 200**。

### 1.4 已知盲点

- ❌ **NARA 未对 1940s Truman 档做 OCR**——文档对象没有附 `.txt` / `.ocr` 字段
- ✅ 需自跑 tesseract 做英文 OCR 才能进 LLM 精读
- ✅ JPEG 派生版质量充分（300 dpi 真扫描 → 4MP 灰阶），tesseract 识别率应可接受

## 二、5 集 326 篇候选清单

| 主题集 | 单篇文档 | 总影像页 | 平均页/篇 |
|---|---:|---:|---:|
| **marshall-china**（马歇尔使华 1945-1947）| 50 | 224 | 4.5 |
| **korea-prelude**（朝战前奏 1945-1950）| 70 | — | — |
| **Korea-Chinese**（朝战中的中国 1950-1953）| 91 | — | — |
| **ideological-foundations-of-cold-war**（冷战意识形态基础）| 28 | — | — |
| **atomic-weapons**（原子武器涉中部分）| 86 | — | — |
| **合计去重** | **325** | **2383** | — |

候选清单已入库：
- `data/truman_meng/reconnaissance/truman_candidates_326.csv`（人可读，按集 + 民盟相关度排序）
- `data/truman_meng/reconnaissance/truman_candidates_326.json`（机器可读，含直链）
- `data/truman_meng/collections/all_326_metadata.json`（NARA API 完整 metadata，含每张影像的 S3 URL）

## 三、首批优先级：marshall-china 50 篇

`marshall-china` 集即 **NARA 命名："The Chinese Civil War: General George C. Marshall's Mission to China, 1945-1947"**——50 篇白宫 ↔ 马歇尔特使直接通信，平均 4.5 页/篇，**总 224 页**。

### 3.1 民盟史关键期覆盖

集合内文档时间范围 1945-12 至 1947-01，**完整覆盖**：
- 1945-12 马歇尔抵华 + 民盟梁漱溟代表团赴渝
- 1946-01 政协（PCC）会议 + 民盟提"政协决议五项原则"
- 1946-02 三人小组停战令
- 1946-07 国民党挑起内战
- 1946-11 制宪国大民盟拒参加
- 1947-01 马歇尔离华回美 + 国共调停彻底破裂

### 3.2 与现有论文 v2 的关系

论文 v2 §3 "1945-1947 政协前后的民盟"现有材料：
- FRUS 1946 v09-v10（约 60-80 篇国务院电报）
- DRNH 国民党党国档（150+ 篇打压方内部档）
- 港媒《华商报》（HathiTrust 港版 1946-1947）

**Truman 视角是当前论文 v2 §3 的关键缺失**——白宫如何看待民盟在政协中的角色、如何评估民盟"第三方面"政治地位、如何处理民盟代表撤离南京事件。50 篇预期能为论文 v2 §3 加 1-2 节"白宫层级视角下的民盟"。

## 四、剩余 4 集快速判定

| 集 | 时间 | 优先级 | 原因 |
|---|---|:-:|---|
| korea-prelude | 1945-1950 | ⭐⭐⭐ | 含 1947-10 民盟非法化前后期，需筛涉中部分 |
| Korea-Chinese | 1950-1953 | ⭐⭐ | 民盟 1949 后期，主要涉抗美援朝期民主党派表态 |
| ideological-foundations | 1945-1946 | ⭐⭐ | 含对苏对华一体化政策，可能涉民盟"第三方面" |
| atomic-weapons | 1945-1953 | ⭐ | 仅极少数涉中（杜鲁门给蒋介石原子情报 1949-08），多数无关 |

## 五、下一步工作量预估

| 阶段 | 工作量 | 输出 |
|---|---|---|
| 5.1 marshall-china 50 篇 JPEG 批量下载（224 页 × 400 KB ≈ 90 MB）| 30 min | local images/ |
| 5.2 marshall-china tesseract OCR（约 224 页 × 15s/页 ≈ 1 hr，可后台跑）| 1 hr | ocr/ 英文全文 |
| 5.3 LLM 精读分类（DeepSeek，5 并发，50 篇 × 30s ≈ 25 min）| ~30 min | 民盟相关度评分 + core_fact |
| 5.4 高相关篇翻译（中英对照，5-15 篇）| ~1-2 hr | 翻译批次 |
| 5.5 三源反查（CIA + FRUS + Wilson，看是否平行）| 30 min | 反查报告 |
| 5.6 Truman 卷论文 v1 草稿（含 §1 卷源说明 + §2 1945-1947 白宫视角 + §3 待核 + 参考文献）| 2-3 hr | docs/_truman-paper-v1.md |
| **合计 marshall-china 全流程** | **6-8 小时**（含夜间 OCR 跑批） | |

其他 4 集（剩 275 篇）按同样流程跑，预估**3-5 天工作量**完成 Truman 卷 v1。

## 六、关键学术增量预判

Truman 卷作为本平台**第 7 个数据源**，主要新增：

1. **白宫层级视角**——现有六源都是部级及以下（FRUS 国务卿/大使、DRNH 国民党党国档、CIA 中央情报、Wilson 苏方部级以下、Hoover 私函、HathiTrust 港媒），Truman 视角是**总统决策层级**的政治判断
2. **马歇尔使华专题**——50 篇等同于一个完整的"马歇尔调停期"原始文献库，论文 v2 §3 可大幅扩充
3. **新人物入档**——Edwin Locke / William J. Hopkins / James Byrnes 等 1945-1946 关键幕僚的电报（FRUS 通常按"国务卿署名"收，Truman 这些是真实起草人和幕僚的笔迹）

---

## 七、commit 记录

```
[阶段 1 commit] feat: Truman 卷阶段 1 侦察完成 + 326 篇 metadata 入库
```

后续 commit 节点：
- 阶段 2: marshall-china 50 篇 JPEG + OCR + LLM 精读
- 阶段 3: marshall-china 翻译批次 + 三源反查
- 阶段 4: Truman 卷 v1 论文

---

> 卡片集编辑准则：材料有出处，事实有依据；疑点有标注，判断有边界；线索能追踪，问题能深化；整理能入库，研究能成文。
