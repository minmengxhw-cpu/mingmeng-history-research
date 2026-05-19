# 英国国家档案馆 Kew Discovery · 民盟史料探勘报告

> 探勘时间：2026-05-18  
> 探勘范围：The National Archives, Kew · Discovery 在线目录系统  
> 探勘方法：Discovery API（`/API/search/v1/records`）+ records 详情接口

## 一、关键词覆盖（1941-1950 时段）

| 关键词 | 命中数 |
|---|---|
| `"Chinese Democratic League"` | 1 |
| `"China Democratic League"` | 2 |
| `"Democratic League"` | 6（含上面 2 条 + 4 条相关 / 不相关） |
| `"Democratic League" Hong Kong` | 3（与上面重叠） |
| `Min Meng` | 0 |
| `Chang Lan` / `Carsun Chang` / `Lo Lung-chi` / `Shen Chun-ju` / `"Chang Po-chun"` / `Tan Ping-shan` | **全部 0** |
| `"Democratic League" outlawed/suppressed` | 0 |
| `"third party" China` | 1（无关：道德社会卫生协会档案） |

**关键观察**：人物名命中全部为 0。这反映 Kew 编目惯例——卷宗标题只录主题词（"Democratic League"、"political parties"），不录具体人名。**真实材料藏在卷内**，目录层面看不到。

## 二、4 个民盟专题核心卷宗

去除噪声（印度政府 Indo-British Democratic League 卷、马来亚共产党档案、英文同形姓名 Chang Lan 等无关命中）后，**精准命中 4 卷**，全部为民盟专题：

### 1. CO 537/3724 — *China Democratic League*（1948）
- **馆藏**: The National Archives, Kew
- **数字化**: ❌ 未数字化
- **公开状态**: N（需现场调阅或申请副本）
- **卷宗性质**: 殖民部（Colonial Office）"Original Correspondence and Papers, Supplementary"，高密级
- **学术意义**: 1948 民盟在港复盘 + 民盟一届三中全会同期英港府视角档案
- **详情**: https://discovery.nationalarchives.gov.uk/details/r/C1252251

### 2. CO 537/4820 — *China Democratic League*（1949）
- **馆藏**: The National Archives, Kew
- **数字化**: ❌ 未数字化
- **公开状态**: N
- **卷宗性质**: 殖民部高密级，与 CO 537/3724 序列接续
- **学术意义**: 1949 民盟成员从港北上 + 参加新政协前后英港府视角
- **详情**: https://discovery.nationalarchives.gov.uk/details/r/C1253349

### 3. FCO 141/16965 — *Singapore: Chinese Democratic League branch in Hong Kong*（1947）
- **馆藏**: The National Archives, Kew
- **数字化**: ❌ 未数字化
- **公开状态**: A（开放）
- **卷宗性质**: FCO 141 = "Migrated Archives" 移交档案（前殖民地撤回的敏感档案），原为新加坡殖民政府档案
- **学术意义**: 民盟在港分部的新加坡视角，1947 年覆盖民盟「非法」事件前后
- **详情**: https://discovery.nationalarchives.gov.uk/details/r/C14050228

### 4. WO 208/4770 — *Reports on political parties: Democratic League*（1947 Sept - 1948 Oct）
- **馆藏**: The National Archives, Kew
- **数字化**: ❌ 未数字化
- **公开状态**: N
- **卷宗性质**: War Office Directorate of Military Intelligence（陆军部军事情报局 MI3/MI4）政党评估系列
- **学术意义**: **最高优先级** —— 英方军事情报部对民盟作为政治组织的专项评估报告，时段覆盖 1947 民盟「非法」事件全程 + 1948 民盟在港改组
- **详情**: https://discovery.nationalarchives.gov.uk/details/r/C4414285

## 三、可行性评估

### 远程获取
- **Discovery 在线下载**: ❌ 全部 4 卷未数字化
- **Kew Image Library 付费扫描**: ✅ 可申请，但需预约报价；通常 £30-100/卷起印费 + 每页扫描费
- **委托学者代查**: ✅ 可联系伦敦学者（如 LSE / SOAS 中国研究所）现场拍照转引
- **微缩胶片副本**: 部分卷宗可购，需另外申请

### 学术价值
- **不可替代性**: ⭐⭐⭐⭐⭐ —— 国内学界几乎未用，与 FRUS（美国务院）/ CIA（美情报）/ 港媒（公开舆论）形成"英方殖民官僚 + 军事情报"第三视角
- **时段契合**: 4 卷全部落在 1947-1949 民盟最重要的"非法"事件 + 在港复盘 + 北上参政时段，是本平台最薄弱的「英方视角」补充
- **数量级**: 4 卷为 piece 级（盒/夹），单卷内估计 50-300 页

## 四、建议下一步

| 优先级 | 行动 | 时间/成本估计 |
|---|---|---|
| 🟢 高 | 联系 Kew 询价：4 卷数字化扫描全卷的报价单 + 工期 | 2-4 周回复 |
| 🟢 高 | 同步联系 LSE / SOAS 中国研究所校友 / 当地华人学者代查可能性 | 视联系人而定 |
| 🟡 中 | 排查 FO 371（外交部一般通信，1947-1949 中国卷）内是否有未被目录关键词捕获的民盟相关报告 —— 需更精细搜索策略（按 FO 371 子卷号、按驻华使馆电报系列） | 需重新设计探勘 |
| 🔴 低 | 赴 Kew 现场调档 | 仅在前两条路径都不通时考虑 |

## 五、技术备忘

- API 接口: `https://discovery.nationalarchives.gov.uk/API/search/v1/records`
- 参数必须用 `sps.` 前缀（`sps.searchQuery`, `sps.dateFrom`, `sps.dateTo`, `sps.resultsPageSize`, `sps.page`）
- 详情接口: `/API/records/v1/details/{iaid}`
- WAF Challenge: 浏览器路径 `/results/r?` 被 CloudFront 拦截，**只能走 API**
- 探勘脚本: `scripts/probe_kew_discovery.py`, `scripts/probe_kew_details.py`
- 原始数据: `data/kew_probe/kew_hits.csv`, `data/kew_probe/kew_summary.csv`, `data/kew_probe/kew_4vol_details.md`
