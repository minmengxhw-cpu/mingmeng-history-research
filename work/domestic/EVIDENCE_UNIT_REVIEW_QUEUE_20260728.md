# 国内证据单元人工复核队列（2026-07-28）

本队列只读生成，不修改主库；所有条目在人工复核前保持 `citation_ready=false`。

- 总数：82
- P1 一手/高价值 OCR：54
- P2 同期候选 OCR：25
- P3 已标记 verified、仍需引用定位复核：3

## 复核门控

1. 对照原图或原 PDF，确认 OCR 字符、日期、标题和文章边界。
2. 写入页码/版面/详情 URL 等可复核定位；不能只凭 OCR 片段升为引用级。
3. 处理完成后再单独生成人工决策文件；本队列本身不执行数据库写入。

## 优先批次

| 优先级 | ID | 日期 | 原题名 | 来源 | OCR | 边界 | 页数/字符数 |
|---|---|---|---|---|---|---|---:|
| P1 | `eu-1944-1945-009` | 1945-10 | 中国民主同盟纲领（OCR试点页） | `domestic-ocr/MMHIST:platform-1945:ocr-pilot` | draft | unknown | 1/393 |
| P1 | `eu-1944-1945-022` | 1944-05-16 | 《民憲》第一卷第一期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1944-v1n1-contents-ocr` | needs_human_review | unknown | 1/220 |
| P1 | `eu-1944-1945-023` | 1944-08-15 | 《民憲》第一卷第六期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1944-v1n6-contents-ocr` | needs_human_review | unknown | 1/200 |
| P1 | `eu-1944-1945-026` | 1944-12-20 | 《民憲》第一卷第十期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1944-v1n10-contents-ocr` | needs_human_review | unknown | 1/198 |
| P1 | `eu-1944-1945-027` | 1944-05-01 | 《民憲》第一卷第二期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1944-v1n2-contents-ocr` | needs_human_review | unknown | 1/156 |
| P1 | `eu-1944-1945-028` | 1944-06-15 | 《民憲》第一卷第三期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1944-v1n3-contents-ocr` | needs_human_review | unknown | 1/171 |
| P1 | `eu-1944-1945-030` | 1944-07-16 | 《民憲》第一卷第五期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1944-v1n5-contents-ocr` | needs_human_review | unknown | 1/226 |
| P1 | `eu-1944-1945-031` | 1944-09-10 | 《民憲》第一卷第七期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1944-v1n7-contents-ocr` | needs_human_review | unknown | 1/201 |
| P1 | `eu-1944-1945-032` | 1944-10-12 | 《民憲》第一卷第八期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1944-v1n8-contents-ocr` | needs_human_review | unknown | 1/216 |
| P1 | `eu-1944-1945-033` | 1945-01-15 | 《民憲》第一卷第十一期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1945-v1n11-contents-ocr` | needs_human_review | unknown | 1/240 |
| P1 | `eu-1944-1945-034` | 1945-02-25 | 《民憲》第一卷第十二期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1945-v1n12-contents-ocr` | needs_human_review | unknown | 1/253 |
| P1 | `eu-1944-1945-035` | 1945-05-15 | 《民憲》第二卷第一期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1945-v2n1-contents-ocr` | needs_human_review | unknown | 1/290 |
| P1 | `eu-1944-1945-036` | 1945-06-13 | 《民憲》第二卷第二期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1945-v2n2-contents-ocr` | needs_human_review | unknown | 1/271 |
| P1 | `eu-1946-041` | 1946-09-18 | 《光明報》新一號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue1-front-ocr` | needs_human_review | unknown | 1/988 |
| P1 | `eu-1946-047` | 1946-08-20 | 《光明報》新九號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue9-front-ocr` | needs_human_review | unknown | 1/1043 |
| P1 | `eu-1947-063` | 1947-06-23 | 《光明報》新二十號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1947-issue20-front-ocr` | needs_human_review | unknown | 1/252 |
| P1 | `eu-1947-065` | 1947-08-01 | 《光明報》新二十二號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1947-issue22-front-ocr` | needs_human_review | unknown | 1/340 |
| P1 | `eu-1941-001` | 1941-10-10 | 中国民主政团同盟成立宣言（OCR试点页） | `domestic-ocr/MMHIST:formation-declaration-1941:ocr-pilot` | draft | likely | 3/1388 |
| P1 | `eu-1941-008` | 1941 | 1941年《光明報》香港工运剪报索引清单（OCR导航） | `domestic-ocr/NLC:guangmingbao-1941-index-list-ocr` | needs_human_review | likely | 2/1076 |
| P1 | `eu-1944-1945-010` | 1945-10-11 | 中国民主同盟临时全国代表大会政治报告（OCR试点页） | `domestic-ocr/MMHIST:political-report-1945:ocr-pilot` | draft | likely | 2/1098 |
| P1 | `eu-1944-1945-011` | 1945-10-16 | 中国民主同盟临时全国代表大会宣言（OCR试点页） | `domestic-ocr/MMHIST:congress-declaration-1945:ocr-pilot` | draft | likely | 2/890 |
| P1 | `eu-1944-1945-012` | 1945-10 | 中国民主同盟纲领（1946年官方汇编OCR试点） (前段) | `domestic-ocr/NLC:minmeng-wenxian-1946-minmeng-platform-1945:ocr-pilot` | needs_human_review | likely | 13/5897 |
| P1 | `eu-1944-1945-013` | 1945-10 | 中国民主同盟纲领（1946年官方汇编OCR试点） (后段) | `domestic-ocr/NLC:minmeng-wenxian-1946-minmeng-platform-1945:ocr-pilot` | needs_human_review | likely | 13/7355 |
| P1 | `eu-1944-1945-014` | 1944-10—1945-01 | 1944—1945早期文件页组（OCR试点） (前段) | `domestic-ocr/NLC:minmeng-wenxian-1946-early-group:ocr-pilot` | needs_human_review | likely | 4/1267 |
| P1 | `eu-1944-1945-015` | 1944-10—1945-01 | 1944—1945早期文件页组（OCR试点） (后段) | `domestic-ocr/NLC:minmeng-wenxian-1946-early-group:ocr-pilot` | needs_human_review | likely | 5/3004 |
| P1 | `eu-1944-1945-016` | 1945 | 1945政治主张文件页组（上，OCR试点） (前段) | `domestic-ocr/NLC:minmeng-wenxian-1946-boundary-group:ocr-pilot` | needs_human_review | likely | 4/2416 |
| P1 | `eu-1944-1945-017` | 1945 | 1945政治主张文件页组（上，OCR试点） (后段) | `domestic-ocr/NLC:minmeng-wenxian-1946-boundary-group:ocr-pilot` | needs_human_review | likely | 5/2370 |
| P1 | `eu-1944-1945-018` | 1945 | 1945政治主张文件页组（下，OCR试点） | `domestic-ocr/NLC:minmeng-wenxian-1946-around-group:ocr-pilot` | needs_human_review | likely | 4/2115 |
| P1 | `eu-1944-1945-021` | 1944-11-20 | 《民憲》第一卷第九期〈民主政治與非民主政治〉正文（OCR试点） (前段) | `domestic-ocr/NLC:minxian-1944-v1n9-democracy-vs-nondemocracy-article-ocr` | needs_human_review | likely | 2/2612 |
| P1 | `eu-1944-1945-024` | 1944-05-16 | 《民憲》第一卷第一期〈努力與思索〉（代發刊詞）正文试点 | `domestic-ocr/NLC:minxian-1944-v1n1-preface-effort-and-thought-ocr` | needs_human_review | likely | 3/3796 |
| P1 | `eu-1944-1945-025` | 1944-08-15 | 《民憲》第一卷第六期〈民主政治的哲學問題（上）〉正文试点 | `domestic-ocr/NLC:minxian-1944-v1n6-democracy-philosophy-upper-ocr` | needs_human_review | likely | 4/5158 |
| P1 | `eu-1944-1945-037` | 1945-10 | 《中國民主同盟言論集》1945年选编前页（OCR试点） | `domestic-ocr/NLC:minmeng-yanlunji-1945-front-ocr` | needs_human_review | likely | 3/123 |
| P1 | `eu-1946-049` | 1946-12 | 《民主同盟文獻》1946年官方汇编交替扫描前页（OCR试点） | `domestic-ocr/NLC:minmeng-wenxian-1946-alternate-front-ocr` | needs_human_review | likely | 3/79 |
| P1 | `eu-1947-050` | 1947-10-28 | 《光明報》1947年新十九號关键页（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1947-19-key-pages` | needs_human_review | likely | 6/9668 |
| P1 | `eu-1947-051` | 1947-10-28 | 《光明報》1947年新十九號关键页（OCR试点） (后段) | `domestic-ocr/NLC:guangmingbao-1947-19-key-pages` | needs_human_review | likely | 6/11049 |
| P1 | `eu-1947-052` | 1947-08-08 | 《光明報》1947年新十二號（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1947-12-full-ocr` | needs_human_review | likely | 8/8508 |
| P1 | `eu-1947-053` | 1947-08-08 | 《光明報》1947年新十二號（OCR试点） (后段) | `domestic-ocr/NLC:guangmingbao-1947-12-full-ocr` | needs_human_review | likely | 8/10753 |
| P1 | `eu-1947-054` | 1947-01-18 | 《光明報》1947年新十三號（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1947-13-full-ocr` | needs_human_review | likely | 8/8146 |
| P1 | `eu-1947-055` | 1947-01-18 | 《光明報》1947年新十三號（OCR试点） (后段) | `domestic-ocr/NLC:guangmingbao-1947-13-full-ocr` | needs_human_review | likely | 8/12480 |
| P1 | `eu-1947-056` | 1947-01-28 | 《光明報》1947年新十四號（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1947-14-full-ocr` | needs_human_review | likely | 8/10463 |
| P1 | `eu-1947-057` | 1947-01-28 | 《光明報》1947年新十四號（OCR试点） (后段) | `domestic-ocr/NLC:guangmingbao-1947-14-full-ocr` | needs_human_review | likely | 8/12461 |
| P1 | `eu-1947-058` | 1947-02-08 | 《光明報》1947年新十五號（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1947-15-full-ocr` | needs_human_review | likely | 8/10326 |
| P1 | `eu-1947-059` | 1947-03-18 | 《光明報》1947年新十六—十七號（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1947-16-17-full-ocr` | needs_human_review | likely | 8/10450 |
| P1 | `eu-1947-060` | 1947-05-14 | 《光明報》1947年新十八號（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1947-18-full-ocr` | needs_human_review | likely | 8/11135 |
| P1 | `eu-1947-061` | 1947-11-04 | 《大剛報》1947年11月4日全版扫描（OCR试点） | `domestic-ocr/NLC:dagangbao-1947-11-04-full-ocr` | needs_human_review | likely | 4/35573 |
| P1 | `eu-1947-069` | 1947-11-08 | 《觀察》第三卷第十一期合订本高价值页（OCR试点） (前段) | `domestic-ocr/NLC:observer-1947-v3n11-bound-selected-ocr` | needs_human_review | likely | 2/2983 |
| P1 | `eu-1948-1949-072` | 1948-03-01 | 《光明報》1948年第一卷第一期（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1948-v1n1-full-ocr` | needs_human_review | likely | 12/19465 |
| P1 | `eu-1948-1949-073` | 1948-03-01 | 《光明報》1948年第一卷第一期（OCR试点） (后段) | `domestic-ocr/NLC:guangmingbao-1948-v1n1-full-ocr` | needs_human_review | likely | 12/20507 |
| P1 | `eu-1948-1949-074` | 1948-08-16 | 《光明報》1948年第一卷第十二期（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1948-v1n12-full-ocr` | needs_human_review | likely | 10/13584 |
| P1 | `eu-1948-1949-075` | 1948-08-16 | 《光明報》1948年第一卷第十二期（OCR试点） (后段) | `domestic-ocr/NLC:guangmingbao-1948-v1n12-full-ocr` | needs_human_review | likely | 10/13585 |
| P1 | `eu-1948-1949-076` | 1949-05-10 | 《光明報》1949年第二卷第一期（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1949-v2n1-full-ocr` | needs_human_review | likely | 10/13274 |
| P1 | `eu-1948-1949-077` | 1949-05-10 | 《光明報》1949年第二卷第一期（OCR试点） (后段) | `domestic-ocr/NLC:guangmingbao-1949-v2n1-full-ocr` | needs_human_review | likely | 10/14410 |
| P1 | `eu-1948-1949-078` | 1949-06-16 | 《光明報》1949年第二卷第十二期（OCR试点） (前段) | `domestic-ocr/NLC:guangmingbao-1949-v2n12-full-ocr` | needs_human_review | likely | 10/13417 |
| P1 | `eu-1948-1949-079` | 1949-06-16 | 《光明報》1949年第二卷第十二期（OCR试点） (后段) | `domestic-ocr/NLC:guangmingbao-1949-v2n12-full-ocr` | needs_human_review | likely | 10/14687 |
| P2 | `eu-1944-1945-029` | 1944-06-30 | 《民憲》第一卷第四期目录页（OCR试点） | `domestic-ocr/NLC:minxian-1944-v1n4-contents-ocr` | needs_human_review | unknown | 1/213 |
| P2 | `eu-1946-038` | 1946-08 | 《光明報》新八號〈論有條件參加國大〉首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue8-conditional-national-assembly-ocr` | needs_human_review | unknown | 1/767 |
| P2 | `eu-1946-039` | 1946-09-13 | 《光明報》新十一號〈反對一黨獨裁的憲法！〉正文首页（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue11-anti-one-party-constitution-ocr` | needs_human_review | unknown | 1/1433 |
| P2 | `eu-1946-040` | 1946-10-08 | 《光明報》新三號〈為完成雙十節的歷史任務而奮鬥〉首页（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue3-double-ten-task-ocr` | needs_human_review | unknown | 1/851 |
| P2 | `eu-1946-042` | 1946-09-28 | 《光明報》新二號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue2-front-ocr` | needs_human_review | unknown | 1/871 |
| P2 | `eu-1946-043` | 1946-10-18 | 《光明報》新四號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue4-front-ocr` | needs_human_review | unknown | 1/881 |
| P2 | `eu-1946-044` | 1946-10-28 | 《光明報》新五號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue5-front-ocr` | needs_human_review | unknown | 1/573 |
| P2 | `eu-1946-045` | 1946-11-08 | 《光明報》新六號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue6-front-ocr` | needs_human_review | unknown | 1/930 |
| P2 | `eu-1946-046` | 1946-11-18 | 《光明報》新七號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue7-front-ocr` | needs_human_review | unknown | 1/898 |
| P2 | `eu-1946-048` | 1946-08-28 | 《光明報》新十號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1946-issue10-front-ocr` | needs_human_review | unknown | 1/939 |
| P2 | `eu-1947-064` | 1947-07-05 | 《光明報》新二十一號首版（OCR试点） | `domestic-ocr/NLC:guangmingbao-1947-issue21-front-ocr` | needs_human_review | unknown | 1/178 |
| P2 | `eu-1947-067` | 1947-11-06 | 《大公報》上海版1947年11月6日第2版民盟消息（OCR试点） | `domestic-ocr/NLC:dagongbao-shanghai-1947-11-06-page2-ocr` | needs_human_review | unknown | 1/914 |
| P2 | `eu-1947-068` | 1947-11-06 | 《大公報》天津版1947年11月6日第2版民盟解散消息（OCR试点） | `domestic-ocr/NLC:dagongbao-tianjin-1947-11-06-page2-ocr` | needs_human_review | unknown | 1/1288 |
| P2 | `eu-1947-071` | 1947-11-06 | 《大公報》第114卷1947年11月6日第2版关键页（OCR试点） | `domestic-ocr/NLC:dagongbao-vol114-1947-11-06-selected-ocr` | needs_human_review | unknown | 1/5593 |
| P2 | `eu-1941-002` | 1941-10-10 | 1941成立文件页组（OCR试点） (前段) | `domestic-ocr/NLC:minmeng-wenxian-1946-formation-group:ocr-pilot` | untagged | likely | 2/3426 |
| P2 | `eu-1941-003` | 1941-10-10 | 1941成立文件页组（OCR试点） (后段) | `domestic-ocr/NLC:minmeng-wenxian-1946-formation-group:ocr-pilot` | untagged | likely | 3/1715 |
| P2 | `eu-1941-004` | 1941-10-10 | 《新华日报》1941年10月10日全版扫描（OCR试点） (前段) | `domestic-ocr/NLC:xinhua-daily-1941-10-10-full-ocr` | needs_human_review | likely | 3/16027 |
| P2 | `eu-1941-005` | 1941-10-10 | 《新华日报》1941年10月10日全版扫描（OCR试点） (后段) | `domestic-ocr/NLC:xinhua-daily-1941-10-10-full-ocr` | needs_human_review | likely | 3/16676 |
| P2 | `eu-1941-006` | 1941-10-16 | 《新华日报》1941年10月16日全版扫描（OCR试点） | `domestic-ocr/NLC:xinhua-daily-1941-10-16-full-ocr` | needs_human_review | likely | 2/13732 |
| P2 | `eu-1941-007` | 1941-10-28 | 《新华日报》1941年10月28日全版扫描（OCR试点） | `domestic-ocr/NLC:xinhua-daily-1941-10-28-full-ocr` | needs_human_review | likely | 2/10859 |
| P2 | `eu-1944-1945-019` | 1945 | 1945文件页组（续，OCR试点） (前段) | `domestic-ocr/NLC:minmeng-wenxian-1946-target-group:ocr-pilot` | needs_human_review | likely | 3/3493 |
| P2 | `eu-1944-1945-020` | 1945-12或待核 | 1945大会宣言后续页组（日期待核，OCR试点） (前段) | `domestic-ocr/NLC:minmeng-wenxian-1946-late-group:ocr-pilot` | untagged | likely | 5/4096 |
| P2 | `eu-1947-062` | 1947-11-06 | 《大剛報》1947年11月6日全版扫描（OCR试点） | `domestic-ocr/NLC:dagangbao-1947-11-06-full-ocr` | needs_human_review | likely | 4/34947 |
| P2 | `eu-1947-066` | 1947-11-08 | 《觀察》第三卷第十一期高价值页（OCR试点） | `domestic-ocr/NLC:observer-1947-v3n11-selected-ocr` | needs_human_review | likely | 4/4334 |
| P2 | `eu-1947-070` | 1947-11-06 | 《大公報》第113卷1947年11月6日第1—2版关键页（OCR试点） | `domestic-ocr/NLC:dagongbao-vol113-1947-11-06-selected-ocr` | needs_human_review | likely | 2/6682 |
| P3 | `eu-1947-080` | 1947-03-18 | 《光明報》1947年新十六—十七號（OCR试点） | `domestic-ocr/NLC:guangmingbao-1947-16-17-full-ocr` | verified | unknown | 1/1290 |
| P3 | `eu-1947-081` | 1947-05-14 | 《光明報》1947年新十八號（OCR试点） | `domestic-ocr/NLC:guangmingbao-1947-18-full-ocr` | verified | unknown | 1/1436 |
| P3 | `eu-1947-082` | 1947-02-08 | 《光明報》1947年新十五號（OCR试点） | `domestic-ocr/NLC:guangmingbao-1947-15-full-ocr` | verified | unknown | 1/1395 |
