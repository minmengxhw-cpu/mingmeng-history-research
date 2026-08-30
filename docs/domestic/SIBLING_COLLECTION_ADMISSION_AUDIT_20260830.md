# Sibling 采集包准入审计（2026-08-30）

本审计只读取 JSON 元数据、公开 URL、文件名和文件统计；未读取 HTML/PDF/图片正文，未 OCR，未写入 SQLite，未复制、移动或删除文件。机器脚本为 [`scripts/domestic/audit_sibling_collection_admission.py`](../../scripts/domestic/audit_sibling_collection_admission.py)。

## 结论

另一份数据 checkout 不是可以整体导入的资料包，而是把正式候选、公开转载、学术网页、海外上下文和中间产物混在了一起。必须先按来源身份和证据角色分流，再决定是否建立主线元数据候选；本轮不改变 P0 状态，也没有正式库写入。

主线 `candidates.jsonl` 当前有 693 条可解析记录；Sibling 的 599 条 JSON sidecar 中，244 条 URL 已与主线候选精确匹配，不能再次导入。国内主线仍有 9 个开放的一手目标，不能因采集量增加而标记为 `research_ready`。

未与主线候选 URL 重合的 355 条已另存为 [`data/domestic/sibling_collection_intake_queue.json`](../../data/domestic/sibling_collection_intake_queue.json)。它是待补证清单，不是正式候选库；每条记录都没有本地路径和正文，只保留公开 URL、来源类别、文件哈希、权限说明和准入建议。

## 目录盘点

| 采集目录 | 文件数 | 文件类型 | sidecar | 判断 |
|---|---:|---|---:|---|
| `grok_public_collection_20260729` | 1,190 | HTML 547、PDF 29、JPG 19、JSON 595 | 595 | 元数据完整度较高，但同时含 FRUS、官方网页、镜像和原件线索 |
| `official_research_public_20260730` | 58 | HTML 28、TXT 26、PDF 4 | 0 | 有文本/页面导出，但没有绑定式来源元数据 |
| `academic_public_20260730` | 135 | HTML 123、PDF 12 | 0 | 不能凭文件名认定作者、机构、刊物或学术资格 |
| `grok_next_stage_20260730` | 48 | HTML 38、JPG 9、PDF 1 | 0 | 跟进线索与公开页面混合，暂不自动准入 |
| `grok_shanghai_wave_20260730` | 8 | PDF 4、JSON 4 | 4 | 4 条 sidecar 均明确标注“未复核、非 citation-ready” |

## 599 条 sidecar 分流

| 来源类别 | 数量 | 处理含义 |
|---|---:|---|
| `foreign_context_or_catalogue` | 257 | 海外上下文或馆藏导航，不进入国内一手闭环 |
| `domestic_official_or_institutional` | 251 | 可从中筛出官方/机构元数据候选，但不等于原件 |
| `public_surrogate_or_mirror` | 72 | 公开转录、镜像或替代本，只作线索/交叉来源 |
| `unclassified_public_source` | 13 | 来源类别和身份需补证 |
| `academic_or_research_portal` | 6 | 需补作者、机构、刊物/学位、年份和稳定入口 |

| 准入建议 | 数量 |
|---|---:|
| `DUPLICATE_EXACT_URL` | 244 |
| `CONTEXT_ONLY` | 247 |
| `PROMOTE_METADATA_REVIEW` | 37 |
| `LEAD_ONLY_SURROGATE_REVIEW` | 46 |
| `KNOWN_ROUTE_NOT_CANDIDATE` | 10 |
| `PROMOTE_ACADEMIC_METADATA_REVIEW` | 4 |
| `UNCLASSIFIED_HOLD` | 11 |

## 第一批复核入口

以下记录只代表“值得先补元数据”的入口，不代表正文已读、版本已闭合或已达到 `citation_ready`：

| object_id | 文件名提示 | 来源 URL |
|---|---|---|
| `GDC-0042` | 南方局工作记述、光明报香港创刊与政团同盟公开 | <https://www.dswxyjy.org.cn/n/2014/0630/c244520-25218618.html> |
| `GDC-0027` | 民盟响应“五一”号召致各民主党派书（1948-06-14） | <https://www.mmzy.org.cn/mobile/ArticleHistoryList.aspx?id=9734&name=Mszl&ColumnId=1195> |
| `GDC-0028` | 民盟现阶段工作纲领（1948-06-19） | <https://www.mmzy.org.cn/mobile/ArticleHistoryList.aspx?id=9733&name=Mszl&ColumnId=1195> |
| `GDC-0041` | 民盟对时局主张纲领、十大纲领内容转载 | <https://www.hljmm.gov.cn/show.aspx?id=1882> |
| `GDC-0146` | 沈钧儒保存的民盟响应“五一”号召会议提纲与记录史事 | <https://www.zytzb.gov.cn/zytzb/2024-11/08/article_2024110814262019636.shtml> |
| `GDC-0152` | “五一口号”75 周年座谈会发言摘编 | <http://www.cppcc.gov.cn/zxww/2023/04/27/ARTI1682564752475338.shtml> |
| `GDC-0154` | 民盟中央文章：弘扬“五一口号”精神 | <https://www.mmzy.org.cn/mobile/ArticleList.aspx?id=74891&name=Llyj&ColumnId=1172> |

## 准入规则

1. 官方网页只能作为官方叙述/线索，只有补齐题名、形成者、日期、版本或档号、稳定 URL、权限和 SHA256 后，才可进入元数据复核队列。
2. 学术文件必须补齐作者、机构资格证据、刊物卷期或学位信息、年份、稳定入口和全文状态；未补齐前不进入学术全文队列。
3. 公开转录、镜像、汇编重刊和同期报道必须保持各自证据等级，不能替代 1941 成立原件或 1947 行政/总部公告原件。
4. 已有可靠文本层的资料不重复 OCR；没有文本层时也只对已完成身份绑定的目标建立定向 OCR 队列。
5. 通过准入审计前，不复制原件、不写正式 SQLite、不提交本地正文或 OCR 派生物；默认不删除任何本地文件。

## 机器复核

```bash
python3 scripts/domestic/audit_sibling_collection_admission.py \
  --sibling-root /path/to/mingmeng-history-research \
  --output-json /tmp/sibling_collection_admission.json \
  --output-md /tmp/sibling_collection_admission.md \
  --output-intake-json data/domestic/sibling_collection_intake_queue.json

python3 scripts/domestic/validate_sibling_collection_intake.py \
  --queue data/domestic/sibling_collection_intake_queue.json
```
