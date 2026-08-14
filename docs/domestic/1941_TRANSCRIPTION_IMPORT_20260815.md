# 1941 成立宣言公开转录导入记录（2026-08-15）

本批次把一份公开的后期电子转录纳入正式检索库，目的仅是提供全文检索、关键词定位和版本对读入口；它不关闭 1941 年《光明報》原刊影像、成立会议底本或版本关系的主证据缺口。

## 来源与边界

| 字段 | 值 |
| --- | --- |
| 公开页面 | <https://zh.wikisource.org/zh-hans/中国民主政团同盟成立宣言> |
| 本地快照 | `data/domestic/official_research_public_20260730/html/GDC2-0087_中国民主政团同盟成立宣言_025.txt` |
| SHA256 | `c9956d88c9fb6b5094849ca7c468c46c6a41c97d935d2303c3bdfdd768d4978c` |
| 文件大小 | 7,414 bytes |
| 抽取文本 | 1,436 字符 |
| 资料层 | `later_transcription` / `LX` |
| OCR | 未执行；来源本身已有电子文本 |
| 引用状态 | `review_only`，`citation_ready=false` |

## 正式库绑定

- 候选：`domestic:WS:democratic-league-declaration-1941`
- 文档：`domestic-text/WS:formation-declaration-1941`，正式文档 ID `1599`
- 页记录：正式页 ID `20931`
- 页级状态：`review_only`，`needs_human_review=true`
- 研究包和来源地图均明确标注：这是后期公开转录，不是 1941 年《光明報》原刊影像或成立会议底本。

## 归属修复

导入前发现该公开转录候选错误指向 1946 年《民主同盟文獻》重印本文档 ID `1349`。本批次在同一事务中完成归属修复：

- 文档 `1349` 恢复归属 `domestic:NLC:minmeng-wenxian-1946-formation-declaration`；
- 公开转录单独归属文档 `1599`；
- 未删除或改写既有来源正文与页记录，只修复候选—文档绑定关系。

## 验收

- 导入前已生成正式库备份；
- dry-run 与 apply 均通过；
- `PRAGMA integrity_check`：`ok`；
- 外键违规：`0`；
- 页表与 FTS：双向对齐；
- 正式库 manifest 已更新；
- 1941 事件证据链和来源地图已加入页 `20931`，但严格引用页和一手闭环计数不增加。

后续如取得 1941 年原刊或成立会议原始影像，应作为独立来源新建来源卡和页级 provenance，不覆盖本转录层，也不把二者自动合并。
