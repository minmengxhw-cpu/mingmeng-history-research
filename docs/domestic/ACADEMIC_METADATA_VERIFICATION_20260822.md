# 学术全文队列元数据核验记录（2026-08-22）

本批只更新学术发现层的题名、作者、机构和发表时间字段，不读取或导入正文，不改变 `citation_ready`、`human_verified` 或国内一手证据状态。

| external_id | 更新 | 公开核验依据 | 边界 |
|---|---|---|---|
| `GAR-7B041C67C2` | 补正题名为“情报、人员和物资的枢纽……”，发表时间细化为 2018-10 | [香港中文大学 PDF](https://www.cuhk.edu.hk/ics/21c/media/articles/c169-201711013.pdf) 首页题名、作者和《二十一世纪》2018 年 10 月号信息 | 作者所属机构未从题名页独立确认，仍保留“待从 PDF 文首核验” |
| `GAR-41D3AC4591` | 作者补为马皓若、王毅，机构补为中共中央党校（国家行政学院）中共党史教研部 | [民进中央转载页](https://www.mj.org.cn/hszl/hsgc/202510/t20251009_299712.htm) 标示作者及机构；队列 PDF 仍作为全文入口 | 仅核验书目信息，不代表正文已逐字复核 |
| `GAR-9EAACC89D5` | 作者补为陈仪深，机构补为中央研究院近代史研究所，年份补为 1994，去除发现性括注 | [中研院原始 PDF 入口](https://www.mh.sinica.edu.tw/MHDocument/PublicationDetail/PublicationDetail_784.pdf)；[上海社科院论文参考文献](https://ih.sass.org.cn/_upload/article/files/0d/3f/e2ff6a9b418b87806f9be042feab/5af6a959-a46d-4e43-8812-792e156f6108.pdf) 给出作者、题名、刊物和年份 | 原始 PDF 本轮未纳入正式库，仍为 `FULLTEXT_PDF`、`citation_ready=0` |
| `ACADEMIC-20260813-LIU-DAYU-CONSTITUTIONAL-NATIONAL-ASSEMBLY` | 补录书目定位为《民国档案》2012 年第 1 期，第 134—139 页；作者机构交叉核验为江南大学马克思主义学院/图书馆 | [公开期刊索引条目](https://history.alljournals.cn/relate_search.aspx?aid=EC6EA820E836138D39D332196D822886&ctl=17&etl=0&language=0&pcid=B105980C46742988AA264212B4BA36DE578B761D73696550)、[江南大学刘大禹主页](https://marxism.jiangnan.edu.cn/info/1018/4603.htm)、[王球云作者简介 PDF](https://library.ttcdw.com/dev/upload/webUploader/202312/170324854415c476fedf4d14d1.pdf) | 仅交叉核验作者机构；本文刊期单位、文章首页和全文仍待正式期刊页核验；质量层级保持 B，未升级 citation-ready |
| `ACADEMIC-20260813-LIU-DAYU-PCC-PARTICIPATION` | 作者机构交叉核验为江南大学马克思主义学院/图书馆；正文和刊期书目仍待正式期刊页核验 | [中国社会科学网条目](https://jds.cssn.cn/xsqk/jdsyj/bkxx/201605/t20160506_5254360.shtml)、[江南大学刘大禹主页](https://marxism.jiangnan.edu.cn/info/1018/4603.htm)、[王球云作者简介 PDF](https://library.ttcdw.com/dev/upload/webUploader/202312/170324854415c476fedf4d14d1.pdf) | 仅交叉核验作者机构；本文刊期单位、文章首页和全文仍待正式期刊页核验；质量层级保持 B，未升级 citation-ready |

## 处理结果

- 学术全文优先队列仍为 24 条，P0/P1 分类未改变；
- 本批没有 OCR、正文入库或 SQLite 写入；
- 这些记录可以更准确地按作者、机构和年份筛选，但仍属于解释层；
- 生成器重新导出元数据时，需将本记录作为人工核验覆盖项复核，避免 staging 导出覆盖已确认字段。
