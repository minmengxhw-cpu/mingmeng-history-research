# 国内研究平台发布与恢复验收（2026-08-24）

## 结论

发布边界和当前本地正式库基线通过；完整灾备恢复演练尚未宣称完成，因为本轮没有从外部数据包重新复制一份数据库和原件资产。

## 已验证项目

| 项目 | 结果 | 证据 |
|---|---|---|
| Git 跟踪面 | PASS | 跟踪文件中没有 `research_index.sqlite`、`raw/` 原件或数据库备份 |
| 正式库 manifest | PASS | `verify_research_index_manifest.py`：SQLite 完整性、外键、FTS、来源文件 SHA 全部通过 |
| 国内正式库 | PASS | 554 篇文档、6277 页、693 条候选；数据库 SHA256 已写入 manifest |
| SQLite 内存恢复烟雾测试 | PASS | 备份到新内存连接后，`integrity_check=ok`、外键 0、FTS 双向无孤儿，6.68 秒完成 |
| 公开 HTML 面 | PASS | 统一门禁的 22 条公开路由无 `/Users/`、`/private/`、`/tmp/`、`file://`、本地字段标记 |
| 研究问题路径 | PASS | 36/36 路径可达，0 条路径失败 |
| 内容闭环 | OPEN | 9/9 可带边界研究，0/9 `research_ready`；P0 原件仍待接收 |

## 恢复流程

数据库和原始/OCR 资产不进入 Git。恢复到另一台 Mac 后，按以下顺序验收：

```bash
python3 scripts/closeout/verify_research_index_manifest.py \
  --db /absolute/path/research_index.sqlite

MINGMENG_RESEARCH_DB=/absolute/path/research_index.sqlite \
MINGMENG_DATA_ROOT=/absolute/path/data \
MINGMENG_WORK_ROOT=/absolute/path/work \
python3 scripts/domestic/validate_unified_research_platform.py \
  --output /tmp/unified_platform_gate_after_restore.json
```

两条命令都通过后，才允许启动研究页面。若使用本项目默认目录，`data/research_index.sqlite` 可以是外部数据 checkout 的软链接，但 manifest 校验必须针对实际目标文件执行。

## 增量入库边界

任何新增资料必须先进入 staging 或授权接收目录：

```text
原件/电子文件 → 文件 SHA256 → 页面 manifest → 来源和权利 →
页级身份复核 → 必要时定向 OCR → dry-run → 备份 → 正式入库 → 全门禁
```

- 已有电子文本不重复 OCR；
- 目录、锁定查看器和学术元数据不写入正式页正文；
- 正式 SQLite 写入前必须保留带日期的可恢复备份；
- 不因空间压力删除原始资料，先做重复确认和可恢复归档；
- `PASS` 只表示机制一致，必须同时查看 `research_content_status`。

## 尚未完成的灾备项

1. 从实际数据包在另一台 Mac 完整恢复数据库、原件资产和 staging；
2. 对恢复后的路径重新计算所有来源 SHA，并运行完整门禁；
3. 验证至少一个研究包、一个页级引用卡和一个国内—海外对读页面可重建；
4. 记录恢复耗时、磁盘占用和失败回滚路径。

内存恢复烟雾测试只证明 SQLite 文件本身可被重新打开和校验，不替代从外部数据包恢复原件、staging 和另一台 Mac 路径的完整演练。

因此当前发布状态是：**代码与元数据可推送，正式数据可按 manifest 恢复，内容仍保持 `OPEN_PRIMARY_GAPS`。**
