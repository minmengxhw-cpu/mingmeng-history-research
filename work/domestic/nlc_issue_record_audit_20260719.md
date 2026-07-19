# 国家图书馆整期原刊记录级审核

审核日期：2026-07-19  
审核人：Codex

本轮审核对象为 39 条 NLC 整期原刊候选，范围是《光明報》和《民憲》整期记录，不包含文章级候选。

## 审核门槛

- 候选为 NLC 来源、L1、`digital_image`，且此前为 `needs_human_review`。
- 记录标题为整期《光明報》或《民憲》，排除候选 ID 中的 `article` 文章卡。
- `access_note` 或 `evidence_locator` 能定位到项目内本地 PDF，且文件真实存在。
- 已有 NLC 馆藏编号、日期和封面/目录页或整期页数记录；相关卷期审核记录和 SHA256 已写入 `work/domestic/`、`docs/domestic/press_scan_manifest.md` 或候选字段。

## 处理结果

- 39/39 条通过整期记录级审核并写回 `data/domestic/candidates.jsonl`。
- SQLite 幂等同步后，待人工复核从 246 条降至 207 条；整期记录的 `authenticity_level_accepted` 为 L1。
- 这次接受不代表期内每篇文章都已逐字转录，不代表复制权利已无条件确认，也不代表《民憲》或《光明報》中的文章就是民盟正式文件原件。
- 文章级候选、1941《光明報》原刊目标日期、1947政府公函、民盟总部解散公告和北平《新民報》原版继续保留在后续工作队列。

执行脚本：`scripts/domestic/accept_verified_nlc_issue_scans_20260720.py`。

