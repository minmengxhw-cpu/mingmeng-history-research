# 项目收口修正报告（2026-08-13）

## 已执行

- MiniMax 生产线与 DeepSeek 审计线以 squash 方式汇入集成分支，提交身份统一为 `xiaoban`。
- 清除仓库内旧机器的绝对项目根路径，脚本改为仓库根或环境变量寻址。
- 正式引用门禁改为：`human_verified`、`needs_human_review=0`、存在人工复核说明，三项缺一不可。
- 4,271 个只有机器状态、没有人工复核说明的页面已从 `citation_ready` 降级；原文本、OCR、provenance 均保留。
- 62 篇日期缺失文档用唯一关联候选的明确日期回填；日期缺失从 141 降至 79。
- 国内摘录页不再为未过人工门禁的页面生成正式引文，只保留检索阅读入口。
- 新增正式数据库 manifest 和 `MINGMENG_RESEARCH_DB` 外部数据库路径支持。

## 正式库结果

| 指标 | 结果 |
|---|---:|
| SHA256 | `326926341e6811a4687b4c08b4825468071aa3a4259e6a844f2dae0891a28491` |
| documents | 1,386 |
| domestic documents | 525 |
| pages / page_fts | 6,157 / 6,157 |
| formal citation pages | 0 |
| domestic pages missing provenance | 577 |
| domestic documents missing date | 79 |
| integrity / FK | ok / 0 |

正式引用数归零是口径纠偏，不是资料丢失。机器核验页继续用于阅读和检索，待人工逐页确认后才能重新晋升。

## 保留问题

- 577 页缺少 provenance，不能通过模型猜测补齐。
- 79 篇文档没有可确定日期。
- 1941—1943 一手原件仍是主要内容缺口。
- MiniMax 计划中的 OCR 与人工抽检尚未执行，不能伪报完成。
