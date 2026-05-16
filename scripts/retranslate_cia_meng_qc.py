#!/usr/bin/env python3
"""CIA 翻译全量复审（machine-draft → machine-reviewed）

策略：
1. 全部 61 篇 CIA 译文用增强 prompt 重译
2. 增强 prompt 重点：
   - 强制术语表（361 条）应用
   - 同一人物全文译名一致
   - 删除 OCR 残留水印
   - 人名首次出现括注英文原名
3. 质量检查：与机器初稿对比，识别明显改善的篇目
4. 输出 machine-reviewed 状态 + 质量报告

每篇翻译耗时约 5-30s，总耗时约 5-15 分钟。
"""
import sqlite3, json, time, sys, os, csv, requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "research_index.sqlite"
GLOSSARY_CSV = ROOT / "data" / "translation_glossary.csv"
LOG = ROOT / "retranslate_cia_qc.log"
REPORT = ROOT / "docs" / "_cia-翻译复审报告.md"

DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DS_KEY:
    print("ERROR: 请设置 DEEPSEEK_API_KEY", file=sys.stderr)
    sys.exit(1)
DS_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

# 读术语表
glossary_lines = []
with open(GLOSSARY_CSV, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        glossary_lines.append(f"  {row['term']} → {row['translation']}")
GLOSSARY_TXT = "\n".join(glossary_lines)

SYSTEM_PROMPT = """你是一名资深的中国近代史档案翻译专家，专精 1940s-1950s 美方一手档案
（FRUS / CIA / Wilson Center），特别熟悉中国民主同盟相关史料。

任务：把以下 CIA 解密档案的英文 OCR 文本翻译成**学术级中文译文**。

【严格要求】

1. **统一术语**（必须按以下表对应翻译）：
""" + GLOSSARY_TXT + """

2. **CIA 档案常见缩写处理**：
   - DL / D.L. → 中国民主同盟（民盟）
   - CCP → 中国共产党
   - KMT / Kmt → 国民党
   - PCC → 政治协商会议（政协）
   - CPPCC → 中国人民政治协商会议
   - PPC → 国民参政会
   - CC Clique → CC系
   - non-Communist → 非中共
   - third force / third party → 第三方面
   - Gimo / Generalissimo → 蒋介石

3. **同一文档内人物译名必须前后一致**：
   - LO Lung-chi / Lo Lung-chi / Lo Lung-Chi → 统一译为「罗隆基」
   - CHANG Lan / Chang Lan → 统一译为「张澜」
   - 同理 SHEN Chun-ju / 沈钧儒、CHANG Po-chun / 章伯钧、Carsun Chang / 张君劢 等
   - 人名首次出现可在中文译名后括注英文原名，如「张澜（Chang Lan）」

4. **OCR 噪声去除**：
   - 忽略 "Approved For Release"、"CONFIDENTIAL"、"SECRET"、"25X1A" 等水印
   - 忽略 "STATE NAVY ARMY AIR FBI" 等表单分发清单
   - 忽略残缺的页眉页脚字符（如 "lm:"、"\\|"、"X"）
   - 但保留正文中的所有实质信息（标题、日期、报告编号、人名、事件）

5. **体例**：
   - 译为档案体中文，准确传达原意，不删减不臆加
   - 保留原文档号、日期、地点、电报号等元数据
   - 长句按汉语习惯拆开，但不丢信息
   - 标点用中文标点
   - 数字保留阿拉伯数字
   - 表格类内容（如人员名单）保留分行结构

6. **输出格式**：纯中文译文，按原文段落分段。"""


def translate(en_text: str) -> str:
    resp = requests.post(
        DS_URL,
        headers={"Authorization": f"Bearer {DS_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": en_text},
            ],
            "max_tokens": 8000,
            "temperature": 0.15,    # 降一点，结果更稳定
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def detect_quality_issues(zh: str, original_en_chars: int) -> list[str]:
    """检测译文常见问题"""
    issues = []
    # 1. 残留英文短语（连续 2 个以上英文单词非元数据上下文）
    import re
    en_runs = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,}', zh)
    # 过滤掉常见 OK 的（已知人名英文括注）
    en_runs_filtered = [r for r in en_runs if not re.search(r'^(Lo Lung|Chang Lan|Shen Chun|Wen I|Liang Shu|Carsun|Chou En)', r)]
    if len(en_runs_filtered) > 5:
        issues.append(f'残留英文片段过多 ({len(en_runs_filtered)} 处)')
    # 2. 译文过短（少于原文字符数的 8%，OCR 噪声大档案除外）
    if len(zh) < original_en_chars * 0.08:
        issues.append(f'译文过短: zh={len(zh)} vs en={original_en_chars}')
    # 3. 仍含 OCR 噪声残留
    for noise in ['Approved For Release', 'CONFIDENTIAL/', '25X1A', '25X1X']:
        if noise in zh:
            issues.append(f'OCR 残留: {noise!r}')
            break
    # 4. 仍含未翻译的英文缩写
    for kw in ['DEMOCRATIC LEAGUE', 'KMT government', 'CCP government']:
        if kw in zh:
            issues.append(f'缩写未翻译: {kw!r}')
    return issues


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT p.id AS page_id, p.text AS en_text, d.title, d.date_guess, d.doc_id,
               t.id AS tid, t.text AS old_zh, t.status AS old_status
        FROM pages p
        JOIN documents d ON d.id = p.document_id
        JOIN translations t ON t.page_id = p.id AND t.language='zh-CN'
        WHERE d.source_platform='cia'
        ORDER BY d.date_guess, p.id
        """
    ).fetchall()

    print(f"待复审 CIA 译文: {len(rows)} 篇")

    report = ['# CIA 翻译全量复审报告', '', f'> 复审日期: {time.strftime("%Y-%m-%d")}', '',
              f'> 复审方式: DeepSeek deepseek-chat + 增强 prompt + 术语表 361 条', '',
              f'> 翻译数量: {len(rows)} 篇', '', '---', '']

    qc_results = []
    done, fail = 0, 0
    with open(LOG, 'w') as logf:
        def log(msg):
            print(msg, flush=True)
            logf.write(msg + '\n')
            logf.flush()

        log(f'==== CIA 复审启动 {time.strftime("%Y-%m-%d %H:%M:%S")} ====')
        for i, r in enumerate(rows, 1):
            pid = r['page_id']
            en = r['en_text']
            log(f'\n--- [{i}/{len(rows)}] page_id={pid} | en={len(en)} | [{r["date_guess"]}] {r["title"][:50]}')
            try:
                t0 = time.time()
                new_zh = translate(en)
                dt = time.time() - t0

                old_zh = r['old_zh'] or ''
                old_issues = detect_quality_issues(old_zh, len(en))
                new_issues = detect_quality_issues(new_zh, len(en))

                # 写回
                cur.execute(
                    "UPDATE translations SET text=?, status=?, translator=? WHERE id=?",
                    (new_zh, 'machine-reviewed', 'deepseek-chat-2026-05-16-cia-qc', r['tid']),
                )
                try:
                    cur.execute("DELETE FROM translation_fts WHERE rowid=?", (r['tid'],))
                    cur.execute(
                        "INSERT INTO translation_fts (rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, '1', ?)",
                        (r['tid'], r['title'], new_zh),
                    )
                except sqlite3.OperationalError:
                    pass
                conn.commit()

                log(f'  复审 OK in {dt:.1f}s | old_zh={len(old_zh)} → new_zh={len(new_zh)}')
                log(f'  old_issues: {old_issues}')
                log(f'  new_issues: {new_issues}')

                qc_results.append({
                    'page_id': pid,
                    'title': r['title'],
                    'date': r['date_guess'],
                    'en_chars': len(en),
                    'old_zh': len(old_zh),
                    'new_zh': len(new_zh),
                    'old_issues': old_issues,
                    'new_issues': new_issues,
                })
                done += 1
            except Exception as e:
                log(f'  ERR: {e}')
                fail += 1
                time.sleep(2)

        log(f'\n==== 复审完成 ====')
        log(f'  成功: {done}')
        log(f'  失败: {fail}')

    # 写质量报告
    report.append('## 复审结果统计')
    report.append('')
    total_improved = sum(1 for q in qc_results if len(q['new_issues']) < len(q['old_issues']))
    total_clean = sum(1 for q in qc_results if not q['new_issues'])
    report.append(f'- 成功复审: **{done}** 篇')
    report.append(f'- 失败: {fail} 篇')
    report.append(f'- 复审后无质量问题: **{total_clean}** / {done}')
    report.append(f'- 较初稿有改善: **{total_improved}** 篇')
    report.append('')
    report.append('## 仍有质量问题的篇目')
    report.append('')
    still_issues = [q for q in qc_results if q['new_issues']]
    if not still_issues:
        report.append('✅ 所有篇目均通过质量检查。')
    else:
        report.append(f'| 日期 | 标题 | 残留问题 |')
        report.append(f'|------|------|---------|')
        for q in still_issues:
            report.append(f'| {q["date"]} | {q["title"][:60]} | {"; ".join(q["new_issues"])} |')
    report.append('')
    report.append('## 状态升级')
    report.append('')
    report.append('所有复审通过的 CIA 译文状态从 `machine-draft` 升级到 **`machine-reviewed`**，')
    report.append('翻译器标记为 `deepseek-chat-2026-05-16-cia-qc`。')
    report.append('')
    report.append('> **注**：这仍是机器翻译（非人工逐句校订）。如需达到 FRUS 同等的 `human-reviewed` 等级，')
    report.append('> 需在 `/review/<page_id>` 校订页人工逐篇精修。')

    REPORT.write_text('\n'.join(report), encoding='utf-8')
    print(f'\n质量报告写入: {REPORT}')
    conn.close()


if __name__ == '__main__':
    main()
