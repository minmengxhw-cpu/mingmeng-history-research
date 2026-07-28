# MMDA 1942–1943 原件核验队列（2026-07-28）

本报告由主库 `domestic_candidates` 只读生成，不下载、不 OCR、不修改 SQLite。
当前条目均为民盟全媒体数据库目录记录；在授权浏览器会话取得正文 PDF/完整图片前，不能转为正式正文入库。

- 队列总数：8
- P1 同期组织原始证据候选：3
- P2 同期一手候选：0
- P3 跨期整理史候选：5
- 当前统一动作：用户登录后逐条核验详情页、正文入口、原件类型和权限状态
- 当前统一门控：没有取得正文 PDF/完整原图，不启动 OCR，不写入正文层，不标记 citation_ready

## 队列

| 优先级 | 日期 | 标题 | 目录定位 | 当前状态 |
|---:|---|---|---|---|
| P1 | 1942 | 陕西省委统战部关于民盟陕西省支部委员人选文件 | `minmeng1941.cn/outline?page=11&ChannelID=9317&resultid=2767#DDE_161` | login; catalogue_only_online |
| P1 | 1942 | 陕西省支部筹备委员会名单 | `minmeng1941.cn/outline?page=11&ChannelID=9317&resultid=2767#DDE_164` | login; catalogue_only_online |
| P1 | 1943 | 西北局关于第二次扩大会议情况报告 | `minmeng1941.cn/outline?page=13&ChannelID=9317&resultid=2767#DDE_185` | login; catalogue_only_online |
| P3 | 1942-1949 | 民盟在陕西 | `minmeng1941.cn/outline?page=10&ChannelID=9317&resultid=2767#DDE_144` | login; catalogue_only_online |
| P3 | 1942-1949 | 民盟在陕西（精） | `minmeng1941.cn/outline?page=10&ChannelID=9317&resultid=2767#DDE_145` | login; catalogue_only_online |
| P3 | 1942-1949 | 西安市民盟西北总支部秘密活动地 | `minmeng1941.cn/outline?page=13&ChannelID=9317&resultid=2767#DDE_184` | login; catalogue_only_online |
| P3 | 1942-2012 | 陕西民盟 70 年 | `minmeng1941.cn/outline?page=11&ChannelID=9317&resultid=2767#DDE_158` | login; catalogue_only_online |
| P3 | 1942-2012 | 陕西民盟史 | `minmeng1941.cn/outline?page=11&ChannelID=9317&resultid=2767#DDE_159` | login; catalogue_only_online |

## 执行顺序

1. 先处理 P1：陕西支部委员人选、支部筹备委员会名单、西北局第二次扩大会议报告。
2. 再处理 P3 中的《民盟在陕西》系列和西安市秘密活动地点条目；它们用于组织史定位和与 P1 原始记录互证。
3. 最后处理 P3：陕西民盟史、陕西民盟 70 年；仅作为整理史和线索，不替代同期原件。
4. 每条下载后保留原文件名、详情 URL、正文 URL、SHA256 和权限/版权说明，再交给 PaddleOCR 做页级试跑。
