# NARA / NSArchive / HathiTrust 下一数据源探勘报告

日期：2026-05-17

## 一、结论

下一阶段建议采用“两条线”：

1. **优先落地：HathiTrust / Internet Archive**
   - 目标不是泛收二手研究，而是先抓美国政府公开出版物、公开档案汇编、当时报刊和可全文下载的 primary/near-primary 材料。
   - 第一批建议从 1949 年《United States Relations with China, With Special Reference to the Period 1944-1949》（即 “China White Paper”）及其相关政府出版物开始。
   - 理由：全文可得性最高，OCR/页码引用链路最容易复用现有 PDF/OCR 入库模块。

2. **并行探勘：NARA**
   - 重点不是一次性抓全 RG 59，而是建立“FRUS 条目 -> NARA 原始档案定位号 -> NARA Catalog/现场调卷线索”的索引。
   - NARA Catalog API 仍可用，但当前官方接口需要 API key；大部分 RG 59 中国 decimal file 仍未数字化，不能把它当作短期批量全文来源。

NSArchive 暂不作为下一主数据源：

- 它是高质量 FOIA 档案库，页面/PDF稳定，适合后续做专题扩展。
- 但对中国民主同盟 1941-1950 年主轴命中密度低，主要价值在中美关系、冷战后期、尼克松/卡特/中苏等专题。

## 二、数据源对比

| 数据源 | 在线全文 | 民盟直接密度 | 工程难度 | 学术价值 | 建议 |
|---|---:|---:|---:|---:|---|
| HathiTrust / IA | 高 | 中 | 低-中 | 中-高 | 下一批优先落地 |
| NARA | 低-中 | 高潜力 | 高 | 极高 | 做定位索引，暂不承诺全量抓取 |
| NSArchive | 高 | 低 | 低 | 中-高 | 后续专题库，不做当前主线 |

## 三、NARA 探勘

### 可用入口

- NARA Catalog: https://catalog.archives.gov/
- NARA Catalog API 文档: https://catalog.archives.gov/api/v2/

### 判断

NARA 是 FRUS 的上游来源，理论价值最高；尤其是 RG 59 国务院 decimal file、RG 226 OSS、RG 84 外交岗位档案等。但当前最大问题不是网页抓取，而是**数字化覆盖率**：

- FRUS 已经把最核心外交电报做了精选。
- NARA 原始档案中会有更多未收入 FRUS 的附件、地方领馆报告、来往函、电报草稿。
- 但大量材料需要 onsite 调阅或缩微胶片，不适合作为马上批量全文入库对象。

### 建议任务

1. 为每篇 FRUS 核心文献增加 `nara_locator` 字段或外部索引表。
2. 从 FRUS 引文、document header、decimal file 编号中抽取 NARA 定位线索。
3. 申请 NARA API key 后，做 catalog 级别检索，不先承诺 PDF 全文。

## 四、NSArchive 探勘

### 可用入口

- National Security Archive: https://nsarchive.gwu.edu/
- Digital National Security Archive collections: https://nsarchive.gwu.edu/dnsa-collections

### 判断

NSArchive 的优势是：

- 已整理专题；
- PDF/扫描件和元数据稳定；
- 引用格式清楚；
- FOIA 文件学术可信度高。

但本项目现阶段关键词（China Democratic League / Democratic League / Chinese Democratic League / third force）在 NSArchive 的直接命中不强。它更适合后续做：

- 中美关系专题；
- 中苏关系专题；
- 1949 后美国对中共/台湾/第三世界政策；
- 与民盟人物晚期政治处境相关的旁证。

### 建议任务

暂不建主库；后续按专题抓取 NSArchive briefing book 中的中国相关 declassified PDFs。

## 五、HathiTrust / Internet Archive 探勘

### 可用入口

- HathiTrust: https://www.hathitrust.org/
- HathiTrust full-text search: https://babel.hathitrust.org/
- Internet Archive: https://archive.org/

### 判断

HathiTrust / IA 最大优势是“马上能形成成果”：

- 可抓公开出版物 PDF / OCR；
- 页码引用容易；
- 与现有 `ingest_pdf_ocr.py` 工作流兼容；
- 可以补 FRUS/CIA/Wilson 没有的公开舆论、政府宣传、白皮书、年鉴、会议文件。

但必须设边界：不把现代二手研究混入档案主库。建议只收：

1. 美国政府公开出版物；
2. 同时代英文报刊/期刊；
3. 1940s-1950s 当时出版的小册子、报告、会议文件；
4. 可证明为原始材料或准原始材料的汇编。

### 第一批候选

1. **United States Relations with China, With Special Reference to the Period 1944-1949**
   - 常称 “China White Paper”。
   - 价值：国务院对 1944-1949 中国政策的官方叙述，和 FRUS/NARA 形成互证。

2. **Department of State Bulletin, 1946-1950**
   - 价值：美国政府公开口径，适合追踪政协、联合政府、民主党派、国共谈判公开表述。

3. **Congressional Record / hearings on China aid, 1946-1950**
   - 价值：美国国会对中国内战、援华、第三方面政治力量的公开讨论。

4. **同期英文期刊中关于 China Democratic League / third force 的材料**
   - 价值：补充外交档案外的公开舆论与智库视角。

## 六、推荐下一步实施

1. 新建 `data/hathitrust_ia/`。
2. 写 `scripts/fetch_hathi_ia_seed.py`，先不做泛搜索，只维护人工确认的 seed 清单。
3. 复用 `scripts/ingest_pdf_ocr.py` 或另写 `scripts/ingest_hathi_ia.py`，写入 `source_platform='hathi_ia'`。
4. 首页来源卡新增 HathiTrust/IA “可上线”状态，但标注“只收 primary/near-primary 材料”。
5. 第一批目标控制在 5-10 份，先跑通 PDF/OCR/全文搜索/页码引用/中文翻译。

