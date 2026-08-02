# Formal DB Rebaseline 方案 — e4417bd1（2026-08-02）

## 状态
| 项 | 值 |
|---|---|
| 冻结基线（此前） | `822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3` |
| 当前 SHA | `e4417bd1dfce77772832e0fcee17f5fb33bbd0fc9d1e6b2618932a64e9c8c0a5` |
| 漂移 | 是（`drift_detected=true`，`new_baseline_approval_pending=true`） |
| 归因 | `application-driven (app.py PID 68642 / supervisor PID 32605)`；非 subagent 写入 |
| write_policy | 对 subagent 仍 FROZEN |

## 漂移成因
`scripts/build/build_translation_quality_report.py` 运行时会 `DROP TABLE IF EXISTS translation_quality_issues` + `CREATE` + 写入约 4400 行，导致正式库 SHA 漂移。该表非内容数据，属 QC 报告副产品。

## 处置选项
### 方案 A（推荐）：接受 e4417bd1 为新冻结基线
1. 若尚未验证，先跑 `work/domestic/FORMAL_DB_SHA_AUDIT_*` 类审计脚本确认除 `translation_quality_issues` 外无其他漂移。
2. 更新 `work/domestic/monitor_status_latest.json` / `.md` 的 `formal_db` 字段（`previous_freeze_sha256` → 822e..., `sha256` → e4417..., `new_baseline_approval_pending` → false）。
3. 批量替换 `scripts/domestic/*.py` 中硬编码的 `EXPECTED_FORMAL_SHA`（现仍为 822e...，需改为 e4417...）。
4. 提交。

### 方案 B：剔除 QC 副作用后再基线
若希望冻结基线不含 `translation_quality_issues` 表写入，则需在干净状态下重建该表（仅结构）再取 SHA；此方案更复杂，除非审计发现内容漂移，否则不建议。

## 修订译文导入（rebaseline 通过后执行）
以下 CSV 与 `scripts/lib/import_translations_csv.py` 兼容（列：page_id, zh_translation, translator_note, translator, status）：

1. `data/domestic/zh_translation_revisions_frus_core.csv` — 11 页 FRUS/CIA 核心修订（126/107/168/228/301/40/300 + 151/332/783/839）。导入命令（在仓库根目录）：
   ```
   python3 scripts/lib/import_translations_csv.py \
     data/domestic/zh_translation_revisions_frus_core.csv \
     --translator cloud-model-revision-v1 --status machine-revised
   ```
2. `data/domestic/zh_translation_revisions_hathitrust_mix.csv` — 28 页 hathitrust 混排标注（追加校订说明）。同上命令。

注意：import 脚本对每页 DELETE+INSERT 并重建 FTS，导入后正式库 SHA 将再次漂移——应在 rebaseline 完成后、且准备接受新 SHA 时再执行导入，随后再补一次基线更新。

## 引用
- 上次 rebaseline：`work/domestic/FORMAL_DB_REBASELINE_20260801.md`
- 本轮翻译修订详情：`work/domestic/TRANSLATION_QUALITY_REVISION_20260802.md`
