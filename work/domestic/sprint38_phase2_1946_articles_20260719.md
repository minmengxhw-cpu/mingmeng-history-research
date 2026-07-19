# Sprint38 阶段2：1946 报刊文章级整理

执行日期：2026-07-19  
范围：已有《光明報》1946 原刊扫描；按题名、作者、日期、版面边界拆分。

## 一、本轮完成

### 1. 新三號《為完成雙十節的歷史任務而奮鬥》止页闭合

| 项 | 内容 |
|---|---|
| ID | `domestic:NLC:guangmingbao-1946-issue03-double-ten-task-article` |
| 题名 / 作者 | 為完成雙十節的歷史任務而奮鬥 / 李平達 |
| 日期 | 1946-10-08 |
| 页界 | **PDF 第1页单页**（第2页转入他文） |
| 本地 | `work/domestic/guangmingbao_1946_phase2_pages/issue03/page-01.png` + `page-02.png` 边界 |
| 等级 | L1 / **needs_human_review**（不自动 accepted） |
| SHA256（整期） | `826fba6a608093972cf54dabf8a9a117ff6e1416767610d6d49a35c0c58328de` |

### 2. 新拆：民盟呼吁停战恢复和平电文

| 项 | 内容 |
|---|---|
| ID | `domestic:NLC:guangmingbao-1946-issue03-ceasefire-telegram` |
| 题名 | 民盟呼吁停战恢复和平电文 |
| 日期 | 1946-10-08（报面日期） |
| 页界 | PDF 第2页（未扩读第3页是否续文，保守） |
| 等级 | L1 / needs_human_review |
| 事件 | 1946旧政协、拒绝国大 |

### 3. 整期 16 页转图

`work/domestic/guangmingbao_1946_phase2_pages/issue03/page-01.png` … `page-16.png`

## 二、明确不拆（避免猜测）

| 期 | 原因 |
|---|---|
| 新六號首面社论 | 160dpi 仍难稳定读出中栏题名；保持整期 `issue06`，**不新建近似标题** |

## 三、既有 1946 文章级（本轮不重拆）

新一/二/四/五/七/八/九/十/十一号已有文章卡（部分 accepted）。详见既有 `minimax_phase2_*` 与 Codex 审核。

## 四、OCR 边界

本轮未把 OCR 写入正式引文；页界以页图目视为准。

## 五、阶段2后候选变化

- 候选：346 → **347**（+1 电文）  
- accepted：160 不变  
- 修改：issue03 双十文止页字段  

## 六、结论

阶段2可执行拆分已推进；新六號题名仍待更高清或人工馆方影像。  
**下一阶段：阶段3（五项硬缺口分项）。**
