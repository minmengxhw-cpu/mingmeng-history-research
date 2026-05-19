#!/usr/bin/env python3
"""CIA 扩展抓取：从 archive.org 批量下载民盟相关 CIA 文档的 OCR 全文并入库"""
import sqlite3, json, time, sys, re, urllib.request, urllib.parse
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "research_index.sqlite"

# ── Step 1: 从 archive.org 获取所有提到 "democratic league" + "China" 的 CIA 文档 ──
def fetch_candidate_list():
    """从 archive.org 搜索 API 获取候选文档列表"""
    base = "https://archive.org/advancedsearch.php"
    params = {
        "q": '"democratic league" AND "China" AND mediatype:texts AND creator:"CIA Reading Room"',
        "fl[]": ["identifier", "title", "date"],
        "sort[]": "date asc",
        "rows": 200,
        "page": 1,
        "output": "json",
    }
    # Build URL manually for fl[] array params
    parts = [f"q={urllib.parse.quote(params['q'])}"]
    for field in ["identifier", "title", "date"]:
        parts.append(f"fl[]={field}")
    parts.append(f"sort[]=date+asc")
    parts.append(f"rows={params['rows']}")
    parts.append(f"page={params['page']}")
    parts.append("output=json")
    url = f"{base}?{'&'.join(parts)}"
    
    print(f"搜索 archive.org: {url[:100]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "MinmengResearchBot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    
    docs = data["response"]["docs"]
    print(f"  找到 {data['response']['numFound']} 篇候选文档")
    return docs


def normalize_id(identifier: str) -> str:
    """标准化 archive.org identifier 到 doc_key"""
    # archive.org identifier 格式: cia-readingroom-document-cia-rdp82-00457r...
    # 或大写格式: CIA-RDP82-00457R...
    lower = identifier.lower()
    if lower.startswith("cia-readingroom-document-"):
        return f"cia-meng:{lower}"
    else:
        # 大写 CIA-RDP 格式
        return f"cia-meng:{lower}"


def fetch_ocr_text(identifier: str) -> str:
    """从 archive.org 下载 OCR 全文"""
    # 尝试多种文本格式
    for suffix in ["_djvu.txt", "_text.pdf", ""]:
        url = f"https://archive.org/download/{identifier}/{identifier}{suffix}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MinmengResearchBot/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.getcode() == 200:
                    text = resp.read().decode("utf-8", errors="replace")
                    if len(text.strip()) > 50:
                        return text.strip()
        except Exception:
            continue
    
    # 最后尝试 metadata API 获取 OCR
    try:
        meta_url = f"https://archive.org/metadata/{identifier}/files"
        req = urllib.request.Request(meta_url, headers={"User-Agent": "MinmengResearchBot/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            files = json.loads(resp.read())["result"]
        
        # 找 .txt 文件
        for f in files:
            if f["name"].endswith(".txt") and f.get("size", "0") != "0":
                txt_url = f"https://archive.org/download/{identifier}/{urllib.parse.quote(f['name'])}"
                req2 = urllib.request.Request(txt_url, headers={"User-Agent": "MinmengResearchBot/1.0"})
                with urllib.request.urlopen(req2, timeout=30) as resp2:
                    text = resp2.read().decode("utf-8", errors="replace")
                    if len(text.strip()) > 50:
                        return text.strip()
    except Exception:
        pass
    
    return ""


def parse_date(date_str: str) -> str:
    """从 ISO 日期提取 YYYY-MM-DD"""
    if not date_str:
        return ""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", date_str)
    return m.group(1) if m else date_str[:10]


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # 获取已有的 doc_key 集合
    existing_keys = set()
    for row in cur.execute("SELECT doc_key FROM documents WHERE source_platform='cia'"):
        existing_keys.add(row["doc_key"].lower())
    print(f"已有 CIA 文档: {len(existing_keys)} 篇")
    
    # 获取候选列表
    candidates = fetch_candidate_list()
    
    # 过滤出新文档
    new_docs = []
    for doc in candidates:
        key = normalize_id(doc["identifier"])
        if key.lower() not in existing_keys:
            new_docs.append(doc)
    
    print(f"新文档: {len(new_docs)} 篇")
    
    if not new_docs:
        print("没有新文档需要抓取！")
        conn.close()
        return
    
    # 获取最大 document id
    max_doc_id = cur.execute("SELECT COALESCE(MAX(id), 0) FROM documents").fetchone()[0]
    max_page_id = cur.execute("SELECT COALESCE(MAX(id), 0) FROM pages").fetchone()[0]
    max_trans_id = cur.execute("SELECT COALESCE(MAX(id), 0) FROM translations").fetchone()[0]
    
    success = 0
    failed = 0
    
    for i, doc in enumerate(new_docs):
        identifier = doc["identifier"]
        title = doc.get("title", identifier)
        date_str = parse_date(doc.get("date", ""))
        doc_key = normalize_id(identifier)
        
        print(f"\n[{i+1}/{len(new_docs)}] {title[:70]}")
        print(f"  ID: {identifier} | 日期: {date_str}")
        
        # 下载 OCR 文本
        text = fetch_ocr_text(identifier)
        if not text:
            print(f"  ⚠️ 无法获取文本，跳过")
            failed += 1
            continue
        
        print(f"  ✅ 获取文本 {len(text):,} 字符")
        
        # 插入 documents
        max_doc_id += 1
        archive_url = f"https://archive.org/details/{identifier}"
        cur.execute("""
            INSERT INTO documents (id, source_id, doc_key, volume_id, volume_title,
                                   doc_id, doc_number, title, date_guess, 
                                   url, hit_type, matched_terms, source_platform)
            VALUES (?, 12, ?, 'CIA-CREST', 'CIA Records Reading Room',
                    ?, '', ?, ?,
                    ?, 'expansion', 'China Democratic League', 'cia')
        """, (max_doc_id, doc_key, identifier, title, date_str, archive_url))
        
        # 插入 pages
        max_page_id += 1
        cur.execute("""
            INSERT INTO pages (id, document_id, page_label, page_url, text)
            VALUES (?, ?, 'full', ?, ?)
        """, (max_page_id, max_doc_id, archive_url, text))
        
        # 插入 page_fts
        cur.execute("""
            INSERT INTO page_fts (rowid, title, page_label, text)
            VALUES (?, ?, 'full', ?)
        """, (max_page_id, title, text))
        
        # 插入空白翻译占位（标记为 machine-draft 待翻译）
        max_trans_id += 1
        cur.execute("""
            INSERT INTO translations (id, page_id, language, text, status, translator)
            VALUES (?, ?, 'zh-CN', ?, 'machine-draft', 'pending-translation')
        """, (max_trans_id, max_page_id, f"【待翻译】{title}"))
        
        # 插入 translation_fts
        cur.execute("""
            INSERT INTO translation_fts (rowid, language, title, page_label, text)
            VALUES (?, 'zh-CN', ?, 'full', ?)
        """, (max_trans_id, title, f"待翻译 {title}"))
        
        # 插入 document_classifications（默认为"相关文献"）
        cur.execute("""
            INSERT INTO document_classifications (document_id, grade, score, reason)
            VALUES (?, '相关文献', 50, 'archive.org 全文检索命中 Democratic League')
        """, (max_doc_id,))
        
        conn.commit()
        success += 1
        
        # 速率控制
        time.sleep(1)
    
    print(f"\n{'='*50}")
    print(f"完成！成功: {success} | 失败: {failed}")
    print(f"CIA 文档总数: {len(existing_keys) + success} 篇")
    
    conn.close()


if __name__ == "__main__":
    main()
