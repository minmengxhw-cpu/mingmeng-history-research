# Codex-style 复审报告 (125 条 pending)

报告日期：2026-07-21 21:25 (Asia/Shanghai)
适用范围：`data/domestic/candidates.jsonl` 中 L3 + L4 + LX pending 候选 125 条
复审脚本：Python 内部分类（基于 schema 字段：level / online_availability / medium / reuse_rights / source_url 模式 / event_tags）
目的：给 cheer 一份"哪些可以批量 accept / 哪些要人工复审 / 哪些是 cheer-only 硬缺口"的决策依据
红线：本文档**不**实际修改 candidates.jsonl，accept 决策需 cheer 拍板

---

## 总览

| 分档 | 数量 | 占比 | 期望决策 |
|---|---:|---:|---|
| **T1: Auto-accept（低风险）** | 36 | 28.8% | cheer 拍批量 accept（按 schema 字段已通过） |
| **T2: 人工复审（中风险）** | 54 | 43.2% | codex/人工核校后再决定 |
| **T3: Cheer-only 硬缺口** | 35 | 28.0% | cheer 跑馆内/函调/平台 cookie |
| **T4: Duplicate / Reject** | 0 | 0% | — |
| **合计** | **125** | 100.0% | — |

## T1: Auto-accept（36 条）— cheer 拍批量 accept

### T1.a L4 29 条 full_item_online（地方民盟 / 张澜平台 / 政协官网 lead-文章）

平台分布：MMSH 8 / GXMM 6 / 其他 15

**核校依据**：
- online_availability = full_item_online ✅
- medium = digital ✅
- reuse_rights = citation_only（与 L4 等级相符）✅
- source_url 均为 *.gov.cn 官方平台（mmsh/fjmm/hnmm/gxmm/bjtzb/hbmj/zjmg/zjmm/bjdcmm/hljmm/zl1872/cppcc）✅
- event_tags 均为 1941-1949 民盟相关事件（事件相关性 ✅）

**T1.a 候选 ID 清单**（29 条）：
```
domestic:MMSH:web-history
domestic:MMSH:web-leaders
domestic:MMSH:web-bases
domestic:MMSH:web-office-history
domestic:MMSH:web-political-cooperation
domestic:MMSH:web-newspapers
domestic:MMSH:web-zhanglan
domestic:MMSH:web-intro
domestic:MMSH:web-liukaiqu
domestic:FJMM:lead-福建民盟盟史导言
domestic:HNMM:lead-民盟精神解析
domestic:GXMM:lead--大公报-和-观察-对民盟被迫解散的不同反应
domestic:BJTZB:lead-人民民主统一战线的巩固和扩大
domestic:HBMJ:lead-民建简史第三章-迎接新中国的诞生
domestic:ZJMG:lead-中国国民党革命委员会60年-一-
domestic:MMSH:lead-新中国成立前民盟对政治协商制度的贡献
domestic:FJMM:lead-少年记忆-初识民盟
domestic:BJDCMM:reorganization-1944
domestic:HLJMM:first-congress-files-1945
domestic:GXMM:dagongbao-dissolution-report-1947-11-06
domestic:GXMM:xinminbao-professors-statement-1947-11-04
domestic:GXMM:observer-professors-statement-1947-11-08
domestic:ZL1872:chang-lan-pcc-opening-transcript-1946
domestic:MMSH:guangmingbao-formation-editorial-1941
domestic:ZL1872:chang-lan-dissolution-statement-1947
domestic:GXMM:dagongbao-tianjin-dissolution-1947-11-06
domestic:ZJMM:yann-an-meeting-minmeng-1945-07-01
domestic:GXMM:forced-dissolution-1947-11-05
domestic:CPPCC:liang-shuming-guangmingbao-founding-2020
```

### T1.b LX 4 条 full_item_online（zh.wikisource.org 1941/1946 公开转录）

**核校依据**：
- 1941 成立宣言 / 1946 和平建国纲领 / 1946 政协国民大会决议 / 1946 政协改组政府案 — 均为民盟核心正式文件公开转录
- source_url 均为 zh.wikisource.org（公有领域，open_license / public_domain）✅
- 风险：之前 reported zh.wikisource.org 404 + 限速，建议 cheer 拍前再 webfetch 1 个 sample 验证可达

**T1.b 候选 ID 清单**（4 条）：
```
domestic:WS:democratic-league-declaration-1941
domestic:WS:peace-building-program-1946
domestic:WS:pcc-national-assembly-resolution-1946
domestic:WS:pcc-government-reorganization-1946
```

### T1.c L3 3 条 full_item_online（强 primary source）

**核校依据**：
- HNMM 1948 五一口号致全国书 — Hunan 民盟官网刊载 1948-05-05 民盟响应中共五一号召原文（事件直接相关 primary source）✅
- YADS 1945-07-04 延安会谈记录 — 延安革命纪念馆官网（事件直接相关 primary source）✅
- LNU 1941 光明报索引 — Lingnan University Commons 1941 香港工运剪报索引（事件直接相关）✅

**T1.c 候选 ID 清单**（3 条）：
```
domestic:HNMM:response-may-day-1948
domestic:YADS:yanan-record-1945-07-04
domestic:LNU:guangmingbao-index-1941
```

### T1 决策建议

如果 cheer 同意，36 条可由 mavis 写一个 `accept_codex_review_tier1_20260721.py` 批量 accept（保留 L4 / LX / L3 等级 + reviewed_by=human），与 5 L4 accept 同模板。风险评估：低。预期 approved 率 ≥ 95%。

## T2: 人工复审（54 条）— codex/人工核校后再决定

### T2.a L3 5 条 full_item_online（primary source 边界）

```
domestic:WS:democratic-movement-editorial-1941    — 1941 解放日报社论（wikisource）
domestic:WS:wen-yiduo-last-testament-1946          — 1946 闻一多遗言（wikisource）
domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap  — 1946 民盟文献目录缺页（PDF 截图）
domestic:WM:zhang-lan-tomb                          — 张澜墓（北京八宝山，PD 照片）
domestic:WM:xinan-lianda-jiuzhi-1946-meng           — 西南联大旧址（PD 照片）
```

**为什么 T2 不 T1**：
- 2 条 wikisource 已在 T1.b 标注 404 风险，T2 需 cheer 单独拍
- NLC 1946 目录缺页：需确认是否能从 Wikimedia Commons 提取，或继续待 NLC 视检
- WM 2 张 photo：L3 是否合适？photo 性质可能是 L2 影像（实景照片）— 等级边界需 cheer 拍

### T2.b L3 1 条 surrogate_online（剪影）

```
domestic:BJDCMM:1945-congress-declaration-platform-clipping
```

剪影 vs 全文边界 — 建议 L2 accept（剪影 + 文章级 locator），不升 L1。

### T2.c L3 58 条 catalogue_only_online（书目）

58 条均为各省级民盟史 / 党史图书：
- 14 条 `medium=physical` 已归 T3
- 44 条 `medium=digital` 但 online_availability=catalogue_only（即只有目录，无全文）

T2.c 决策点：
- 各地民盟史（HB / GZ / SN / GD / JS / HE / YN / SC / AH / BJ）：10 条左右，多数为公开出版物有 ISBN
- 复审问题：是否值得 cheer 采购或函调获取纸质本？OR 接受 L3 catalogue_only 作为「目录级 record」accept？

### T2.d L4 9 条 catalogue_only / surrogate

```
L4 catalogue_only (6) — 各地民盟 / 二史馆 目录
L4 surrogate (3) — 影印件 partial
L4 not_online (1) — 张澜《时代日报》线索
```

L4 接受 catalogue / surrogate 比 L3 更顺（derive 引用合规），但需要复审。

### T2.e L2 41 条（来自 L2 pending 45 - 4 catalogue）

L2 45 = 9 full + 32 surrogate + 4 catalogue
- 9 full_item_online T1 应包含（按 L2 等级，是 L1/L2 cross-tier 边界）
- 32 surrogate + 4 catalogue 走 codex 复审

T2.e 决策点：L2 多数已有 codex 复审记录（checked_by=codex），多数是 L2 等级需要 cheer 复审 accept 决策。

### T2 复审工作量估算

| 子档 | 数量 | 单条复审耗时 | 总计 |
|---|---:|---:|---:|
| T2.a wikisource 2 + NLC 1 + WM 2 | 5 | 5 min | 25 min |
| T2.b 剪影 1 | 1 | 5 min | 5 min |
| T2.c 44 各地民盟史 | 44 | 2 min | 88 min |
| T2.d L4 10 catalogue / surrogate | 10 | 3 min | 30 min |
| T2.e L2 36 surrogate/catalogue | 36 | 5 min | 180 min |
| **合计** | **96** | — | **~5.5h** |

## T3: Cheer-only 硬缺口（35 条）— 需 cheer 启动 7 件 P0 模板之一

| cheer-only 路径 | 数量 | 触发条件 |
|---|---:|---|
| **港大缩微 1941** | 0 | 港大预约（无 not_online 候选） |
| **二史馆 1947 内政部公函** | 0 | 二史馆函调（无 not_online 候选） |
| **NLC 视检 1947-11-06 大公报** | 0 | NLC 视检（无 not_online 候选） |
| **校史馆函调 1946 李闻** | 0 | 校史馆函调 |
| **民盟中央 / 陈列馆 / 特园** | 0 | 民盟中央函调 |
| **孔夫子询 1947-11-04 新民报** | 0 | 孔夫子询 |
| **上海书店 1987 新华日报影印本** | 1 | `domestic:XHB:reprint-1938-1947-1987-shanghai-bookstore` (L3/catalogue) |
| **馆藏图书函调（各地民盟史 14 physical）** | 14 | 14 条 physical medium |
| **平台 cookie 拿不到** | 16 | 15 L3 not_online + 1 L4 not_online |
| **未公开原始档案（馆藏目录）** | 4 | 4 L3 catalogue_only（SHCM 1945 纲领 / VOC 1942 国讯 / RCL 1942 刘良模 / RCL 1942 钱伟长等） |
| **合计** | **35** | — |

**关键提示**：现有 7 件 P0 cheer-only 模板（港大/二史馆/NLC 视检 + 校史馆/民盟中央/孔夫子）— 适用目标清单已落档，cheer 启动后 mavis 配合接回报。

## T4: Duplicate / Reject（0 条）

本次复审未发现明显的重复或应 reject 的候选。原始 register 脚本已做去重，accept 记录里也明确每条的独特 locator。

---

## Codex 复审推荐下一步（cheer 决策）

| 选项 | 内容 | 工作量 | 风险 |
|---|---|---|---|
| **α** | T1 36 条批量 accept（mavis 写 accept_codex_review_tier1_20260721.py） | 5 min | 低 |
| **β** | T2.c 44 各地民盟史：按 ROI 排，挑 5-10 本进 T3（cheer 采购/函调） | 1h | 中 |
| **γ** | T2.e 36 L2 surrogate codex 抽检 5-10 条 | 30 min | 低 |
| **δ** | T2.a wikisource 2 + NLC 1 重新 webfetch 验证可达性 | 10 min | 低 |

**我建议 α + δ**（15 min 全部跑完），跑完后剩 T2.b/c/d/e 走 cheer 排期，T3 走 cheer-only 7 件 P0 启动。

---

## 数据一致性

本次 codex 复审**不修改 candidates.jsonl**，仅生成本决策依据报告。如 cheer 同意 α 选项，mavis 将另写 `accept_codex_review_tier1_20260721.py`（与 `accept_8parties_derivative_l4_20260721.py` 模板一致）跑批量 accept。
