# Claude Code 接手核对：B1–B5 五项原件硬缺口 OPEN 状态

**日期：** 2026-07-19
**操作：** Claude Code
**目的：** §6 处理五项原件硬缺口 → 状态核对（不虚报闭环）
**对接人：** cheer（需发函回传）

---

## 一、五项硬缺口卡（按 handover §4）

| ID | 目标 | 缺口卡 candidate_id | 等级 | 当前状态 |
|---|---|---|---|---|
| **B1** | 1941-10-10/16 香港《光明報》原刊 | `domestic:HKU:guangmingbao-1941-microform-holdings` | L2 | needs_human_review |
| **B2** | 1946《民主同盟文獻》政治报告正文 | `domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap` | L3 | needs_human_review |
| **B3** | 1947-10-27 内政部公函/公报原页 | `domestic:MMHIST:league-banned-1947-10-27` | L2 | needs_human_review |
| **B4** | 1947-11-06 总部解散独立印本 | `domestic:MMHIST:league-dissolution-announcement-1947-11-06` | L2 | needs_human_review |
| **B5** | 1947-11-04 北平《新民报》原版 | `domestic:GXMM:xinminbao-professors-statement-1947-11-04` | L4 | needs_human_review |

5 张缺口卡**全部以 needs_human_review 状态存在于 candidates.jsonl**，未被虚报闭环。

---

## 二、B1 关联候选（1941 香港光明报整组待 HKU 缩微回传）

| candidate_id | L | 状态 | 说明 |
|---|---|---|---|
| `domestic:WS:democratic-league-declaration-1941` | LX | needs_human_review | 公开转录，无原刊 |
| `domestic:WS:democratic-movement-editorial-1941` | L3 | needs_human_review | 解放日报社论公开转录 |
| `domestic:MMHIST:formation-declaration-1941` | L2 | **accepted** | 历史文献汇编 |
| `domestic:MMSH:guangmingbao-formation-editorial-1941` | L4 | needs_human_review | 二级网页 |
| `domestic:LNU:guangmingbao-index-1941` | L3 | needs_human_review | 香港工运剪报索引（非光明报） |
| `domestic:HKU:guangmingbao-1941-microform-holdings` | L2 | needs_human_review | 港大缩微馆藏清单（缺原刊影像） |
| `domestic:HKU:guangmingbao-primo-record` | L2 | needs_human_review | JULAC/Primo 书目记录 |
| `domestic:NLC:minmeng-wenxian-1946-formation-declaration` | L2 | **accepted** | 1946 文獻汇编 |
| `domestic:NLC:minmeng-wenxian-1946-ten-program` | L2 | **accepted** | 1946 文獻汇编 |

B1 缺口：**港大 HKC 951 G91 M 缩微件未到手** → 一旦 cheer 发函回传，**可立即写新 L1 + SHA256 + 页界**：
- 1941-09-18 创刊号
- 1941-10-10 成立宣言号
- 1941-10-16 社论号
- 1941-10-28 民盟动态号
- 至 1941-12-12 末日刊

**操作约束：** 不把"二次转录""解放日报社论""汇编 L2""网页 L4"升 L1 假冒 B1 原件。

---

## 三、B2 缺口卡结构

```text
domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap
  L3  needs_human_review
  缺口属性：1946《民主同盟文獻》NLC416 + NLC511 双扫描目录错位
  现最强替代：言论集 L2（PDF 19—36 体文 / 14—19 宣言）+ MMHIST L2（汇编）—— **不填此缺口**
```

**B2 缺口：** 政治报告"正文"原始影像（1945-10 一大政治报告，沈钧儒宣读）—— 即使言论集与 MMHIST 有同文双源，仍非 1945 原件。

**修复路径：** 二史馆 / 港大 / 北大 / 复旦 / 哥伦比亚大学 / 国会图书馆缩微
**操作约束：** 不把言论集/MMHIST 升 L1 假冒 B2 原件。

---

## 四、B3 / B4 / B5 缺口卡结构（1947 解散事件链）

| B3 | `domestic:MMHIST:league-banned-1947-10-27` | L2  needs_human_review |
| B4 | `domestic:MMHIST:league-dissolution-announcement-1947-11-06` | L2  needs_human_review |
| B5 | `domestic:GXMM:xinminbao-professors-statement-1947-11-04` | L4  needs_human_review |

三张卡都已挂在事件 `domestic-1947-illegal-dissolution`（当前 80 候选 + 19 = 99 条）。

**修复路径：**
- B3 → 二史馆 1354 函（cheer_P0_dual_launch_20260719.md 模板就绪）
- B4 → 二史馆或民盟档案
- B5 → 孔夫子 / 校史馆

**操作约束：** 不为"闭环"猜测 1947 公函页码；不把汇编 L2 / 网页 L4 升 L1。

---

## 五、不做什么（红线复述）

- ❌ **不写"伪已取得原件"**：cheer 发函回传前，B1/B2/B3/B4/B5 全部维持 OPEN。
- ❌ **不升 L4/LX → L1 假冒**：HTTP 二次转录、现代网页、研究论文均不可假冒原件。
- ❌ **不自动 commit**：缺口卡保持 needs_human_review，等用户手动复核。
- ❌ **不猜测页码**：1947-10-27 公函、1947-11-06 公告独立印本的具体页码，必须等馆藏回传。

---

## 六、cheer P0 双路径发函（hand-off §3.5 模板）

- `work/domestic/cheer_P0_dual_launch_20260719.md` — 双路径一页总册
- `work/domestic/cheer_action_hku_microform_20260719.md` — 港大缩微执行清单（B1 + 部分 B2）
- `work/domestic/cheer_action_shac_1354_20260719.md` — 二史馆 1354 执行清单（B3 / B4）
- `work/domestic/hku_guangmingbao_1941_request_template_20260719.md` — 港大邮件模板 v2.1
- `work/domestic/shac_1354_request_template_20260719.md` — 二史馆模板 v1.1
- `work/domestic/cheer_only_queue_20260719.md` — 6 件 cheer-only 总表

港大邮箱：`libspeco@hku.hk`；索书号：`HKC 951 G91 M`。

---

## 七、cheer 回传后的 Claude Code 接收流程

一旦 cheer 提供扫描/PDF：

1. **核对原件三要件**：原件 + 扫描 + 页图（page-NN.png 落到 `work/domestic/continue_pages/<期号>/`）
2. **写新候选条目**（`data/domestic/candidates.jsonl`）：
   - 复制 B1/B3/B4/B5 缺口卡的元信息模板
   - 改 `repository_code`、`archive_item`（如港大缩微号 / 二史馆 6-5-1216 子件）
   - 增 `source_url`（原件 PDF URL）、`evidence_locator`（含 SHA256 与页图）
   - `authenticity_level_proposed = "L1"`、`relevance_grade_proposed = "core"`（或按实际）
   - `review_status = "accepted"`、`reviewed_by = "claude-code"`、`reviewed_at = 2026-07-19`（回传当日）
   - `review_note` 标注"原件扫描回传记录级接受（cheer 提供）"
3. **更新 event_coverage**：B1 → `domestic-1941-formation`（新增）；B2 → `domestic-1945-first-congress`（新增）；B3/B4 → `domestic-1947-illegal-dissolution`（已有）；B5 → 同事件
4. **更新 source_registry**（若新馆藏）
5. **跑 §1 四校验**
6. **追加 wiki log**（wiki/log.md 一行）

---

## 八、§1 校验状态

本核对未触动数据文件，校验数字未变：

- candidates: 425 / 0 / 425 ✅
- event_coverage: 9 events / 0 悬空 / 1+8 pair ✅
- ingest: 89 / 425 / 205 pending / 425 ✅
- audit: 220 accepted / missing_paths 0 ✅

---

## 九、结论

**5 张缺口卡全部以 needs_human_review 状态正确跟踪，未虚报闭环。**

Claude Code 不在 cheer 发函回传前可推进 B1–B5 的实质修复。**#6 任务保持 in_progress，状态正常**，等待 cheer 行动。
