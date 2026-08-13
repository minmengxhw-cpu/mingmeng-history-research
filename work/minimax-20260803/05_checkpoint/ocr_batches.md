# OCR 批次调度

- 计划文件：216
- 切分批次：7
- 估计总时间：27.1 分钟

## 按优先级

### p1 (1 batches, 174 files, 174 pages, 23.2 min)
- `OCR-BATCH-p1-1946-1950-01` | 1946-1950 | 174 files / 174 pages / 23.2 min
  - 1946-1950 L1 关键件，优先排程; 大批量，建议分夜处理

### p2 (3 batches, 34 files, 34 pages, 3.4 min)
- `OCR-BATCH-p2-1944-1945-02` | 1944-1945 | 7 files / 7 pages / 0.7 min
  - L2 汇编，可补页级定位; 含民盟自身原件
- `OCR-BATCH-p2-1941-1943-03` | 1941-1943 | 15 files / 15 pages / 1.5 min
  - L2 汇编，可补页级定位; 含民盟自身原件
- `OCR-BATCH-p2-1946-1950-04` | 1946-1950 | 12 files / 12 pages / 1.2 min
  - L2 汇编，可补页级定位; 含民盟自身原件

### p3 (3 batches, 8 files, 8 pages, 0.5 min)
- `OCR-BATCH-p3-1944-1945-05` | 1944-1945 | 5 files / 5 pages / 0.3 min
  - L3 剪报 / 待处理 LX; 含民盟自身原件
- `OCR-BATCH-p3-1941-1943-06` | 1941-1943 | 2 files / 2 pages / 0.1 min
  - L3 剪报 / 待处理 LX
- `OCR-BATCH-p3-1946-1950-07` | 1946-1950 | 1 files / 1 pages / 0.1 min
  - L3 剪报 / 待处理 LX

## 阶段 2 建议

1. **第一晚**: p1 + 1946-1950（高价值关键件，估计 1-2 晚可完成）
2. **第二晚**: p2 + 1944-1945（汇编类，可补页级定位）
3. **第三晚**: p3 + 1941-1943（最早事件，需要 cheer-only 接力）

每批跑完后：
- 重新跑 `python3 scripts/minimax/minimax_20260803_ocr_manifest.py --done <batch_id>`
- 升级 passing 候选的 citation_ready（人工复核后）
- 跑 `python3 scripts/minimax/minimax_20260803_three_lists.py` 重新生成清单