# FRUS 10 篇批量翻译样本校验

- 翻译批次：`codex-batch-v1`
- 状态：`machine-draft-review-needed`
- 用途：验证术语统一、原文/译文并排阅读、中文检索和人工校订流程。

## 选文

| 文档 | 日期 | 片段 | 选取理由 |
|---|---|---:|---|
| frus1943China/d232 | July 31, 1943 | 2 | 1943 梁漱溟访谈，显示民盟前身的改革而非反国民党定位 |
| frus1943China/d272 | September 18, 1943 | 1 | 1943 中国民主政团同盟政治纲领线索 |
| frus1944v06/d287 | February 21, 1944 | 1 | 1944 张澜《中国需要真正的民主》摘要 |
| frus1944v06/d349 | May 24, 1944 | 1 | 1944 民盟前身关于民主改革和国共调和的声明 |
| frus1945v07/d573 | December 26, 1945 | 1 | 1945 中国民主同盟致马歇尔材料，说明组织来源和政治诉求 |
| frus1946v09/d31 | January 1, 1946 | 1 | 1946 政协代表席位和公开会议争议 |
| frus1946v10/d82 | September 11, 1946 | 1 | 1946 罗隆基、沈钧儒批评美国小组委员会 |
| frus1946v09/d735 | August 6, 1946 | 2 | 1946 昆明暗杀后民盟恐惧、流亡和转向判断 |
| frus1947v07/d279 | November 6, 1947 | 1 | 1947 政府处理民盟解散和非法状态的表述 |
| frus1949v08/d608 | September 24, 1949 | 2 | 1949 新政协筹备常务委员会中民盟人物位置 |

## 术语表

| 原词 | 固定译名 | 说明 |
|---|---|---|
| Democratic League | 中国民主同盟 | FRUS 1945 以后常见译名 |
| Chinese Democratic League | 中国民主同盟 | 与 Democratic League 同指民盟 |
| China Democratic League | 中国民主同盟 | 与 Chinese Democratic League 同指民盟 |
| Federation of Chinese Democratic Parties | 中国民主政团同盟 | 1941-1944 年资料中常见早期译名 |
| Political Consultative Council | 政治协商会议 | 1946 年 PCC |
| Political Consultative Conference | 政治协商会议 | 1949 年 PCC 或新政协语境 |
| People's Political Council | 国民参政会 | 战时政治机关 |
| Kuomintang | 国民党 | 保留为国民党 |
| Generalissimo | 委员长 | 通常指蒋介石 |
| General Marshall | 马歇尔将军 | George C. Marshall |
| Lo Lung-chi | 罗隆基 | 人名异写 |
| Liang Shu-ming | 梁漱溟 | 人名异写 |
| Chang Lan | 张澜 | FRUS 中也作 Chang Piao-fang |
| Shen Chun-ju | 沈钧儒 | 人名异写 |
| Huang Yen-pei | 黄炎培 | 人名异写 |
| Chang Po-chun | 章伯钧 | 人名异写 |
| Shih Liang | 史良 | 人名异写 |
| Peiping | 北平 | 1949 前后地名 |
| Nanking | 南京 | 历史地名 |
| Chungking | 重庆 | 历史地名 |
| Kweilin | 桂林 | 历史地名 |
| Kunming | 昆明 | 历史地名 |
| Yenan | 延安 | 历史地名 |

## 校验要点

- 译文按 `pages` 片段写入，不覆盖英文原文。
- 每条译文带 `zh-CN`、翻译批次和状态，便于后续人工校订。
- 术语统一采用 `data/translation_glossary.csv`；重点固定了 Democratic League、中国民主政团同盟、PCC、主要人名和地名。
- 当前译文状态仍是 `machine-draft-review-needed`，可用于检索和阅读体验验证，不应直接作为最终出版译文。

## 复核建议

- 第一轮人工校订优先检查人名、机构名、日期、引文口吻。
- 对 FRUS 中 `Democratic League` 在 1944 年前后是否应译为“中国民主政团同盟”或“中国民主同盟”，需要按文献日期和上下文逐条确认。
- 长文档后续应按页码或段落进一步切分，避免一个片段过长影响并排阅读。
