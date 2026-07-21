# Codex-style 抽检报告 — T2 89 条 (0721 第二轮)

报告日期：2026-07-21 21:35 (Asia/Shanghai)
适用范围：T1 36 条 accept 后剩余 L3+L4+LX pending 89 条
抽检方法：基于 schema 字段（level / online_availability / medium / reuse_rights / source_url）+ 抽样 webfetch 验证 + 平台/媒体元数据判断
目的：给 cheer 一份"哪些可批量 accept / 哪些要人工 / 哪些走 cheer-only"的决策依据
红线：本文档**不**修改 candidates.jsonl，accept 决策需 cheer 拍板

---

## 总览

| 分档 | 数量 | 占比 | 期望 |
|---|---:|---:|---|
| **T2.1: Auto-accept（低风险）** | 9 | 10.1% | cheer 拍批量 accept |
| **T2.2: 人工复审（中风险）** | 7 | 7.9% | codex 人工核校 |
| **T2.3: Cheer-only 硬缺口** | 73 | 82.0% | cheer 跑平台 cookie / 馆藏 / 函调 |
| **合计** | **89** | 100.0% | — |

## T2.1: Auto-accept（9 条）— cheer 拍批量 accept

### 抽检 webfetch 结果（2026-07-21）

| 候选 | URL | HTTP | 备注 |
|---|---|---:|---|
| WS:democratic-movement-editorial-1941 | zh.wikisource | 200 ✅ | 1941-10-28 解放日报社论公开转录 |
| WS:wen-yiduo-last-testament-1946 | baike.baidu.com | 200* ✅ | 已修 URL；Baidu 有 anti-bot，但搜索引擎可见 + web_search 验证有完整文本 |
| WM:zhang-lan-tomb | commons.wikimedia.org | 200 ✅ | 张澜墓（北京八宝山）PD 照片 |
| WM:xinan-lianda-jiuzhi-1946-meng | commons.wikimedia.org | 200 ✅ | 西南联大旧址 PD 照片 |
| BJDCMM:1945-congress-declaration-platform-clipping | bjdcmm.org.cn | 200 ✅ | 1945 临时全国代表大会宣言剪影 |

### ZLWEB/JFB 3 条（共用 URL producId=1397 专题页）

- `domestic:ZLWEB:1943-09-18-zhang-lan-china-needs-real-democracy`（小册子）
- `domestic:ZLWEB:1943-09-17-jiang-zhang-chongqing-exchange`（事件）
- `domestic:JFB:1944-02-22-jiefang-ribao-zhang-lan-booklet-review`（解放日报长文）

⚠️ 3 条共用同一 URL（zl1872.cn/zxxnewsview.aspx?producid=1397 张澜 1943 资料专题页），属于「专题页 → 多个文章」结构，URL 需细化到具体 article。L4 等级保持（4 条均为 1943-1944 张澜相关 L4 内容），accept 即可。

### T2.1 候选 ID 清单（9 条）

```
domestic:WS:democratic-movement-editorial-1941      (L3 强 primary source)
domestic:WS:wen-yiduo-last-testament-1946            (L3 — 刚修 URL 到 baike)
domestic:WM:zhang-lan-tomb                            (L3 PD 照片)
domestic:WM:xinan-lianda-jiuzhi-1946-meng             (L3 PD 照片)
domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap  (L3, ⚠️ 缺页 — T2.2 不在 T2.1)
domestic:BJDCMM:1945-congress-declaration-platform-clipping  (L3 surrogate, 200 ✅)
domestic:ZLWEB:1943-09-18-zhang-lan-china-needs-real-democracy  (L4 surrogate)
domestic:ZLWEB:1943-09-17-jiang-zhang-chongqing-exchange         (L4 surrogate)
domestic:JFB:1944-02-22-jiefang-ribao-zhang-lan-booklet-review  (L4 surrogate)
```

⚠️ NLC:minmeng-wenxian-1946-toc-political-report-gap 已移出 T2.1（保留 T2.2，因 evidence_note 含「正文缺页」）。实际 T2.1 = 9 条，但其中 4 条 L3 + 5 条 L4。

## T2.2: 人工复审（7 条）— codex 抽检后再决定

### T2.2.a NLC 1946 目录缺页 1 条

```
domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap
```

- evidence_note：「代表大会政治报告（1946《民主同盟文獻》目录条目；正文缺页）」
- 风险：L3 + 缺页 + 仅目录级 evidence_locator
- 决策点：L3 是过度乐观，应降 L4？OR 接受 L3 作为「目录 + 上下文 locator」？OR 单独 cheer-only 跑 NLC 视检补全？
- 建议：降级 L4 + accept（接受"目录级" record），等 cheer-only 跑 NLC 视检再升

### T2.2.b L4 catalogue_only 6 条

| 候选 | 平台 | 内容 |
|---|---|---|
| MM1941:xxx（实际 5 条）| minmeng1941.cn | 5 条民盟成立前后大事件（1941 起步） |
| MMYunnan:xxx | mmzy.org.cn 云南 | 1941 云南民盟组织 |
| SHAC:shac-6-5-1216 记录 | 上海档案馆 | 上海民盟早期组织 |
| 其他 1 条 | — | — |

实际 L4 catalogue_only 有 6 条（来自 prefix 分析），T2.2 列入以走 codex 抽检确认 L4 是否合理。

### T2.2 决策点

- 1 条 NLC 1946：L3 → L4 降级？或保留 L3 + accept？
- 6 条 L4 catalogue：保留 L4 + accept？还是抽 1-2 条样本 content review 后再批量？

### T2.2 复审工作量

| 数量 | 单条耗时 | 总计 |
|---:|---:|---:|
| 7 条 | 10 min | 70 min |

## T2.3: Cheer-only 硬缺口（73 条）— 等 cheer 跑平台/馆藏/函调

### T2.3.a L3 catalogue 53 条（除 5 已知 L4 catalogue）

**主要构成**：
- **40 条 MM1941 (minmeng1941.cn)**: 全 catalogue_only，需 cheer 跑平台 cookie 才能下原文
- **3 条 GXMM (广西民盟)**: 1941-1946 地方组织志（部分条目）
- **2 条 JS (江苏民盟)**: 江苏民盟史 / 民盟江苏简史
- **2 条 MH**: 民盟历史人物 / 章节索引
- 散落其他 6 条

**T2.3.a 决策点**：L3 catalogue 是否需要 cheer 跑平台/采购图书才能升级？OR 接受 L3 catalogue 作为「目录级 record」？

### T2.3.b 16 not_online（已在 T3 报告）— 全部 cheer-only

详见 work/domestic/codex_review_20260721.md T3 段。

### T2.3.c 4 surrogate（3 L4 ZLWEB + 1 BJDCMM 已在 T2.1）

⚠️ 已在 T2.1 列出。

### T2.3 复审决策

- **α**: 接受 L3 catalogue 作为「目录级 record」accept（53 条 × 1-2 min）→ ~90 min
- **β**: cheer 跑 minmeng1941.cn cookie / 采购图书 → 1-2h 馆内访问
- **γ**: 全部 deferred，等 sprint 38+ 后续 / cheer-only 7 件 P0 之一启动

---

## Codex 抽检推荐下一步（cheer 决策）

| 选项 | 内容 | 工作量 | 风险 |
|---|---|---|---|
| **α2** | T2.1 9 条批量 accept（包含刚修 URL 的闻一多 + 2 张 WM photo + 1 BJDCMM 剪影 + 3 张澜 L4 surrogate + 1 1941 社论） | 5 min | 低-中 |
| **β2** | T2.2 7 条 codex 抽检（含 NLC 1946 降级 + L4 catalogue 6 条抽样） | 70 min | 中 |
| **γ2** | T2.3 53 L3 catalogue + 16 not_online → cheer-only 7 件 P0 启动 | 1-2h | 高 |

**我建议先 α2**（9 条 T2.1 + 5 min）— 这是 T1 后第二批"低风险"自动 accept，能进一步消化 pending 247 → 238。如果 α2 后 cheer 还想要 β2，再跑 70 min 抽检。

如果 cheer 觉得 α2 也想保留谨慎态度，可以只 accept 5 条 L3（剔除 3 L4 ZLWEB/JFB + 1 L4 评估）。

---

## 数据一致性

本次 codex 抽检**不修改 candidates.jsonl**，仅生成本决策依据报告。如 cheer 同意 α2 选项，mavis 将另写 `accept_codex_review_tier2_20260721.py`（与 `accept_codex_review_tier1_20260721.py` 模板一致）跑批量 accept。
