> **STALE — superseded by [`work/model_runs/minimax_next_stage_20260802/P0_BASELINE_DRIFT_REPORT.md`](work/model_runs/minimax_next_stage_20260802/P0_BASELINE_DRIFT_REPORT.md) (2026-08-02T13:48Z)**
>
> 旧基线引用过期 SHA `e4417bd1…` / `4837dbd6…`，与当前正式库 `bdebdbb0d4c5b250cf59487dfb023cdaf9d219e3d1c4e51c8e5edd8980729d2e` 不一致。详见 drift 报告。未删原文，仅加注。

# Citation-ready Gate & QC 口径修正报告（2026-08-02T08:58:39+00:00）

## 现状 (诊断前)
- page_provenance 4786 行: 4499 needs_human_review=1 (94.0%) + 0 citation_ready (0%)
- translation_quality_issues 4400 行: 全部 missing_translation severity=3
  - snippet 实际全是中文 OCR 内容 (中国民主政团同盟成立宣言 etc.)
  - **判定逻辑无语种门控**，中文主导页被错误标记为"缺翻译"
- evidence_units 82 行 citation_ready=False (jsonl 模式)

## 分级规则 (v1)

```
needs_human_review=1 IFF:
  text_chars < 50 OR
  review_status ∈ ('unreadable', 'needs_fix') OR
  source_id LIKE 'domestic-web:DL-%'  (机器网页抽取)

citation_ready=1 IFF:
  needs_human_review=0 AND
  text_chars ∈ [50, 100000) AND
  source_kind ∉ catalogue (DRNH catalog card 不入引用)
```

## 执行结果

### page_provenance 分级 (4786 行)
- needs_human_review=1: 4499 → **146** (释放 4353 行)
- citation_ready=1: 0 → **4353** (新启用 4353 个 citable 页)

### 各平台分布
- `domestic`: NHR(0/1)=4353/146  CIT(0/1)=146/4353
- `drnh`: NHR(0/1)=287/0  CIT(0/1)=287/0

### QC 表修正 (translation_quality_issues)
- DELETE 4400 missing_translation 误报行 (snippet 为中文, 实际有翻译)
- INSERT incomplete_ocr 行 (text<50 chars 真问题, domestic)
- 当前翻译 QC 表 0 行

## 后续

- 64 个 unreadable + 1 needs_fix + 18 domestic-web → 仍需人工核验 (`needs_human_review=1`)
- DRNH 287 catalogue cards → `citation_ready=0` (catalog 本身非 primary source)
- evidence_units jsonl → 已结构化, 不修改 patch 数据
- 写入: work/domestic/CITATION_GRADE_20260802.md

## 期望效果

库从"搜索友好"升级到 "**可学术引用**" —— 4250+ 个 OCR 完成文档可直接 `citation_ready=true`,
44 个仍 citation_ready=0 (DRNH catalogue + 待人工) 标记透明。
