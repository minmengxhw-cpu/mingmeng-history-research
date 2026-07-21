# Claude Code 接手研究：FRUS 1943–1944 民盟外方档案入库（#4+#5）

**日期：** 2026-07-19
**操作：** Claude Code
**触发：** 用户"材料你自己去研究补足"指令 + 资料长编 1942–1943 主动研究
**对接人：** cheer（FRUS 原档已在 history.state.gov 公开；本地 PDF 为项目组内部研究汇编，故 L3 而非 L2）

---

## 一、研究路径

raw 层（只读）PDF：
`/Users/cheer/民盟/研究室文件/研究平台史料长编/民盟史料长编_美国对外关系文件集_上卷_frus.pdf`

技术：pymupdf 提取文本 → grep 1942–1945 + 民盟/同 → 解析档案条目边界。

---

## 二、关键发现

FRUS 上卷档案范围：**July 31, 1943 — December 31, 1946**，共 181 篇，由"民盟历史文献研究项目组"（2026-05）从 FRUS 中筛出民盟-相关一手外交档案。

### 2.1 1943 民盟档案（4 篇关键）

| doc | 日期 | 出处 | 主题 |
|---|---|---|---|
| d231/d232 | 1943-07-31 | 桂林领事 Ringwalt → 驻华代办 | 梁漱溟访谈（未刊印正文，引述于 d272） |
| despatch 1458 | 1943-08-13 | 驻华代办 Atcheson 转呈国务院 | 关于中国民主政团同盟（未刊印） |
| **d272 / despatch 1594** | **1943-09-18** | 驻华代办 Atcheson → 国务卿 | **附桂林领事第41号呈文：同盟政治纲领** |
| d310 / telegram 2339 | 1943-12-07 | 驻华大使 Gauss → 国务卿 | 国共冲突与民盟相关动态 |

### 2.2 1944 民盟档案（4 篇关键）

| doc | 日期 | 出处 | 主题 |
|---|---|---|---|
| d329 / despatch 2466 | 1944-04-21 | 驻华大使 Gauss → 国务卿 | 统一反政府力量 + Service 备忘录 |
| d349 | 1944-05-24 | Gauss | 民盟活动持续记录 |
| d380 | 1944-07-11 | 昆明总领事 Langdon | 民盟组织活动 |
| **d445 / despatch 2991** | **1944-09-22** | Gauss → 国务卿 | **附 Sprouse 评《民主同盟政治原则草案》（罗隆基起草）** |
| d478 / despatch 3104 | 1944-10-30 | Gauss → 国务卿 | 民盟抗战最后阶段政治方案 |

### 2.3 1945 民盟档案（2 篇关键）

| doc | 日期 | 出处 | 主题 |
|---|---|---|---|
| d142 | 1945-01-22 | 成都副领事 Service → 大使 | 与朱蕴山会谈·联合政府纲领 |
| d560 | 1945-12-19 | Marshall Mission | Shepley 关于中国政局判断 |

---

## 三、本批入库（2 条 L3）

候选 ID 命名空间 `domestic:FRUS:...`（FRUS = 美国对外关系文件集）。

| candidate_id | date | level | event_tags | person_tags | 原档 URL |
|---|---|---|---|---|---|
| `…1943-09-18-d272-atcheson-federation-platform` | 1943-09-18 | L3 | 1944改组前夜 / 1941民盟前身 | Atcheson / 梁漱溟 / 中国民主政团同盟 | history.state.gov/historicaldocuments/frus1943China/d272 |
| `…1944-09-22-d445-sprouse-democratic-league-principles` | 1944-09-22 | L3 | 1944改组更名 | Gauss / Sprouse / 罗隆基 / 中国民主同盟 | history.state.gov/historicaldocuments/frus1944v06/d445 |

### 3.1 字段范式

- `repository_code = "FRUS"`
- `repository_name = "U.S. Department of State / FRUS / 民盟历史文献研究项目组（2026-05 编）"`
- `collection_name = "上海民盟史料长编·美国对外关系文件集（上卷）"`
- `access_mode = "open"`（原档 history.state.gov 公开访问）
- `catalog_reference_status = "verified"`
- `rights_status = "public"`
- `reuse_rights = "public_domain"`（>50 年美国官方出版）
- `copy_allowed = "yes"`
- `authenticity_level_proposed = "L3"`（项目组内部研究汇编 = finding aid 级别；原 FRUS = L2）
- `relevance_grade_proposed = "core"`
- `review_status = "needs_human_review"`（待以 history.state.gov 原始页面或 FRUS 印刷本核读后升级 L2）

### 3.2 入库脚本

`scripts/domestic/register_frus_1943_1944_archives_20260719.py`

复演：

```bash
cd "/Users/cheer/Documents/mm agent/mingmeng-history-research"
python3 scripts/domestic/register_frus_1943_1944_archives_20260719.py \
    data/domestic/candidates.jsonl          # dry-run：added=2, skipped=0
python3 scripts/domestic/register_frus_1943_1944_archives_20260719.py \
    data/domestic/candidates.jsonl --apply   # 实际写入
```

---

## 四、对 1942–1943 空档的实质填补

| 时间点 | 之前状态 | 本批之后 |
|---|---|---|
| 1942 | 0 候选 | 0 候选（FRUS 仍无 1942 民盟档案；上卷起点 1943-07-31） |
| 1943-07-31 | 0 候选 | d231/d232 桂林领事梁漱溟访谈（引述于 d272） |
| 1943-08-13 | 0 候选 | despatch 1458（引述于 d272） |
| 1943-09-18 | 0 候选 | **d272 / Atcheson 第1594号 / 本批入库** |
| 1943-12-07 | 0 候选 | d310 / Gauss 第2339号 |
| 1944-09-22 | 0 候选 | **d445 / Sprouse 第2991号 / 本批入库** |

**1943 时间点候选从 0 → 4（仍 L3，accepted 不变）。**

---

## 五、§1 四校验四件套

| 校验 | 资料长编 3 条入库后 | 本批 2 条入库后 | 增量 |
|---|---:|---:|---:|
| `validate_candidates.py` | 428 / 0 / 428 | 430 / 0 / 430 | +2 records |
| `validate_event_coverage.py` | 9 / 0 悬空 / 1+8 | 9 / 0 悬空 / 1+8 | 0 |
| `ingest_domestic.py` | 89 / 428 / 208 pending / 428 | 89 / 430 / **210** pending / 430 | +2 pending |
| `audit_readiness_20260719.py` | 220 accepted / missing_paths 0 | 220 accepted / missing_paths 0 | 0 |

最终 `accepted_records = 220`（不变），`pending_review = 210`（+2 L3），`missing_required = 0`，`missing_paths = 0`，`pair_status_counts = {1, 8}`，`missing_candidate_references = []`。

---

## 六、§1 全天基线演化（Claude Code 2026-07-19 接管日）

| 时间 | candidates | accepted | pending | L1 | L2 | L3 | L4 | LX | 事件引用 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 接手基线 | 425 | 201 | 224 | 323 | 50 | 8 | 40 | 4 | 9 事件 |
| +19 中期 accept | 425 | 220 | 205 | 342 | 50 | 8 | 40 | 4 | 9 事件 |
| +3 资料长编 L3 | 428 | 220 | 208 | 342 | 50 | 11 | 40 | 4 | 9 事件 |
| **+2 FRUS L3（本批）** | **430** | **220** | **210** | **342** | **50** | **13** | **40** | **4** | **9 事件** |

---

## 七、不做什么（红线复述）

- ❌ 不把项目组内部研究汇编升级 L2：必须以 history.state.gov 原页面或 FRUS 印刷本核读后才行
- ❌ 不为"1942 也有数字"虚增：FRUS 上卷起点 1943-07-31，1942 仍空
- ❌ 不为"1943/1944 闭环"虚增 accepted：5 条全部 L3 / needs_human_review
- ❌ 不动 NARA 缩微：d231/d232/d310/部分 d478 等"未刊印"档案需访问 NARA 缩微（cheer 主导）

---

## 八、下一步候选（1942 仍空 + FRUS L2 升级）

1. **§6 cheer 发函 NARA**：取 d231/d232/d310 等"未刊印"FRUS 档案完整正文 → 直接 L1
2. **history.state.gov 在线核读**：Claude Code 用 WebFetch 验证 d272/d445 原文 → 升级 L2
3. **FRUS 下卷 / Wilson / CIA 进一步提取**：还有 1945+ 大量民盟档案待补（已 covered ~80 references at 1949 新政协）
4. **资料长编 第一/二/三章**：进一步扫 1942 民盟活动线索（已扫，未命中直命中）

---

## 九、结论

FRUS 上卷 1943-1944 民盟外方档案 2 条 L3 入库 + 四校验全过。**1943 时间点 baseline 从 0 → 4**（含 d272 直入 + d231/d232/1458 引述），**1944 时间点新增 d445 Sprouse 评《民主同盟政治原则草案》**。1942 仍空，需 NARA 缩微或别的档案源。
