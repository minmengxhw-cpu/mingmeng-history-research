# CIA FOIA 探勘报告（AI 内部研究参考，非平台收录内容）

> **重要边界**：本文件是 AI 协作时的内部规划文档，**不属于平台对外展示内容**。
> 探勘范围严格限定于 **国外一手原始档案** 的目录元数据，符合本平台收录原则。
> 探勘日期：2026-05-16

---

## 一、探勘目的

为 Wilson Center 抓取之后、CIA FOIA 阶段的全面下载与入库做技术与内容前置规划：

1. 验证 CIA Reading Room 电子阅览室集群侧可达性
2. 估算民盟相关一手档案的规模与时间分布
3. 列出候选档案清单，分主题分级，供后续抓取参考
4. 评估与已有 FRUS 1941-1950 数据库的互补价值

---

## 二、CIA FOIA 站点可达性

### 主站反爬情况

CIA 官网 Reading Room（https://www.cia.gov/readingroom/）使用 **Akamai Bot Manager** 反爬：

- 集群侧任何 curl 请求被反复 302 重定向 + bm-verify token + JavaScript challenge
- 普通 curl 即使配全套浏览器 header 也无法绕过
- 需要 JavaScript-capable scraper（Playwright / Puppeteer / Selenium）才能通过验证

**结论**：CIA 官网集群侧不可直接抓取，需小班 Mac 端住宅 IP + JS 爬虫。

### 替代方案：archive.org 镜像 ✓ 集群可达

**重大发现**：archive.org 已将 CIA Reading Room 全套档案镜像入 `ciareadingroom` collection，
集群侧通过 archive.org Advanced Search API 可直接查询和下载：

```
https://archive.org/advancedsearch.php?q=<query>&collection=ciareadingroom&output=json
https://archive.org/details/<identifier>          # 档案详情页 + PDF/OCR text
https://archive.org/download/<identifier>/<file>   # 直接下载
```

每个档案在 archive.org 上有：
- 原始 CIA PDF
- OCR text（自动 OCR 提取的英文全文，已可直接 DeepSeek 翻译）
- 元数据 JSON（标题、日期、CIA RDP 编号、收藏归属）

**抓取技术方案确定**：集群侧直接通过 archive.org 抓 CIA 档案，不需走 CIA 官网。

---

## 三、候选档案规模

### 关键词检索（含民盟英文名 + 创始人韦氏拼音 + 第三方力量）

|关键词|archive.org 命中（1941-1955）|
|---|---|
|`China Democratic League`|42|
|`Chang Lan` (张澜)|12|
|`Lo Lung-chi` (罗隆基)|7|
|`Shih Liang` (史良)|9|
|`Chang Po-chun` (章伯钧)|5|
|`Chang Tung-sun` (张东荪)|4|
|`Shen Chun-ju` (沈钧儒)|4|
|`Huang Yen-pei` (黄炎培)|3|

去重合并后 **62 篇唯一档案**，其中：
- **核心民盟主题档案：21 篇**（P1-P11 分类）
- 主题偏离但命中关键词：41 篇（多数是同期东南亚华人社区、缅甸/印尼共产党活动等 CIA 区域情报）

### 时间分布（去重后 62 篇）

| 年份 | 数量 | 说明 |
|------|------|------|
| 1946 | 4 | 与 FRUS 已有覆盖重叠 |
| 1947 | 2 | 与 FRUS 已有覆盖重叠 |
| 1948 | 1 | FRUS 部分覆盖 |
| 1949 | 17 | **关键增量**——民盟从受难期转向新政协的细节 |
| 1950 | 12 | **关键增量**——FRUS 1950 部分覆盖，CIA 是补充 |
| 1951 | 6 | FRUS 不覆盖，CIA 独家 |
| 1952 | 9 | FRUS 不覆盖，CIA 独家 |
| 1953 | 4 | FRUS 不覆盖，CIA 独家 |
| 1954 | 7 | FRUS 不覆盖，CIA 独家 |

**与 FRUS 数据互补**：FRUS 主要覆盖 1941-1950，CIA 主要价值在 1949-1954 段。

---

## 四、核心档案清单（21 篇，按主题）

### P1. 民盟核心人物专档（3 篇）⭐⭐⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1949-12-20 | **LO LUNG-CHI**（罗隆基专档）| CIA-RDP82-00457R004000340003-1 |
| 1950-04-04 | **CHANG LAN**（张澜专档）| CIA-RDP82-00457R004600450010-5 |
| 1950-05-08 | POSITION OF SHEN CHUN-JU（沈钧儒立场）| CIA-RDP82-00457R004800420003-7 |

> **政治安全评估**：1950-05-08 沈钧儒立场档案因标题含敏感比较语境，需先看全文再决定前台展示策略。罗隆基、张澜专档可直接入库。

### P2. 民盟领导成员名单（1 篇）⭐⭐⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1950-07-12 | **LEADING MEMBERS OF THE CHINA DEMOCRATIC LEAGUE** | CIA-RDP82-00457R005200480001-5 |

> CIA 1950 年整理的民盟中央领导人名单。**入库高优先级**，对人物档案对照极有价值。

### P3. 民盟整体性档案（2 篇）⭐⭐⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1949-03-31 | CHINA DEMOCRATIC LEAGUE（民盟综合报告）| CIA-RDP82-00457R002700450009-8 |
| 1949-08-08 | **PLAN FOR CHANGE IN POLICY FOR MEMBERSHIP IN DEMOCRATIC LEAGUE - LO LUNG-CHI AND CHANG LAN** | CIA-RDP82-00457R003000670005-4 |

### P4. 民盟上海撤离（1949）⭐⭐⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1949-05-23 | **POLITICAL INFORMATION: CHINA DEMOCRATIC LEAGUE MEMBERS' ESCAPE FROM SHANGHAI TO HONG KONG** | CIA-RDP82-00457R002800130003-8 |

> 与本平台关键事件「黄竞武上海殉难」（1949.5.12）同期。**入库高优先级**。

### P5. 民盟参与新政协筹备（1 篇）⭐⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1949-01-01 | PREPARATIONS FOR THE ALL-CHINA DEMOCRATIC WOMEN'S CONGRESS | CIA-RDP82-00457R002700170002-6 |

> 全国民主妇女大会筹备——史良、邓颖超等民盟妇女工作活动。

### P6. 地方民盟（华南）（2 篇）⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1946-10-02 | POLITICAL INFORMATION: WENG SHIH-LIANG, SOUTH CHINA DEMOCRATIC LEAGUE CHAIRMAN | CIA-RDP82-00457R000300360006-7 |
| 1947-01-28 | POLITICAL INFORMATION: SOUTH CHINA DEMOCRATIC LEAGUE ANTI-AMERICAN ACTIVITY | CIA-RDP82-00457R000300170001-3 |

> 与 FRUS 同期重叠，可互相印证。

### P7. 民盟教育活动（2 篇）⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1949-11-28 | MEMBERS OF THE CULTURAL AND EDUCATIONAL COMMISSION OF THE CENTRAL PEOPLE'S GOVERNMENT | CIA-RDP80-00809A000600270035-3 |
| 1951-08-08 | SUMMER TEACHERS' CLASSES SPONSORED BY CHINA DEMOCRATIC LEAGUE | CIA-RDP82-00457R007900210006-0 |

### P8. 第三方面政党在新中国的角色（2 篇）⭐⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1950-11-09 | **ROLE OF NON-COMMUNIST POLITICAL PARTIES IN PEIPING** | CIA-RDP82-00457R006100780010-2 |
| 1950-12-12 | PLAN FOR MEETINGS OF NON-COMMUNIST PARTIES OF COMMUNIST CHINA | CIA-RDP82-00457R006500400006-7 |

> 1950 年代 CIA 对中国非中共政党（含民盟）作用的分析。

### P9. 民盟参与中央/人大机构（4 篇）⭐⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1954-02-10 | MEMBERS OF THE EXECUTIVE COMMITTEE | CIA-RDP80-00810A003500680001-8 |
| 1954-02-16 | LIST OF IMPORTANT COMMITTEE OFFICIALS | CIA-RDP81-01036R000100120085-5 |
| 1954-09-16 | **ROSTER OF PRESIDIUM OF FIRST CONGRESS**（一届人大主席团名单）| CIA-RDP61S00527A000200010065-4 |

### P10. 民盟在新政协中的活动（1 篇）⭐⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1950-05-22 | ARRIVAL OF CHINESE PEOPLE'S POLITICAL CONSULTATIVE CONFERENCE DELEGATES | CIA-RDP82-00457R004900220002-6 |

### P11. 人物索引/化名清单（2 篇）⭐⭐⭐

| 日期 | 标题 | 档案号 |
|------|------|--------|
| 1949-02-16 | POLITICAL INFORMATION: PSEUDONYMS USED BY CHINESE COMMUNISTS REFERRING TO... | CIA-RDP82-00457R002300710010-1 |
| 1949-08-10 | WHO'S WHO - CHINESE LEFTIST PERSONALITIES | CIA-RDP80-00809A000600240818-7 |

> 人物名单与化名对照，对翻译标准化和人物索引有价值。

---

## 五、政治安全分级评估

按本平台「前台展示边界」原则，对候选档案分级：

| 等级 | 时间范围 | 主题特征 | 建议 |
|------|----------|----------|------|
| 🟢 **A 级（直接入库 + 前台展示）** | 1946-1949 | 民盟创立、政协、受难、上海撤离 | 与 FRUS 同期，安全 |
| 🟡 **B 级（入库 + 前台谨慎展示）** | 1949-1954 | 民盟领导名单、新政协活动、第三方面角色 | 档案本身是 CIA 第三方观察，非政治运动叙事；展示时如有具体敏感段落按现有脱敏规则处理 |
| 🔴 **C 级（暂不入库，待评估）** | 1950+ | 标题明显涉及 1950s 政治运动主题 | 例如「PROTEST AGAINST THREE-ANTI'S CAMPAIGN」(1952.5)、「ARRESTS, EXECUTIONS」(1951.8) 等需先审 PDF 全文再决定 |

| 等级 | P1-P11 分布 | 数量 |
|------|-----------|------|
| 🟢 A 级 | P3.1949 综合 / P4.上海撤离 / P5.新政协筹备 / P6.华南民盟 / P11.人物化名 | **8 篇** |
| 🟡 B 级 | P1.人物专档 / P2.领导名单 / P3.政策变化 / P7.教育 / P8.第三方面 / P9.人大主席团 / P10.政协代表 | **12 篇** |
| 🔴 C 级（核心档案中无明确 C 级，待全文审） | — | **1 篇**（沈钧儒立场含批评毛语境） |
| **核心档案合计** | | **21 篇** |

P99 其他相关 41 篇：建议先不入库，待 A+B 级核心档案完成后再评估。

---

## 六、抓取技术方案

### archive.org API

```python
# 元数据查询
GET https://archive.org/metadata/<identifier>

# OCR text 下载（已有英文全文）
GET https://archive.org/download/<identifier>/<identifier>_djvu.txt

# 原始 PDF 下载
GET https://archive.org/download/<identifier>/<identifier>.pdf
```

集群侧已验证可达，**无需 Codex Mac 端**。

### 入库流程（与 Wilson 方案对齐）

```
archive.org OCR text → DeepSeek 翻译 → 入 zipei_data SQLite
  ↓
按 source_platform='cia' 入 documents / pages / translations 表
  ↓
触发现有人物索引 / 关键事件自动联动
  ↓
人工精修核心几篇（特别是 LO LUNG-CHI / CHANG LAN / LEADING MEMBERS）
```

### 翻译质量预期

CIA 档案的英文比 FRUS 更口语化、缩写多（CCP / KMT / DL 等），术语表需要扩充：
- "DL" / "Democratic League" → 民盟
- "CCP" → 中国共产党
- "KMT" → 国民党
- "PCC" → 政治协商会议
- "non-Communist" → 非中共
- "leftist" → 左翼
- "third force" → 第三方面

→ 与第二梯队 D（术语表扩到 300+）任务联动，可同步做。

---

## 七、下一步建议

供小班决定：

### 选项 α：先抓 A 级 8 篇试点
- 集群侧直接拉 archive.org OCR text → DeepSeek 翻译 → 入库
- 验证 CIA 档案翻译质量
- 与 FRUS 数据形成第一次跨源融合
- 预估工作量：1-2 小时（不需要 Codex）

### 选项 β：抓全部 A+B 级 20 篇（核心档案除沈钧儒立场）
- 一次性完成 CIA 阶段核心档案入库
- 不含需特别审阅的沈钧儒立场档案
- 预估工作量：2-3 小时

### 选项 γ：先扩术语表（D 任务），再启动 CIA 抓取
- 先把术语表从 147 → 300+，准备好 CIA 档案翻译需要的术语
- 然后 CIA 抓取时翻译质量更高
- 预估工作量：术语表 1 小时 + CIA 抓取 2 小时 = 3 小时

### 选项 δ：仅本报告作为规划存档，CIA 抓取等 Wilson 完成后再启动
- 保持当前 Wilson 优先级
- CIA 阶段暂不启动

---

## 八、附录：A+B 级 20 篇完整清单

按时间顺序：

```
[A] 1946-10-02  POLITICAL INFORMATION: WENG SHIH-LIANG, SOUTH CHINA DEMOCRATIC LEAGUE
[A] 1947-01-28  POLITICAL INFORMATION: SOUTH CHINA DEMOCRATIC LEAGUE ANTI-AMERICAN
[A] 1949-01-01  PREPARATIONS FOR THE ALL-CHINA DEMOCRATIC WOMEN'S CONGRESS
[A] 1949-02-16  POLITICAL INFORMATION: PSEUDONYMS USED BY ...
[A] 1949-03-31  CHINA DEMOCRATIC LEAGUE
[A] 1949-05-23  CHINA DEMOCRATIC LEAGUE MEMBERS' ESCAPE FROM SHANGHAI TO HONG KONG
[A] 1949-08-08  PLAN FOR CHANGE IN POLICY FOR MEMBERSHIP IN DL - LO LUNG-CHI AND CHANG LAN
[A] 1949-08-10  WHO'S WHO - CHINESE LEFTIST PERSONALITIES
[B] 1949-11-28  MEMBERS OF THE CULTURAL AND EDUCATIONAL COMMISSION
[B] 1949-12-20  LO LUNG-CHI
[B] 1950-04-04  CHANG LAN
[B] 1950-05-22  ARRIVAL OF CHINESE PEOPLE'S POLITICAL CONSULTATIVE CONFERENCE DELEGATES
[B] 1950-07-12  LEADING MEMBERS OF THE CHINA DEMOCRATIC LEAGUE
[B] 1950-11-09  ROLE OF NON-COMMUNIST POLITICAL PARTIES IN PEIPING
[B] 1950-12-12  PLAN FOR MEETINGS OF NON-COMMUNIST PARTIES
[B] 1951-08-08  SUMMER TEACHERS' CLASSES SPONSORED BY CHINA DEMOCRATIC LEAGUE
[B] 1954-02-10  MEMBERS OF THE EXECUTIVE COMMITTEE
[B] 1954-02-16  LIST OF IMPORTANT COMMITTEE OFFICIALS (×2 同名重复档案号不同)
[B] 1954-09-16  ROSTER OF PRESIDIUM OF FIRST CONGRESS
```

详细元数据 JSON 已暂存于 `/tmp/cia_recon/final_dedupe.json`，正式抓取时入仓库。
