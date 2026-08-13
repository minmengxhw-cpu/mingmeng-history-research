# LX 4 条升级提案

LX = 等级未确认。本节对 LX 候选逐条评估升级建议。

评估维度：
- 是否 source_url
- 是否 catalog_reference
- 是否 document_date
- 是否 creator
- URL 主机是否为 zh.wikisource.org

## 决策矩阵

| 条件 | 等级 | 理由 |
|---|---|---|
| 4 字段全有 + wikisource URL | L1 | 公开转录 + 完整溯源 |
| 4 字段全有 + 非 wikisource | L2 | 公开转录 + 完整溯源 |
| 3 字段 | L4 | 二手呈现 |
| < 3 字段 | LX | 继续人工复核 |

## 升级提案

## 阶段 2 行动项

- **L1 升级候选**：0 条
- **L2 升级候选**：0 条
- **L4 降级候选**：0 条
- **保持 LX**：0 条

**实施步骤**：
1. 跑 `python3 scripts/minimax/minimax_20260803_lx_apply.py`
2. 对每条 L1 升级候选，复核 source_url 实际可访问性 + 文本是否真包含 title
3. 通过后写入 `staging_domestic_candidates.authenticity_level_accepted` = 'L1'
4. 重新跑 `three_lists.py` 生成新清单