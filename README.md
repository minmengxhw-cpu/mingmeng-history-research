# 民盟历史文献研究库

> 1941—1950 中国大陆境外一手档案的系统整理、双语翻译与多源交叉印证。

## 一、项目简介

本平台是「民盟历史文献研究」项目组维护的内部研究工作台，聚焦中国民主同盟筹建、参政与重大转折时期的一手档案。

- **时段**：1941—1950
- **数据源**：7 大档案系统、900+ 篇核心档案（实际以本地 `data/research_index.sqlite` 动态统计为准）
- **功能**：抓取 / 清洗 / 翻译 / 全文索引 / 引用 / 事件梳理 / 研究卡片导出

### 当前数据规模（以数据库动态统计为准）

| 档案源 | 视角 |
|---|---|
| FRUS（美国对外关系文件集）| 美方驻华使馆与国务院 |
| CIA Records Reading Room | 美方情报系统 |
| Wilson Center Digital Archive | 苏联／东欧档案 |
| Hoover Institution Archives | 张君劢私人卷宗（现场调档）|
| HathiTrust ／ Internet Archive | 香港同代英文报刊 |
| 台北档案史料文物查询系统（DRNH）| 民国政府最高层视角（蒋档／国民政府档案／戴笠呈件）|
| **NewspaperSG（新加坡国家图书馆）** | **南洋华侨与英殖民地公共舆论场** |

各源精读入库篇数随研究进度变化，前台栏目页、首页、`/dashboard` 与 `/sourcebooks` 均按 `data/research_index.sqlite` 实时计算，不在 README 内静态写死。可在浏览器打开 `/dashboard` 查看当前数字。

## 二、收录原则

只收录 **中国大陆境外一手原始档案** 的原文与中译；不收录民盟官网、维基百科、新闻报道、研究论文等任何二手资料。前台展示遵循民盟史的学术分期与中性表述原则。

收录边界与误收防线：
- "China Democratic League / 中国民主同盟" 在 NewspaperSG / HathiTrust 等公开报刊源中容易与 **马来亚民主同盟（Malayan Democratic Union/League）**、**台湾民主自治同盟**、**Korean Democratic League**、**Indo-British Democratic League** 等同名／近名组织混淆。本平台 NewspaperSG 卷设置二次复核脚本（`scripts/build/review_newspapersg_exclusions.py`）逐篇判断 "是否真涉中国民盟"，输出 `data/newspapersg/exclusions.csv` 误收清单。
- 复核口径：China Democratic League 的新加坡／马来亚分部 → 保留；马来亚民主同盟独立政党 → 剔除或降级隐藏；只笼统提及 "Democratic League" 但上下文与中国民盟无关 → 剔除。

## 三、快速上手（Mac 本地运行）

### 1. 克隆代码

```bash
git clone https://github.com/minmengxhw-cpu/mingmeng-history-research.git
cd mingmeng-history-research
```

### 2. 安装依赖

```bash
pip3 install --user python-docx zhconv weasyprint
# 可选（如需重抓 PDF、生成研究包等）
pip3 install --user pypdf pillow openpyxl
```

### 3.（可选）下载台北档案的访客水印图

代码库**不含**台北档案系统的图像（约 660MB，受 `.gitignore` 排除）。如需在详情页看到缩略图墙，请在 Mac 上跑一次下载脚本：

```bash
python3 scripts/download_drnh_images.py 0 --only-a
# 大约 30-50 分钟，下载 A 档 ~280 个文档 ~870 页 JPG 到 data/drnh_images/
```

不下载也不影响正常使用，只是详情页没有缩略图预览。

### 4. NewspaperSG 译文入库（首次或更新译文后）

`data/newspapersg/zh_translations.csv` 含 93 篇正文中译（DeepSeek-v4-flash 精译）。入库到本地 sqlite：

```bash
# 先确保已 ingest 过 NewspaperSG 原始 OCR
python3 scripts/ingest/ingest_newspapersg_meng.py
# 注入译文 + 同步 title_translations.csv
python3 scripts/ingest/ingest_newspapersg_translations_from_csv.py
# 重建 FTS5 trigram 索引
python3 scripts/oneshot/rebuild_fts_trigram.py
```

### 5. 启动本地阅读器

```bash
python3 app.py
```

浏览器打开 <http://127.0.0.1:8765>。

### 6. 常用入口

| 路径 | 用途 |
|---|---|
| `/` | 首页 |
| `/sources/<plat>` | 单个档案源的栏目页（`frus` / `cia` / `wilson` / `hoover` / `hathitrust` / `drnh` / `newspapersg`）|
| `/docs?platform=<plat>` | 单平台全文档列表 |
| `/doc/<doc_key>` | 单条档案详情 |
| `/search?q=<词>&platform=<plat>` | 全文检索（含繁简自动展开、trigram 中文分词）|
| `/people` `/topics` `/places` `/organizations` | 人物 / 专题 / 地点 / 机构索引 |
| `/events` | 事件线索 |
| `/cite/<page_id>` | 摘录卡片（短引文 + GB/T 7714/BibTeX/Chicago）|
| `/papers` | 七源对照研究论文 |
| `/sourcebooks` | 各源史料长编 PDF 与研究资料包 ZIP |
| `/public` | 公开展示版（隐藏内部校订入口）|
| `/dashboard` | 研究进度仪表盘（动态统计）|

## 四、项目结构

```
mingmeng-history-research/
├── app.py                       # 单文件 Web 应用（HTTP server + 路由 + 渲染）
├── key_events.py                # 关键事件骨架（境外档案驱动）
├── person_archive.py            # 人物索引基础数据
├── README.md
├── data/
│   ├── research_index.sqlite    # 核心数据库（本地文件，不进 git；备份走 data/backups/）
│   ├── frus_meng/               # FRUS 原始抓取
│   ├── cia_meng/                # CIA 原始抓取
│   ├── wilson_center/           # Wilson 镜像
│   ├── hoover/                  # 胡佛档案现场拍摄
│   ├── hathitrust_ia/           # 港媒 OCR
│   ├── drnh_probe/              # 台北档案目录元数据
│   ├── drnh_images/             # 访客水印图（不进 git，本地下载）
│   ├── newspapersg/             # 新加坡国家图书馆报刊 OCR + 译文 + 误收清单
│   └── translation_glossary.csv # 译名标准化
├── docs/                        # 内部研究文档 + 探勘报告
│   ├── _*.md                    # 内部参考（以 _ 开头）
│   ├── _seven-source-overview-paper-v2.md  # 七源对照总论 v2（NewspaperSG 纳入框架）
│   ├── _overview-paper.md       # 原六源对照总论（历史版本，保留）
│   ├── _evidence-card-*.md      # 多源对位证据卡片
│   ├── drnh/                    # 台北档案调档申请
│   ├── sinica/                  # 近史所调档申请
│   └── exploration/             # 各档案源探勘报告
├── scripts/                     # 数据处理脚本
│   ├── probe/                   # 探勘类
│   ├── ingest/                  # 入库类
│   ├── translate/               # 翻译类
│   ├── build/                   # 报告/包生成 + 质量复核
│   ├── oneshot/                 # 一次性任务（含史料长编生成、FTS 重建）
│   └── export/                  # 论文 PDF 渲染
└── workspace/                   # 研究产出工作目录（导出 docx 等）
```

## 五、典型数据更新流程

```bash
# 抓取 FRUS 新卷
python3 scripts/crawl_frus_meng.py

# 重建研究索引（含 FTS5 trigram）
python3 scripts/build/build_research_index.py
python3 scripts/oneshot/rebuild_fts_trigram.py

# 入库新源（以台北档案史料为例）
python3 scripts/probe/probe_drnh_archives.py
python3 scripts/build/classify_drnh_hits.py
python3 scripts/ingest/ingest_drnh.py
python3 scripts/oneshot/rebuild_fts_trigram.py

# NewspaperSG 精翻 + 误收复核 + 入库（一次性流程）
python3 scripts/translate/translate_newspapersg_deepseek.py          # 跑 93 篇正文精翻
python3 scripts/build/review_newspapersg_exclusions.py               # 二次复核误收
python3 scripts/ingest/ingest_newspapersg_translations_from_csv.py   # 注入 sqlite
python3 scripts/oneshot/rebuild_fts_trigram.py

# 翻译批次导出与回填
python3 scripts/export_translation_batches.py --max-chars 50000 \
        --out-dir data/translation_batches_core
python3 scripts/lib/import_translations_csv.py data/translation_batches_core/batch_001.csv
```

## 六、研究输出

| 输出位置 | 内容 |
|---|---|
| `docs/_*.md` | 内部研究参考（探勘报告、人物档案、AI 协作说明、七源对照论文 v2 等）|
| `output/sourcebooks/` | 各源史料长编 PDF（按时间线英文/旧字原文 + 现代汉语对照）|
| `output/pdf/` | 综述论文 PDF |
| `output/research_packages/` | 研究资料包 ZIP（长编 PDF + 综述 PDF + 证据卡片 + 数据 CSV）|
| `exports/` | 学术研究专集 docx（不进 git）|
| `workspace/` | 临时工作产物（白皮书、问卷、调研报告等）|

## 七、技术备忘

- **后端**：Python 3.10+ 标准库（`http.server` + `sqlite3`）+ python-docx + zhconv + weasyprint
- **前端字体**：思源宋体 Noto Serif SC 自托管（`static/fonts/` 101 个 woff2，unicode-range 子集化按需加载）
- **全文检索**：SQLite FTS5 trigram tokenizer（中文友好），含繁简自动展开和 LIKE 兜底
- **引文**：7 大档案源各自的 GB/T 7714-2015 / BibTeX / Chicago 模板（NewspaperSG 引用模板支持 NLB 原文链接回溯）
- **数据库**：`data/research_index.sqlite`，主表 `documents` / `pages` / `translations` / `document_classifications` / `translation_fts`
- **URL UTF-8**：`do_GET()` 内对 `self.path` 做 latin-1 → UTF-8 重解，修中文 URL 乱码

## 八、引用规范

引用本平台研究成果，请按 GB/T 7714-2015 标准著录档案来源信息，并标注本平台为整理者。各档案的学术引用格式可在档案详情页一键复制（含 GB/T 7714 / BibTeX / Chicago 三种格式）。

NewspaperSG 引用须包含 NLB 原文链接，证据卡片中每条 NewspaperSG 引用末尾自动附加 `[(NLB 原文)](https://eresources.nlb.gov.sg/...)`。

## 九、许可

代码部分采用 **MIT License**（见 `LICENSE`）。

数据部分（双语翻译与研究编排）采用 **CC BY-NC 4.0**（署名 - 非商业），原始档案的版权归各档案馆所属机构所有，本平台仅作研究编排和翻译整理。

学术使用请按各档案源的引用规范注明出处。
