# Hoover Institution Library & Archives 探勘报告（AI 内部研究参考，非平台收录内容）

> **重要边界**：本文件是 AI 协作时的内部规划文档，**不属于平台对外展示内容**。
> 探勘范围限定于 **国外一手原始档案** 的目录元数据可达性评估，符合本平台收录原则。
> 探勘日期：2026-05-16

---

## 一、探勘目的

为 CIA 阶段之后、下一个国外档案源选型提供决策依据。Hoover 因其私人卷宗
（personal papers）特色，是民盟人物研究的潜在富矿。本探勘评估：
1. Hoover 在线检索系统的集群侧可达性
2. archive.org 上的 Hoover 镜像规模
3. Hoover 中国卷宗中民盟相关内容的实际规模

---

## 二、可达性结果

### 2.1 Hoover 官网 https://www.hoover.org/library-archives

| 测试项 | 结果 |
|--------|------|
| 主站 200 响应 | ✅ |
| Collections 主入口 200 | ✅ |
| `/library-archives/collecting-areas/china` | ❌ 404 |
| 主站结构 | SPA + JS 异步渲染，curl 仅拿到导航壳 |

**结论**：Hoover 官网集群侧只能拿到页面骨架，**无法直接抓内容**。需要 Playwright 等 JS-capable 客户端。

### 2.2 OAC (Online Archive of California) https://oac.cdlib.org/

OAC 是 Hoover、Stanford、UC 等加州学术机构 finding aids 公共平台。

| 测试项 | 结果 |
|--------|------|
| 主站 200 响应 | ✅ |
| `/search?query=xxx` 异步搜索 | ❌ 返回 HTTP 202 + 0 字节（Blacklight 异步队列）|
| `/institutions/Hoover+Institution+Library+%26+Archives` 机构入口 | ⚠️ 200 + 192K bytes，但抽到的有效 ark 链接 = 1（SPA 渲染列表）|
| **单篇 ark 详情页**（如 `/findaid/ark:/13030/<id>`）| ✅ 可拿（含 finding aid 完整描述）|

**结论**：OAC 搜索接口集群侧不可用，**但**已知 ark ID 的单篇 finding aid 可拿。需要外部渠道（如学术引文）获得 ark ID 列表。

### 2.3 archive.org Hoover 镜像

```
collection:hooverinstitution → 83 篇文档
关键词 "China Democratic League" → 0 命中
关键词 "Lo Lung-chi" → 0 命中
关键词 "Chang Lan" → 0 命中
关键词 "Carsun Chang" → 0 命中
关键词 "Wen I-tuo" → 0 命中
```

archive.org 上的 Hoover 集合（83 篇）**全是 20 世纪加州历史口述史**（`csth_xxx` 编号），与中国民盟无关。

---

## 三、Hoover 中国卷宗结构分析

基于学术界对 Hoover 中国档案的通行认知，Hoover 中国卷宗主要覆盖：

### 3.1 中美外交人物
- **T. V. Soong Papers**（宋子文档案，约 70 box）— KMT 财政部长、行政院长
- **John Leighton Stuart Papers**（司徒雷登档案）— 美国驻华大使 1946-1949
- **Patrick J. Hurley Papers**（赫尔利档案）— 美国 1944-1945 驻华大使
- **Albert C. Wedemeyer Papers**（魏德迈档案）— 美军中国战区参谋长

### 3.2 KMT 高层与文人
- **Hu Shih Papers**（胡适档案）— 1949 赴美的自由主义学者，与民盟有边缘往来
- **Chen Cheng Papers**（陈诚档案）— KMT 高级将领
- 其他 KMT 党政人物私人档案多种

### 3.3 美国 China Hands
- John Service Papers（谢伟思）
- John P. Davies Jr. Papers（戴维斯）— FRUS 中常出现的「中国通」

### 3.4 **民盟核心人物私人档案 — 几乎不存藏**

关键发现：**Hoover 几乎没有民盟核心人物（罗隆基、章伯钧、张君劢、史良等）的私人卷宗**。

**结构性原因**：
- 民盟核心人物 1949 后大多**留在大陆**（罗隆基、章伯钧、张澜、沈钧儒、史良等）
- 他们的私人档案、信件、手稿、日记等**主要存于国内**（民盟中央、各级民盟省委、中国人民大学家属捐赠等）
- Hoover 主要收藏的是**1949 后赴台或赴美**的政治人物档案

唯一可能的例外：
- **张君劢**（Carsun Chang）1951 年赴美定居，其晚年档案**可能**部分在 Hoover 或 Columbia
- 但 Hoover 在线目录搜索受限，无法直接证实

---

## 四、与已收录数据源对比

| 数据源 | 民盟相关命中 | 集群侧可达 | 学术价值 |
|--------|-------------|-----------|---------|
| FRUS 1941-1950 | 299 篇文档 / 416 段 | ✅ 直接抓 | ⭐⭐⭐⭐⭐ 美方外交视角 |
| CIA Reading Room | 62 篇文档（去重） | ✅ archive.org 镜像 | ⭐⭐⭐⭐ 美方情报视角 |
| Wilson Center（待抓）| 21+ 候选 | ❌ Cloudflare 反爬 → Mac 代抓 | ⭐⭐⭐⭐ 智库视角 |
| **Hoover Institution** | **几乎为零** | ❌ SPA + 异步队列 | ⭐ 民盟主题价值低 |

---

## 五、结论与建议

### 5.1 Hoover 不建议作为当前阶段优先数据源

**理由**：
1. 集群侧抓取**技术上很难**（SPA + 异步队列），即使走 Mac 端也需要逐篇手工操作
2. 学术上**民盟核心私人档案几乎不存藏于 Hoover**（结构性原因 — 民盟人留在大陆）
3. Hoover 主要价值是**KMT/中美外交人物视角**，与已有的 FRUS + CIA 重叠度高
4. 投入产出比远低于继续推 Wilson Center / NARA / HathiTrust

### 5.2 建议下一阶段优先级

| 优先级 | 数据源 | 理由 |
|--------|--------|------|
| 🥇 **第一**（明晚 Codex 回血推）| **Wilson Center** | 已有 21 篇预设清单，Mac 代抓流程已就绪 |
| 🥈 **第二** | **NARA RG 59 / RG 226** | FRUS 是 NARA 的精选集，NARA 原始档案更细颗粒；OSS RG 226（1941-1945）可补 CIA 1947 前的空白期 |
| 🥉 **第三** | **HathiTrust 学术专著** | 同期美国学界对民盟的研究专著（如 1940s-1950s 的中国政治研究博士论文）|
| ⭐ **可选** | **Stanford / Columbia 中国研究中心** | 张君劢晚年（1951-1969 赴美）档案可能在此 |
| ❌ **建议跳过** | Hoover | 见 5.1 |

### 5.3 Hoover 的合理用法（如果将来要做）

如果将来时间充裕、又要补充 Hoover 视角，建议：
1. 让小班 Mac 端用 Playwright 跑 Hoover finding aids 搜索
2. 重点检索 **Carsun Chang / 张君劢** 单一人物（他是唯一民盟核心赴美的）
3. T. V. Soong / Stuart / Hurley / Wedemeyer 等档案可作为**FRUS 互证补充**，但不直接展示民盟视角

---

## 六、附录：本次探勘抓取的最小数据样本

| 项 | 路径 |
|----|------|
| OAC 机构入口 HTML | `data/hoover_recon/oac_hoover.html`（仅作可达性证据，不入库）|
| OAC 单篇 ark ID 样本 | `ark:/13030/tf8p3006xd`（LeConte family papers，无关样本，仅证明详情页可达）|
| archive.org Hoover 集合搜索 JSON | `data/hoover_recon/oac_search.json`（关键词 0 命中证据）|

这些临时数据不入数据库（仅作探勘证据），按平台收录原则不构成资料库内容。
