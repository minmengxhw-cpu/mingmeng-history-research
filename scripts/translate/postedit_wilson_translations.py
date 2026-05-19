#!/usr/bin/env python3
"""Wilson Center 111 段机器初稿批量后编辑（无需 API）

策略：
1. 分离元数据头部（Digital Archive ... Contents: English Translation）和正文
2. 元数据头部用标准格式重建（从英文原文提取关键字段）
3. 正文部分做术语表替换 + 常见错误修正
4. 纯元数据页（无正文）标记为 system-note
"""
import sqlite3, re, csv, sys
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "research_index.sqlite"
GLOSSARY_CSV = Path(__file__).parent.parent / "data" / "translation_glossary.csv"

# ── 术语表 ──
TERM_FIXES = {}
try:
    with open(GLOSSARY_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("term") and row.get("translation"):
                TERM_FIXES[row["term"]] = row["translation"]
except FileNotFoundError:
    pass

# ── 人名修正（Argos 常见错译）──
NAME_FIXES = {
    "王若菲": "王若飞",
    "王若发": "王若飞",
    "阿波罗·彼得罗夫": "彼得罗夫",
    "蒋洁石": "蒋介石",
    "蒋杰石": "蒋介石",
    "谢尔盖·拉德琴科": "谢尔盖·拉德琴科",  # 这个是正确的，保留
    "毛泽通": "毛泽东",
    "毛则东": "毛泽东",
    "周恩赖": "周恩来",
    "刘绍奇": "刘少奇",
    "刘韶琦": "刘少奇",
    "斯塔林": "斯大林",
    "史大林": "斯大林",
    "斯达林": "斯大林",
    "科瓦廖夫": "科瓦廖夫",  # 保留
    "米高杨": "米高扬",
    "米科杨": "米高扬",
    "米可扬": "米高扬",
    "彭德淮": "彭德怀",
    "彭得怀": "彭德怀",
    "罗什钦": "罗申",
    "罗什琴": "罗申",
    "罗什金": "罗申",
    "GMD": "国民党",
    "KMT": "国民党",
    "Cde.": "同志",
    "Cde。": "同志",
    "cde.": "同志",
    "cde。": "同志",
    "Cdes.": "同志们",
    "cdes.": "同志们",
    "全球监测司": "国民党",  # GMD 被错译
    "胶东革命委员会": "国民党革命委员会",  # Kuomintang Revolutionary Committee
}

# ── 元数据头部检测 ──
HEADER_PATTERNS = [
    re.compile(r"Digital\s+Archive.*?(?:Contents:\s*(?:English\s+)?Translation|(?:Original\s+Language:\s*\w+))", re.DOTALL | re.IGNORECASE),
    re.compile(r"^Digital\s+Archive\s+digitalarchive\.wilsoncenter\.org.*?$", re.MULTILINE),
]

# 从英文原文提取元数据
def extract_metadata(en_text: str) -> dict:
    meta = {}
    # 日期
    m = re.search(r"(\w+ \d{1,2}, \d{4}|\d{4}-\d{2}-\d{2})", en_text[:500])
    if m:
        meta["date"] = m.group(1)
    # 标题（Citation 中的标题）
    m = re.search(r'Citation:\s*["\u201c](.+?)["\u201d]', en_text[:1000], re.DOTALL)
    if m:
        meta["citation_title"] = re.sub(r"\s+", " ", m.group(1).strip())
    # 原始语言
    m = re.search(r"Original Language:\s*(\w+)", en_text)
    if m:
        meta["original_lang"] = m.group(1)
    # Wilson URL
    m = re.search(r"(https?://digitalarchive\.wilsoncenter\.org/document/\d+)", en_text)
    if m:
        meta["url"] = m.group(1)
    # Archive reference
    m = re.search(r"(AVPRF|RGASPI|APRF|TsKhSD|CWIHP)[:\s]+(.+?)(?:\.\s|Translated)", en_text)
    if m:
        meta["archive_ref"] = f"{m.group(1)}: {m.group(2).strip()}"
    # Summary
    m = re.search(r"Summary:\s*(.+?)(?:\n\s*\n|Original Language:)", en_text, re.DOTALL)
    if m:
        meta["summary"] = re.sub(r"\s+", " ", m.group(1).strip())
    return meta


def build_header(meta: dict, doc_title: str) -> str:
    """生成标准化的元数据头部"""
    lines = ["【Wilson Center 数字档案】"]
    if "citation_title" in meta:
        lines.append(f"题名：{meta['citation_title']}")
    if "date" in meta:
        lines.append(f"日期：{meta['date']}")
    if "original_lang" in meta:
        lang_zh = {"Russian": "俄文", "Chinese": "中文", "English": "英文"}.get(meta["original_lang"], meta["original_lang"])
        lines.append(f"原文语言：{lang_zh}")
    if "archive_ref" in meta:
        lines.append(f"档案出处：{meta['archive_ref']}")
    if "url" in meta:
        lines.append(f"来源：{meta['url']}")
    if "summary" in meta:
        lines.append(f"摘要：{meta['summary']}")
    return "\n".join(lines)


def split_header_body(en_text: str) -> tuple[str, str]:
    """分离 Wilson 元数据头部和正文"""
    # 尝试找 "Contents: English Translation" 或 "Contents:\n      English Translation"
    m = re.search(r"Contents:\s*(?:English\s+)?Translation\s*", en_text, re.IGNORECASE)
    if m:
        return en_text[:m.end()], en_text[m.end():].strip()
    # 尝试找 "Original Language: ..." 后面的正文
    m = re.search(r"Original Language:\s*\w+\s*(?:Contents:\s*)?", en_text, re.IGNORECASE)
    if m:
        return en_text[:m.end()], en_text[m.end():].strip()
    return "", en_text


def fix_zh_text(zh: str) -> str:
    """术语表替换 + 常见错误修正"""
    for wrong, right in NAME_FIXES.items():
        zh = zh.replace(wrong, right)
    
    # 修正 "fond" → 保留原文
    zh = re.sub(r"love (\d+)", r"fond \1", zh)  # AVPRF: love -> fond
    
    # 修正 "(中文(简体) )" → 移除
    zh = re.sub(r"\(中文\(简体\)\s*\)\.\s*", "", zh)
    
    # 修正 "历史与公共政策方案 数字档案" → 标准化
    zh = zh.replace("历史与公共政策方案 数字档案", "历史与公共政策项目数字档案")
    
    # 修正 "[永久失效連結]" 等无意义标注
    zh = re.sub(r"\[永久失效連結\]", "", zh)
    
    # 修正 "Cde" 残留
    zh = re.sub(r"Cde\s*。?\s*", "", zh)
    
    return zh


def process_page(pid: int, en_text: str, zh_text: str, doc_title: str) -> tuple[str, str]:
    """处理一个页面，返回 (new_zh, new_status)"""
    en_header, en_body = split_header_body(en_text)
    
    # 纯元数据页（无正文或正文极短）
    if len(en_body.strip()) < 50:
        meta = extract_metadata(en_text)
        new_zh = build_header(meta, doc_title)
        return new_zh, "machine-reviewed"
    
    # 有正文的页面：
    # 1. 检查机器翻译中是否有元数据头部
    zh_has_header = "Digital Archive" in zh_text[:100] or "digitalarchive" in zh_text[:200]
    
    if zh_has_header and en_header:
        # 从机器翻译中去掉元数据头部，用标准化版本替换
        meta = extract_metadata(en_text)
        # 找到机器翻译中元数据结束的位置
        zh_body = zh_text
        # 尝试找 "原文:" 或 "内容:" 后面的正文
        for marker in ["内容:", "内容：", "英语翻译记录", "英文翻译", "Translation"]:
            idx = zh_text.find(marker)
            if idx > 0:
                zh_body = zh_text[idx + len(marker):].strip()
                break
        
        zh_body = fix_zh_text(zh_body)
        header = build_header(meta, doc_title)
        new_zh = f"{header}\n\n{zh_body}"
    else:
        # 正文已经是纯翻译，只做术语修正
        new_zh = fix_zh_text(zh_text)
    
    return new_zh, "machine-reviewed"


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT t.id AS tid, t.text AS zh, p.id AS pid, p.text AS en, 
               p.page_label, d.title
        FROM translations t
        JOIN pages p ON p.id=t.page_id
        JOIN documents d ON d.id=p.document_id
        WHERE d.source_platform='wilson' AND t.language='zh-CN'
        AND t.status='machine-draft-local-review-needed'
        ORDER BY p.id
    """).fetchall()
    
    print(f"Wilson 待复审: {len(rows)} 段")
    
    updated = 0
    for r in rows:
        new_zh, new_status = process_page(r["pid"], r["en"], r["zh"], r["title"])
        
        if new_zh != r["zh"] or new_status != "machine-draft-local-review-needed":
            conn.execute(
                "UPDATE translations SET text=?, status=?, translator='postedit-2026-05-17' WHERE id=?",
                (new_zh, new_status, r["tid"])
            )
            # 更新 FTS
            conn.execute("DELETE FROM translation_fts WHERE rowid=?", (r["tid"],))
            conn.execute(
                "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, ?, ?)",
                (r["tid"], r["title"], r["page_label"], new_zh)
            )
            updated += 1
            
            if updated <= 5:
                print(f"\n--- page {r['pid']} ---")
                print(f"  标题: {r['title'][:60]}")
                print(f"  状态: machine-draft-local-review-needed → {new_status}")
                old_len = len(r["zh"])
                new_len = len(new_zh)
                print(f"  长度: {old_len} → {new_len}")
                print(f"  新译文前200字: {new_zh[:200]}")
            elif updated == 6:
                print("\n  ... (后续省略) ...")
    
    conn.commit()
    
    # 统计
    remaining = conn.execute("""
        SELECT status, count(*) AS n FROM translations t
        JOIN pages p ON p.id=t.page_id
        JOIN documents d ON d.id=p.document_id
        WHERE d.source_platform='wilson' AND t.language='zh-CN'
        GROUP BY status
    """).fetchall()
    
    print(f"\n=== 完成 ===")
    print(f"更新: {updated} 段")
    print(f"\nWilson 翻译状态:")
    for r in remaining:
        print(f"  {r['status']}: {r['n']}")
    
    conn.close()


if __name__ == "__main__":
    main()
