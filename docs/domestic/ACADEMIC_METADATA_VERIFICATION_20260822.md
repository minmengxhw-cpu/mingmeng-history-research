# 学术全文队列元数据核验记录（2026-08-22）

本批只更新学术发现层的题名、作者、机构和发表时间字段，不读取或导入正文，不改变 `citation_ready`、`human_verified` 或国内一手证据状态。

| external_id | 更新 | 公开核验依据 | 边界 |
|---|---|---|---|
| `GAR-7B041C67C2` | 补正题名为“情报、人员和物资的枢纽……”，发表时间细化为 2018-10 | [香港中文大学 PDF](https://www.cuhk.edu.hk/ics/21c/media/articles/c169-201711013.pdf) 首页题名、作者和《二十一世纪》2018 年 10 月号信息 | 作者所属机构未从题名页独立确认，仍保留“待从 PDF 文首核验” |
| `GAR-41D3AC4591` | 作者补为马皓若、王毅，机构补为中共中央党校（国家行政学院）中共党史教研部 | [民进中央转载页](https://www.mj.org.cn/hszl/hsgc/202510/t20251009_299712.htm) 标示作者及机构；队列 PDF 仍作为全文入口 | 仅核验书目信息，不代表正文已逐字复核 |
| `GAR-9EAACC89D5` | 作者补为陈仪深，机构补为中央研究院近代史研究所，年份补为 1994，去除发现性括注 | [中研院原始 PDF 入口](https://www.mh.sinica.edu.tw/MHDocument/PublicationDetail/PublicationDetail_784.pdf)；[上海社科院论文参考文献](https://ih.sass.org.cn/_upload/article/files/0d/3f/e2ff6a9b418b87806f9be042feab/5af6a959-a46d-4e43-8812-792e156f6108.pdf) 给出作者、题名、刊物和年份 | 原始 PDF 本轮未纳入正式库，仍为 `FULLTEXT_PDF`、`citation_ready=0` |

## 处理结果

- 学术全文优先队列仍为 24 条，P0/P1 分类未改变；
- 本批没有 OCR、正文入库或 SQLite 写入；
- 这些记录可以更准确地按作者、机构和年份筛选，但仍属于解释层；
- 生成器重新导出元数据时，需将本记录作为人工核验覆盖项复核，避免 staging 导出覆盖已确认字段。
