# P0 原件跨 checkout 复核记录（2026-08-29）

## 复核目的

当前正式 checkout 的授权原件接收目录为空。为排除“原件已经放在另一份本地数据 checkout、但未被接收门禁发现”的可能性，对 sibling checkout
`<local-user>/<local-checkout>/mingmeng-history-research/data/domestic/gazette_scans/`
进行了文件名级和文件元数据级核对。

## 发现的文件

| 文件 | 文件大小 | 页数 | SHA256 | 处理结论 |
|---|---:|---:|---|---|
| `ROC1947-10-27國民政府公報2964.pdf` | 1,253,502 bytes | 17 | `3fa55d79a386f840d08c9268b39a301cf4322453e3134a5ab608acd3e3150e9c` | 已有官方公报负向核查记录，不是目标公函原件 |
| `ROC1947-11-06國民政府公報2973.pdf` | 575,263 bytes | 9 | `0a7c39bc0aa426d5f6672a302d7e64e37b43557d68762099ab75941b56d18b03` | 已有官方公报负向核查记录，不是目标解散公告底本 |

## 证据判断

- 两份文件的刊名、日期、期号和页数已由本地文件元数据及既有来源记录确认。
- 既有逐页核查记录明确：第 2964 号、第 2973 号未命中“民盟”“中国民主同盟”或民盟非法化/解散目标公文标题；它们只能作为官方公报的负向核查或整册导航层。
- P0 的目标仍是 1947-10-27 政府宣布民盟为非法的行政原件，以及 1947-11-06 民盟总部解散公告/正式声明的原始底本。上述两期公报不满足这两个目标的正文条件。

## 处理决定

1. 不把这两份 PDF 复制到 `data/domestic/raw/authorized_originals/incoming` 作为 P0 原件。
2. 不新增 P0 映射、不执行正式库晋级、不改变 `research_content_status`。
3. 保留 sibling checkout 原文件不动；正式 checkout 继续以 `WAITING_FOR_LOCAL_ORIGINAL` 管理两个授权接收目标。

## 可复核记录

- 现行官方公报负向核查说明：`docs/domestic/press_scan_manifest.md`、`docs/domestic/ROC_GAZETTE_1947_2973_2974_REVIEW_20260814.md`。
- P0 接收门禁：`scripts/domestic/prepare_authorized_original_intake.py`。
- 复核时接收目录文件数：`0`；映射数：`0`；未读取两份 PDF 正文，也未执行 OCR。
