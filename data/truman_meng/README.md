# Truman Library 卷 · 卷级 README

> 民盟历史文献研究库 · 第 7 个数据源
> 2026-06-02 阶段 1 侦察 + 候选清单完成

## 一、源简介

**Harry S. Truman Presidential Library & Museum**（杜鲁门总统图书馆，密苏里州独立城）
- 主域名：`https://www.trumanlibrary.gov/`
- 馆藏：杜鲁门 1945-1953 任期所有总统档（PSF 总统秘书档、Official Files、Korean War Files 等）
- 与 FRUS 的**关键差异**：
  - FRUS = 大使馆 ↔ 国务卿往来电报（State Dept 内部）
  - Truman = 杜鲁门收到的**白宫层级**备忘录 + Acheson / Marshall / Lovett 国务卿私档
  - **完全互补，非重复源**

## 二、技术通路（关键发现，2026-06-02 实测）

Truman 页面是 Drupal 10 server-side rendered，**curl 直接拿**：
- **主题集页面**（5 个中国相关）：`/library/online-collections/<slug>`
  - `marshall-china`（马歇尔使华 1945-1947，50 篇）
  - `Korea-Chinese`（朝鲜战争中的中国，91 篇）
  - `korea-prelude`（朝战前奏 1945-1950，71 篇）
  - `ideological-foundations-of-cold-war`（冷战意识形态基础，28 篇）
  - `atomic-weapons`（原子武器涉中部分，86 篇）
- 每条文档列表项：`<a href="https://catalog.archives.gov/id/<NAID>">完整标题</a>, <日期> (NAID: <NAID>)`
- 文档**单篇详情**跳到 `catalog.archives.gov/id/<NAID>`（NARA 全国档案馆 SPA）

### NARA 真实 API（隐藏路径）

`catalog.archives.gov` 是 React SPA，但内部走 ElasticSearch proxy：

```
https://catalog.archives.gov/proxy/v3/records/search?naId_is=<NAID>&limit=1
```

返回 ES 风格 JSON，含：
- `record.title`（完整标题）
- `record.productionDates[]`（年月日）
- `record.physicalOccurrences[]`（实物存储位置 + 联系信息）
- `record.ancestors[]`（所属 collection / series / file unit 层级）
- `record.digitalObjects[]`（影像列表，每张含 `objectUrl` 指向 S3）

### 影像 S3 直链

```
https://s3.amazonaws.com/NARAprodstorage/lz/presidential-libraries/truman/<group>/<series>/<file_unit>/<filename>.tif  # 高清 TIFF
https://s3.amazonaws.com/NARAprodstorage/lz/.../<filename>.jpg  # access JPEG 派生版
```

- TIFF 单页约 10-15 MB（300 dpi 真扫描档）
- JPEG 单页约 200-800 KB（用于浏览）
- **无 OCR 文本**（NARA 对 1940s Truman 档未做 OCR）
- 入库必须自跑 OCR（pytesseract / tesseract）方能拿英文全文做 LLM 精读

## 三、候选清单（5 集去重）

| 主题集 | 单篇文档数 | 民盟史核心相关度 |
|---|---:|---|
| marshall-china | 50 | ⭐⭐⭐⭐⭐ 1945-1947 国共调停 + PCC + 民盟核心期 |
| korea-prelude | 71 | ⭐⭐⭐ 1945-1950 含 1947-10 民盟非法化前后期 |
| Korea-Chinese | 91 | ⭐⭐ 1950 朝战中的中国，含 1950-12 民主党派 |
| ideological-foundations-of-cold-war | 28 | ⭐⭐ 含 1945-1946 对苏对华政策 |
| atomic-weapons | 86 | ⭐ 仅极少数涉中 |
| **合计去重** | **326** | — |

候选清单 CSV：`reconnaissance/truman_candidates_326.csv`（含完整 NAID + 标题 + 日期 + archives.gov 详情链接）

## 四、当前阶段状态

| 项 | 状态 |
|---|:-:|
| 侦察入口 + 主题集识别 | ✅ |
| 5 集 326 篇候选完整清单 | ✅ |
| API 通路实测（NAID → metadata + S3 影像 URL） | ✅ |
| 1 篇真实下载验证（NAID 290015466 TIFF/JPEG 都通） | ✅ |
| 326 篇完整 metadata + digitalObjects 列表入库 | ✅ collections/all_326_metadata.json |
| 影像批量下载（marshall-china 50 篇优先）| ⏳ 待开干 |
| OCR 处理（pytesseract）| ⏳ 待开干 |
| LLM 精读 + 民盟相关度筛 | ⏳ 待开干 |
| 翻译批次 + 入前台 | ⏳ 待开干 |
| Truman 卷论文 v1 | ⏳ 待开干 |

## 五、估算（marshall-china 50 篇首批）

| 步骤 | 工作量 | 输出 |
|---|---|---|
| 影像下载（JPEG 派生版，约 50 篇 × 平均 12 页 × 400 KB ≈ 250 MB）| ~30 min | local `images/` |
| OCR（pytesseract，CPU 单线程约 15-20s/页 × 600 页 ≈ 2-3 hr）| 2-3 hr 后台 | `ocr/` 英文全文 |
| LLM 精读分类（DeepSeek，5 并发，约 50 篇 × 30s ≈ 25 min） | ~30 min | 民盟相关度评分 |
| 高相关篇翻译（中英对照，按 CIA 卷套路）| ~1-2 hr | 翻译批次 |
| Truman 卷 v1 论文（"1945-1947 白宫视角下的国共调停与民盟" 6000-8000 字）| ~2-3 hr | docs/_truman-paper-v1.md |

**首批 marshall-china 50 篇全流程预估：1-2 天工作量**（含夜间 OCR 跑批）

## 六、关键学术价值预判

`marshall-china` 集 50 篇全部是 **杜鲁门 ↔ 马歇尔特使** 直接通信，时间 1945-12 至 1947-01——
**正好覆盖**民盟参与重庆政协（1946-01）、马歇尔三人小组停战令、1946-07 国民党挑起内战、1947-03 民盟代表撤离南京 等关键节点。

预期能补强论文 v2 的：
- §3.1 政协前后的民盟（FRUS 视角 → Truman/Marshall 白宫视角）
- §3.2 民盟与马歇尔调停（迄今论文 v2 主要靠 FRUS 1946v09-v10，Truman 视角缺失）
- §3.3 1947-03 民盟代表撤离南京（白宫如何看待）

---

> 卡片集编辑准则：材料有出处，事实有依据；疑点有标注，判断有边界；线索能追踪，问题能深化；整理能入库，研究能成文。
