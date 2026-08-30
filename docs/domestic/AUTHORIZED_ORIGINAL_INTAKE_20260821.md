# 国内 P0 授权原件接收流程

本流程用于承接用户在已授权浏览器、档案馆服务或其他明确许可路径取得的国内一手原件。当前预置两个目标：

- 1947-10-27 政府宣布民盟为非法团体的行政原件；
- 1947-11-06 民盟总部解散公告或正式声明原始底本。

它是“接收和验收前置层”，不是自动入库工具。它只盘点 incoming 文件并计算 SHA256；不解码、不抽取正文、不 OCR、不改正式 SQLite、不删除或重命名文件，也不修改 `citation_ready`、`human_verified` 或专题 `primary_evidence_status`。

## 使用

先把获得许可保存的 PDF/图片放入：

```text
data/domestic/raw/authorized_originals/incoming/
```

然后编辑脚本自动生成的映射模板：

```text
work/domestic/authorized_original_intake_20260821/EXPLICIT_MAPPING.jsonl
```

运行：

```bash
python3 scripts/domestic/prepare_authorized_original_intake.py
```

也可以用参数指定临时 incoming 和输出目录：

```bash
python3 scripts/domestic/prepare_authorized_original_intake.py \
  --incoming /path/to/authorized/incoming \
  --mapping /path/to/EXPLICIT_MAPPING.jsonl \
  --output work/domestic/authorized_original_intake_20260821
```

## 从民盟全媒体数据库交接原件

在已登录且有正文/下载权限的浏览器中，按下面顺序交接：

1. 以目标日期和标题检索记录，先确认记录页显示的来源、卷期/档号和原件类型。
2. 只有明确属于“1947-10-27 政府行政原件”或“1947-11-06 民盟总部公告/正式声明底本”的 PDF/影像，才下载到 `incoming/`；同期报道、汇编重刊、纪念馆转录和已有 OCR 草稿只作为替代或交叉线索。
3. 在 `EXPLICIT_MAPPING.jsonl` 中为每个文件填写对应 `target_id`、记录页/档号、访问时间、保存与复制许可、公开展示边界、PDF 页数，并确认 `page_identity_reviewed=true`。
4. 运行接收脚本。只有得到 `STAGED_READY_FOR_DRY_RUN` 才进入后续 dry-run；脚本不会自动把文件写进正式库。

如果记录页没有清楚显示原件身份、权限或版本关系，保留为待审线索，不要用文件名或 OCR 内容强行映射到 P0 目标。

## 映射和状态

每个文件必须显式映射到 `target_id`，并填写详情页 URL/馆藏档号、记录号/案卷号、访问时间、保存许可、复制许可和公开展示边界。脚本会自动记录文件名、字节数和 SHA256。

状态含义：

| 状态 | 含义 |
|---|---|
| `WAITING_FOR_LOCAL_ORIGINAL` | 还没有本地原件 |
| `WAITING_FOR_EXPLICIT_MAPPING` | 已有文件，但没有显式目标映射 |
| `HOLD_MAPPING_METADATA` | 映射缺来源或权利字段 |
| `HOLD_SHA256_MISMATCH` | 用户声明的哈希与本地文件不一致 |
| `HASHED_NEEDS_PAGE_COUNT` | 文件已哈希，但尚未登记页数 |
| `STAGED_NEEDS_PAGE_IDENTITY_REVIEW` | 元数据齐，但 PDF 页/物理页/印刷页尚未人工复核 |
| `STAGED_READY_FOR_DRY_RUN` | 达到 staging dry-run 的输入条件，仍不能直接写正式库 |

`STAGED_READY_FOR_DRY_RUN` 也不等于严格引用。后续仍需页身份复核、原图/可靠版本核验、必要的定向 OCR、正式库备份、dry-run、SQLite integrity/外键/FTS 回归和研究包回链。

## 与 1947 缺口的关系

上海档案馆 `上档6-5-1216` 是地方执行转令路线，不能预先等同于 10 月 27 日中央决定原件；1983 年汇编第 355 页是后出重刊，不能等同于 11 月 6 日公告底本。接收清单保留这些版本关系，避免“已有替代本”误关闭原件目标。

当前没有本地授权原件时，正确结果是 `WAITING_FOR_LOCAL_ORIGINAL`，而不是生成空正文或把目录升级为证据。
