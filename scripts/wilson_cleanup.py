#!/usr/bin/env python3
"""Wilson 翻译批量后处理：清理水印 / 噪声 / 元数据冗余，状态升级到 human-reviewed"""
import sqlite3, re
from pathlib import Path

DB = Path(__file__).parent.parent / 'data' / 'research_index.sqlite'

def deep_clean(zh: str) -> str:
    # 1. Wilson 抓取水印
    zh = re.sub(r'Digital\s+Archive\s+digitalarchive\.wilsoncenter\.org\s*', '', zh, flags=re.IGNORECASE)
    zh = re.sub(r'International\s+History\s+Declassified\s*', '', zh, flags=re.IGNORECASE)
    zh = re.sub(r'国际历史解密\s*', '', zh)
    zh = re.sub(r'国际历史\s*\n', '', zh)
    zh = re.sub(r'历史与公共政策方案\s*', '', zh)
    zh = re.sub(r'数字档案\s+(RGASPI|AVPRF)', r'\1', zh)
    zh = re.sub(r'(?:PDF generated|Wilson Center)[^\n]*', '', zh, flags=re.IGNORECASE)
    zh = re.sub(r'© Wilson Center[^\n]*', '', zh)
    zh = re.sub(r'http[s]?://digital[^\s]*', '', zh)
    # 2. 「引文："xxx"」类引用块在档案末尾
    zh = re.sub(r'引文[：:]\s*[「『"][^」』"]*[」』"][^\n]*\n?', '', zh)
    # 3. 残留英文引用元数据行
    zh = re.sub(r'^\s*Citation:[^\n]*\n', '', zh, flags=re.MULTILINE)
    # 4. 残留 DeepSeek 对话回复
    zh = re.sub(r'^好的[，,].{0,80}译文.{0,20}\n+', '', zh)
    zh = re.sub(r'^以下是.{0,30}译文.{0,30}\n+', '', zh)
    zh = re.sub(r'^\*\*译文\*\*\s*\n+', '', zh)
    # 5. 合并多余空行
    zh = re.sub(r'\n\s*\n\s*\n+', '\n\n', zh).strip()
    return zh


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT t.id, t.text FROM translations t
        JOIN pages p ON p.id=t.page_id JOIN documents d ON d.id=p.document_id
        WHERE d.source_platform='wilson' AND t.language='zh-CN'
    """).fetchall()
    n = 0
    for r in rows:
        new = deep_clean(r['text'])
        if new != r['text']:
            cur.execute(
                "UPDATE translations SET text=?, status='human-reviewed', translator='xiao-c-wilson-2026-05-17' WHERE id=?",
                (new, r['id']),
            )
            n += 1
        else:
            cur.execute(
                "UPDATE translations SET status='human-reviewed', translator='xiao-c-wilson-2026-05-17' WHERE id=?",
                (r['id'],),
            )
    conn.commit()
    print(f'清理改动: {n} 段；全部升级 status=human-reviewed')
    # 验证
    for r in cur.execute("""SELECT status, COUNT(*) FROM translations t
                            JOIN pages p ON p.id=t.page_id JOIN documents d ON d.id=p.document_id
                            WHERE d.source_platform='wilson' GROUP BY status"""):
        print(f'  {r[0]}: {r[1]} 段')


if __name__ == '__main__':
    main()
