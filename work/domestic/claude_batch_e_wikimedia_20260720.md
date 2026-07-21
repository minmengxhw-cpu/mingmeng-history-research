# Claude 批次 E 收口报告（路线 3：维基文库+CADAL+Archive+HathiTrust / 2026-07-20）

## 一、§1 四校验终态

```
candidates:     538 / 0 / 538 ✅
event_coverage: 538 / 9 / 0 missing / 1 pair_available + 8 pair_partial ✅
ingest:         89 sources / 538 candidates / 306 pending / 538 decisions
audit:          538 records / 257 accepted (210 L1 + 47 L2) / 0 missing_paths
```

**基线累计（从 7-19 接管至今）：**

| 指标 | 接管 7-19 | 现在 7-20 | 增量 |
|---|---:|---:|---:|
| candidates | 425 | **538** | **+113** |
| accepted | 201 | **257** | **+56** |
| pending | 224 | **306** | **+82** |
| L2 accepted | 10 | **47** | **+37** |
| sources | 89 | 89 | 0 |

## 二、批次 E 公开资源测试结果（6 站点）

| 站点 | 测试结果 | 处理 |
|---|---|---|
| **Wikimedia Commons** | ✅ 2 张 PD-China 民国扫描件可下载 | **已登记 2 条 L2 accepted** |
| archive.org /search | ❌ HTTP 404 | 站点结构已变；直接 ID 未找到 |
| zh.wikisource.org | ❌ 404 + Retry-After: 3600 限速 | 频次受限 |
| catalog.hathitrust.org | ❌ HTTP 403 Forbidden | 站点反爬 |
| www.cadal.edu.cn | ❌ DNS ENOTFOUND | 网络层不可达 |
| mgwxbh.nlc.cn (国图) | ❌ Socket closed + SSL 错 | 同网络层 |

## 三、Wikimedia Commons 2 张民国扫描件（已 accept）

### 3.1 1946 中共代表团撤离前委托民盟代管房产的信
- **文件**：`File:中共代表团撤离前委托民盟代管房产的信.jpg`
- **来源**：中国政协 cppcc.people.com.cn/BIG5/35948/9974422.html
- **版权**：PD-China 公有领域
- **规格**：JPEG 64KB 220×308
- **直接下载**：upload.wikimedia.org/wikipedia/commons/7/70/...
- **事件**：1946 政治协商会议 / 1947 民盟解散

### 3.2 1947 中共及民盟地方组织抗议政府解散民盟
- **文件**：`File:中共及民盟的地方组织抗议政府解散民盟.jpg`
- **来源**：中国政协 cppcc.people.com.cn/BIG48/9974424.html
- **描述**：1947 newspaper clipping showing reports and statements from local CCP and
  China Democratic League organizations protesting the Kuomintang's illegal dissolution
  of the Democratic League on October 27, 1947
- **版权**：PD-China 公有领域
- **规格**：JPEG 106KB 400×335
- **直接下载**：upload.wikimedia.org/wikipedia/commons/f/ff/...
- **事件**：1947 民盟解散（10-27 国府宣布非法）

## 四、其他路线 3 测试发现（不入档）

### 4.1 人民政协网 rmzxw.com.cn
- 改版（rmzxb.com.cn → rmzxw.com.cn 301）
- "史料钩沉" / "政协史话"栏目不含民盟 1941-1949 专题（页面空）
- 来源 cppcc.people.com.cn/BIG5/35948/9974422-9974424.html 含 2 张扫描件（已收录）

### 4.2 国家图书馆 mgwxbh.nlc.cn
- SSL cert mismatch（CDN 链）+ Socket closed
- 子库：民国图书 ~10 万种 + 民国期刊 ~10 万种 + 民国法律 + 民国报纸
- 需 cheer 在 NLC 馆内访问

### 4.3 中央档案馆 saac.gov.cn（批次 D 已注册 16 条）
- 共 93 件档案，本批筛 15 件民主党派直接相关
- 剩 78 件可继续登记（部分非民主党派直接相关）

## 五、远程不可办（cheer 主导）

| 资源 | 状态 | cheer 主导动作 |
|---|---|---|
| archive.org 1941 光明报原刊 | 站点结构变化，需具体 ID | 浏览器登录 + 下载 |
| HathiTrust 民盟期刊 | 403 反爬 | 需 institutional IP |
| CADAL 民盟文献 | DNS 不可达 | 需国内 institutional IP |
| mgwxbh.nlc.cn 民盟期刊 | SSL 不可达 | NLC 馆内访问 |
| cppcc.gov.cn 政协档案 | SSL 不可达 | 浏览器访问 |

## 六、本批 2 条新候选分布

| 类别 | 数量 | 等级 | 来源 |
|---|---:|---|---|
| Wikimedia Commons PD 民国扫描件 | 2 | **L2 accepted** | cppcc.people.com.cn 官方源 |

## 七、交付物

- 脚本：`scripts/domestic/register_wikimedia_commons_pd_scans_20260720.py`

## 八、红线全程遵守

- ❌ 不动 raw 层文件
- ❌ 不为"闭环"虚增 accepted（仅 2 条严格按 Wikimedia PD-China 实测）
- ❌ 不自动 commit
- ✅ 所有 source_url 经 WebFetch 实测 + 直链验证
- ✅ 全部基于 Wikimedia Commons 公有领域 + 中国政协官方源
- ✅ 不假装已下载高分辨率原件（明确标注 220×308 / 400×335 中小分辨率）

## 九、下一步建议

### 路径 A：批次 E 后续扩展
- 抓 Wikimedia Commons 民盟人物子分类（33 子分类）
- 抓 Wikimedia Commons 光明日报分类（8 文件，已分析）
- 试 archive.org 直接 URL（如 archive.org/details/光明报）

### 路径 B：saac.gov.cn 剩余 78 件
- 继续筛民主党派直接相关（约 30+ 件可再注册）
- 主要分布在 Page 02 (筹备会各小组) + Page 06 (开国大典)

### 路径 C：cheer 主导路径
- 浏览器跑 minmeng1941.cn 下载脚本（带 cookie）
- NLC 馆内访问 mgwxbh.nlc.cn 民国期刊库
- 二史馆 220 万民国档案查阅

**请批示。**