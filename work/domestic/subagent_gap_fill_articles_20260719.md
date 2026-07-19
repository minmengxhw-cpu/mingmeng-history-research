# Gap-fill 文章级执行报告（新六號题名 + 新二十二暂缓项）

- **日期**：2026-07-19  
- **执行**：grok（mingmeng-history-research 执行 agent）  
- **范围**：任务 A（1946 新六號中栏社论题名）、任务 B（1947 新二十二暂缓项）、任务 C（校验 + 本报告）  
- **禁令遵守**：不自动 `accepted`；不猜测作者；不 git commit  

## 0. 结果总览

| 项 | 结果 |
|----|------|
| 本轮**新建**文章候选 | **0** |
| 新建 IDs | （无） |
| 新六號是否建卡 | **否**（负向：无与新五號同型的大字题名区） |
| 新二十二暂缓项是否建卡 | **否**（全部登记「故意不拆」） |
| `validate_candidates` | **通过** 405/405 |
| `validate_event_coverage` | **通过** missing=[] |

---

## 1. 任务 A：1946 新六號中栏社论题名

### 1.1 渲染与裁切

| 项 | 路径 / 参数 |
|----|-------------|
| PDF | `data/domestic/press_scans/NLC404-01J000514-10427_光明報_1946年6期.pdf` |
| 页图目录 | `work/domestic/guangmingbao_1946_phase2_pages/issue06/` |
| 本轮 pymupdf 全页 | `page-01-hi180.png`（180dpi）、`page-01-hi200.png`（200dpi＝2067×2645）、`page-01-hi240.png`（240dpi）、`page-02-hi200.png`（边界） |
| 中栏/题名裁切 | `crops_hi200/`、`crops_hi240/`、`crops_hi300/`（含 `center_title`、`shehun_and_right`、`far_right_col`、`editorial_all_right_half`、竖条带等） |

渲染方式：`fitz.Matrix(dpi/72)`，clip 按页矩形比例裁切。

### 1.2 目视结论（对照新五號）

| 对照 | 新五號（已拆社论） | 新六號（本轮） |
|------|-------------------|----------------|
| 社论标 | 有「社論」徽 | 有「社論」徽（清晰） |
| 大字题名 | 中栏旁有**显著放大**竖排题《為赴京的同盟同志們！》，与正文字号明显不同 | **无**同等放大题名块 |
| 起读正文（RTL 最右栏） | 题名后另起正文 | 日期线下即同字号竖排正文起句 |

新六號最右栏起句（300dpi 可逐字）大致为：

> 從政協決議成立到今天已經十個月了。今天，在野黨派無黨派人士和在朝的國民黨……

此句是**社论正文起笔**，排版上与后续各栏同级，**不能**按本库「题名—正文」版式标准升为文章题名。

### 1.3 建卡决定：**不新建**

**负向原因（稳定、可复查）：**

1. ≥180dpi（至 300dpi）仍看不到与新五／新九／新十号同型的**大字题名区**；  
2. 起句可读 ≠ 题名可稳定辨认；若将起句当题名，会把正文首句误登为题，且与既有 Codex／Sprint38「题名不清不拆」口径冲突；  
3. 既有 minimax 近似题「從政協決議成立到今天**已**十個月了」较目视起句少「經」字，本身已说明题名层不稳定；  
4. 整期记录 `domestic:NLC:guangmingbao-1946-issue06` 已是 **accepted L1**，足以承载期次身份；文章级待有大字题或目录互证后再拆。

### 1.4 既有 issue06 文章卡（本轮不删、不改 status，仅审计标注）

| candidate_id | 题名 | 问题 |
|--------------|------|------|
| `…issue06-editorial-pcc-ten-months` | 從政協決議成立到今天已十個月了 | 把正文起句当题；字面与目视「已經」不一致；建议人工降级/撤回 |
| `…issue06-shen-zhiyuan-truce-statement-review` | 評蔣主席的停戰令和時局聲明 | 与 `…issue07-shen-zhiyuan-truce-statement-review` 题名撞车；新六號第1页高清未见该署名文稳定共现 |
| `…issue06-qian-jiaju-unequal-treaty` | 不平等待遇的新條約 | 同上，疑与 issue07 重复误挂 |

→ **cheer/Codex 人工队列**：复核是否撤回上述 3 条 minimax 卡，避免与 issue07 双挂。

---

## 2. 任务 B：新二十二暫缓项

页图齐备：`work/domestic/continue_pages/1947_22/page-01.png`–`page-20.png`。  
本轮辅助裁切：`work/domestic/continue_pages/1947_22/crops/gap_fill/`（p2 短評、p3 续栏、p10 左栏、p19 等）。

### 2.1 封面目录（RTL）核对

- （社論）為爭取基本的人權而奮鬥 + **短評四則**（目录**不列**各则作者）  
- 已拆署名文：鄧初民、陸詒、張曼筠、胡仲持…（见既有 21 篇报告）  
- 通讯：烈風／理晋 等  

### 2.2 故意不拆清单

| 版面 | 可见题名（目视） | 署名 | 页界 | 决定 |
|------|------------------|------|------|------|
| p2 下「短評」栏 | 《魏特邁將軍此來何為？》 | **无**独立署名；文末偶见单字括注，不足作作者 | 短評栏内，与社论下半同页 | **故意不拆** |
| p2 下「短評」栏 | 《總動員就是搜刮》 | 文末有「（藥）」类单字，**不扩写、不猜全名**；非题下署名 | 同上 | **故意不拆** |
| p3 中下（社论结束后） | 《廣東也應要求自治》 | 文末「（史）」类单字，同上 | 与邻栏交错，页界可估但署名不稳 | **故意不拆** |
| p3 下 | 《香港工商業家的自救之路》 | 文末单字括注，同上 | 止页近 p3 末 | **故意不拆** |
| p10 左栏 | 《我們要學習》 | 本栏**未见**「胡仲持」与题名同栏共现；封面长题「我們要學習韜奮的精神」与 p11《習韜奮精神》关系未锁 | 不单独建卡 | **故意不拆** |
| p19 | 《牧野之戰》 | 题名清，**署名未稳**；目录无此独立条（或属读史栏延伸） | 单页可读，作者未共现 | **故意不拆** |
| 广告／有利刊物等 | — | — | — | 非文章 |

> 说明：先前报告中的「為什麼特輯再來一次」在本轮 p2–p3 高清带扫中**未稳定复现**为独立大题；短評四则目视为上表魏特邁／總動員／廣東自治／香港工商四则。不据记忆补题。

### 2.3 建卡决定：**0 条**

规则执行：**有署名且页界清才建卡**；短評四则仅有栏标、无题下署名 → 一律故意不拆。  
既有 `…issue22-fight-for-human-rights-editorial` 与 21 篇署名纪念文保持不动（不改 accepted）。

---

## 3. 任务 C：校验

```text
$ python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
{"records": 405, "failed": 0, "passed": 405}

$ python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
{"candidate_ids": 405, "events": 9, "missing_candidate_references": [], "pair_status_counts": {"pair_available": 1, "pair_partial": 8}}
```

| 指标 | 值 |
|------|---:|
| records | 405 |
| failed | 0 |
| accepted | 165 |
| needs_human_review | 240 |
| L1 / L2 / L3 / L4 / LX | 304 / 49 / 8 / 40 / 4 |
| events | 9 |
| missing_candidate_references | [] |

本轮**未**向 `candidates.jsonl` / `event_coverage.json` 写入新行。

---

## 4. 产出文件

1. 本报告：`work/domestic/subagent_gap_fill_articles_20260719.md`  
2. 新六號高清：`…/issue06/page-01-hi{180,200,240}.png` + `crops_hi{200,240,300}/`  
3. 新二十二 gap 裁切：`…/1947_22/crops/gap_fill/`  

---

## 5. 返回摘要（给编排层）

| 问 | 答 |
|----|----|
| 新建条数 | **0** |
| 新建 IDs | （无） |
| 新六是否建卡 | **否**（无稳定大字题名；正文起句可读但不升题） |
| 校验结果 | candidates **405 pass**；event_coverage **missing=[]** |
| 后续人工 | 复核是否撤回 issue06 三条 minimax 文章卡；短評单字括注是否另立「笔名短評」规范 |

---

## 6. 明确未做

- 未自动 accepted  
- 未猜测短評作者全名  
- 未 git commit  
- 未全文转录；OCR 仅历史辅助，不作本轮引文  
