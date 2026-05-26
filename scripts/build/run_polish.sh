#!/usr/bin/env bash
# 周末扫地 - 一键执行所有维护脚本，输出汇总日志
# 用法： bash scripts/build/run_polish.sh
# 必须在项目根目录执行

set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"

LOG=workspace/polish-$(date +%Y%m%d-%H%M).log
mkdir -p workspace
exec > >(tee "$LOG") 2>&1

echo "==== 扫地启动 $(date '+%Y-%m-%d %H:%M:%S') ===="
echo "项目根目录：$ROOT"
echo "日志：$LOG"

run_step() {
    local title="$1"
    shift
    echo
    echo "---- [$title] ----"
    "$@" || { echo "⚠ 该步失败，但继续后续："; }
}

# 1. CIA 译文残留清理（含通用 regex + 威氏拼音对照）
run_step "CIA 译文残留清理" \
    python3 scripts/build/refine_cia_translation_residue.py

# 2. 翻译质量报告（含新加的 translation_failed 检测 + DRNH 跳过）
run_step "重新生成翻译质量报告" \
    python3 scripts/build/build_translation_quality_report.py

# 3. DRNH 自动转写校订分层
run_step "重建 DRNH 校订分层队列" \
    python3 scripts/build/build_drnh_review_layers.py

# 4. 外部档案获取优先队列（Kew / HKPRO / 中研院 / Hoover）
run_step "更新外部档案获取优先队列" \
    python3 scripts/build/build_external_acquisition_queue.py

# 5. HathiTrust 质量分诊
run_step "重建 HathiTrust 质量分诊" \
    python3 scripts/build/build_hathitrust_quality_triage.py

# 6. 译文优先问题处理
run_step "处理优先翻译问题" \
    python3 scripts/build/resolve_priority_translation_issues.py

# 7. 术语索引注解
run_step "应用术语索引注解" \
    python3 scripts/build/apply_glossary_index_notes.py

# 8. CIA 误匹配剔除（24 篇与中国民盟无关：朝鲜 / 日本 / 东南亚 / 1956+）
run_step "CIA 误匹配剔除（朝鲜 / 日本 / 东南亚 / 1956+）" \
    python3 scripts/build/exclude_cia_off_topic.py

echo
echo "==== 扫地完成 $(date '+%Y-%m-%d %H:%M:%S') ===="
echo
echo "下一步建议："
echo "  - 查看 docs/translation_quality_report.md 看本次的 issue 清单"
echo "  - 如有 translation_failed 类型，跑 scripts/translate/retranslate_with_deepseek.py 重译"
echo "  - 如有 missing_translation，跑 scripts/translate/translate_missing_pages_argos.py"
echo "  - 提交本次扫地结果： git add -A && git commit -m 'chore: 扫地维护 YYYY-MM-DD'"
