# 民盟历史文献研究库

> 1941—1950 中国大陆境外一手档案的系统整理、双语翻译与多源交叉印证。

## 一、项目简介

本平台是「民盟历史文献研究」项目组维护的内部研究工作台，聚焦中国民主同盟筹建、参政与重大转折时期的一手档案。

- **时段**：1941—1950
- **数据源**：6 大档案系统、800+ 篇核心档案
- **功能**：抓取 / 清洗 / 翻译 / 全文索引 / 引用 / 事件梳理 / 研究卡片导出

### 当前数据规模

| 档案源 | 篇数 | 视角 |
|---|---:|---|
| FRUS（美国对外关系文件集）| 299 | 美方驻华使馆与国务院 |
| CIA Records Reading Room | 102 | 美方情报系统 |
| Wilson Center Digital Archive | 24 | 苏联/东欧档案 |
| Hoover Institution Archives | 2 | 张君劢私人卷宗（现场调档） |
| HathiTrust / Internet Archive | 54 | 香港同代英文报刊 |
| 台北档案史料文物查询系统 | 364 | 民国政府最高层视角（蒋档/国民政府档案/戴笠呈件）|

实际数字以 `data/research_index.sqlite` 为准；详情页与平台栏目页所显示的统计为运行时动态计算。

## 二、收录原则

只收录 **中国大陆境外一手原始档案** 的原文与中译；不收录民盟官网、维基百科、新闻报道、研究论文等任何二手资料。前台展示遵循民盟史的学术分期与中性表述原则。

## 三、快速上手（Mac 本地运行）

### 1. 克隆代码

```bash
git clone https://github.com/minmengxhw-cpu/mingmeng-history-research.git
cd mingmeng-history-research
```

### 2. 安装依赖

```bash
pip3 install --user python-docx zhconv
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

### 4. 启动本地阅读器

```bash
python3 app.py
```

浏览器打开 <http://127.0.0.1:8765>。

### 5. 常用入口

| 路径 | 用途 |
|---|---|
| `/` | 首页 |
| `/sources/<plat>` | 单个档案源的栏目页（`frus` / `cia` / `wilson` / `hoover` / `hathitrust` / `drnh`）|
| `/docs?platform=<plat>` | 单平台全文档列表 |
| `/doc/<doc_key>` | 单条档案详情 |
| `/search?q=<词>&platform=<plat>` | 全文检索（含繁简自动展开、trigram 中文分词）|
| `/people` `/topics` `/places` `/organizations` | 人物 / 专题 / 地点 / 机构索引 |
| `/events` | 事件线索 |
| `/cite/<page_id>` | 摘录卡片（短引文 + GB/T 7714/BibTeX/Chicago）|
| `/dashboard` | 研究进度仪表盘 |

## 四、项目结构

```
mingmeng-history-research/
├── app.py                       # 单文件 Web 应用（HTTP server + 路由 + 渲染）
├── key_events.py                # 关键事件骨架（境外档案驱动）
├── person_archive.py            # 人物索引基础数据
├── README.md
├── data/
│   ├── research_index.sqlite    # 核心数据库（本地文件，不进 git；备份走 data/backups/ 或单独同步）
│   ├── frus_meng/               # FRUS 原始抓取（HTML/TXT 快照）
│   ├── cia_meng/                # CIA 原始抓取
│   ├── wilson_center/           # Wilson 镜像
│   ├── hoover/                  # 胡佛档案现场拍摄
│   ├── hathitrust_ia/           # 港媒 OCR 文本
│   ├── drnh_probe/              # 台北档案目录元数据
│   ├── drnh_images/             # 访客水印图（不进 git，本地下载）
│   └── translation_glossary.csv # 译名标准化
├── docs/                        # 内部研究文档 + 探勘报告
│   ├── _*.md                    # 内部参考（以 _ 开头）
│   ├── drnh/                    # 台北档案调档申请等
│   ├── sinica/                  # 近史所调档申请（历史档案）
│   └── exploration/             # 各档案源探勘报告
├── scripts/                     # 数据处理脚本
│   ├── probe_*.py               # 探勘类
│   ├── ingest_*.py              # 入库类
│   ├── translate_*.py           # 翻译类
│   ├── build_*.py               # 报告/包生成类
│   └── ...
└── workspace/                   # 研究产出工作目录（导出 docx 等）
```

## 五、典型数据更新流程

```bash
# 抓取 FRUS 新卷
python3 scripts/crawl_frus_meng.py

# 重建研究索引（含 FTS5 trigram）
python3 scripts/build_research_index.py
python3 scripts/rebuild_fts_trigram.py  # 必要时

# 入库新源（以台北档案史料为例）
python3 scripts/probe_drnh_archives.py
python3 scripts/classify_drnh_hits.py
python3 scripts/ingest_drnh.py
python3 scripts/rebuild_fts_trigram.py

# 数据严格复核
python3 scripts/reclassify_drnh_strict.py

# 翻译批次导出与回填
python3 scripts/export_translation_batches.py --max-chars 50000 \
        --out-dir data/translation_batches_core
python3 scripts/import_translations_csv.py data/translation_batches_core/batch_001.csv
```

## 六、研究输出

| 输出位置 | 内容 |
|---|---|
| `docs/_*.md` | 内部研究参考（探勘报告、人物档案、AI 协作说明等）|
| `exports/` | 研究包、事件卡片、专集 docx（不进 git）|
| `workspace/` | 临时工作产物（白皮书、问卷、调研报告等）|

## 七、技术备忘

- **后端**：Python 3.10+ 标准库（`http.server` + `sqlite3`）+ python-docx + zhconv
- **全文检索**：SQLite FTS5 trigram tokenizer（中文友好），含繁简自动展开和 LIKE 兜底
- **引文**：6 大档案源各自的 GB/T 7714-2015 / BibTeX / Chicago 模板
- **数据库**：`data/research_index.sqlite`，主表 `documents` / `pages` / `translations` / `document_classifications`
- **URL UTF-8**：`do_GET()` 内对 `self.path` 做 latin-1 → UTF-8 重解，修中文 URL 乱码

## 八、引用规范

引用本平台研究成果，请按 GB/T 7714-2015 标准著录档案来源信息，并标注本平台为整理者。各档案的学术引用格式可在档案详情页一键复制（含 GB/T 7714 / BibTeX / Chicago 三种格式）。

## 九、许可

代码部分采用 **MIT License**（见 `LICENSE`）。

数据部分（双语翻译与研究编排）采用 **CC BY-NC 4.0**（署名 - 非商业），原始档案的版权归各档案馆所属机构所有，本平台仅作研究编排和翻译整理。

学术使用请按各档案源的引用规范注明出处。
