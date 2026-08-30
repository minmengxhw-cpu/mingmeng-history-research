# 国内正式库元数据例外审计（2026-08-30）

## 目的与边界

本轮只对正式 SQLite 的两个计数型例外做字段级定位：1 个国内页缺少 `page_provenance`，10 个国内文献对象没有 `date_guess`。本轮不读取正文、不执行 OCR、不修改正式库、不删除或移动任何本地文件。

## 结果

| 例外 | 对象 | 处理决定 | 原因 |
|---|---|---|---|
| 页级 provenance 缺失 | `domestic-web/SAAC-ALBUM` · 《从「五一口号」到开国大典》档案文献专辑总索引 · `album-index` | 保留为导航层，不升级为 citation-ready | 这是专题总索引入口，不是可直接引用的档案正文页；补写 provenance 会制造“正文证据”假象 |
| 文献无日期（6 个 OCR 草稿对象） | `COLLECTION:P3-012`、`COLLECTION:P3-013`、`LOCALFULL:P3-012`、`LOCALFULL:P3-013`、`LOCALFULL:P3-014`、`LOCALFULL:P3-023` | 保留，日期维持空值 | 对象是 OCR/staging 或公开转录工作对象，题名不足以推出原始出版日期；不以文件生成日期替代文献日期 |
| 文献无日期（3 个页级对象） | `SRC-088458899f`、`NLC511-027032016010761-42571`、`NLC511-027032013012333-19131` | 保留，日期维持空值 | 这些对象需要书目页、馆藏记录或版本页来确认日期；当前没有足够的版本证据 |
| 文献无日期（1 个学术对象） | `GAR-9EAACC89D5` · 国共斗争下的自由主义（1941—1949） | 保留，日期维持空值 | 题名中的研究时段不是发表日期；应等待正式书目信息或出版物页，不从研究内容反推 |

## 验收结论

- 正式库完整性、外键、页/FTS 对齐和来源文件哈希门禁继续通过。
- 以上例外不构成删除理由，也不构成整本 OCR 理由。
- `SAAC-ALBUM` 继续作为导航入口；10 个对象继续留在其既有 staging/学术层级。
- 后续只有拿到明确的馆藏书目、版权页、记录号或页级来源证据，才补 `date_guess` 或 provenance；不能用猜测值填空。

## 复核命令

```bash
python3 -B scripts/closeout/verify_research_index_manifest.py
python3 -B scripts/domestic/validate_unified_research_platform.py
```
