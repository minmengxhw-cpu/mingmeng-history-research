# 《民主同盟文獻》（1946）公开扫描复核

审核日期：2026-07-19（Asia/Shanghai）

## 文件身份与核验

- 国家图书馆标识：`NLC416-01jh004281-12557`
- 外部文件页：[Wikimedia Commons 文件页](https://commons.wikimedia.org/wiki/File:NLC416-01jh004281-12557_%E6%B0%91%E4%B8%BB%E5%90%8C%E7%9B%9F%E6%96%87%E7%8D%BB.pdf)
- 本地文件：`data/domestic/sourcebooks/NLC416-01jh004281-12557_民主同盟文獻_1946.pdf`
- 页数：176；未加密；文件大小：13,898,719 bytes
- SHA256：`276a82242c445bd7d6ca468f9022090922e0c2c243054e0e5af4353a1456e43f`
- PDF第2页书名页明确写有“中國民主同盟總部編印”和“中華民國三十五年十二月”，即1946年12月；这证明它是民盟总部同期编印的官方文献集，不是后期历史汇编。

## 目录与页级核读

- PDF第5—8页为目录，列出42件文献，覆盖1941成立、1941《对时局主张纲领》、1944改组前后文件以及1945代表大会政治报告、宣言等。
- PDF第9页标题为《中国民主政团同盟成立宣言》，题下注明“中华民国三十年十月十日”；正文延续至PDF第11页，OCR底稿在 `work/domestic/minmeng_wenxian_1946/ocr_contents/page009.ocr.md` 至 `page011.ocr.md`。
- PDF第12页标题为《中国民主政团同盟对时局主张纲领》，题下注明同一日期；正文延续至PDF第13页，PDF第12页可定位十项主张，OCR底稿在 `work/domestic/minmeng_wenxian_1946/ocr_contents/page012.ocr.md`。
- PDF第14页开始《中国民主政团同盟对目前时局的看法与主张》，说明该汇编还收录1944年相关文件；本轮未先拆分该文，避免在未完成边界核读前过度登记。
- 抽样 OCR 和页图进一步定位：PDF第22—25页为《对抗战最后阶段的政治主张》，报头日期1944-10-10；PDF第26—29页为《时局宣言》，报头日期1945-01-15。两件均已回到页图核对标题和日期，OCR只作定位辅助。
- PDF第48页正文标题为《中国民主同盟纲领》，题下注明“民国三十四年十月临时全国代表大会通过”；正文连续至PDF第72页，印刷页40—64，覆盖政治、经济、教育、妇女等章节。正文没有可确认的具体日，登记为1945-10月精度。
- PDF第73页正文标题为《中国民主同盟临时全国代表大会宣言》，题下注明中华民国三十四年十月十六日；正文连续至PDF第78页，印刷页65—70，PDF第79页起进入下一件1945-12-06昆明惨案文件。
- 目录PDF第6页另列“代表大会政治报告”（日期为民国三十四年十月十一日），但在本次公开扫描中尚未找到可连续核对的正文起止页；当前不把目录条目直接当作文件候选，列为硬缺口。

## 入库决定

- 新增来源：`domestic:source:nlc_minmeng_documents_1946`
- 新增候选：
  - `domestic:NLC:minmeng-wenxian-1946-whole`：整本官方汇编，L2；
  - `domestic:NLC:minmeng-wenxian-1946-formation-declaration`：PDF第9—11页，L2；
  - `domestic:NLC:minmeng-wenxian-1946-ten-program`：PDF第12—13页，L2。
- `domestic:NLC:minmeng-wenxian-1946-final-war-political-platform`：PDF第22—25页，L2；
- `domestic:NLC:minmeng-wenxian-1946-situation-declaration-1945-01-15`：PDF第26—29页，L2。
- `domestic:NLC:minmeng-wenxian-1946-minmeng-platform-1945`：PDF第48—72页，L2；
- `domestic:NLC:minmeng-wenxian-1946-congress-declaration-1945-10-16`：PDF第73—78页，L2。
- 以上七条均保持 `needs_human_review`，原因是它们是1946年官方汇编中的再编文件，不是同期独立原始印本；原始形成机关、底本版本、版次和复制权利仍需互校。
- 这组记录挂入 `1941成立`；整本记录另挂入 `1944改组更名`、`1945第一次全国代表大会`，作为早期时间轴的官方汇编支撑。

## 下一步

1. 继续追索目录所列1945-10-11《代表大会政治报告》的正文起止页，并与已登记的后期正式汇编互校；当前公开扫描不作猜测性补录。
2. 追查这些文件在1941—1945同期报刊、民盟总部印本和档案中的原始载体。
3. 不把本书的再编文本自动提升为 L1 或 accepted。
