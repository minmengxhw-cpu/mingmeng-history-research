# 研究工作台进展

## 已完成模块

- 全部文档列表：按等级与译文状态筛选。
- 双语阅读页：英文原文与中文译文并排显示，并保留 FRUS 来源链接。
- 中文全文搜索：支持中文译文和英文原文检索。
- 译文质量检查：按严重度、术语、英文残留、长度异常和核心初稿筛选。
- 校订任务队列：将多个质量提示合并为片段级任务，并按优先级排序。
- 单段校订页：可编辑中文译文、修改状态，并更新中文全文检索。
- 人物索引：按人物聚合相关 FRUS 文档和片段。
- 核心主题专题：按研究问题聚合原文、译文和校订入口。
- 地点索引：按南京、昆明、北平、重庆、上海等地点聚合事件线索。
- 机构索引：按中国民主同盟、国民党、中国共产党、美国国务院、美国驻华使馆等机构聚合事件线索。
- 地点/机构核心筛选：地点页和机构页可切换全部材料或只看核心文献。
- 首页继续研究入口：首页显示罗隆基、南京核心、民盟核心、研究卡片和核心校订入口，并列出高价值事件。
- 首页清单配置：`/focus` 可编辑首页继续研究入口和高价值事件范围，配置保存于 `data/home_focus.json`。
- 研究进度仪表盘：`/dashboard` 汇总资料库规模、译文覆盖、事件索引、质量提示和最近导出文件。
- 仪表盘建议校订：`/dashboard` 显示今日建议处理的 10 条校订任务，并提供校订、并排阅读、摘录卡片入口。
- 连续校订：校订页提供“下一条校订”和“保存并进入下一条”，可按优先级队列连续处理。
- 引用摘录卡片：生成可复制的短引文、参考文献、原文、译文、页码和 FRUS 来源。
- 术语批量回扫：已对罗隆基、张澜、黄炎培、张东荪、梁漱溟、李公朴、闻一多、北平、重庆、延安、沈阳等高频误译做批量修正。
- 年表视图：支持全库年表、人物年表和专题年表。
- 事件线索：按专题和人物生成事件节点，节点保留中文摘要、原文摘录、FRUS 链接、摘录卡片和并排阅读入口。
- 事件筛选：事件页可按事件标签、相关人物、地点和机构继续过滤，便于从“民盟”“南京”“中国民主同盟”“马歇尔调处”等线索切入。
- 事件研究卡片：可将单个人物或专题的事件节点整理成 Markdown 卡片，包含地点、机构、短引文、参考文献、原文摘录、中文译文和本库引用入口。
- 事件卡片导出：可按人物、专题、地点、机构导出 Markdown 文件，也可按主题标签、地点、机构分册。
- 导出目录：`exports/event_cards_index.md` 汇总所有事件研究卡片文件。
- Markdown 研究笔记导出：可按专题或人物导出原文摘录、译文、FRUS 链接和片段编号。

## 当前入口

- `/docs`
- `/`
- `/search?q=罗隆基`
- `/quality`
- `/tasks`
- `/people`
- `/topics`
- `/places`
- `/places/南京`
- `/places/南京?grade=core`
- `/organizations`
- `/organizations/中国民主同盟`
- `/organizations/中国民主同盟?grade=core`
- `/timeline`
- `/events`
- `/focus`
- `/dashboard`
- `/events?person=lo-lung-chi`
- `/events?person=lo-lung-chi&tag=民盟`
- `/events?person=lo-lung-chi&place=南京`
- `/events?person=lo-lung-chi&org=中国民主同盟`
- `/events?topic=kunming-assassinations`
- `/events/cards?person=lo-lung-chi`
- `/events/cards?topic=kunming-assassinations`
- `/cite/<page_id>`

## 下一阶段建议

1. 对 `/tasks` 的前 20 个高优先级片段进行人工风格校订。
2. 处理仪表盘建议的前 10 条校订任务。
3. 给质量检查增加批量“标记已复核”能力。
4. 引入 CIA、Wilson Center 和国内 PDF 时复用同一套全文、译文、质量检查、摘录卡片和事件线索流程。

## 最新事件索引

- 事件节点：1066
- 覆盖片段：385
- 带地点识别事件：1043
- 带机构识别事件：1047
- 罗隆基事件线索：98
- 昆明暗杀事件线索：47

## 最新质量扫描

- 风险提示：599
- 有提示片段：351
- 高优先级片段：194
- 严重误译提示：0

## 最新导出样本

- `exports/topic_kunming-assassinations_notes.md`
- `exports/person_lo-lung-chi_notes.md`
- `exports/event_cards_person_lo-lung-chi.md`
- `exports/event_cards_topic_kunming-assassinations.md`
- `exports/event_cards_place_南京.md`
- `exports/event_cards_organization_中国民主同盟.md`
- `exports/event_cards_person_lo-lung-chi_tag_民盟.md`
- `exports/event_cards_person_lo-lung-chi_tag_马歇尔调处.md`
- `exports/event_cards_person_lo-lung-chi_place_南京.md`
- `exports/event_cards_person_lo-lung-chi_organization_中国民主同盟.md`
- `exports/event_cards_index.md`
